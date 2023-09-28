import traceback
from .meta import Meta
from .typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union,
    MutableSequence,
    MutableMapping,
    Iterable,
    Iterator,
    TypeVar,
    Generic,
    overload,
    SupportsIndex,
    Type,
    Generator,
    Callable,
    NOTHING,
    Nothing,
    NoneOrNothing,
    Pass,
    PASS,
    is_none_or_nothing,
    Set,
    Missing,
    MISSING
)
from functools import partial
from types import TracebackType
import re

# TypeVars
_T = TypeVar('_T')
_T1 = TypeVar('_T1')
_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

#
# Scoped Attribute
#

class ScopedAttr:
    
    def assign__(self, **kwargs) -> "ScopedAttrAssign":
        return ScopedAttrAssign.m__(self)(**kwargs)
    
    def restore__(self, *attrs: str) -> "ScopedAttrRestore":
        return ScopedAttrRestore.m__(self)(*attrs)

#
# Base
#

class Base(ScopedAttr):
    """
    Base class, making its subclasses be able to use '[]' operations(just like python dict).
    Return 'Nothing' if the object does not have the property being retrieved, without throwing Errors.
    What's more, it allows its subclasses assign properties using a dict.
    """

    def from_kwargs__(self, **kwargs):
        self.from_dict__(kwargs)

    def from_dict__(self, _dict: Dict):
        """assign properties to the object using a dict.
        Args:
            kwargs (Dict): property dict.
        """
        from . import dict_merge
        self.__dict__ = dict_merge(self.__dict__, _dict)

    def check__(self, item: str):
        """check whether the object has a specific attribute.
        dot operator supported.
        Args:
            items (str): _description_
        """
        attrs = item.split('.')
        temp = self
        for attr in attrs:
            try:
                temp = temp[attr]
                # if the value is NOTHING, then return False directly.
                if temp is NOTHING:
                    return False
            except Exception:
                # output error information
                self.process_exc__()
                return False
        return True

    def hasattr__(self, __name: str) -> bool:
        return str(__name) in self.__dict__

    @staticmethod
    def process_exc__():
        from torchslime.logging.logger import logger
        # output error
        logger.error(
            'Python exception raised:\n' +
            traceback.format_exc()
        )
        return NOTHING

    def pop__(self, __name: str):
        attr = getattr(self, __name)
        delattr(self, __name)
        return attr

    def __getattr__(self, *_):
        return NOTHING

    def __delattr__(self, __name: str) -> None:
        # safe delete
        try:
            return super().__delattr__(__name)
        except AttributeError:
            return

    def __getitem__(self, __name: str):
        return getattr(self, __name)

    def __setitem__(self, __name: str, __value: Any):
        return setattr(self, __name, __value)

    def __delitem__(self, __name: str):
        return delattr(self, __name)
    
    def __str__(self) -> str:
        from .common import dict_to_key_value_str
        classname=str(self.__class__.__name__)
        _id=str(hex(id(self)))
        _dict=dict_to_key_value_str(self.__dict__)
        return f'{classname}<{_id}>({_dict})'

#
# Base List
#

