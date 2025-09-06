# Dear Andy

Python tools for creating static HTML from PDF-extracted SVG content.

## Setup

Install dependencies using uv:

```bash
make setup
```

## Usage

1. Place PDF files in a `../pdfs/` directory (out-of-tree)
2. Extract SVG from PDFs: `make extract`
3. Generate HTML from SVG: `make html`
4. Or run both: `make all`

## Testing

Run tests with: `make test`

## Project Structure

```
src/
├── pdf_tools/          # PDF processing modules
│   └── extract_svg.py  # SVG extraction from PDFs
├── html_gen/           # HTML generation modules
│   └── generate.py     # HTML template rendering
tests/
├── unit/               # Unit tests
output/
├── svg/                # Extracted SVG files
└── html/               # Generated HTML files
```

## Development

- Format code: `make format`
- Run linter: `make lint`
- Clean build artifacts: `make clean`