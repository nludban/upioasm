from typing import List, Union, TYPE_CHECKING

from . import opcodes
from .error import PIOSyntaxError

from array import array

Symbol = str
Value = Union[Symbol, int]


# @no_type_check -- does nothing???
class InstructionVisitor:  # Maybe use ABC here

    def side(self, side: Value) -> 'InstructionVisitor': return self
    def delay(self, delay: Value) -> 'InstructionVisitor': return self
    def jmp(self, cond: str, addr: Value) -> 'InstructionVisitor': return self
    def wait(self, pol: Value, source: str, index: Value, *, rel=False) -> 'InstructionVisitor': return self
    def in_(self, source: str, count: Value) -> 'InstructionVisitor': return self
    def out(self, dest: str, count: Value) -> 'InstructionVisitor': return self
    def push(self, *, iffull: bool=False, block: bool=True) -> 'InstructionVisitor': return self
    def pull(self, *, ifempty: bool=False, block: bool=True) -> 'InstructionVisitor': return self
    def mov(self, dest: str, op: str, source: str='') -> 'InstructionVisitor': return self
    def irq(self, irq_num: Value, *, rel=False, clear=False, wait=False) -> 'InstructionVisitor': return self
    def set(self, dest: str, data: Value) -> 'InstructionVisitor': return self
    def nop(self) -> 'InstructionVisitor': return self