class BaseList(MutableSequence[_T], Generic[_T]):

    def __init__(
        self,
        __list_like: Union[Iterable[_T], NoneOrNothing] = None
    ):
        self.__list: List[_T] = []
        if not is_none_or_nothing(__list_like):
            # Use ``self.extend`` here to make the initialization process controllable.
            # Otherwise, if ``self.__list = list(__list_like)`` is used here, the initialization process won't be restricted by the user-defined operations.
            self.extend(__list_like)

    @classmethod
    def create__(
        cls,
        __list_like: Union[_T, Iterable[_T], NoneOrNothing, Pass] = None,
        *,
        strict = False,
        return_none: bool = True,
        return_nothing: bool = True,
        return_pass: bool = True
    ):
        # TODO: update document
        """
        If the ``list_like`` object is ``None``, ``NOTHING`` or ``...`` and the corresponding return config is True, then
        return itself, otherwise return ``BaseList`` object.
        WARNING: This changes the default behavior of ``BaseList``, which creates an empty list when the list_like object is 
        ``None`` or ``NOTHING`` and creates ``[...]`` when the list_like object is ``...``.
        """
        if (__list_like is NOTHING and return_nothing is True) or \
                (__list_like is None and return_none is True) or \
                (__list_like is PASS and return_pass is True):
            # return the item itself
            __list_like: Union[NoneOrNothing, Pass]
            return __list_like
        elif isinstance(__list_like, Iterable) or is_none_or_nothing(__list_like):
            return cls(__list_like)
        
        if strict:
            classname = type(__list_like).__name__
            raise TypeError(f'BaseList - ``strict`` is True and ``{classname}`` object is not iterable')
        else:
            return cls([__list_like])

    def set_list__(self, __list: List[_T]) -> None:
        self.__list = __list

    def get_list__(self) -> List[_T]:
        return self.__list
    
    @overload
    def __getitem__(self, __i: SupportsIndex) -> _T: pass
    @overload
    def __getitem__(self, __s: slice) -> List[_T]: pass
    @overload
    def __setitem__(self, __key: SupportsIndex, __value: _T) -> None: pass
    @overload
    def __setitem__(self, __key: slice, __value: Iterable[_T]) -> None: pass
    @overload
    def __delitem__(self, __key: Union[SupportsIndex, slice]) -> None: pass
    @overload
    def insert(self, __index: SupportsIndex, __object: _T) -> None: pass
    
    def __getitem__(self, __key):
        return self.__list[__key]
    
    def __setitem__(self, __key, __value):
        self.__list[__key] = __value
    
    def __delitem__(self, __key):
        del self.__list[__key]
    
    def __len__(self):
        return len(self.__list)
    
    def insert(self, __index, __object):
        return self.__list.insert(__index, __object)
    
    def __str__(self) -> str:
        classname=str(self.__class__.__name__)
        _id=str(hex(id(self)))
        _list=str(self.__list)
        return f'{classname}<{_id}>({_list})'

#
# Bidirectional List
#

class BiListItem:
    
    def __init__(self) -> None:
        self.__parent = NOTHING
    
    def set_parent__(self, parent) -> None:
        prev_parent = self.get_parent__()
        if not is_none_or_nothing(prev_parent) and parent is not prev_parent:
            # duplicate parent
            from torchslime.logging.logger import logger
            logger.warning(
                f'BiListItem ``{str(self)}`` has already had a parent, but another parent is set. '
                'This may be because you add a single BiListItem object to multiple BiLists '
                'and may cause some inconsistent problems.'
            )
        self.__parent = parent
    
    def get_parent__(self) -> Union["BiList", Nothing]:
        return self.__parent if hasattr(self, '_BiListItem__parent') else NOTHING
    
    def del_parent__(self):
        self.__parent = NOTHING


_T_BiListItem = TypeVar('_T_BiListItem', bound=BiListItem)

class BiList(BaseList[_T_BiListItem]):
    
    def set_list__(self, __list: List[_T_BiListItem]) -> None:
        prev_list = self.get_list__()
        
        for prev_item in prev_list:
            prev_item.del_parent__()
        
        for item in __list:
            item.set_parent__(self)
        
        return super().set_list__(__list)

    @overload
    def __setitem__(self, __key: SupportsIndex, __value: _T_BiListItem) -> None: pass
    @overload
    def __setitem__(self, __key: slice, __value: Iterable[_T_BiListItem]) -> None: pass
    
    def __setitem__(
        self,
        __key: Union[SupportsIndex, slice],
        __value: Union[_T_BiListItem, Iterable[_T_BiListItem]]
    ) -> None:
        # delete parents of the replaced items and set parents to the replacing items
        if isinstance(__key, slice):
            for replaced_item in self[__key]:
                replaced_item.del_parent__()
            
            for item in __value:
                item: _T_BiListItem
                item.set_parent__(self)
        else:
            self[__key].del_parent__()
            __value: _T_BiListItem
            __value.set_parent__(self)
        return super().__setitem__(__key, __value)
    
    @overload
    def __delitem__(self, __key: SupportsIndex) -> None: pass
    @overload
    def __delitem__(self, __key: slice) -> None: pass
    
    def __delitem__(self, __key: Union[SupportsIndex, slice]) -> None:
        if isinstance(__key, slice):
            for item in self[__key]:
                item.del_parent__()
        else:
            self[__key].del_parent__()
        return super().__delitem__(__key)
    
    def insert(self, __index: SupportsIndex, __item: _T_BiListItem) -> None:
        __item.set_parent__(self)
        return super().insert(__index, __item)

