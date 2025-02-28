from .error import PIOSyntaxError

from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from . import pioasm


class Token:
    def __init__(self, line_no, col_no, inp):
        self.line_no = line_no
        self.col_no = col_no
        self.inp = inp

    def __str__(self):
        return self.inp

    def __repr__(self):
        return f'{self.TYPE}({self.inp})'


class NewlineToken(Token):
    TYPE = 'Newline'

class EOFToken(Token):
    TYPE = 'EOF'

class KeywordToken(Token):
    TYPE = 'Keyword'

class LabelToken(Token):
    TYPE = 'Label'

class SymbolToken(Token):
    TYPE = 'Symbol'


class NumberToken(Token):
    TYPE = 'Number'

    def __init__(self, line_no, col_no, inp):
        super().__init__(line_no, col_no, inp)
        n, base = inp.replace('_', ''), 10
        if n.startswith('0x'):
            base = 16
            n = n[2:]
        elif n.startswith('0b'):
            base = 2
            n = n[2:]
        if not n.isdigit():
            raise PIOSyntaxError(f'Bad number at <file>:{line_no}.{col_no}')
        self.value = int(n, base)

#--------------------------------------------------#

class Scanner:
    # Generates tokens from input text.

    def char_reader(self, readline):
        # Removes comments
        s = 0  # 0-4 => "_/**/"
        line_no = col_no = 0
        while line := readline():
            line_no += 1
            col_no = -1
            for c in line:
                col_no += 1
                if s == 0:
                    if c == '/':
                        s = 1
                    elif c == ';':
                        # Comment to end of line
                        yield line_no, col_no, '\n'
                        s = 0
                        break
                    else:
                        yield line_no, col_no, c
                elif s == 1:
                    if c == '*':
                        # Begin multi-line comment
                        s = 2
                    elif c == '/':
                        # Comment to end of line
                        yield line_no, col_no, '\n'
                        s = 0
                        break
                    else:
                        yield line_no, col_no - 1, '/'
                        yield line_no, col_no, c
                        s = 0
                elif s == 2:
                    if c == '*':
                        s = 3
                elif s == 3:
                    if c == '/':
                        # End multi-line comment
                        s = 0
                    else:
                        s = 2
        if s != 0:
            raise PIOSyntaxError('Unterminated comment')
        yield line_no, col_no, '\n'  # Easier EOF handling.
        yield line_no + 1, 0, ''  # EOF

    def token_reader(self, readline) -> Iterator[Token]:
        PCHARS = '~!%^&*+-=<>/'
        csrc = self.char_reader(readline)
        c = ''
        while True:
            # Find start of next input token
            if not c:
                line_no, col_no, c = next(csrc)
            if not c:
                break

            # Discard whitespace
            if c in ' \t':
                c = ''
                continue

            # Newline
            if c == '\n':
                yield NewlineToken(line_no, col_no, '\\n')
                c = ''
                continue

            # Single-char punct
            if c in '()[].,':
                yield KeywordToken(line_no, col_no, c)
                c = ''
                continue

            # Multi-char punct
            if c in PCHARS:
                p_line_no, p_col_no, p = line_no, col_no, c
                while True:
                    line_no, col_no, c = next(csrc)
                    if c not in PCHARS:
                        break
                    p += c
                yield KeywordToken(p_line_no, p_col_no, p)
                continue

            # Identifiers (labels, keywords, symbols)
            if c.isalpha() or c == '_':
                i_line_no, i_col_no, i = line_no, col_no, c
                while True:
                    line_no, col_no, c = next(csrc)
                    if not (c.isalpha() or c.isdigit() or c == '_'):
                        break
                    i += c
                if c == ':':
                    yield LabelToken(i_line_no, i_col_no, i)
                    c = None
                elif is_reserved(lc := i.lower()):
                    # 3.3.6 NOTE "pioasm instruction names, keywords
                    # and directives are case insensitive"
                    yield KeywordToken(i_line_no, i_col_no, lc)
                else:
                    yield SymbolToken(i_line_no, i_col_no, i)
                continue

            # Number
            if c.isdigit():
                n_line_no, n_col_no, n = line_no, col_no, c
                while True:
                    line_no, col_no, c = next(csrc)
                    if not (c.isalpha() or c.isdigit() or c == '_'):
                        break
                    n += c.lower()
                yield NumberToken(n_line_no, n_col_no, n)
                continue

            # Error
            raise PIOSyntaxError(f'Bad input at <file>:{line_no}.{col_no}')

        # Non-printable control chars
        yield EOFToken(line_no, col_no, '<eof>')


