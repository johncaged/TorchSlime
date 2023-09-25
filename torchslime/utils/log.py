import logging
from logging import Formatter, Filter, Handler, LogRecord, StreamHandler, Logger
from rich.logging import RichHandler
from torchslime.components.store import StoreListener, store, StoreListen
from .launch import LaunchUtil, Launcher
from .typing import (
    NOTHING,
    is_none_or_nothing,
    Iterable,
    Union,
    NoneOrNothing,
    Pass,
    MISSING,
    Missing,
    Any
)
from .bases import BaseDict
from .decorators import Singleton
import sys


# initialize log template (if not specified)
if is_none_or_nothing(store.builtin__().log_template):
    store.builtin__().log_template = '{prefix__} - {asctime} - "{filename}:{lineno}" - {message}'

if is_none_or_nothing(store.builtin__().log_rich_template):
    store.builtin__().log_rich_template = '{message}'

if is_none_or_nothing(store.builtin__().log_dateformat):
    store.builtin__().log_dateformat = '%Y/%m/%d %H:%M:%S'

#
# Slime Logger
#

class SlimeLogger(Logger, Launcher, StoreListener):
    
    def __init__(
        self,
        launch: Union[str, LaunchUtil, Missing] = MISSING,
        exec_ranks: Union[Iterable[int], NoneOrNothing, Pass, Missing] = MISSING,
        *args,
        **kwargs
    ) -> None:
        if exec_ranks is MISSING:
            exec_ranks = [0]
        
        Logger.__init__(self, *args, **kwargs)
        Launcher.__init__(self, launch, exec_ranks)
        StoreListener.__init__(self)

    def addHandler(self, handler: Handler) -> None:
        if not handler.formatter:
            if isinstance(handler, RichHandler):
                handler.setFormatter(SlimeRichFormatter())
            else:
                handler.setFormatter(SlimeFormatter())
        super().addHandler(handler)

#
# Logger Func Arg Adapter
#

class LoggerKwargs(BaseDict[str, Any]):
    
    def __init__(self, **kwargs):
        # ``stacklevel`` argument was added after py3.8
        if sys.version_info < (3, 8):
            kwargs.pop('stacklevel', NOTHING)
        super().__init__(**kwargs)

#
# Slime Filter
#

class SlimeFilter(Filter):
    
    def filter(self, record: LogRecord) -> bool:
        record.prefix__ = f'[TorchSlime {record.levelname.upper()}]'
        record.rank__ = f'{logger.launch__.get_rank()}'
        return logger.is_exec__()

#
# Slime Formatters
#

class SlimeFormatter(Formatter):

    def __init__(self) -> None:
        super().__init__(
            store.builtin__().log_template,
            store.builtin__().log_dateformat,
            style='{'
        )

class SlimeRichFormatter(Formatter):
    
    def __init__(self) -> None:
        super().__init__(
            store.builtin__().log_rich_template,
            store.builtin__().log_dateformat,
            style='{'
        )

@Singleton
class SlimeFormatterListener(StoreListener):
    
    @StoreListen
    def log_template_listen__(self, new_value, old_value) -> None:
        for handler in logger.handlers:
            if isinstance(handler.formatter, SlimeFormatter):
                handler.setFormatter(SlimeFormatter())
    
    @StoreListen
    def log_rich_template_listen__(self, new_value, old_value) -> None:
        for handler in logger.handlers:
            if isinstance(handler.formatter, SlimeRichFormatter):
                handler.setFormatter((SlimeRichFormatter()))
    
    @StoreListen
    def log_dateformat_listen__(self, new_value, old_value) -> None:
        for handler in logger.handlers:
            if isinstance(handler.formatter, SlimeFormatter):
                handler.setFormatter(SlimeFormatter())
            if isinstance(handler.formatter, SlimeRichFormatter):
                handler.setFormatter((SlimeRichFormatter()))

slime_formatter_listener = SlimeFormatterListener()
# set ``init`` to False. ``logger`` instance has not been created here
store.builtin__().add_listener__(slime_formatter_listener, init=False)

#
# initialize logger
#

logger: SlimeLogger = SlimeLogger(name='builtin__', level=logging.INFO)
logger.propagate = False
logger.addFilter(SlimeFilter())
logger.addHandler(RichHandler())
