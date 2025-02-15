from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .defines import Defines

from .emitter import InstructionVisitor

Symbol = str
Value = Union[int, Symbol]


class ResolverVisitor(InstructionVisitor):
    """Wedge converting symbols to numbers"""

    def __init__(self, pdefs: Defines, nextv: InstructionVisitor):
        self._pdefs = pdefs
        self._nextv = nextv
        return

    def _resolve(self, x: Value) -> int:
        # maybe eval (expression) here?
        # A `Label` converts to a `str`.
        return x if isinstance(x, int) else self._pdefs.resolve(str(x))

    def side(self, side: Value) -> InstructionVisitor:
        self._nextv.side(self._resolve(side))
        return self

    def delay(self, delay: Value) -> InstructionVisitor:
        self._nextv.delay(self._resolve(delay))
        return self

    def jmp(self, cond: str, addr: Value) -> InstructionVisitor:
        self._nextv.jmp(cond, self._resolve(addr))
        return self

    def wait(self, pol: Value, source: str, index: Value, *, rel=False) -> InstructionVisitor:
        self._nextv.wait(self._resolve(pol), source, self._resolve(index), rel=rel)
        return self

    def in_(self, source: str, count: Value) -> InstructionVisitor:
        self._nextv.in_(source, self._resolve(count))
        return self

    def out(self, dest: str, count: Value) -> InstructionVisitor:
        self._nextv.out(dest, self._resolve(count))
        return self

    def push(self, *, iffull: bool=False, block: bool=True) -> InstructionVisitor:
        self._nextv.push(iffull=iffull, block=block)
        return self

    def pull(self, *, ifempty: bool=False, block: bool=True) -> InstructionVisitor:
        self._nextv.pull(ifempty=ifempty, block=block)
        return self

    def mov(self, dest: str, op: str, source: str='') -> InstructionVisitor:
        self._nextv.mov(dest, op, source)
        return self

    def irq(self, irq_num: Value, *, rel=False, clear=False, wait=False) -> InstructionVisitor:
        self._nextv.irq(self._resolve(irq_num), rel=rel, clear=clear, wait=wait)
        return self

    def set(self, dest: str, data: Value) -> InstructionVisitor:
        self._nextv.set(dest, self._resolve(data))
        return self

    def nop(self) -> InstructionVisitor:
        self._nextv.nop()
        return self

#--#