RESERVED_TAB: list[str] = (
    # Must be sorted by alpha
    'auto',
    'block',
    'clear',
    'clock_div',
    'define',
    'exec',
    'fifo',
    'gpio',
    'ifempty',
    'iffull',
    'in',
    'irq',
    'isr',
    'jmp',
    'jmppin',
    'lang_opt',
    'left',
    'manual',
    'mov',
    'mov_status',
    'next',
    'noblock',
    'nop',
    'nowait',
    'null',
    'opt',
    'origin',
    'osr',
    'out',
    'pc',
    'pin',
    'pindirs',
    'pins',
    'pio_version',
    'prev',
    'program',
    'public',
    'pull',
    'push',
    'putget',
    'rel',
    'right',
    'rp2040',
    'rp2050',
    'rx',
    'rxfifo',
    'set',
    'side',
    'side_set',
    'status',
    'tx',
    'txfifo',
    'txget',
    'txput',
    'txrx',
    'wait',
    'word',
    'wrap',
    'wrap_target',
    'x',
    'y',
)

def is_reserved(s: str):
    r = RESERVED_TAB
    a, b = 0, len(r)
    # bisect_left
    while a < b:
        c = (a + b) // 2
        if r[c] < s:
            a = c + 1
        else:
            b = c
    t = (a < len(r) and r[a] == s)
    f = r[a] if a < len(r) else None
    #print(f'is_reserved({s} {a=} {f=}) => {t}')
    return t

#---------------------------------------------------------------------#

class Prec:
    STMT = -1
    NONE = 0
    ASSIGN = 1
    OR = 2	# |
    AND = 3	# &
    EQUALITY = 4 # == !=
    COMPARE = 5	#
    SHIFT = 6	# << >>
    TERM = 7	# + -
    FACTOR = 8	# * / %
    UNARY = 9	# - ~ ! ::
    PRIMARY = 10 #

    EXPR = OR

class Expr:
    """Parsed expression"""


class Stmt:
    """Parsed statement"""


