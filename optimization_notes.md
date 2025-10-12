# SVG Optimization Strategy

This project uses a two-stage optimization approach for SVG files extracted from PDFs:

## Stage 1: Coordinate Precision Reduction (Python)

**Implementation**: `src/pdf_tools/extract_svg.py` - `optimize_svg_precision()` function

**What it does**:
- Reduces decimal precision from 8-9 places to 2 decimal places
- Uses BeautifulSoup to safely parse and modify SVG as XML
- Handles all numeric attributes (coordinates, transforms, path data)

**Savings**: ~20% reduction in file size

## Stage 2: SVGO Optimization (Optional)

**Implementation**: `Makefile` - `optimize` target  

**What it does**:
- Runs `svgo` command-line tool with `--multipass` flag
- Removes unnecessary whitespace, comments, and metadata
- Optimizes path data and transforms
- Shortens IDs and consolidates styles
- Gracefully skips if `svgo` is not installed

**Savings**: Additional ~43% reduction (on top of Stage 1)

## Combined Results

**Test case**: Single handwritten PDF page (1.8MB original SVG)
- After coordinate precision: 1.49MB (20% reduction)
- After svgo: 761KB (58% total reduction)
- Gzipped on wire: ~250KB (87% total reduction from original)

## Installation

To get full optimization, install svgo:
```bash
npm install -g svgo
```

## Usage

The optimization runs automatically when you build HTML:
```bash
make html  # Runs: extract → optimize → generate HTML
```

Or run optimization separately:
```bash
make optimize
```