#
# Base Dict
#

class BaseDict(MutableMapping[_KT, _VT], Generic[_KT, _VT]):

    def __init__(
        self,
        __dict_like: Union[Dict[_KT, _VT], Iterable[Tuple[_KT, _VT]], NoneOrNothing] = None,
        **kwargs
    ):
        self.__dict: Dict[_KT, _VT] = {}
        if is_none_or_nothing(__dict_like):
            __dict_like = {}
        # Use ``self.update`` here to make the initialization process controllable.
        # Otherwise, if ``self.__dict = dict(__dict_like, **kwargs)`` is used here, the initialization process won't be restricted by the user-defined operations.
        self.update(__dict_like, **kwargs)

    def set_dict__(self, __dict: Dict[_KT, _VT]) -> None:
        self.__dict = __dict

    def get_dict__(self) -> Dict[_KT, _VT]:
        return self.__dict
    
    @overload
    def __getitem__(self, __key: _KT) -> _VT: pass
    @overload
    def __setitem__(self, __key: _KT, __value: _VT) -> None: pass
    @overload
    def __delitem__(self, __key: _KT) -> None: pass
    @overload
    def __iter__(self) -> Iterator[_KT]: pass
    @overload
    def __len__(self) -> int: pass
    
    def __getitem__(self, __key):
        return self.__dict[__key]
    
    def __setitem__(self, __key, __value):
        self.__dict[__key] = __value
    
    def __delitem__(self, __key):
        del self.__dict[__key]
    
    def __iter__(self):
        return iter(self.__dict)
    
    def __len__(self):
        return len(self.__dict)
    
    def __str__(self) -> str:
        classname=str(self.__class__.__name__)
        _id=str(hex(id(self)))
        _dict=str(self.__dict)
        return f'{classname}<{_id}>({_dict})'


# Type Vars
_YieldT_co = TypeVar('_YieldT_co', covariant=True)
_SendT_contra = TypeVar('_SendT_contra', contravariant=True)
_ReturnT_co = TypeVar('_ReturnT_co', covariant=True)

class BaseGenerator(
    Generator[_YieldT_co, _SendT_contra, _ReturnT_co],
    Generic[_YieldT_co, _SendT_contra, _ReturnT_co]
):

    def __init__(
        self,
        __gen: Generator[_YieldT_co, _SendT_contra, _ReturnT_co],
        *,
        exit_allowed: bool = True
    ) -> None:
        if not isinstance(__gen, Generator):
            raise TypeError(f'Argument ``__gen`` should be a generator.')
        self.gen = __gen
        self.exit_allowed = exit_allowed
        
        self.exit = False

    def __call__(self) -> Any:
        return next(self)

    def send(self, __value: _SendT_contra) -> _YieldT_co:
        return self.call__(partial(self.gen.send, __value))

    @overload
    def throw(
        self,
        __typ: Type[BaseException],
        __val: Union[BaseException, object] = None,
        __tb: Union[TracebackType, None] = None
    ) -> _YieldT_co: pass
    @overload
    def throw(
        self,
        __typ: BaseException,
        __val: None = None,
        __tb: Union[TracebackType, None] = None
    ) -> _YieldT_co: pass

    def throw(self, __typ, __val=None, __tb=None) -> _YieldT_co:
        return self.call__(partial(self.gen.throw, __typ, __val, __tb))

    def call__(self, __caller: Callable[[], _T]) -> Union[_T, Nothing]:
        if self.exit and not self.exit_allowed:
            from torchslime.components.exception import APIMisused
            raise APIMisused('``exit_allowed`` is set to False, and the generator already stopped but you still try to call ``next``.')
        elif self.exit:
            return NOTHING

        try:
            return __caller()
        except (StopIteration, GeneratorExit):
            self.exit = True

#
# Composite Structure
#

