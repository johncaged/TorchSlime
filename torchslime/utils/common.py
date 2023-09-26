from textwrap import indent
from .typing import (
    NOTHING,
    Mapping,
    NoneOrNothing,
    Sequence,
    Union,
    is_none_or_nothing
)

#
# dict and list formatter
#

def dict_to_key_value_str_list(
    __dict: Mapping,
    key_value_sep: str = '='
) -> list:
    return [f'{key}{key_value_sep}{value}' for key, value in __dict.items()]

def dict_to_key_value_str(
    __dict: Mapping,
    key_value_sep: str = '=',
    str_sep: str = ', '
) -> str:
    return str_sep.join(dict_to_key_value_str_list(__dict, key_value_sep=key_value_sep))

def concat_format(
    __left: str,
    __content: Sequence[str],
    __right: str,
    *,
    item_sep: str = ',',
    indent_prefix: Union[str, NoneOrNothing] = NOTHING,
    break_line: bool = True
) -> str:
    if len(__content) < 1:
        # empty content: simply concat ``__left`` and ``__right``
        return __left + __right

    break_line_sep = '\n'
    if not break_line:
        indent_prefix = ''
    elif is_none_or_nothing(indent_prefix):
        from torchslime.components.store import store
        indent_prefix: str = store.builtin__().indent_str
    # format content
    content_sep = item_sep + (break_line_sep if break_line else '')
    __content = indent(content_sep.join(__content), prefix=indent_prefix)
    # format concat
    concat_sep = break_line_sep if break_line else ''
    return concat_sep.join([__left, __content, __right])
