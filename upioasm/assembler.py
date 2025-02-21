from typing import cast, Any, Dict, Generator, List, Optional, Union, TYPE_CHECKING

try:
    from micropython import const  # type: ignore[import-not-found]
except:
    const = lambda x: x

if TYPE_CHECKING:
    from . import pioasm
    from .syntax import Instruction

from .defines import Defines
from .emitter import InstructionVisitor, PIOEmitter
from .error import PIOSyntaxError
from .program import PIOProgram
from .registers import Register
from .resolver import ResolverVisitor
from .xpileemitter import EmitterVisitor
from .xpilelabels import LabelsVisitor
from .xpileprinter import PrintVisitor
from . import syntax

Value = Union[str, int]

class Word(syntax.Instruction):
    def __init__(self, value):
        self._code = value
        super(self).__init__()


def _use_label_noop(label: syntax.Label):
    pass


class PIOAssembler:
    def __init__(self, pioasm: pioasm) -> None:
        self._pioasm = pioasm
        self._adefs = Defines()
        self._program: Optional[PIOProgram] = None
        self._pdefs: Optional[Defines] = None
        self._ilist: List[Instruction] = [ ]
        self._options: Dict[str, Any] = { }
        return

    def asm_pio(self, name: str, **kwargs):
        def deco(func) -> PIOProgram:
            p = self.phase_one(name, kwargs)
            gl = func.__globals__
            org_gl = gl.copy()
            try:
                gl.clear()
                self.import_syntax(gl)
                syntax._asm = self
                func()
            finally:
                del syntax._asm
                gl.clear()
                gl.update(org_gl)
                del gl
            self.phase_two()
            return p
        return deco

    def phase_one(self, name: str, kwargs: Dict[str, Any]):
        self.program(name, **kwargs)
        self._pdefs = self._adefs.copy(True)
        return self._program

    def import_syntax(self, g: Dict[str, Any]):
        for key, val in syntax.__dict__.items():
            # No privates or Types
            if 'a' <= key[0] <= 'z':
                g[key] = val
        return

    def phase_two(self) -> PIOProgram:
        if self._program is None or self._pdefs is None:
            raise PIOSyntaxError('phase two without a program')
        p = self._program
        try:
            opcodes = self.generate(self._pdefs, self._ilist)
            #p.set_opcodes()
            #p.set_defines(self._pdefs)
        finally:
            self._program = None
            self._pdefs = None
            self._ilist = [ ]
            self._options = { }
        return p

    def program(self, name: str, pio_version='rp2040'):
        # Begin a new program.
        p = self._pioasm.program(name, pio_version=pio_version)
        self._program = p
        return p

    def define(self, name: str, value: Value, public=False):
        if self._pdefs is None:
            if isinstance(value, str):
                value = self._adefs.resolve(name)
            self._adefs.define(name, value, public)
        else:
            if isinstance(value, str):
                value = self._pdefs.resolve(name)
            self._pdefs.define(name, value, public)
        return

    def origin(self, offset: Value):
        #offset = _check_5_bits(offset)
        #return self
        if self._program is None:
            raise PIOSyntaxError('origin outside of program')
        #self._program.origin(offset)

    def side_set(self, count: Value, opt: bool=True, pindirs: bool=False):
        return self

    #def set(count)
    #def in_(count, right, autopush, threshold)
    #def out(count, right, autopush, threshold)

    def wrap(self) -> None:
        if '.wrap' in self._options:
            raise PIOSyntaxError('.wrap already used')
        self._options['.wrap'] = len(self._ilist)
        return

    def wrap_target(self) -> syntax.Label:
        if '.wrap_target' in self._options:
            raise PIOSyntaxError('.wrap_target already defined')
        self._options['.wrap_target'] = len(self._ilist)
        return syntax.Label('.wrap_target', _use_label_noop)

    def word(self, value: Value):
        Word(value)

    def label(self, name: str='', *, public: bool=False, forward: bool=False) -> syntax.Label:
        if self._pdefs is None:
            raise PIOSyntaxError('label outside of program')
        if not name:
            name = 'L%d' % len(self._pdefs)
        elif name.startswith(';'):
            forward = True
        if forward:
            self._pdefs.declare(name, public)
            return syntax.Label(name, self._label_used)
        self._pdefs.define(name, len(self._ilist), public)
        return syntax.Label(name, _use_label_noop)

    def _label_used(self, label: syntax.Label):
        cast(Defines, self._pdefs).assign(label._name, len(self._ilist))
        return

    def append(self, i: Instruction) -> None:
        if self._pdefs is None:
            raise PIOSyntaxError('instruction outside of program')
        if len(self._ilist) >= 32:
            raise PIOSyntaxError('program > 32 instructions')
        self._ilist.append(i)
        return

    def generate(self, pdefs: Defines, ilist: List[Instruction]):
        print('-- defines')
        for d in pdefs._tab:
            print(d)

        # Instructions to opcodes
        ee = PIOEmitter() #**self._options)
        rw = ResolverVisitor(pdefs, ee)

        # Extract jmp target addrs/labels
        # todo - add .wrap and .wrap_target
        lv = LabelsVisitor()

        # Simplified source
        pv = PrintVisitor()

        for i in ilist:
            i.visit(rw)
            i.visit(lv)
            i.visit(pv)

        codes = ee.get_array()
        addrs = lv.get_jmp_addrs()

        def matching_addrs(ofs):
            for addr in addrs:
                a = addr if isinstance(addr, int) else pdefs.resolve(addr)
                if a == ofs:
                    yield addr

        print('-- output')
        print('{name}_opcodes = [')
        for ofs, (code, src) in enumerate(zip(codes, pv)):
            for addr in matching_addrs(ofs):
                print(f'    # ==> {addr}:')
            print('    0x%04x, # %2d ; %s' % (code, ofs, src))
        print(']')

        # Visitor source
        print('-- visitor')
        vv = EmitterVisitor()
        rw = ResolverVisitor(pdefs, vv)
        for i in ilist:
            i.visit(rw)
        print('def {name}_emit(v: InstructionVisitor):')
        for ofs, line in enumerate(vv):
            for addr in matching_addrs(ofs):
                print(f'    # [{ofs:2}] ==> {addr}:')
            print('   ', line)

#--#
