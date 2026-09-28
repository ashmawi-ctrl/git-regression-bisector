.PHONY: install lint test quality

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check regression_bisector tests

test:
	pytest

quality: lint test
