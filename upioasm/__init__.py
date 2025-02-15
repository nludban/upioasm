from typing import Iterable

from .program import PIOProgram
from .error import PIOSyntaxError


class pioasm:
    """pioasm - assembler for the PIO peripheral, in micropython

    This class is a facade for the upioasm package and holds all
    the programs.  Several ways of defining a program are provided,
    having tradeoffs in speed, memory usage, and developer support.

    Smallest is the PIOProgram initialized with an array of pre-
    compiled opcodes.

    Next is the PIOEmitter which provides per-instruction methods
    to generate opcodes from literal strings and values.  Syntax
    errors are detected at run-time.

    The PIOAssembler is similar to the `rp2.pio_asm` decorator,
    with some changes to syntax but full IDE auto-completion support
    and static type checks.

    The PIOParser accepts a string/file and supports most of the
    official SDK tools pioasm syntax.
    """
    def __init__(self) -> None:
        self._programs: dict[str, PIOProgram] = { }
        return

    def __getitem__(self, name: str) -> PIOProgram:
        """Get a previously defined program by name"""
        return self._programs[name]

    def asm_pio(self, func):
        """Create a new assembler and decorates `func`"""
        a = self.assembler()
        return a.asm_pio(func)

    def emit_pio(self, func):
        """Create a new emitter and decorates `func`"""
        e = self.emitter()
        return a.emit_pio(func)

    def program(self, name: str, **kwargs) -> PIOProgram:
        """Create a new program from raw data"""
        p = PIOProgram(name, **kwargs)
        self._programs[name] = p
        return p

    def emitter(self):
        """Create a new emitter"""
        from .emitter import PIOEmitter
        return PIOEmitter(self)

    def assembler(self):
        """Create a new assembler"""
        from .assembler import PIOAssembler
        return PIOAssembler(self)

    def parse(self, filename: str, source: Iterable[str]):
        from .parser import PIOParser
        p = PIOParser(self)
        return p.parse(filename, source)

    def parse_str(self, source: str):
        return self.parse('-', source)

    def parse_file(self, filename: str):
        with open(filename) as fobj:
            return self.parse(filename, fobj)

#--#