class PIOParser:
    def __init__(self):
        self._previous: Optional[Token] = None
        self._current: Optional[Token] = None
        self._reader: Optional[Iterator[Token]] = None
        self._exprs: list[Expr] = [ ]
        self._stmts: list[Stmt] = [ ]
        return

    def next_token(self):
        tok = next(self._reader)
        #print('next:', tok)
        return tok

    @property
    def previous(self) -> Token:
        """The "previous" or most recently handled token

        Often used by a generic parsing function to inspect the
        token (operator) being handled.
        """
        return self._previous

    @property
    def current(self) -> Token:
        """The "current" or next unhandled token

        Often used by parsing function as a lookahead.  See also the
        consume methods.
        """
        return self._current

    def advance(self):
        """Pull the next unhandled token to current

        Shifts the old current to previous in case a rule handler needs
        it.  Parsing functions should almost always prefer one of the
        consume methods.
        """
        self._previous = self._current
        # Maybe loop until non-error
        self._current = self.next_token()
        # Error? => report...
        print(f'  Advance ==> {self._previous} . {self._current}')
        return

    def consume_cls(self, token_cls, error=''):
        # Advance if current matches matches by type, or throw an
        # exception if required by error.  Returns the token if
        # matched, otherwise None.
        if isinstance(self.current, token_cls):
            print('Consuming the', token_cls)
            c = self.current
            self.advance()
            return c
        elif error:
            # Error message implies required token
            raise PIOSyntaxError(f'{error} (at {self.previous} . {self.current})')
        return None

    def consume_kw(self, keyword: str, error: str=''):
        # Advance if current token matches keyword, or throw an
        # exception if required by error.  Returns True iff matched.
        c = self.current
        if isinstance(c, KeywordToken) and c.inp == keyword:
            print('Consuming the', keyword)
            self.advance()
            return True
        elif error:
            raise PIOSyntaxError(f'{error} (at {self.previous} . {self.current})')
        return False

    def consume_one_of(self, keywords: list[str], error: str='') -> str|None:
        for kw in keywords:
            if self.consume_kw(kw):
                return kw
        if error:
            raise PIOSyntaxError(error)
        return None

    def parse_precedence(self, precedence: int):

        # Move unhandled current to previous, and then handle it.
        self.advance()
        previous_rule = get_rule(self.previous, True)
        print('Got prev rule=', previous_rule)
        prefix_fn = previous_rule[1]
        if prefix_fn is None:
            raise PIOSyntaxError('Not a prefix operator')

        # Note for a true prefix operator, additional parsing will
        # occur leaving current at the next unhandled token.  For
        # literals, current remains at the next uhandled token.
        before = f'{self.previous} . {self.current}'
        prefix_fn(self)
        after = f'{self.previous} . {self.current}'

        print(f'Update by prefix-fn {before} ==> {after}')

        if isinstance(self.previous, NewlineToken):
            # Force restart to get prefix-fn at start of next line.
            return

        # Process more for as long as the next unhandled token is lower
        # or equal precedence.  Note a missing rule generally indicates
        # starting non-expression syntax.
        current_rule = get_rule(self.current)
        while current_rule and precedence <= current_rule[3]:
            print(f'Loop: {precedence} <= {current_rule}')
            infix_fn = current_rule[2]
            self.advance()  # shift previous . current
            if infix_fn is None:
                raise PIOSyntaxError(f'Not an infix operator {self.previous}')
            before = f'{self.previous} . {self.current}'
            # Call the infix handler for the now previous token.
            # It must consume current via a recursive call to
            # parse_precedence, leaving the next unhandled token in
            # current.
            infix_fn(self)
            after = f'{self.previous} . {self.current}'
            print(f'Update by infix-fn {before} ==> {after}')
            current_rule = get_rule(self.current)
        print(f'Done: {precedence} > {current_rule}')

        return

    def parse(self, filename: str, readline: Callable[[], str]):
        self._reader = Scanner().token_reader(readline)
        self.advance()  # First unhandled token in current.
        while not isinstance(self.current, EOFToken):
            print()
            self.parse_precedence(Prec.NONE)
            print('Emitted stmts:', self._stmts)
            while self._stmts:
                yield self._stmts.pop(0)
            print(f'Left on stack: {self.previous} . {self.current}')

    def parse_value(self, error: str) -> Expr:
        # Note pioasm requires parens around non-trivial exprs,
        # so all special cases here...
        # Number
        # Symbol
        # "(" expr ")"
        # non-value => throw error
        if number := self.consume_cls(NumberToken):
            return number
        if symbol := self.consume_cls(SymbolToken):
            return symbol
        if not self.consume_kw('('):
            raise PIOSyntaxError(error)
        self.parse_precedence(Prec.EXPR)
        self.consume_kw(')', 'Expecting ")"')
        expr = self.pop_expr()
        return expr

    def push_expr(self, expr: Expr):
        print('-->> push:', expr)
        self._exprs.append(expr)

    def pop_expr(self):
        expr =  self._exprs.pop(-1)
        print('--<< pop:', expr)
        return expr

    def emit_stmt(self, stmt: Stmt):
        self._stmts.append(stmt)

#--------------------------------------------------#

class NumberExpr(Expr):
    # Wraps a NumberToken in an Expr

    def __init__(self, p: PIOParser):
        self._token = p.previous
        p.push_expr(self)

    def __str__(self):
        return str(self._token)

    def __repr__(self):
        return f'NumberExpr({self._token})'


