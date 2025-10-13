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

1. Copy templates/sample_base.html to templates/base.html
2. Place PDF files in a `pdfs/` directory.
3. **Optional**: Add images to display at the bottom of HTML pages:
   - Place images in the same `pdfs/` directory
   - Name them with the PDF prefix: `{pdf_name}-{description}.{ext}`
   - Example: For `2025-09-28.pdf`, add `2025-09-28-photo1.jpg`, `2025-09-28-beach.png`
   - Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
4. Extract SVG from PDFs: `make extract`
5. Generate HTML from SVG: `make html`
6. Or run both: `make all`

Using the default template, images will automatically appear at the bottom of
the generated HTML with polaroid-style formatting.

## SVG Optimization

This project uses a two-stage optimization approach for SVG files extracted from PDFs:

### Stage 1: Coordinate Precision Reduction (Python)

**Implementation**: `src/pdf_tools/extract_svg.py` - `optimize_svg_precision()` function

Reduces decimal precision from 8-9 places to 2 decimal places using BeautifulSoup to safely parse and modify SVG as XML. Handles all numeric attributes (coordinates, transforms, path data).

**Savings**: ~20% reduction in file size

### Stage 2: SVGO Optimization (Optional)

**Implementation**: `Makefile` - `optimize` target

Runs `svgo` command-line tool with `--multipass` flag to remove unnecessary whitespace, comments, and metadata, optimize path data and transforms, and consolidate styles. Gracefully skips if `svgo` is not installed.

**Savings**: Additional ~43% reduction (on top of Stage 1)

### Combined Results

**Test case**: Single handwritten PDF page (1.8MB original SVG)
- After coordinate precision: 1.49MB (20% reduction)
- After svgo: 761KB (58% total reduction)
- Gzipped on wire: ~250KB (87% total reduction from original)

### Installation

To get full optimization, install svgo:
```bash
npm install -g svgo
```

The optimization runs automatically when you build HTML with `make html`.

## Publishing

The `publish/` directory is where `make publish` will copy generated HTML files.

### Option 1: Symlink to Your Website (Recommended)

Create a symlink that points to your static website directory:

```bash
ln -s /path/to/your/website/directory publish
```

Now `make publish` will copy files directly to your website.

### Option 2: Regular Directory

Create a regular directory:

```bash
mkdir publish
```

Then manually copy or deploy files from `publish/` to your website.

### Publishing Workflow

1. Generate HTML: `make html`
2. Publish: `make publish`

The publish command will:
- Copy all `YYYY-MM-DD.html` files
- Copy `index.html`
- Copy the `images/` directory if it exists
- Preserve other files in the publish directory (won't delete anything)

**Note**: The `make clean` command will NOT delete the `publish/` directory or symlink, so it's safe to run.

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
