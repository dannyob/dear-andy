import json
from pathlib import Path

import fitz  # PyMuPDF


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