class SymbolExpr(Expr):
    # Wraps a SymbolToken in an Expr

    def __init__(self, p: PIOParser):
        self._token = p.previous
        p.push_expr(self)

    def __str__(self):
        return str(self._token)

    def __repr__(self):
        return f'SymbolExpr({self._token})'


class PrefixExpr(Expr):
    _OP = '-?-'
    
    def __init__(self, p: PIOParser):
        p.parse_precedence(Prec.UNARY)
        # f'"{self._OP}" expect <expr>'
        self._expr: Expr = p.pop_expr()
        p.push_expr(self)

    def __str__(self):
        return f'({self._OP} {str(self._expr)})'

class UnaryNotInv(PrefixExpr):
    _OP = '!'  # Also '~'

class UnaryPlus(PrefixExpr):
    _OP = '+'

class UnaryMinus(PrefixExpr):
    _OP = '-'

class UnaryReverse(PrefixExpr):
    _OP = '::'


class BinaryExpr(Expr):
    _OP = '-?-'

    def __init__(self, p: PIOParser):
        print('gimme...')
        p.parse_precedence(get_rule(self._OP)[3] + 1)
        self._rhs: Expr = p.pop_expr()
        self._lhs: Expr = p.pop_expr()
        p.push_expr(self)

    def __str__(self):
        return f'({self._OP} {str(self._lhs)} {str(self._rhs)})'

class CompareNE(BinaryExpr):
    _OP = '!='

class InfixMod(BinaryExpr):
    _OP = '%'

class InfixTimes(BinaryExpr):
    _OP = '*'

class InfixPlus(BinaryExpr):
    _OP = '+'

class InfixMinus(BinaryExpr):
    _OP = '-'

class InfixDiv(BinaryExpr):
    _OP = '/'

class LessThan(BinaryExpr):
    _OP = '<'

class InfixLShift(BinaryExpr):
    _OP = '<<'

class InfixRShift(BinaryExpr):
    _OP = '>>'


class ParenExpr(Expr):

    def __init__(self, p: PIOParser):
        p.parse_precedence(Prec.EXPR)
        #f'"(" expect <expr>'
        p.consume_kw(')', '"(" <expr> expected ")"')
        self._expr: Expr = p.pop_expr()
        p.push_expr(self)

    def __str__(self):
        return f'"("{str(self._expr)}")"'

#--------------------------------------------------#

class NewlineStmt:
    def __init__(self, p: PIOParser):
        pass  # Will be discarded.


class UnaryDot(Stmt):
    def __init__(self, p: Parser):
        if p.consume_kw('program'):
            self._parse_program(p)
        elif p.consume_kw('define'):
            self._parse_define(p)
        elif p.consume_kw('lang_opt'):
            self._parse_lang_opt(p)
        elif p.consume_kw('side_set'):
            self._parse_side_set(p)
        elif p.consume_kw('word'):
            self._parse_word(p)
        elif p.consume_kw('wrap'):
            self._parse_wrap(p)
        elif p.consume_kw('wrap_target'):
            self._parse_wrap_target(p)
        else:
            raise PIOSyntaxError(f'Invalid .{p.current.inp}')

    def _parse_program(self, p: Parser):
        # "." program . <name>
        name = p.consume_cls(SymbolToken, '.program expected <name>')
        p.emit_stmt(f'.program {name.inp}')

    def _parse_define(self, p: Parser):
        # "." define . <name> <expr>
        is_public = bool(p.consume_kw('public'))
        name = p.consume_cls(SymbolToken, '.define expected <name>')
        p.parse_precedence(Prec.EXPR)
        # '.define <name> expected <expr>')
        value = p.pop_expr()
        p.emit_stmt(f'.define{" public" if is_public else ""} {name.inp} {value}')

    def _parse_lang_opt(self, p: Parser):
        # "." lang_opt . <lang> <key> = <value>
        lang = p.consume_cls(SymbolToken, '.lang_opt expected <lang>')
        key = p.consume_cls(SymbolToken, '.lang_opt <lang> expected <key>')
        p.consume_kw('=', '.lang_opt <lang> <key> expected "="')
        val = [ ]
        while not isinstance(p.current, NewlineToken):
            # Not parsing, blindly take the rest of the line
            val.append(str(p.current))
            p.advance()
        p.emit_stmt(f'.lang_opt {lang.inp} {key.inp} = {"".join(val)}')

    def _parse_side_set(self, p: Parser):
        # "." side_set . <count>
        count = p.consume_cls(NumberToken, '.side_set expected <number>')
        p.emit_stmt(f'.side_set {count.value}')

    def _parse_wrap(self, p: Parser):
        # "." wrap
        p.emit_stmt(f'.wrap')

    def _parse_wrap_target(self, p: Parser):
        # "." wrap_target
        p.emit_stmt(f'.wrap_target')


