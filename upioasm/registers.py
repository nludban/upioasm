## Register types

class Register:
    _name: str

class InSourceReg(Register): pass

class OutDestReg(Register): pass

class MovDestReg(Register): pass

class MovSourceReg(Register): pass

class MovSourceMixin(MovSourceReg):

    def __invert__(self) -> MovSourceReg:
        """~<source>"""
        reg = MovSourceReg()
        reg._name = '~' + self._name
        return reg

    @property
    def inverted(self) -> MovSourceReg:
        """~<source>"""
        return ~self

    @property
    def reversed(self) -> MovSourceReg:
        """::<source>"""
        reg = MovSourceReg()
        reg._name = '::' + self._name
        return reg

class SetDestReg(Register): pass

## Register classes

class _pins(InSourceReg, OutDestReg, MovDestReg, MovSourceMixin, SetDestReg):
    _name = 'pins'

class _x(InSourceReg, OutDestReg, MovDestReg, MovSourceMixin, SetDestReg):
    _name = 'x'

class _y(InSourceReg, OutDestReg, MovDestReg, MovSourceMixin, SetDestReg):
    _name = 'y'

class _null(InSourceReg, OutDestReg, MovSourceMixin):
    _name =  'null'

class _pindirs(OutDestReg, SetDestReg):
    _name = 'pindirs'

class _pc(OutDestReg, MovDestReg):
    _name = 'pc'

class _status(MovSourceMixin):
    _name = 'status'

class _isr(InSourceReg, OutDestReg, MovSourceMixin):
    _name = 'isr'

class _osr(InSourceReg, OutDestReg, MovSourceMixin):
    _name = 'osr'

class _exec(OutDestReg, MovDestReg):
    _name = 'exec'

## Register objects

pins = _pins()
x = _x()
y = _y()
null = _null()
pindirs = _pindirs()
pc = _pc()
status = _status()
isr = _isr()
osr = _osr()
exec_ = _exec()

#--#
