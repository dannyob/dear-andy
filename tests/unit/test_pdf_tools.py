import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import shutil

from src.pdf_tools.extract_svg import PDFSVGExtractor


class TestPDFSVGExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = PDFSVGExtractor(pdf_dir="test_pdfs", output_dir="test_output")

    def tearDown(self):
        # Clean up test directories
        if Path("test_output").exists():
            shutil.rmtree("test_output")

    @patch("src.pdf_tools.extract_svg.fitz")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_extract_svg_from_pdf(self, mock_mkdir, mock_file, mock_fitz):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_svg_image.return_value = "<svg>test</svg>"
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        result = self.extractor.extract_svg_from_pdf("test.pdf")

        self.assertEqual(len(result), 1)
        mock_fitz.open.assert_called_once_with("test.pdf")
        mock_file.assert_called_once()
        mock_doc.close.assert_called_once()

    @patch("src.pdf_tools.extract_svg.fitz")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_extract_svg_empty_page(self, mock_mkdir, mock_file, mock_fitz):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_svg_image.return_value = None
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        result = self.extractor.extract_svg_from_pdf("test.pdf")

        self.assertEqual(len(result), 0)
        mock_file.assert_not_called()

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_extract_all_pdfs_no_directory(self, mock_glob, mock_exists):
        mock_exists.return_value = False

        result = self.extractor.extract_all_pdfs()

        self.assertEqual(result, [])
        mock_glob.assert_not_called()


if __name__ == "__main__":
    unittest.main()
