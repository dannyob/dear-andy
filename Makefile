.PHONY: all clean test lint setup install dev-install html svg extract optimize help

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
	@echo "  optimize    - Optimize SVG files with svgo (if available)"
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

optimize: setup
	@echo "Checking for svgo..."
	@if command -v svgo >/dev/null 2>&1; then \
		echo "Found svgo, optimizing SVG files..."; \
		svgo -f $(OUTPUT_DIR)/svg --multipass --quiet; \
		echo "SVG optimization complete"; \
	else \
		echo "svgo not found - skipping SVG optimization"; \
		echo "Install with: npm install -g svgo"; \
	fi

html: setup extract optimize
	$(UV) run python -m src.html_gen.generate

clean:
	rm -rf $(OUTPUT_DIR)/*
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +