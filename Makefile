.PHONY: all clean test lint setup install dev-install html svg extract optimize publish help

UV := uv
SRC_DIR := src
TEST_DIR := tests
OUTPUT_DIR := output
PUBLISH_DIR := publish

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
	@echo "  publish     - Copy generated HTML files to PUBLISH_DIR"
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

publish:
	@echo "Publishing HTML files to $(PUBLISH_DIR)..."
	@# Check if PUBLISH_DIR exists (following symlinks with -L)
	@if [ ! -e "$(PUBLISH_DIR)" ]; then \
		echo "Error: PUBLISH_DIR '$(PUBLISH_DIR)' does not exist"; \
		echo "Create it with: mkdir $(PUBLISH_DIR)"; \
		echo "Or symlink it to your website: ln -s /path/to/website $(PUBLISH_DIR)"; \
		exit 1; \
	fi
	@if [ ! -d "$(OUTPUT_DIR)/html" ]; then \
		echo "Error: No HTML files to publish. Run 'make html' first."; \
		exit 1; \
	fi
	@# Copy generated HTML files (YYYY-MM-DD.html pattern and index.html)
	cp -v $(OUTPUT_DIR)/html/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].html $(PUBLISH_DIR)/ 2>/dev/null || true
	cp -v $(OUTPUT_DIR)/html/index.html $(PUBLISH_DIR)/ 2>/dev/null || true
	@# Copy images directory if it exists
	@if [ -d "$(OUTPUT_DIR)/html/images" ]; then \
		echo "Copying images directory..."; \
		cp -r $(OUTPUT_DIR)/html/images $(PUBLISH_DIR)/; \
	fi
	@echo "Published to $(PUBLISH_DIR)"

clean:
	@echo "Cleaning generated files (preserving $(PUBLISH_DIR))..."
	@# Clean SVG and HTML directories, but not publish
	rm -rf $(OUTPUT_DIR)/svg $(OUTPUT_DIR)/html
	@# Clean Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +