from typing import Iterator, Union

from .emitter import InstructionVisitor

Symbol = str
Value = Union[Symbol, int]


class AssemblerVisitor(InstructionVisitor):
    """Transpiles instructions to py source"""

    def __init__(self) -> None:
        self._lines: list[str] = [ ]

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)

    def side(self, side: Value) -> InstructionVisitor:
        self._lines[-1] += f'.side({side})'
        return self

    def delay(self, delay: Value) -> InstructionVisitor:
        self._lines[-1] += f'[{delay}]'
        return self

    def jmp(self, cond: str, addr: Value) -> InstructionVisitor:
        self._lines.append(f'v.jmp({cond}, {addr})')
        return self

    def wait(self, pol: Value, source: str, index: Value, *, rel=False) -> InstructionVisitor:
        self._lines.append(f'v.wait({pol}, {source}, {index}, {rel=}')
        return self

    def in_(self, source: str, count: Value) -> InstructionVisitor:
        self._lines.append(f'v.in_({source}, {count})')
        return self

    def out(self, dest: str, count: Value) -> InstructionVisitor:
        self._lines.append(f'v.out({dest}, {count})')
        return self

    def push(self, *, iffull: bool=False, block: bool=True) -> InstructionVisitor:
        self._lines.append(f'v.push({iffull=}, {block=})')
        return self

    def pull(self, *, ifempty: bool=False, block: bool=True) -> InstructionVisitor:
        self._lines.append(f'v.pull({ifempty=}, {block=})')
        return self

    def mov(self, dest: str, op: str, source: str='') -> InstructionVisitor:
        self._lines.append(f'v.mov({dest}, {op}{source})')
        return self

    def irq(self, irq_num: Value, *, rel=False, clear=False, wait=False) -> InstructionVisitor:
        self._lines.append(f'v.irq({irq_num}, {rel=}, {clear=}, {wait=})')
        return self

    def set(self, dest: str, data: Value) -> InstructionVisitor:
        self._lines.append(f'v.set({dest}, {data})')
        return self

    def nop(self) -> InstructionVisitor:
        self._lines.append('nop')
        return self

#--#
