from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from . import pioasm

class PIOParser:
    def __init__(self, pioasm: pioasm):
        self._pioasm = pioasm

    def parse(self, filename: str, source: Iterable[str]):
        pass


# 3.3.2 Values
# integer
# hex
# binary
# symbol
# <label>
# ( <expression> )

# 3.3.3 Expressions
# +, -, *, /, -expr, ::expr, <value>

# 3.3.4 Comments
# //, ;, /*...*/

# 3.3.5 Labels
# (PUBLIC) <symbol>:

# preprocessor: str -> iter[line_no, line]
# scanner: iter -> iter[line_no, tokens...]
# parser:

#--#
