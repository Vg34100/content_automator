.PHONY: help setup test clean lint format

help:
	@echo "Available commands:"
	@echo "setup    - Install dependencies and set up pre-commit"
	@echo "test     - Run tests"
	@echo "lint     - Run linters"
	@echo "format   - Format code"
	@echo "clean    - Clean up build files"

setup:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v

lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".tox" -exec rm -r {} +
	find . -type d -name "build" -exec rm -r {} +
	find . -type d -name "dist" -exec rm -r {} +