class PIOEmitter(InstructionVisitor):

    def __init__(self, sideset_count: int=0, side_en: bool=False):
        """PIOEmitter - generates machine opcodes

        sideset_count: 0..5 bits for side-set pins
        side_en: steal one bit for per-instruction side-set enable

        Note per-instruction delay width is (5 - sideset_count) bits.

        Run-time checking is limited to keeping bits in their assigned
        positions.
        """
        self._out = array('H')
        self._delay_count = 5 - sideset_count
        self._sideset_count = sideset_count
        if (sideset_count < 0
            or sideset_count > 5
            or side_en and sideset_count < 2
        ):
            raise PIOSyntaxError('invalid side-set count / en')
        self._side_en = int(bool(side_en))
        return

    def _resolve_value(self, value: Value, where: str) -> int:
        if not isinstance(value, (int, bool)):
            raise PIOSyntaxError(where + f': invalid type {value=}')
        return int(value)

    def _check_pin_count(self, value: Value, where: str):
        count = self._resolve_value(value, where)
        if count < 1 or count > 32:
            raise PIOSyntaxError(where + ": must be in range 1..32")
        return count & 31  # Note 32 truncates to 0.

    def _check_1_bit(self, value: Value, where: str):
        value = self._resolve_value(value, where)
        if value < 0 or value > 1:
            raise PIOSyntaxError(where + ": must be in range 0..1")
        return value

    def _check_5_bits(self, value: Value, where: str):
        value = self._resolve_value(value, where)
        if value < -16 or value > 31:
            raise PIOSyntaxError(where + ": must be in range -16..31")
        return value & 31

    def _check_16_bits(self, value: Value, where: str):
        value = self._resolve_value(value, where)
        if value < -32768 or value > 65535:
            raise PIOSyntaxError(where + ": must be in range -32768..65535")
        return value & 0xffff

    def _emit(self, op, *other):
        code = op
        for o in other:
            code |= o
        self._out.append(code)
        return self

    def _get(self, tab, key, where):
        val = tab.get(key)
        if val is None:
            raise PIOSyntaxError(where + ': invalid key')
        return val

    def get_array(self):
        return self._out

    def side(self, side: Value):
        """add a side-set value to the last instruction"""
        ss = self._resolve_value(side, 'side-set')
        if not (0 < ss < (1 << (self._sideset_count + self._side_en))):
            raise PIOSyntaxError('side-set count exceeded')
        if self._side_en:
            ss |= (16 >> self._delay_count)
        self._out[-1] |= (ss << 8)
        return self

    def delay(self, delay: Value):
        """add a delay to the last instruction"""
        nd = self._check_5_bits(delay, 'delay')
        if not (0 < nd < (1 << self._delay_count)):
            raise PIOSyntaxError('delay count exceeded')
        nd <<= self._sideset_count
        self._out[-1] |= (nd << 8)
        return self

    def jmp(self, cond: str, addr: Value):
        """jmp <cond> <addr>

        <cond> = ''|always|!x|x--|!y|y--|x!=y|pin|!osre
        <addr> = target address 0..31
        """
        # 0b000 delay/side:5 cond:3 addr:5
        return self._emit(
            opcodes.op_jmp,
            self._get(opcodes.jmp_cond, cond, '<cond>'),
            self._check_5_bits(addr, '<addr>'),
        )

    def wait(self, pol: Value, source: str, index: Value, *, rel=False):
        """wait <pol> <source> <index> (rel)

        <pol> = 0 or 1
        <source> = gpio|pin|irq
        <index> = 0..31
        rel = True when <source>=irq and add SM index to <index>
        """
        # 0b001 delay/side:5 pol:1 source:2 index:5
        return self._emit(
            opcodes.op_wait,
            self._check_1_bit(pol, '<pol>') << 7,
            self._get(opcodes.wait_source, source, '<source>'),
            self._check_5_bits(index, '<index>'),
        )

    def in_(self, source: str, count: Value):
        """in <source> <bit-count>

        <source> = pins|x|y|null|isr|osr
        <count> = number of bits, 1..32
        """
	# 0b010 delay/side:5 src:3 nbits:5
        return self._emit(
            opcodes.op_in,
            self._get(opcodes.in_source, source, '<source>'),
            self._check_pin_count(count, '<count>'),
        )

    def out(self, dest: str, count: Value):
        """out <dest> <count>

        <dest> = pins|x|y|null|pindirs|pc|isr|osr
        <count> = number of bits, 1..32
        """
	# 0b011 delay/side:5 dst:3 nbits:5
        return self._emit(
            opcodes.op_out,
            self._get(opcodes.out_dest, dest, '<dest>'),
            self._check_pin_count(count, '<count>'),
        )

    def push(self, *, iffull: bool=False, block: bool=True):
        """push (iffull) (block|noblock)

        iffull = True for `push iffull (block|noblock)`
        block = True for `push (iffull) (block)`
        """
	# 0b100 delay/side:5 0b0 ifF:1 Blk:1 0b00000
        return self._emit(
            opcodes.op_push,
            opcodes.push_iff if iffull else 0,
            opcodes.push_blk if block else 0,
        )

    def pull(self, *, ifempty: bool=False, block: bool=True):
        """pull (ifempty) (block|noblock)

        ifempty = True for `pull ifempty (block|noblock)`
        block = True for `pull (ifempty) (block)`
        """
	# 0b100 delay/side:5 0b1 ifE:1 Blk:1 0b00000
        return self._emit(
            opcodes.op_pull,
            opcodes.pull_ife if ifempty else 0,
            opcodes.pull_blk if block else 0,
        )

    def mov(self, dest: str, op: str, source: str=''):
        """mov <dest>, (<op>) <src>

        <dest> = pins|x|y|exec|pc|isr|osr
        <op> = ''|~|::
        <source> = pins|x|y|null|status|isr|osr

        A single <op><source> string also works here.
        """
	# 0b101 delay/side:5 dst:3 op:2 src:3
        src = (op + source) if (op and source) else (op or source)
        return self._emit(
            opcodes.op_mov,
            self._get(opcodes.mov_dest, dest, '<dest>'),
            self._get(opcodes.mov_source, src, '<source>'),
        )

    def irq(self, irq_num: Value, *, rel=False, clear=False, wait=False):
        """irq (-|set|nowait)|wait|clear <irq_num> (rel)

        rel = True to add SM index to <irq_num> (modulo 4)
        clear = True for `irq clear <irq_num> (rel)`
        wait = True for `irq wait <irq_num> (rel)`
        """
        # clear=0 wait=0 => irq -|set|nowait
        # clear=0 wait=1 => irq wait
        # clear=1 wait=? => irq clear
	# 0b110 delay/side:5 0b0 Clr:1 Wait:1 index:5
        return self._emit(
            opcodes.op_irq,
            opcodes.irq_clr if clear else 0,
            opcodes.irq_wait if wait else 0,
            0x10 if rel else 0,
            self._check_5_bits(irq_num, '<irq_num>'),  # 3 bits?
        )

    def set(self, dest: str, data: Value):
        """set <dest>, <data>

        <dest> = pins|x|y|pindirs
        <data> = 5 bits
        """
	# 0b111 delay/side:5 dst:3 data:5
        return self._emit(
            opcodes.op_set,
            self._get(opcodes.set_dest, dest, '<dest>'),
            self._check_5_bits(data, '<data>'),
        )

    def nop(self):
        """nop ;; mov y, y"""
        return self.mov('y', 'y')

#--#
