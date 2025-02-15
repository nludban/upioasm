MYPY		= mypy --no-color-output
MPREMOTE	= mpremote
MICROPYPATH	= `pwd`:`pwd`/lib
MPY		= MICROPYPATH=$(MICROPYPATH) micropython

all: type-check run-examples

type-check:
	$(MYPY) -p upioasm
	$(MYPY) -p examples

install:
	$(MPREMOTE) mkdir :lib/ || exit 0
	$(MPREMOTE) cp lib/typing*.py :lib/
	$(MPREMOTE) mkdir :upioasm/ || exit 0
	$(MPREMOTE) cp upioasm/*.py :upioasm/

run-examples:
	$(MPY) examples/pio_1hz.py
