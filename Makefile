
.PHONY: install test
.DEFAULT: install test

TRIAL:=$(shell which trial)
VERSION:=$(shell git describe)

define PYTHON_WHICH
import platform
import sys
sys.stdout.write(platform.python_implementation())
endef

PYTHON_IMPLEMENTATION:=$(shell python3 -c '$(PYTHON_WHICH)')

test:
	python3 setup.py test

coverage-test:
ifeq ($(PYTHON_IMPLEMENTATION),PyPy)
	@echo "Detected PyPy... not running coverage."
	python setup.py test
else
	coverage run --rcfile=".coveragerc" $(TRIAL) ./test/test_*.py
	coverage report --rcfile=".coveragerc"
endif

coverage-html:
	coverage html --rcfile=".coveragerc"

coverage: coverage-test coverage-html

tags:
	find ./gettor -type f -name "*.py" -print | xargs etags
