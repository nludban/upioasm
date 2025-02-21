from typing import Iterator, Union

from .emitter import InstructionVisitor

Symbol = str
Value = Union[Symbol, int]


class LabelsVisitor(InstructionVisitor):
    """Extract the jmp targets"""

    def __init__(self) -> None:
        self._targets: list[Value] = [ ]

    def get_jmp_addrs(self) -> list[Value]:
        return self._targets

    def jmp(self, cond: str, addr: Value) -> InstructionVisitor:
        self._targets.append(addr)
        return self

#--#
