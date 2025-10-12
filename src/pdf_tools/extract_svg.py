import json
import re
from pathlib import Path

import fitz  # PyMuPDF
from bs4 import BeautifulSoup


def optimize_svg_precision(svg_text, precision=2):
    """
    Reduce decimal precision in SVG coordinates to compress file size.

    Uses XML parsing to safely modify numeric attributes and path data
    without breaking the SVG structure.

    Args:
        svg_text: Raw SVG string
        precision: Number of decimal places to keep (default: 2)

    Returns:
        Optimized SVG string
    """

    def round_number(num_str):
        """Round a number string to specified precision."""
        try:
            num = float(num_str)
            rounded = round(num, precision)
            # Format and remove unnecessary trailing zeros and decimal point
            formatted = f"{rounded:.{precision}f}".rstrip('0').rstrip('.')
            return formatted if formatted else '0'
        except (ValueError, TypeError):
            return num_str

    def round_numbers_in_string(text):
        """Find and round all numbers in a string (for path data, etc)."""
        if not text:
            return text
        # Match floating point numbers:
        # - Optional minus sign
        # - Either: digits + optional decimal + optional digits
        # - Or: just decimal point + digits (for .999 style numbers)
        pattern = r'-?(?:\d+\.?\d*|\.\d+)'

        def replace_num(match):
            num_str = match.group(0)
            # Only round if it has a decimal point
            if '.' in num_str:
                return round_number(num_str)
            return num_str

        return re.sub(pattern, replace_num, text)

    # Parse SVG with BeautifulSoup
    soup = BeautifulSoup(svg_text, 'xml')

    # Attributes that contain numeric values to round
    numeric_attrs = ['x', 'y', 'width', 'height', 'cx', 'cy', 'r', 'rx', 'ry',
                     'x1', 'y1', 'x2', 'y2', 'stroke-width', 'font-size']

    # Attributes that contain lists of numbers (space or comma separated)
    list_attrs = ['viewBox', 'points']

    # Attributes that contain complex number sequences (path data, transforms)
    complex_attrs = ['d', 'transform']

    # Process all elements
    for element in soup.find_all():
        # Round simple numeric attributes
        for attr in numeric_attrs:
            if attr in element.attrs:
                element[attr] = round_number(element[attr])

        # Round list-based attributes
        for attr in list_attrs:
            if attr in element.attrs:
                values = re.split(r'[\s,]+', element[attr])
                rounded_values = [round_number(v) for v in values if v]
                element[attr] = ' '.join(rounded_values)

        # Round complex attributes (paths and transforms)
        for attr in complex_attrs:
            if attr in element.attrs:
                element[attr] = round_numbers_in_string(element[attr])

    # Return optimized SVG
    return str(soup)



class PDFSVGExtractor:
    def __init__(self, pdf_dir="./pdfs", output_dir="output/svg"):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_svg_from_pdf(self, pdf_path, page_range=None):
        """Extract SVG content from PDF pages with hyperlink metadata."""
        doc = fitz.open(pdf_path)
        pdf_name = Path(pdf_path).stem
        extracted_files = []

        pages = range(len(doc)) if page_range is None else page_range

        for page_num in pages:
            page = doc[page_num]
            svg_text = page.get_svg_image()

            # Optimize SVG by reducing coordinate precision
            if svg_text:
                svg_text = optimize_svg_precision(svg_text, precision=2)

            if svg_text:
                # Extract hyperlinks from this page
                links = page.get_links()
                hyperlinks = []
                for link in links:
                    if link["kind"] == 2:  # URI link
                        hyperlinks.append(
                            {
                                "uri": link["uri"],
                                "bbox": {
                                    "x": link["from"].x0,
                                    "y": link["from"].y0,
                                    "width": link["from"].width,
                                    "height": link["from"].height,
                                },
                            }
                        )

                # Save SVG file
                output_file = self.output_dir / f"{pdf_name}_page_{page_num + 1}.svg"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(svg_text)
                extracted_files.append(output_file)

                # Save hyperlink metadata if any links found
                if hyperlinks:
                    metadata_file = (
                        self.output_dir / f"{pdf_name}_page_{page_num + 1}_links.json"
                    )
                    with open(metadata_file, "w", encoding="utf-8") as f:
                        json.dump(hyperlinks, f, indent=2)
                    print(
                        f"Extracted SVG with {len(hyperlinks)} hyperlinks: "
                        f"{output_file}"
                    )
                else:
                    print(f"Extracted SVG: {output_file}")

        doc.close()
        return extracted_files

    def extract_all_pdfs(self):
        """Extract SVG from all PDFs in the PDF directory."""
        if not self.pdf_dir.exists():
            print(f"Error: PDF directory '{self.pdf_dir.resolve()}' does not exist.")
            print("Please create the directory and add PDF files to it.")
            return []

        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"Error: No PDF files found in '{self.pdf_dir.resolve()}'.")
            print("Please add PDF files to the directory.")
            return []

        print(f"Found {len(pdf_files)} PDF file(s) in '{self.pdf_dir.resolve()}'")

        all_extracted = []
        for pdf_file in pdf_files:
            print(f"Processing {pdf_file.name}")
            extracted = self.extract_svg_from_pdf(pdf_file)
            all_extracted.extend(extracted)

        return all_extracted


def main():
    extractor = PDFSVGExtractor()
    extracted_files = extractor.extract_all_pdfs()
    print(f"Extracted {len(extracted_files)} SVG files")


if __name__ == "__main__":
    main()
