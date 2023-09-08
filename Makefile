# Define variables
PYTHON = python
PIP = pip
TEST_DIR = backend/tests/cli


# Run Python tests
test_cli:
	$(PYTHON) -m pytest $(TEST_DIR)


# Phony targets
.PHONY: install test clean all
