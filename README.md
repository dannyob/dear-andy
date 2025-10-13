# Dear Andy

Python tools for creating static HTML from PDF-extracted SVG content with automatic hyperlink preservation.

Written so I could write handwritten letters to [Andy R.](https://misterandyriley.com/)
using a [Daylight DC-1](https://daylightcomputer.com/) and [Xodo](https://xodo.com/) and output
them as dinky little web pages, because I can't be bothered to buy stamps.

You might find it useful too!

## Quick Start

```bash
# Install dependencies
make setup

# Set up your template
cp templates/sample_base.html templates/base.html

# Add your PDFs to pdfs/ directory, then:
make html

# View output in output/html/
```

## Basic Workflow

1. Place PDFs in `pdfs/` directory
2. Run `make html` to generate HTML pages in `output/html/`
3. (Optional) Run `make publish` to copy files to your website

### Adding Images

Place images in the `pdfs/` directory with matching PDF names:
- For `2025-09-28.pdf`, add `2025-09-28-photo1.jpg`, `2025-09-28-beach.png`, etc.
- Supported: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Images appear at the bottom of pages with polaroid-style formatting

## Publishing

Create a symlink from `publish/` to your website directory:

```bash
ln -s /path/to/your/website/directory publish
make publish
```

Or create a regular `publish/` directory and manually copy files from there to your website.

The publish command copies generated HTML, `index.html`, and `images/` directory while preserving other files.

## Optimization

SVG files are automatically optimized in two stages:

1. **Coordinate precision reduction** (built-in): ~20% size reduction
2. **SVGO optimization** (optional): Additional ~43% reduction

For full optimization, install svgo: `npm install -g svgo`

**Results**: A 1.8MB handwritten PDF becomes ~250KB on the wire (87% reduction)

## Development

- **Test**: `make test`
- **Format**: `make format`
- **Lint**: `make lint`
- **Clean**: `make clean` (preserves `publish/` directory)
