MYPY		= mypy --no-color-output
MPREMOTE	= mpremote
MICROPYPATH	= `pwd`:`pwd`/lib
MPY		= MICROPYPATH=$(MICROPYPATH) micropython

BASE_SRCS =				\
	upioasm/__init__.py		\
	upioasm/error.py		\
	upioasm/program.py		\

EMITTER_SRCS =				\
	upioasm/emitter.py

DEFINES_SRCS =				\
	upioasm/defines.py		\
	upioasm/resolver.py

ASM_PIO_SRCS =				\
	upioasm/assembler.py		\
	upioasm/opcodes.py		\
	upioasm/parser.py		\
	upioasm/registers.py		\
	upioasm/syntax.py

OTHER_SRCS =				\
	upioasm/xpileassembler.py	\
	upioasm/xpileemitter.py		\
	upioasm/xpilelabels.py		\
	upioasm/xpileprinter.py


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