class CompositeStructure:
    
    def composite_iterable__(self) -> Union[Iterable["CompositeStructure"], Nothing]: pass


_T_CompositeStructure = TypeVar('_T_CompositeStructure', bound=CompositeStructure)

def CompositeDFT(
    __item: _T_CompositeStructure,
    __func: Callable[[_T_CompositeStructure], None]
) -> None:
    from queue import LifoQueue
    q = LifoQueue()
    
    q.put((__item, MISSING))
    while q.qsize() > 0:
        item: Tuple[_T_CompositeStructure, Union[Iterator[_T_CompositeStructure], Nothing, Missing]] = q.get()
        searcher, iterator = item
    
        if iterator is MISSING:
            # create children iterator
            iterator = iter(searcher.composite_iterable__())
            # visit the parent node
            __func(searcher)
        
        try:
            child = next(iterator)
        except StopIteration:
            continue
        # put the parent and the corresponding children
        q.put((searcher, iterator))
        q.put((child, MISSING))


def CompositeDFS(
    __item: _T_CompositeStructure,
    __func: Callable[[_T_CompositeStructure], bool]
) -> List[_T_CompositeStructure]:
    results = []
    
    def _search(item):
        if __func(item):
            results.append(item)
    
    CompositeDFT(__item, _search)
    return results

#
# Attr Proxy
#

class AttrProxy(Generic[_T]):
    
    def __init__(
        self,
        __obj: _T,
        __attrs: List[str]
    ) -> None:
        super().__init__()
        self.obj__ = __obj
        self.attrs__ = __attrs
    
    def __getattribute__(self, __name: str) -> Any:
        if __name in ['obj__', 'attrs__']:
            return super().__getattribute__(__name)
        # attr proxy
        if __name in self.attrs__:
            return getattr(self.obj__, __name)
        return super().__getattribute__(__name)

#
# Attr Observer
#

OBSERVE_FUNC_SUFFIX = '_observe__'
OBSERVE_FUNC_SUFFIX_PATTERN = re.compile(f'{OBSERVE_FUNC_SUFFIX}$')
OBSERVE_FLAG = 'attr_observe__'

class AttrObserver:
    
    def observe_inspect__(self) -> Set[str]:
        return set(
            map(
                # get the real observed attribute name
                lambda name: OBSERVE_FUNC_SUFFIX_PATTERN.sub('', name),
                filter(
                    # filter out attr observe function
                    lambda name: OBSERVE_FUNC_SUFFIX_PATTERN.search(name) is not None and getattr(getattr(self, name), OBSERVE_FLAG, NOTHING),
                    dir(self)
                )
            )
        )


class AttrObservable:
    
    def __init__(self) -> None:
        # attr name to observers
        self.__observe: Dict[str, List[AttrObserver]] = {}
        # observer id to observe attr names
        self.__observe_attrs: Dict[str, Set[str]] = {}
    
    def attach__(self, __observer: AttrObserver, *, init: bool = True) -> None:
        observer_id = self.get_observer_id__(__observer)
        names = __observer.observe_inspect__()
        
        if observer_id in self.__observe_attrs:
            # inspect new observe attrs
            # use a copy of observe attrs to avoid value change during iteration
            names = names - set(self.__observe_attrs[observer_id])
        
        for name in names:
            self.attach_attr__(__observer, name, init=init)
    
    def attach_attr__(self, __observer: AttrObserver, __name: str, *, init: bool = True):
        observer_id = self.get_observer_id__(__observer)
        if observer_id not in self.__observe_attrs:
            self.__observe_attrs[observer_id] = set()
        
        if __name not in self.__observe:
            self.__observe[__name] = []
        
        self.__observe_attrs[observer_id].add(__name)
        self.__observe[__name].append(__observer)
        
        if init:
            value = getattr(self, __name, NOTHING)
            self.notify__(__observer, __name, value, NOTHING)
    
    def detach__(self, __observer: AttrObserver) -> None:
        observer_id = self.get_observer_id__(__observer)
        if observer_id not in self.__observe_attrs:
            return
        
        # use a copy of observe attrs to avoid value change during iteration
        for name in list(self.__observe_attrs[observer_id]):
            self.detach_attr__(__observer, name)
    
    def detach_attr__(self, __observer: AttrObserver, __name: str) -> None:
        observer_id = self.get_observer_id__(__observer)
        if observer_id in self.__observe_attrs:
            names = self.__observe_attrs[observer_id]
            if __name in names:
                names.remove(__name)
            if len(names) < 1:
                del self.__observe_attrs[observer_id]

        if __name in self.__observe:
            observers = self.__observe[__name]
            if __observer in observers:
                observers.remove(__observer)
            if len(observers) < 1:
                del self.__observe[__name]
    
    def notify__(self, __observer: AttrObserver, __name: str, __new_value: Any, __old_value: Any) -> None:
        func: Callable[[Any, Any], None] = getattr(__observer, f'{__name}{OBSERVE_FUNC_SUFFIX}')
        return func(__new_value, __old_value)
    
    @staticmethod
    def get_observer_id__(__observer: AttrObserver) -> str:
        # this behavior may change through different torchslime versions
        return str(id(__observer))
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name not in self.__observe:
            return super().__setattr__(__name, __value)
        else:
            old_value = getattr(self, __name, NOTHING)
            super().__setattr__(__name, __value)
            # observer is called only when the new value is different from the old value
            if __value is not old_value:
                for observer in self.__observe[__name]:
                    self.notify__(observer, __name, __value, old_value)


