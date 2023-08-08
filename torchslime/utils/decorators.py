from functools import wraps
import multiprocessing
import threading
from typing import Any, Union
from types import FunctionType, MethodType
from torchslime.utils.bases import NOTHING, is_none_or_nothing, is_nothing
from torchslime.utils import get_exec_info, is_function_or_method

#
# ClassWraps decorator
#
FUNC_CREATED = ('__module__', '__name__', '__qualname__')

def _create_func(
    func: Union[FunctionType, MethodType],
    cls: type,
    name: str,
    created: Union[list, tuple]
):
    """
    Separately set function attributes.
    """
    # __module__ should be the same as cls
    if '__module__' in created and hasattr(cls, '__module__'):
        setattr(func, '__module__', getattr(cls, '__module__'))
    
    # __name__ should be set
    if '__name__' in created:
        setattr(func, '__name__', name)

    # __qualname__ should be 'cls_qualname.name'
    if '__qualname__' in created and hasattr(cls, '__qualname__'):
        setattr(func, '__qualname__', '{}.{}'.format(getattr(cls, '__qualname__'), name))
    return func

def ClassWraps(cls):
    if isinstance(cls, type) is False:
        from torchslime.components.exception import APIMisused
        raise APIMisused('ClassWraps can only be used for class, not {cls_item}.'.format(
            cls_item=str(cls)
        ))

    from functools import WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES

    class Decorator:

        def __getattribute__(self, __name: str) -> Any:
            __func = _get_function_or_method(cls, __name)
            cls_func = get_cls_func(cls, __name)
            super_func = get_super_func(cls, __name)

            def FuncWrapper(
                _func=NOTHING,
                *,
                assigned=WRAPPER_ASSIGNMENTS,
                updated=WRAPPER_UPDATES,
                created=FUNC_CREATED
            ):
                def wrapper(func):
                    if is_none_or_nothing(__func) is False:
                        func = wraps(__func, assigned=assigned, updated=updated)(func)
                    else:
                        func = _create_func(func=func, cls=cls, name=__name, created=created)
                    # set wrapper__ attribute to denote it is a func wrapper
                    func.wrapper__ = True
                    # set cls_func and super_func to func wrapper
                    func.cls_func__ = cls_func
                    func.super_func__ = super_func
                    # set func wrapper to cls
                    setattr(cls, __name, func)
                    return func
                
                if is_none_or_nothing(_func) is True:
                    return wrapper
                
                return wrapper(func=_func)
            
            # set cls_func__ and super_func__
            FuncWrapper.cls_func__ = cls_func
            FuncWrapper.super_func__ = super_func
            return FuncWrapper
    
    return Decorator()

def _get_function_or_method(cls: type, name: str):
    __item = cls.__dict__.get(name, NOTHING)
    return __item if is_function_or_method(__item) else NOTHING

def _get_func_from_mro(cls: type, name: str, start: int=0):
    # get attr from the super class
    for class__ in cls.__mro__[start:]:
        return getattr(class__, name, NOTHING)
    return NOTHING

def get_cls_func(cls: type, name: str):
    return _get_func_from_mro(cls, name, start=0)

def get_super_func(cls: type, name: str):
    return _get_func_from_mro(cls, name, start=1)

def get_original_cls_func(func):
    while getattr(func, 'wrapper__', False) is True and hasattr(func, 'cls_func__'):
        func = getattr(func, 'cls_func__')
    return func


