from typing import Dict

try:
    from micropython import const  # type: ignore[import-not-found]
except:
    def const(x: int): return x  # This file only.


op_jmp = const(0b000 << 13)
jmp_cond: Dict[str, int]  = {
    '': const(0b000 << 5),
    'always': const(0b000 << 5),
    '!x': const(0b001 << 5),
    'x--': const(0b010 << 5),
    '!y': const(0b011 << 5),
    'y--': const(0b100 << 5),
    'x!=y': const(0b101 << 5),
    'pin': const(0b110 << 5),
    '!osre': const(0b111 << 5),
}

op_wait = const(0b001 << 13)
wait_source: Dict[str, int] = {
    'gpio': const(0b00 << 5),
    'pin': const(0b01 << 5),
    'irq': const(0b10 << 5),
    # 11 - reserved
    # todo: rp2350 => jmppin
}

op_in = const(0b010 << 13)
in_source: Dict[str, int] = {
    'pins': const(0b000 << 5),
    'x': const(0b001 << 5),
    'y': const(0b010 << 5),
    'null': const(0b011 << 5),
    # 100 reserved
    # 101 reserved
    'isr': const(0b110 << 5),
    'osr': const(0b111 << 5),
}

op_out = const(0b011 << 13)
out_dest: Dict[str, int] = {
    'pins': const(0b000 << 5),
    'x': const(0b001 << 5),
    'y': const(0b010 << 5),
    'null': const(0b011 << 5),
    'pindirs': const(0b100 << 5),
    'pc': const(0b101 << 5),
    'isr': const(0b110 << 5),
    'osr': const(0b111 << 5),
}

op_push = const((0b100 << 13) | (0 << 7))
push_iff = const(1 << 6)
push_blk = const(1 << 5)

op_pull = const((0b100 << 13) | (1 << 7))
pull_ife = const(1 << 6)
pull_blk = const(1 << 5)

op_mov = const(0b101 << 13)
mov_dest: Dict[str, int] = {
    'pins': const(0b000 << 5),
    'x': const(0b001 << 5),
    'y': const(0b010 << 5),
    # 011 - reserved
    'exec': const(0b100 << 5),
    'pc': const(0b101 << 5),
    'isr': const(0b110 << 5),
    'osr': const(0b111 << 5),
}
mov_source: Dict[str, int] = {
    # -- op=00 none
    'pins': 0b00_000,
    'x': 0b00_001,
    'y': 0b00_010,
    'null': 0b00_011,
    # 100 - reserved
    'status': 0b00_101,
    'isr': 0b00_110,
    'osr': 0b00_111,
    # -- op=01 invert
    '~pins': 0b01_000,
    '~x': 0b01_001,
    '~y': 0b01_010,
    '~null': 0b01_011,
    # 100 - reserved
    '~status': 0b01_101,
    '~isr': 0b01_110,
    '~osr': 0b01_111,
    # -- op=10 bit-reverse
    '::pins': 0b10_000,
    '::x': 0b10_001,
    '::y': 0b10_010,
    '::null': 0b10_011,
    # 100 - reserved
    '::status': 0b10_101,
    '::isr': 0b10_110,
    '::osr': 0b10_111,
    # -- op=11 reserved
}

op_irq = const(0b110 << 13)
irq_clr = const(1 << 6)
irq_wait = const(1 << 5)
# todo: 2350 => prev|next

op_set = const(0b111 << 13)
set_dest: Dict[str, int] = {
    'pins': const(0b000 << 5),
    'x': const(0b001 << 5),
    'y': const(0b010 << 5),
    # 011 - reserved
    'pindirs': const(0b100 << 5),
    # 101 - reserved
    # 110 - reserved
    # 111 - reserved
}

#--#