from .decorators import ContextDecoratorBinding, DecoratorCall, RemoveOverload

@overload
def AttrObserve(_func: NoneOrNothing = NOTHING, *, flag: bool = True) -> Callable[[_T], _T]: pass
@overload
def AttrObserve(_func: _T, *, flag: bool = True) -> _T: pass

@DecoratorCall(index=0, keyword='_func')
def AttrObserve(_func=NOTHING, *, flag: bool = True):
    def decorator(func: _T) -> _T:
        try:
            setattr(func, OBSERVE_FLAG, flag)
        except Exception:
            from torchslime.logging.logger import logger
            logger.warning(f'Set ``{OBSERVE_FLAG}`` attribute failed. Observe object: {str(func)}. Please make sure it supports attribute set.')
        return func
    return decorator

#
# Scoped Attr Utils
#

@ContextDecoratorBinding
@RemoveOverload(checklist=[
    'm__',
    '__call__'
])
class ScopedAttrRestore(Meta, Generic[_T], directly_new_allowed=False):

    def __init__(self, *attrs: str) -> None:
        self.attrs: Tuple[str, ...] = attrs
        self.prev_value_dict: Dict[str, Any] = {}

    def m_init__(
        self,
        obj: _T,
        restore: bool = True
    ) -> None:
        self.obj: _T = obj
        self.restore = restore

    @overload
    @classmethod
    def m__(
        cls: Type[_T1],
        obj: Any,
        restore: bool = True
    ) -> Type[_T1]: pass

    # just for type hint
    @overload
    def __call__(self, func: _T1) -> _T1: pass

    def __enter__(self) -> "ScopedAttrRestore":
        for attr in self.attrs:
            self.prev_value_dict[attr] = getattr(self.obj, attr, NOTHING)
        return self

    def __exit__(self, *args, **kwargs):
        if self.restore:
            for attr, value in self.prev_value_dict.items():
                try:
                    setattr(self.obj, attr, value)
                except Exception as e:
                    from torchslime.logging.logger import logger
                    logger.error(f'Restoring scoped attribute failed. Object: {str(self.obj)}, attribute: {attr}. {str(e.__class__.__name__)}: {str(e)}')


@RemoveOverload(checklist=['m__'])
class ScopedAttrAssign(ScopedAttrRestore[_T]):

    def __init__(self, **kwargs) -> None:
        super().__init__(*kwargs.keys())
        self.attr_dict: Dict[str, Any] = kwargs

    def __enter__(self) -> "ScopedAttrAssign":
        # backup previous values
        super().__enter__()
        for attr, value in self.attr_dict.items():
            try:
                setattr(self.obj, attr, value)
            except Exception as e:
                from torchslime.logging.logger import logger
                logger.error(f'Assigning scoped attribute failed. Object: {str(self.obj)}, attribute: {attr}. {str(e.__class__.__name__)}: {str(e)}')
