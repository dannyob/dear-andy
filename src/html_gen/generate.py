import os
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup


class HTMLGenerator:
    def __init__(self, svg_dir="output/svg", html_dir="output/html", template_dir="templates", images_dir="images"):
        self.svg_dir = Path(svg_dir)
        self.html_dir = Path(html_dir)
        self.template_dir = Path(template_dir)
        self.images_dir = Path(images_dir)
        
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def create_default_template(self):
        """Create a default HTML template if none exists."""
        template_path = self.template_dir / "base.html"
        if not template_path.exists():
            template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .svg-container {
            text-align: center;
            margin: 40px 0;
            padding: 20px;
            border-bottom: 1px solid #ddd;
            page-break-after: always;
            min-height: 600px;
            display: block;
        }
        .svg-container:last-child {
            border-bottom: none;
            page-break-after: auto;
        }
        .svg-container svg {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        {% for svg_content in svg_contents %}
        <div class="svg-container">
            {{ svg_content|safe }}
        </div>
        {% endfor %}
    </div>
</body>
</html>"""
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            print(f"Created default template: {template_path}")

    def process_svg(self, svg_path):
        """Process SVG file and return cleaned content with unique IDs."""
        svg_path = Path(svg_path)  # Ensure it's a Path object
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        soup = BeautifulSoup(svg_content, 'xml')
        svg_element = soup.find('svg')
        
        if svg_element:
            # Add data attributes to identify the source file
            svg_element['data-source-file'] = svg_path.name
            page_number = svg_path.stem.split('_page_')[1] if '_page_' in svg_path.stem else '1'
            svg_element['data-page-number'] = page_number
            
            # Make all IDs unique by adding page number suffix
            page_suffix = f"_p{page_number}"
            
            # Find all elements with id attributes and make them unique
            for element in soup.find_all(attrs={'id': True}):
                old_id = element['id']
                new_id = f"{old_id}{page_suffix}"
                element['id'] = new_id
            
            # Update all url(#id) references to match the new IDs
            svg_str = str(svg_element)
            import re
            # Find all url(#something) patterns and add the page suffix
            def replace_url_ref(match):
                ref_id = match.group(1)
                return f'url(#{ref_id}{page_suffix})'
            
            svg_str = re.sub(r'url\(#([^)]+)\)', replace_url_ref, svg_str)
            
            return svg_str
        return svg_content

    def copy_images_to_html_dir(self):
        """Copy all images from images directory to html output directory."""
        if not self.images_dir.exists():
            return []
        
        copied_images = []
        html_images_dir = self.html_dir / "images"
        html_images_dir.mkdir(exist_ok=True)
        
        # Get all image files and sort them alphabetically by filename
        image_files = [f for f in self.images_dir.glob("*") 
                      if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']]
        image_files.sort(key=lambda x: x.name.lower())
        
        for image_file in image_files:
            dest_path = html_images_dir / image_file.name
            shutil.copy2(image_file, dest_path)
            copied_images.append(f"images/{image_file.name}")
        
        return copied_images

    def generate_html_from_svg_group(self, svg_files, output_name):
        """Generate HTML from a group of SVG files."""
        self.create_default_template()
        
        template = self.env.get_template('base.html')
        svg_contents = []
        
        for svg_file in svg_files:
            svg_content = self.process_svg(svg_file)
            svg_contents.append(svg_content)
        
        # Copy images and pass all of them to the template
        copied_images = self.copy_images_to_html_dir()
        
        html_content = template.render(
            title=output_name.replace('_', ' ').title(),
            svg_contents=svg_contents,
            photo_filenames=copied_images
        )
        
        output_path = self.html_dir / f"{output_name}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Generated HTML: {output_path}")
        return output_path

    def generate_all_html(self):
        """Generate HTML files from all SVG files, grouped by PDF source."""
        if not self.svg_dir.exists():
            print(f"SVG directory {self.svg_dir} does not exist")
            return []

        svg_groups = {}
        for svg_file in self.svg_dir.glob("*.svg"):
            pdf_name = svg_file.stem.rsplit('_page_', 1)[0]
            if pdf_name not in svg_groups:
                svg_groups[pdf_name] = []
            svg_groups[pdf_name].append(svg_file)

        generated_files = []
        for pdf_name, svg_files in svg_groups.items():
            # Sort by page number numerically instead of alphabetically
            svg_files.sort(key=lambda x: int(x.stem.split('_page_')[1]) if '_page_' in x.stem else 0)
            output_file = self.generate_html_from_svg_group(svg_files, pdf_name)
            generated_files.append(output_file)

        return generated_files


def main():
    generator = HTMLGenerator()
    generated_files = generator.generate_all_html()
    print(f"Generated {len(generated_files)} HTML files")


if __name__ == "__main__":
    main()