class PublicStmt(Stmt): pass


class LabelStmt:
    def __init__(self, p: PIOParser):
        p.emit_stmt(f'{p.previous.inp}:')


class InstructionStmt:  # Mixin
    def _parse_side_delay(self, p: PIOParser):
        side = None
        delay = None

        if p.consume_kw('side'):
            side = p.parse_value('side expected <value>')

        if p.consume_kw('['):
            #delay = p.consume_cls(NumberToken, '"[" expected <value>')
            p.parse_precedence(Prec.EXPR)
            # '"[" expected <expr>'
            delay = p.pop_expr()
            p.consume_kw(']', 'delay <value> expected "]"')

        if side is None and p.consume_kw('side'):
            side = p.parse_value('side expected <expr>')

        #return side, delay
        return (
            f'{"" if side is None else " side %s" % side}'
            + f'{"" if delay is None else " [%s]" % delay}'
        )


class JmpStmt(InstructionStmt):
    
    def __init__(self, p: PIOParser):
        # jmp [<cond>] [,] <target>
        cond = self._parse_condition(p)
        print(f'got jmp cond={cond}')
        if cond:
            p.consume_kw(',')
        p.parse_precedence(Prec.EXPR)
        #'jmp expected <target>'
        target = p.pop_expr()
        side_delay = self._parse_side_delay(p)
        p.emit_stmt(
            f'jmp{(" %s," % cond) if cond else ""} {target}{side_delay}'
        )

    def _parse_condition(self, p: PIOParser):
        # !x x-- !y y-- x!=y pin !osre <always>
        if p.consume_kw('!'):
            if p.consume_kw('x'):
                return '!x'
            if p.consume_kw('y'):
                return '!y'
            if p.consume_kw('osre'):
                return '!osre'
            raise PIOSyntaxError('jmp ! expected "x|y|osre"')
        if p.consume_kw('x'):
            if p.consume_kw('!='):
                p.consume_kw('y', 'jmp x!= expected "y"')
                return 'x!=y'
            p.consume_kw('--', 'jmp x expected "--"')
        if p.consume_kw('y'):
            p.consume_kw('--', 'jmp y expected "--"')
            return 'y--'
        if p.consume_kw('pin'):
            return 'pin'
        return ''


class WaitStmt(InstructionStmt):
    SOURCE = ( 'gpio', 'pin', 'irq', 'jmppin' )

    def __init__(self, p: PIOParser):
        # wait [<pol>] <source> ...
        pol = p.parse_value('wait <pol>')
        source = p.consume_one_of(self.SOURCE)
        irq_pn = ''
        irq_rel = False
        if source == 'gpio':
            # ... [,] <index>
            p.consume_kw(',')
            index = p.parse_value('wait <pol> <gpio>, expected <index>')
        elif source == 'pin':
            # ... [,] <index>
            p.consume_kw(',')
            index = p.parse_value('wait <pol> <pin>, expected <index>')
        elif source == 'irq':
            # ... [-|prev|next] [,] <index> [rel]
            if p.consume_kw('prev'):
                irq_pn = 'prev'
            elif p.consume_kw('next'):
                irq_pn = 'next'
            p.consume_kw(',')
            index = p.parse_value('wait irq "," expected <index>')
            irq_rel = p.consume_kw('rel')
        elif source == 'jmppin':
            # ... [+ <value>]
            index = (
                p.parse_value('wait <pol> <jmppin> "+" expected <index>')
                if p.consume_kw('+')
                else 0
            )
        else:
            raise PIOSyntaxError(f'Unexpected {source=}')
        p.emit_stmt(
            f'wait {pol} {source}'
            + f'{" %s," % irq_pn if irq_pn else ","}'
            # jmppin ["+" index]
            + f' {index}{" irq_rel" if irq_rel else ""}'
            # side_delay
        )


