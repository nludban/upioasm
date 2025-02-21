from typing import List, Tuple, Optional, TYPE_CHECKING

from .error import PIOSyntaxError


class Defines:
    def __init__(self) -> None:
        self._tab: List[Tuple[str, Optional[int], bool]] = [ ]

    def __len__(self):
        return len(self._tab)

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

    def assign(self, key: str, value: int):
        for i, e in enumerate(self._tab):
            if e[0] == key:
                if e[1] is not None:
                    raise PIOSyntaxError('already assigned')
                self._tab[i] = ( e[0], value, e[2] )
                return
        raise PIOSyntaxError('not declared')

    def declare(self, key: str, public: bool):
        if key in self:
            raise PIOSyntaxError('already defined')
        self._tab.append(( key, None, public ))
        return

    def resolve(self, key: str) -> int:
        for e in self._tab:
            if e[0] == key:
                if e[1] is None:
                    raise PIOSyntaxError('value not assigned')
                return e[1]
        raise PIOSyntaxError('not defined')

    def copy(self, public: bool):
        c = Defines()
        for e in self._tab:
            if not public or e[2]:
                if e[1] is None:
                    raise PIOSyntaxError('value not assigned')
                c._tab.append(e)
        return c

#--#