def DecoratorCall(*, index=NOTHING, keyword=NOTHING):
    """
    [func-decorator]
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            arg_match = NOTHING

            if is_none_or_nothing(keyword) is False:
                arg_match = kwargs.get(str(keyword), NOTHING)
            
            if is_none_or_nothing(index) is False and is_none_or_nothing(arg_match) is True:
                arg_match = NOTHING if index >= len(args) else args[index]

            _decorator = func(*args, **kwargs)
            return _decorator if is_none_or_nothing(arg_match) is True else _decorator(arg_match)
        return wrapper
    return decorator


def Singleton(cls):
    """
    [class, level-1]
    Decorator that makes decorated classes singleton.
    It makes the creation of the singleton object thread-safe by using double-checked locking.
    """
    t_lock = threading.Lock()
    p_lock = multiprocessing.Lock()
    _instance = NOTHING

    cls_wraps = ClassWraps(cls)
    new_wraps = cls_wraps.__new__
    new_cls_func = new_wraps.cls_func__

    @new_wraps
    def _wrapper(*args, **kwargs):
        nonlocal _instance
        if is_none_or_nothing(_instance) is True:
            with t_lock, p_lock:
                if is_none_or_nothing(_instance) is True:
                    _instance = new_cls_func(*args, **kwargs)
        return _instance
    
    return cls


@DecoratorCall(index=0, keyword='_func')
def CallDebug(_func=NOTHING, *, module_name=NOTHING):
    """
    [func, level-2]
    A decorator that output debug information before and after a method is called.
    Args:
        func (_type_): _description_
    """
    def decorator(func):
        from torchslime.log import logger
        from torchslime.components.store import store
        from time import time

        func_id = '{_id}_{_time}'.format(
            _id=str(id(func)),
            _time=str(time())
        )

        nonlocal module_name

        if is_none_or_nothing(module_name) is True:
            module_name = getattr(func, '__name__', NOTHING)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # do not use debug
            if store.scope__('inner__').use_call_debug is not True:
                return func(*args, **kwargs)

            # cache debug info
            call_debug_cache = store.scope__('inner__').call_debug_cache
            _exec_info = call_debug_cache[func_id]
            if is_none_or_nothing(_exec_info) is True:
                _exec_info = get_exec_info(func)
                call_debug_cache[func_id] = _exec_info

            logger.debug('{} begins.'.format(module_name), _exec_info=_exec_info)
            result = func(*args, **kwargs)
            logger.debug('{} ends.'.format(module_name), _exec_info=_exec_info)
            return result
        return wrapper
    return decorator


def MethodChaining(func):
    """
    [func, level-1]
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        return self
    return wrapper


def Deprecated():
    """
    [func, level-1]
    """
    pass


@DecoratorCall(keyword='_cls')
def ReadonlyAttr(attrs: list, *, _cls=NOTHING, nothing_allowed: bool = True, empty_allowed: bool = True):
    """
    [class, level-2]
    """
    def decorator(cls):
        cls_wraps = ClassWraps(cls)
        setattr_wraps = cls_wraps.__setattr__
        setattr_cls_func = setattr_wraps.cls_func__

        @setattr_wraps
        def wrapper(self, __name: str, __value: Any):
            # directly set attr here for performance optimization
            if __name not in attrs:
                return setattr_cls_func(self, __name, __value)

            hasattr__ = hasattr(self, __name)
            attr__ = getattr(self, __name, None)

            if (hasattr__ is False and empty_allowed is True) or \
                    (is_nothing(attr__) is True and nothing_allowed is True):
                return setattr_cls_func(self, __name, __value)
            else:
                raise AttributeError('{name} is readonly attribute'.format(name=__name))
        
        return cls
    return decorator


@DecoratorCall(index=0, keyword='_cls')
def ItemAttrBinding(_cls=NOTHING, *, set_binding: bool = True, get_binding: bool = True, del_binding: bool = True):
    """
    [class]
    """
    def decorator(cls):
        cls_wraps = ClassWraps(cls)

        if set_binding is True:
            setitem_wraps = cls_wraps.__setitem__

            @setitem_wraps
            def setitem(self, __name: str, __value: Any) -> None:
                setattr(self, __name, __value)
        
        if get_binding is True:
            getitem_wraps = cls_wraps.__getitem__

            @getitem_wraps
            def getitem(self, __name: str) -> Any:
                return getattr(self, __name)
        
        if del_binding is True:
            delitem_wraps = cls_wraps.__delitem__

            @delitem_wraps
            def delitem(self, __name: str) -> None:
                delattr(self, __name)
        
        return cls

    return decorator


@DecoratorCall(index=0, keyword='_cls')
def ObjectAttrBinding(_cls=NOTHING, *, set_binding: bool = True, get_binding: bool = True, del_binding: bool = True):
    """
    [class]
    """
    def decorator(cls):
        cls_wraps = ClassWraps(cls)

        if set_binding is True:
            object_set_wraps = cls_wraps.object_set__

            @object_set_wraps
            def object_set(self, __name: str, __value: Any) -> None:
                object.__setattr__(self, __name, __value)
        
        if get_binding is True:
            object_get_wraps = cls_wraps.object_get__

            @object_get_wraps
            def object_get(self, __name: str) -> Any:
                return object.__getattribute__(self, __name)
        
        if del_binding is True:
            object_del_wraps = cls_wraps.object_del__

            @object_del_wraps
            def object_del(self, __name: str) -> None:
                object.__delattr__(self, __name)
        
        return cls

    return decorator