class InStmt(InstructionStmt):
    DEST = ( 'pins', 'x', 'y', 'null', 'isr', 'osr' )

    def __init__(self, p: PIOParser):
        # in <source> [,] <value>
        source = p.consume_cls(KeywordToken, 'in expected <source>')
        if source.inp not in self.DEST:
            raise PIOSyntaxError(f'Invalid in <source> "{p.current.inp}"')
        p.consume_kw(',')
        count = p.parse_value('in <source> expected <count>')
        side_delay = self._parse_side_delay(p)
        p.emit_stmt(f'in {source.inp}, {count.value}{side_delay}')


class OutStmt(InstructionStmt):
    DEST = ( 'pins', 'x', 'y', 'null', 'pindirs', 'pc', 'isr', 'osr' )

    def __init__(self, p: PIOParser):
        # out . <dest> [,] <value>
        dest = p.consume_cls(KeywordToken, 'out expected <dest>')
        if dest.inp not in self.DEST:
            raise PIOSyntaxError(f'Invalid out <dest> "{p.current.inp}"')
        p.consume_kw(',')
        count = p.parse_value('out <dest> expected <count>')
        side_delay = self._parse_side_delay(p)
        p.emit_stmt(f'out {dest.inp}, {count.value}{side_delay}')


class PushStmt(InstructionStmt):
    def __init__(self, p: PIOParser):
        # push [iffull] [blocking]
        iffull = p.consume_kw('iffull')
        block = p.consume_kw('block') or not p.consume_kw('noblock')
        # side_delay
        p.emit_stmt('push ...')


class PullStmt(InstructionStmt):
    def __init__(self, p: PIOParser):
        # pull [ifempty] [blocking]
        ifempty = p.consume_kw('ifempty')
        block = p.consume_kw('block') or not p.consume_kw('noblock')
        # side_delay
        p.emit_stmt('pull ...')


class MovStmt(InstructionStmt):
    DEST = ( 'pins', 'x', 'y', 'pc', 'exec' )
    OP = ( '!', '~', '::' )
    SOURCE = ( 'pins', 'x', 'y', 'null', 'status', 'isr', 'osr' )

    def __init__(self, p: PIOParser):
        # mov <dest> [,] [op] <source>
        dest = self._parse_dest(p)
        p.consume_kw(',')
        op = self._parse_op(p)
        source = self._parse_source(p)
        side_delay = self._parse_side_delay(p)
        p.emit_stmt(f'mov {dest}, {op}{source}')

    def _parse_dest(self, p: PIOParser):
        dest = p.consume_one_of(self.DEST, 'mov expected <dest>')
        return dest

    def _parse_op(self, p: PIOParser):
        op = p.consume_one_of(self.OP)
        return op

    def _parse_source(self, p: PIOParser):
        source = p.consume_one_of(
            self.SOURCE, 'mov <dest>, [<op>] expected <source>'
        )
        if source == '!':
            source = '~'
        return source


class IrqStmt(InstructionStmt):
    def __init__(self, p: PIOParser):
        # irq [-|prev|next] ...
        irq_pn = None
        if p.consume_kw('prev'):
            irq_pn = 'prev'
        elif p.consume_kw('next'):
            irq_pn = 'next'
        # ... clear <value> [rel]
        # ... wait <value> [rel]
        # ... [-|nowait|set] <value> [rel]
        if p.consume_kw('clear'):
            action = 'clear'
        elif p.consume_kw('wait'):
            action = 'clear'
        elif p.consume_kw('set') or p.consume_kw('nowait') or True:
            action = 'set'
        index = p.parse_value('irq expected <index>')
        rel = p.consume_kw('rel')
        p.emit_stmt(
            f'irq {"%s " % irq_pn if irq_pn else ""}'
            + f'{action} {index}{" rel" if rel else ""}'
        )


