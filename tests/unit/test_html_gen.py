import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from src.html_gen.generate import HTMLGenerator


class TestHTMLGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = HTMLGenerator(
            svg_dir="test_svg", html_dir="test_html", template_dir="test_templates"
        )

    def tearDown(self):
        # Clean up test directories
        for dir_name in ["test_html", "test_templates"]:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)

    @patch("builtins.open", new_callable=mock_open, read_data="<svg>test content</svg>")
    def test_process_svg(self, mock_file):
        result = self.generator.process_svg("test.svg")

        self.assertIn("<svg", result)
        self.assertIn("test content", result)
        self.assertIn('data-source-file="test.svg"', result)
        mock_file.assert_called_once()

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_default_template(self, mock_file, mock_exists, mock_mkdir):
        mock_exists.return_value = False

        self.generator.create_default_template()

        mock_file.assert_called()
        written_content = mock_file().write.call_args[0][0]
        self.assertIn("<!DOCTYPE html>", written_content)
        self.assertIn("{{ title }}", written_content)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_generate_all_html_no_svg_directory(self, mock_glob, mock_exists):
        mock_exists.return_value = False

        result = self.generator.generate_all_html()

        self.assertEqual(result, [])
        mock_glob.assert_not_called()

    @patch("src.html_gen.generate.HTMLGenerator.copy_images_to_html_dir")
    @patch("src.html_gen.generate.HTMLGenerator.create_default_template")
    @patch("src.html_gen.generate.HTMLGenerator.process_svg")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    def test_generate_html_from_svg_group(
        self, mock_mkdir, mock_file, mock_process, mock_template, mock_copy_images
    ):
        mock_process.return_value = "<svg>processed</svg>"
        mock_copy_images.return_value = []  # No images

        # Mock the jinja2 template
        mock_template_obj = MagicMock()
        mock_template_obj.render.return_value = "<html><body>test</body></html>"
        self.generator.env.get_template = MagicMock(return_value=mock_template_obj)

        svg_files = [Path("test_page_1.svg"), Path("test_page_2.svg")]
        result = self.generator.generate_html_from_svg_group(svg_files, "test_output")

        self.assertIsInstance(result, Path)
        mock_process.assert_called()
        mock_file.assert_called()


if __name__ == "__main__":
    unittest.main()
