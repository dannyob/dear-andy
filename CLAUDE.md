# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python tool for converting handwritten letters from PDF files (created on tablets) into static HTML pages. The workflow extracts SVG content from PDFs and renders them into HTML using Jinja2 templates with a vintage letter aesthetic.

## Key Commands

- **Setup**: `make setup` - Initialize uv project and install dependencies
- **Extract SVG**: `make extract` - Extract SVG from PDFs in `../pdfs/` directory
- **Optimize SVG**: `make optimize` - Run svgo on SVG files (if svgo is installed)
- **Generate HTML**: `make html` - Full pipeline: extract → optimize → convert to HTML
- **Publish**: `make publish` - Copy generated HTML files to PUBLISH_DIR (configurable in Makefile)
- **Full pipeline**: `make all` - Run tests and generate HTML
- **Test**: `make test` - Run pytest with verbose output
- **Lint**: `make lint` - Run ruff linting and format checking
- **Format**: `make format` - Auto-format code with ruff
- **Single test**: `uv run pytest tests/unit/test_html_gen.py::TestHTMLGenerator::test_specific_method -v`

## Architecture

### Three-stage processing pipeline:

1. **PDF → SVG** (`src/pdf_tools/extract_svg.py`):
   - `PDFSVGExtractor` class uses PyMuPDF to extract SVG from each PDF page
   - Automatically detects and extracts PDF hyperlink annotations
   - Built-in coordinate precision reduction (2 decimal places) via `optimize_svg_precision()`
   - Outputs to `output/svg/` with naming pattern: `{pdf_name}_page_{n}.svg`
   - Saves hyperlink metadata as `{pdf_name}_page_{n}_links.json` when links are found

2. **SVG Optimization** (Makefile `optimize` target):
   - Automatically runs `svgo` on extracted SVG files if available
   - Provides additional compression beyond coordinate rounding
   - Gracefully skips if svgo is not installed
   - Install svgo with: `npm install -g svgo`

3. **SVG → HTML** (`src/html_gen/generate.py`):
   - `HTMLGenerator` class processes SVG files and renders HTML using Jinja2
   - Groups SVG files by original PDF name and sorts pages numerically
   - Handles SVG ID conflicts by adding unique page suffixes to IDs and `url()` references
   - Automatically applies PDF hyperlinks by turning intersecting SVG paths blue and making them clickable
   - Filters out background paths to ensure precise hyperlink targeting
   - Copies images from `images/` directory to `output/html/images/`

### Template System

- Base template: `templates/base.html` - Letter-style layout with Sutro Tower header
- Supports polaroid-style image integration via `photo_filenames` variable
- SVG content rendered with `|safe` filter and unique data attributes

### Directory Structure

- PDFs must be placed in `../pdfs/` (out-of-tree)
- SVG extraction: `output/svg/`
- Hyperlink metadata: `output/svg/` (JSON files alongside SVG when links exist)
- HTML generation: `output/html/`
- Images copied from `images/` to `output/html/images/`
- Published files: `publish/` directory (can be a symlink to your website)

## Development Notes

- Uses uv for dependency management
- Python 3.8+ compatibility required
- Ruff for linting/formatting (88 char line length)
- PyTest for testing with coverage support
- Key dependencies: PyMuPDF, BeautifulSoup4, Jinja2, Pillow