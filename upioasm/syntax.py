# rp2.pio.syntax

from typing import Any, Callable, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .assembler import PIOAssembler

from .emitter import InstructionVisitor
from .registers import *

_asm: PIOAssembler # = None

Symbol = str
Value = Union[int, Symbol]


class Label:
    """Label - supports indentation in py source

    jmp('L30')  # forward ref

    L10 = label('L10')
    jmp(L10)

    if label('L20'):
        jmp.not_x('L20')

    with label('L30'):
        jmp.y_dec('L30')

    if L40 := label('L40'):
        jmp.x_not_y(L40)

    with (L50 := label('L50')):
        jmp(L50)
    """

    def __init__(self, name: str, callback: Callable[['Label'], None]):
        self._name = name
        self._callback = callback

    def __str__(self) -> str:
        return self._name

    def __bool__(self):
        self._callback(self)
        return True

    def __enter__(self):
        self._callback(self)
        return self

    def __exit__(self, t, v, tb):
        pass


# 3.3.1 Directives

def dot_define(symbol: str, value: Value, *, public: bool=False):
    """.define (public) <symbol> <value>"""
    return _asm.define(symbol, value, public)

def dot_origin(offset: Value):
    """.origin <offset>"""
    return _asm.origin(offset)

def dot_side_set(count: int, *, opt=True, pindirs=False):
    """.side_set <count> (opt) (pindirs)"""
    return _asm.side_set(count, opt, pindirs)

def dot_wrap_target():
    """.wrap_target"""
    return _asm.wrap_target()

def dot_wrap():
    """.wrap"""
    return _asm.wrap()

#def dot_lang_opt(): pass

def dot_word(value: Value):
    """.word <value>"""
    return _asm.word(value)

#def dot_pio_version(): pass

#def dot_clock_div(): pass

#def dot_fifo():
    
def dot_mov_status():
    """.mov_status txfifo|rxfifo < <count>"""
    pass

#def dot_set(): pass -> set_set_count
#def dot_out(): pass -> set_out (pin count) right, autop, threshold
#def dot_in(): pass -> set_in (pin count) right, autop, threshold

#--------------------------------------------------#

def label(symbol: str='', *, public=False, forward=False):
    return _asm.label(symbol, public=public, forward=forward)

#--------------------------------------------------#

class Instruction:
    _delay: Value|None = None
    _side: Value|None = None
    _name = '-setme-'

    def __init__(self) -> None:
        _asm.append(self)
        return

    def side(self, value: Value):
        self._side = value
        return self

    def delay(self, count: Value):
        self._delay = count
        return self

    def __getitem__(self, count: Value):
        return self.delay(count)

    def visit(self, v: InstructionVisitor) -> None:
        if self._delay is not None:
            v.delay(self._delay)
        if self._side is not None:
            v.side(self._side)


class _jmp(Instruction):
    _name = 'jmp'
    _cond = 'always'

    def __init__(self, target: Union[Label, Value]):
        if isinstance(target, Label):
            target = str(target)
        self._target = target
        super().__init__()

    def visit(self, v: InstructionVisitor):
        v.jmp('' if self._cond == 'always' else self._cond, self._target)
        super().visit(v)


class jmp(_jmp):
    """jmp <target>"""

    class not_x(_jmp):
        """jmp !x <target>"""
        _cond = '!x'

    class x_dec(_jmp):
        """jmp x--, <target>"""
        _cond = 'x--'

    class not_y(_jmp):
        """jmp !y, <target>"""
        _cond = '!y'

    class y_dec(_jmp):
        """jmp y--, <target>"""
        _cond = 'y--'

    class x_not_y(_jmp):
        """jmp x!=y, <target>"""
        _cond = 'x!=y'

    class pin(_jmp):
        """jmp pin, <target>"""
        _cond = 'pin'

    class not_osre(_jmp):
        """jmp !osre, <target>"""
        _cond = '!osre'


class wait(Instruction):
    _name = 'wait'
    _rel = False

    def __init__(self, pol: int):
        self._pol = pol
        self._source = '?'
        super().__init__()

    def gpio(self, gpio_num: int):
        self._source = 'gpio'
        self._index = gpio_num

    def pin(self, pin_num: int):
        self._source = 'gpio'
        self._index = pin_num

    def irq(self, irq_num: int, *, rel=False):
        self._source = 'gpio'
        self._index = irq_num
        self._rel = rel

    def visit(self, v: InstructionVisitor):
        v.wait(self._pol, self._source, self._index, rel=self._rel)
        super().visit(v)


class in_(Instruction):
    """in <source>, <bit_count>"""
    _name = 'in'
    def __init__(self, source: InSourceReg, bit_count: int):
        self._source = source
        self._count = bit_count
        super().__init__()

    def visit(self, v: InstructionVisitor):
        v.in_(self._source._name, self._count)
        super().visit(v)


class out(Instruction):
    """out <destination>, <bit_count>"""
    _name = 'out'
    def __init__(self, dest: OutDestReg, bit_count: int):
        self._dest = dest
        self._count = bit_count
        super().__init__()

    def visit(self, v: InstructionVisitor):
        v.out(self._dest._name, self._count)
        super().visit(v)


class push(Instruction):
    """push (iffull) (block|noblock)"""
    _name = 'push'

    def __init__(self, *, iffull=False, block=True):
        self._iffull = iffull
        self._block = block
        super().__init__()

    def visit(self, v: InstructionVisitor):
        v.push(iffull=self._iffull, block=self._block)
        super().visit(v)


class pull(Instruction):
    """pull (ifempty) (block|noblock)"""
    _name = 'pull'

    def __init__(self, *, ifempty=False, block=True):
        self._ifempty = ifempty
        self._block = block
        super().__init__()

    def visit(self, v: InstructionVisitor):
        v.pull(ifempty=self._ifempty, block=self._block)
        super().visit(v)


class mov(Instruction):
    """mov <destination>, (op) <source>"""
    _name = 'mov'

    def __init__(self, dest: MovDestReg, source: MovSourceReg):
        self._dest = dest
        self._source = source
        super().__init__()

    def visit(self, v: InstructionVisitor):
        v.mov(self._dest._name, self._source._name)
        super().visit(v)


class _irq(Instruction):
    _name = 'irq'
    _clear = False
    _wait = True

    def __init__(self, irq_num: int, *, rel=False):
        self._index = irq_num
        self._rel = rel
        super().__init__()

    def visit(self, v: InstructionVisitor):
        v.irq(self._index, rel=self._rel, clear=self._clear, wait=self._wait)
        super().visit(v)


class irq(_irq):
    """irq <irq_num> (rel) ;; same as irq.set"""

    class set(_irq):
        """irq set <irq_num> (rel) ;; set irq flag, nowait"""

    class nowait(_irq):
        """irq nowait <irq_num> (rel) ;; same as irq.set"""

    class wait(_irq):
        """irq wait <irq_num> (rel) ;; set irq flag, wait for it to clear"""
        _wait = True

    class clear(_irq):
        """irq clear <irq_num> (rel) ;; clear irq flag"""
        _clear = True


class set(Instruction):
    """set <destination>, <value>"""
    _name = 'set'

    def __init__(self, dest: SetDestReg, data: Value):
        self._dest = dest
        self._data = data
        super().__init__()

    def visit(self, v: InstructionVisitor):
        v.set(self._dest._name, self._data)
        super().visit(v)


class nop(Instruction):
    """nop ;; same as mov y, y"""
    _name = 'nop'

    def visit(self, v: InstructionVisitor):
        v.nop()
        super().visit(v)

#--#
