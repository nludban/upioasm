from typing import List, Tuple, TYPE_CHECKING

from .error import PIOSyntaxError


class Defines:
    def __init__(self) -> None:
        self._tab: List[Tuple[str, int, bool]] = [ ]

    def __contains__(self, key: str):
        for e in self._tab:
            if e[0] == key:
                return True
        return False

    def define(self, key: str, value: int, public: bool):
        if key in self:
            raise PIOSyntaxError('already defined')
        self._tab.append(( key, value, public ))
        return

    def resolve(self, key: str) -> int:
        for e in self._tab:
            if e[0] == key:
                return e[1]
        raise PIOSyntaxError('not defined')

    def copy(self, public: bool):
        c = Defines()
        for e in self._tab:
            if not public or e[2]:
                c._tab.append(e)
        return c

#--#
