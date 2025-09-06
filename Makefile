.PHONY: all clean test lint setup install dev-install html svg extract help

UV := uv
SRC_DIR := src
TEST_DIR := tests
OUTPUT_DIR := output

all: test html

help:
	@echo "Available targets:"
	@echo "  setup       - Initialize uv project and install dependencies"
	@echo "  install     - Install production dependencies"
	@echo "  dev-install - Install development dependencies"
	@echo "  test        - Run all tests"
	@echo "  lint        - Run code linting"
	@echo "  extract     - Extract SVG from PDFs"
	@echo "  html        - Generate HTML from SVG"
	@echo "  clean       - Remove generated files and cache"
	@echo "  all         - Run tests and generate HTML"

setup:
	$(UV) sync

install:
	$(UV) sync --no-dev

dev-install:
	$(UV) sync

test: setup
	$(UV) run pytest $(TEST_DIR) -v

lint: setup
	$(UV) run ruff check $(SRC_DIR) $(TEST_DIR)
	$(UV) run ruff format --check $(SRC_DIR) $(TEST_DIR)

format: setup
	$(UV) run ruff format $(SRC_DIR) $(TEST_DIR)

extract: setup
	$(UV) run python -m src.pdf_tools.extract_svg

html: setup extract
	$(UV) run python -m src.html_gen.generate

clean:
	rm -rf $(OUTPUT_DIR)/*
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +