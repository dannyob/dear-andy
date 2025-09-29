# Dear Andy

Python tools for creating static HTML from PDF-extracted SVG content with automatic hyperlink preservation.

Written so I could write handwritten letters to [Andy R.](https://misterandyriley.com/) 
using a [Daylight DC-1](https://daylightcomputer.com/) and [Xodo](https://xodo.com/) and output
them as dinky little web pages, because I can't be bothered to buy stamps. 

You might find it useful too!

## Setup

Install dependencies using uv:

```bash
make setup
```

## Usage

1. Place PDF files in a `pdfs/` directory.
2. **Optional**: Add images to display at the bottom of HTML pages:
   - Place images in the same `pdfs/` directory
   - Name them with the PDF prefix: `{pdf_name}-{description}.{ext}`
   - Example: For `2025-09-28.pdf`, add `2025-09-28-photo1.jpg`, `2025-09-28-beach.png`
   - Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
3. Extract SVG from PDFs: `make extract`
4. Generate HTML from SVG: `make html`
5. Or run both: `make all`

Images will automatically appear at the bottom of the generated HTML with polaroid-style formatting.

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
