# Adapted from: https://github.com/micropython/micropython/blob/master/examples/rp2/pio_1hz.py
# Example using PIO to blink an LED and raise an IRQ at 1Hz.
# Note: this does not work on Pico W because it uses Pin(25) for LED output.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from upioasm.syntax import *

from upioasm import pioasm

pa = pioasm()


#@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
@pa.asm_pio('blink_1hz')
def blink_1hz() -> None:
    L_loop = label('; some loop')
    L_test = label(forward=True)

    # Cycles: 1 + 1 + 6 + 32 * (30 + 1) = 1000
    with dot_wrap_target():
        irq(0, rel=True)
        set(pins, 1)
        set(x, 31)              [5]
    with label("delay_high"):
        nop()                   [29]
        jmp.x_dec("delay_high")

    # Cycles: 1 + 1 + 6 + 32 * (30 + 1) = 1000
        nop()
        set(pins, 0)
        set(x, 31)              [5]
    with label("delay_low"):
        nop()                   [29]
        jmp.x_dec("delay_low")

        dot_wrap()

    with L_loop:
        wait(1).gpio(5)
        in_(x, 7)
        jmp.not_x(L_test)
        out(y, 8)
    if L_test:
        push(iffull=True)
        pull(block=False)
        # error: Argument 2 to "mov" has incompatible type "_pc"; expected "MovSourceReg"  [arg-type]
        # mov(x, pc)
        mov(pc, ~isr)
        mov(pc, osr.reversed)
        irq.wait(7)
        set(y, 12)
        jmp(L_loop)


# Create the StateMachine with the blink_1hz program, outputting on Pin(25).
#sm = rp2.StateMachine(0, blink_1hz, freq=2000, set_base=Pin(25))

# Set the IRQ handler to print the millisecond timestamp.
#sm.irq(lambda p: print(time.ticks_ms()))

# Start the StateMachine.
#sm.active(1)
