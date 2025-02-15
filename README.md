# upioasm

Micropython assembler for the Raspberry PIO peripheral


## Overview

A very experimental work in progress.  Project goals:

* Python syntax supporting static type checking and IDE completion
* A much smaller runtime but still allowing Python source to be modified on the target
* A minimal runtime to load a pre-assembled program from an array of int opcodes
* Automated translation between the various source formats

Stretch goal:
* Compatible with input to the official pico SDK [pioasm](https://github.com/raspberrypi/pico-sdk/tree/master/tools/pioasm)


## Initial Set Up

https://docs.micropython.org/en/latest/reference/mpremote.html

Install:
`$ python3 -m pip install mpremote`

Verify:
```
$ mpremote 
Connected to MicroPython at /dev/cu.usbmodem2101
Use Ctrl-] or Ctrl-x to exit this shell

>>> 
```

Get [typing](https://micropython-stubs.readthedocs.io/en/main/typing_mpy.html) stubs:
```
$ git clone git@github.com:Josverl/micropython-stubs.git
$ cd micropython-stubs
$ mpremote cp mip/typing.py :lib/typing.py
$ mpremote cp mip/typing_extensions.py :lib/typing_extensions.py
```

Install and run type checks:
```
$ python3 -m pip install mypy
$ mypy -p upioasm
$ mypy -p examples
```

Run an example on the host:
```
$ mkdir lib
$ cp ../micropython-stubs/mip/typing* lib/
$ MICROPYPATH=`pwd`:`pwd`/lib micropython examples/pio_1hz.py
```


## Architecture

Source files have been split to avoid importing everything when it's not needed.

Component Diagram TBD, start with [class pioasm](upioasm/__init__.py)...


## Examples

Just a translation of [blink_1hz](examples/pio_1hz.py) at the moment.
Running `make` (after the Initial Set Up steps) should demonstrate some capabilities...

Outputs an annotated array of opcodes:
```
{name}_opcodes = [
    0xc030, #  0 ; irq 0 rel=True clear=False wait=True
    0xe001, #  1 ; set pins 1
    0xe53f, #  2 ; set x 31 [5]
    # ==> delay_high:
    0xbd42, #  3 ; nop [29]
    0x0043, #  4 ; jmp x-- delay_high
    0xa042, #  5 ; nop
    0xe000, #  6 ; set pins 0
    0xe53f, #  7 ; set x 31 [5]
    # ==> delay_low:
    0xbd42, #  8 ; nop [29]
    0x0048, #  9 ; jmp x-- delay_low
    # ==> other:
    0x000a, # 10 ; jmp  other
    0x2085, # 11 ; wait 1 gpio 5 rel=False
    0x4027, # 12 ; in x, 7
    0x6048, # 13 ; out y, 8
    0x8060, # 14 ; push iffull=True block=True
    0x8080, # 15 ; pull ifempty=False block=False
    0xa0ae, # 16 ; mov pc, ~isr
    0xa0b7, # 17 ; mov pc, ::osr
    0xc027, # 18 ; irq 7 rel=False clear=False wait=True
    0xe04c, # 19 ; set y 12
]
```

Outputs editable source with smaller runtime:
```
def {name}_emit(v: InstructionVisitor):
    v.irq(0, rel=True, clear=False, wait=True)
    v.set("pins", 1)
    v.set("x", 31)[5]
    # [ 3] ==> delay_high:
    v.nop()[29]
    v.jmp("x--", 3)
    v.nop()
    v.set("pins", 0)
    v.set("x", 31)[5]
    # [ 8] ==> delay_low:
    v.nop()[29]
    v.jmp("x--", 8)
    # [10] ==> other:
    v.jmp("", 10)
    v.wait(1, "gpio", 5, rel=False)
    v.in_("x", 7)
    v.out("y", 8)
    v.push(iffull=True, block=True)
    v.pull(ifempty=False, block=False)
    v.mov("pc", "~isr")
    v.mov("pc", "::osr")
    v.irq(7, rel=False, clear=False, wait=True)
    v.set("y", 12)
```
