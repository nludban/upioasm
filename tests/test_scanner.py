from upioasm.parser import Scanner, RESERVED_TAB, is_reserved
from io import StringIO

def test_reserved():
    # List must be sorted or is_reserved fails
    r = list(RESERVED_TAB)
    s = list(sorted(r))
    assert r == s
    # Check some non-reserved words
    assert not is_reserved('aardvark')
    assert not is_reserved('zebra')
    # Check all reserved words
    for kw in RESERVED_TAB:
        assert is_reserved(kw)


def test_ws2812():
    s = Scanner()
    for tok in s.token_reader(open('tests/ws2812.pio').readline):
        print(tok)


print('==> Test reserved')
test_reserved()

print('==> Test scanner[ws2812.pio]')
test_ws2812()

print('==> ok.')

#--#