class SetStmt(InstructionStmt):
    _DEST = ( 'pins', 'x', 'y', 'pindirs' )

    def __init__(self, p: PIOParser):
        # set <dest> [,] <value>
        dest = self._parse_dest(p)
        p.consume_kw(',')
        value = p.parse_value('set <dest>, expcteed <value>')
        p.emit_stmt(f'set {dest}, {value}')

    def _parse_dest(self, p: PIOParser):
        dest = p.consume_one_of(self._DEST, 'set expected <dest>')
        return dest


class NopStmt(InstructionStmt):
    def __init__(self, p: PIOParser):
        side_delay = self._parse_side_delay(p)
        p.emit_stmt(f'nop{side_delay}')

#--------------------------------------------------#

PRATT_TAB = (
    # ( token, prefixFn, infixFn, prec ),
    # Must be sorted by alpha
    ( '!', UnaryNotInv, None, Prec.NONE ),
    ( '!=', None, CompareNE, Prec.COMPARE ),
    ( '%', None, InfixMod, Prec.FACTOR ),
    ( '(', ParenExpr, None, Prec.NONE ),
    #( ')', None, None, Prec.NONE ),
    ( '*', None, InfixTimes, Prec.FACTOR ),
    ( '+', UnaryPlus, InfixPlus, Prec.TERM ),
    ( '-', UnaryMinus, InfixMinus, Prec.TERM ),
    ( '.', UnaryDot, None, Prec.NONE ),
    ( '/', None, InfixDiv, Prec.FACTOR ),
    ( '::', UnaryReverse, None, Prec.NONE ),
    ( '<', None, LessThan, Prec.COMPARE ),
    ( '<<', None, InfixLShift, Prec.SHIFT ),
    ( '>>', None, InfixRShift, Prec.SHIFT ),
    # A-Z
    ( '[', None, None, Prec.NONE ),
    #( ']', None, None, Prec.NONE ),
    # ^
    # a-z
    ( 'in', InStmt, None, Prec.NONE ),
    ( 'irq', IrqStmt, None, Prec.NONE ),
    ( 'jmp', JmpStmt, None, Prec.NONE ),
    ( 'mov', MovStmt, None, Prec.NONE ),
    ( 'nop', NopStmt, None, Prec.NONE ),
    ( 'out', OutStmt, None, Prec.NONE ),
    ( 'public', PublicStmt, None, Prec.NONE ),
    ( 'pull', PullStmt, None, Prec.NONE ),
    ( 'push', PushStmt, None, Prec.NONE ),
    ( 'set', SetStmt, None, Prec.NONE ),
    ( 'wait', WaitStmt, None, Prec.NONE ),
    # { }
    ( '~', UnaryNotInv, None, Prec.NONE ),
)

def get_rule(token: str | Token, required: bool = False):
    if isinstance(token, KeywordToken):
        token = token.inp
    if isinstance(token, str):
        r = PRATT_TAB
        a, b = 0, len(r)
        while a < b:
            c = (a + b) // 2
            if r[c][0] < token:
                a = c + 1
            else:
                b = c
        if a < len(r) and r[a][0] == token:
            return r[a]
        if required:
            print('---', a, r[a], token)
            raise PIOSyntaxError(f'No rule for {token=}')
        return None
    if isinstance(token, LabelToken):
        return ( '<label>', LabelStmt, None, Prec.NONE )
    if isinstance(token, NewlineToken):
        return ( '<newline>', NewlineStmt, None, Prec.STMT )
    if isinstance(token, NumberToken):
        return ( '<number>', NumberExpr, None, Prec.NONE )
    if isinstance(token, SymbolToken):
        return ( '<symbol>', SymbolExpr, None, Prec.NONE )
    raise PIOSyntaxError(f'Bad {token=}')

#--#
