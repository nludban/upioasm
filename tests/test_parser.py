from upioasm.parser import PIOParser, PRATT_TAB, get_rule


def test_rules():
    # Rules must be sorted or lookup fails
    r = list(PRATT_TAB)
    s = sorted(list(r))
    assert r == s
    # Verify all rule lookups
    for rule in PRATT_TAB:
        print('get-rule', rule)
        assert get_rule(rule[0]) is rule


def test_ws2812():
    p = PIOParser()
    stmts = [ ]
    for stmt in p.parse('ws2812.pio', open('tests/ws2812.pio').readline):
        print(')))))', stmt)
        stmts.append(stmt)

    print(';; Result')
    for stmt in stmts:
        if ':' in stmt or stmt.startswith('.'):
            print(stmt)
        else:
            print('   ', stmt)

print('==> Test rules')
test_rules()

print('==> Test parser[ws2812.pio]')
test_ws2812()

print('==> ok.')

#--#
