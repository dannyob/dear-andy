import json
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


class HTMLGenerator:
    def __init__(
        self,
        svg_dir="output/svg",
        html_dir="output/html",
        template_dir="templates",
        pdfs_dir="pdfs",
    ):
        self.svg_dir = Path(svg_dir)
        self.html_dir = Path(html_dir)
        self.template_dir = Path(template_dir)
        self.pdfs_dir = Path(pdfs_dir)

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
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            print(f"Created default template: {template_path}")

    def process_svg(self, svg_path):
        """Process SVG file and return cleaned content with unique IDs."""
        svg_path = Path(svg_path)  # Ensure it's a Path object
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        soup = BeautifulSoup(svg_content, "xml")
        svg_element = soup.find("svg")

        if svg_element:
            # Add data attributes to identify the source file
            svg_element["data-source-file"] = svg_path.name
            page_number = (
                svg_path.stem.split("_page_")[1] if "_page_" in svg_path.stem else "1"
            )
            svg_element["data-page-number"] = page_number

            # Make all IDs unique by adding page number suffix
            page_suffix = f"_p{page_number}"

            # Find all elements with id attributes and make them unique
            for element in soup.find_all(attrs={"id": True}):
                old_id = element["id"]
                new_id = f"{old_id}{page_suffix}"
                element["id"] = new_id

            # Update all url(#id) references to match the new IDs
            svg_str = str(svg_element)
            import re

            # Find all url(#something) patterns and add the page suffix
            def replace_url_ref(match):
                ref_id = match.group(1)
                return f"url(#{ref_id}{page_suffix})"

            svg_str = re.sub(r"url\(#([^)]+)\)", replace_url_ref, svg_str)

            # Apply PDF hyperlinks if metadata exists
            svg_str = self.apply_pdf_hyperlinks(svg_str, svg_path)

            return svg_str
        return svg_content

    def load_hyperlink_metadata(self, svg_path):
        """Load hyperlink metadata for an SVG file if it exists."""
        svg_path = Path(svg_path)
        metadata_file = svg_path.parent / f"{svg_path.stem}_links.json"

        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def extract_path_bbox(self, path_d):
        """Extract rough bounding box from SVG path data."""
        if not path_d:
            return None

        # Skip full-page background/frame paths
        if "M0 0H595V842H0Z" in path_d or "M 0 0 H 595 V 842 H 0 Z" in path_d:
            return None

        # Find all coordinate pairs in the path
        coords = re.findall(r"[-+]?\d*\.?\d+", path_d)
        if len(coords) < 2:
            return None

        # Convert to floats and pair them up
        numbers = [float(c) for c in coords]
        x_coords = numbers[::2]  # Every other starting with 0
        y_coords = numbers[1::2]  # Every other starting with 1

        if not x_coords or not y_coords:
            return None

        bbox = {
            "x1": min(x_coords),
            "y1": min(y_coords),
            "x2": max(x_coords),
            "y2": max(y_coords),
        }

        # Multi-criteria filtering for background/container elements
        width = bbox["x2"] - bbox["x1"]
        height = bbox["y2"] - bbox["y1"]

        # 1. Skip very large paths (page-spanning backgrounds)
        if width > 400 or height > 600:
            return None

        # 2. Skip geometric shapes that are likely backgrounds/containers
        if self.is_likely_background_element(path_d, width, height):
            return None

        return bbox

    def is_likely_background_element(self, path_d, width, height):
        """Detect if a path is likely a background/container element."""
        # Count different command types
        h_v_count = len(re.findall(r"[HV]", path_d))  # Horizontal/Vertical lines
        curve_count = len(re.findall(r"C", path_d))  # Curves
        coords_count = len(re.findall(r"[-+]?\d*\.?\d+", path_d))

        # Geometric shapes: mostly H/V commands, no curves, simple structure
        is_geometric = h_v_count >= 2 and curve_count == 0

        # Low coordinate density indicates simple geometric shapes
        area = width * height
        coord_density = coords_count / max(area, 1) if area > 0 else 0
        is_simple = coord_density < 0.01  # Very few coordinates per pixel

        # Wide elements are often containers/backgrounds
        is_wide = width > 200

        # Combine criteria: geometric OR (simple AND wide)
        return is_geometric or (is_simple and is_wide)

    def rect_intersects(self, rect1, rect2):
        """Check if two rectangles intersect."""
        return not (
            rect1["x2"] < rect2["x1"]
            or rect2["x2"] < rect1["x1"]
            or rect1["y2"] < rect2["y1"]
            or rect2["y2"] < rect1["y1"]
        )

    def path_intersects_rect(self, path_d, rect):
        """Check if any part of an SVG path actually intersects with a rectangle."""
        if not path_d:
            return False

        # Skip full-page background/frame paths
        if "M0 0H595V842H0Z" in path_d or "M 0 0 H 595 V 842 H 0 Z" in path_d:
            return False

        # Apply existing background filtering first
        path_bbox = self.extract_path_bbox(path_d)
        if not path_bbox:
            return False

        # Removed debug logging - keeping for future debugging if needed
        is_iso_case = False

        # Parse path data to extract coordinates and check for intersections
        import re

        # Find all coordinate pairs in the path
        coords = re.findall(r"[-+]?\d*\.?\d+", path_d)
        if len(coords) < 2:
            return False

        # Convert to floats and pair them up
        numbers = [float(c) for c in coords]
        points = [(numbers[i], numbers[i + 1]) for i in range(0, len(numbers) - 1, 2)]

        if not points:
            return False

        # Count points inside the rectangle and total points
        points_inside = 0
        for x, y in points:
            if rect["x1"] <= x <= rect["x2"] and rect["y1"] <= y <= rect["y2"]:
                points_inside += 1

        # Require a significant portion of points to be inside (at least 20%)
        # OR the path bounding box to have substantial overlap
        if len(points) > 0:
            percentage_inside = points_inside / len(points)

            if is_iso_case and (percentage_inside > 0 or path_bbox):
                print(f"ISO DEBUG: Path with bbox {path_bbox}")
                print(
                    f"  Points inside: {points_inside}/{len(points)} = "
                    f"{percentage_inside:.2%}"
                )
                print(f"  First few points: {points[:5]}")
                print(f"  Path preview: {path_d[:100]}...")

            if percentage_inside >= 0.5:  # At least 50% of points inside
                if is_iso_case:
                    print("  -> INCLUDED (percentage)")
                return True

        # Fallback: check if the path bounding box has good overlap with hyperlink box
        if path_bbox:
            # Calculate overlap area
            overlap_x1 = max(path_bbox["x1"], rect["x1"])
            overlap_y1 = max(path_bbox["y1"], rect["y1"])
            overlap_x2 = min(path_bbox["x2"], rect["x2"])
            overlap_y2 = min(path_bbox["y2"], rect["y2"])

            if overlap_x1 < overlap_x2 and overlap_y1 < overlap_y2:
                overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                path_area = (path_bbox["x2"] - path_bbox["x1"]) * (
                    path_bbox["y2"] - path_bbox["y1"]
                )

                overlap_percentage = overlap_area / path_area if path_area > 0 else 0

                if is_iso_case and overlap_percentage > 0:
                    print(
                        f"  Overlap: {overlap_area:.1f}/{path_area:.1f} = "
                        f"{overlap_percentage:.2%}"
                    )

                # Require at least 50% of the path's bounding box to overlap
                if path_area > 0 and overlap_percentage >= 0.5:
                    if is_iso_case:
                        print("  -> INCLUDED (overlap)")
                    return True
                elif is_iso_case and overlap_percentage > 0:
                    print("  -> EXCLUDED (overlap too small)")

        return False

    def line_intersects_rect(self, x1, y1, x2, y2, rect):
        """Check if a line segment intersects with a rectangle."""
        # Check if either endpoint is inside the rectangle
        if (rect["x1"] <= x1 <= rect["x2"] and rect["y1"] <= y1 <= rect["y2"]) or (
            rect["x1"] <= x2 <= rect["x2"] and rect["y1"] <= y2 <= rect["y2"]
        ):
            return True

        # Check intersection with each rectangle edge
        # Left edge
        if self.line_segments_intersect(
            x1, y1, x2, y2, rect["x1"], rect["y1"], rect["x1"], rect["y2"]
        ):
            return True
        # Right edge
        if self.line_segments_intersect(
            x1, y1, x2, y2, rect["x2"], rect["y1"], rect["x2"], rect["y2"]
        ):
            return True
        # Top edge
        if self.line_segments_intersect(
            x1, y1, x2, y2, rect["x1"], rect["y1"], rect["x2"], rect["y1"]
        ):
            return True
        # Bottom edge
        if self.line_segments_intersect(
            x1, y1, x2, y2, rect["x1"], rect["y2"], rect["x2"], rect["y2"]
        ):
            return True

        return False

    def line_segments_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Check if two line segments intersect."""

        # Calculate the direction of the lines
        def ccw(Ax, Ay, Bx, By, Cx, Cy):
            return (Cy - Ay) * (Bx - Ax) > (By - Ay) * (Cx - Ax)

        # Check if the segments intersect
        return ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and ccw(
            x1, y1, x2, y2, x3, y3
        ) != ccw(x1, y1, x2, y2, x4, y4)

    def apply_pdf_hyperlinks(self, svg_content, svg_path):
        """Apply PDF hyperlinks to SVG content using simple overlay technique.

        This creates blue strokes in link areas by:
        1. Keeping original paths visible in black
        2. Creating masks for link areas
        3. Duplicating paths in blue masked groups (paint on top in link areas)
        """
        hyperlinks = self.load_hyperlink_metadata(svg_path)
        if not hyperlinks:
            return svg_content

        soup = BeautifulSoup(svg_content, "xml")
        svg_element = soup.find("svg")

        if not hyperlinks:
            return str(soup)

        # Get page number for unique IDs
        page_number = svg_element.get("data-page-number", "1")

        # Create defs element if it doesn't exist
        defs = soup.find("defs")
        if not defs:
            defs = soup.new_tag("defs")
            svg_element.insert(0, defs)

        # Collect all path elements (these are the strokes we want to recolor)
        # Exclude paths that are inside defs (they're used for clipping/masking)
        all_paths = []
        for path in svg_element.find_all("path"):
            # Check if this path is inside a defs element
            is_in_defs = any(parent.name == "defs" for parent in path.parents)
            if not is_in_defs:
                all_paths.append(path)

        # Process each hyperlink - create masks for blue strokes inside link areas
        for idx, link_data in enumerate(hyperlinks):
            uri = link_data["uri"]
            bbox = link_data["bbox"]

            mask_id_inside = f"linkMaskInside_{page_number}_{idx}"

            # Create mask for inside link area (blue strokes ONLY in link area)
            mask_inside = soup.new_tag("mask")
            mask_inside["id"] = mask_id_inside

            link_rect_inside = soup.new_tag("rect")
            link_rect_inside["x"] = f"{bbox['x']:.1f}"
            link_rect_inside["y"] = f"{bbox['y']:.1f}"
            link_rect_inside["width"] = f"{bbox['width']:.1f}"
            link_rect_inside["height"] = f"{bbox['height']:.1f}"
            link_rect_inside["fill"] = "white"
            mask_inside.append(link_rect_inside)

            defs.append(mask_inside)

        # Create blue groups for each link area (blue strokes paint on top of black originals)
        for idx, link_data in enumerate(hyperlinks):
            uri = link_data["uri"]
            bbox = link_data["bbox"]
            mask_id_inside = f"linkMaskInside_{page_number}_{idx}"

            # Create group for blue strokes inside this link
            blue_group = soup.new_tag("g")
            blue_group["mask"] = f"url(#{mask_id_inside})"

            # Clone all paths into blue group
            for path in all_paths:
                path_clone = soup.new_tag("path")
                for attr, value in path.attrs.items():
                    # Skip style attribute to avoid copying display:none
                    if attr != "style":
                        path_clone[attr] = value
                # Make stroke blue
                path_clone["stroke"] = "blue"
                path_clone["pointer-events"] = "none"
                blue_group.append(path_clone)

            svg_element.append(blue_group)

            # Create clickable overlay
            link_elem = soup.new_tag("a")
            link_elem["xlink:href"] = uri
            link_elem["target"] = "_blank"

            overlay_rect = soup.new_tag("rect")
            overlay_rect["x"] = f"{bbox['x']:.1f}"
            overlay_rect["y"] = f"{bbox['y']:.1f}"
            overlay_rect["width"] = f"{bbox['width']:.1f}"
            overlay_rect["height"] = f"{bbox['height']:.1f}"
            overlay_rect["fill"] = "none"
            overlay_rect["stroke"] = "none"
            overlay_rect["pointer-events"] = "all"

            link_elem.append(overlay_rect)
            svg_element.append(link_elem)

        return str(soup)

    def copy_images_to_html_dir(self, pdf_name):
        """Copy images with matching PDF prefix from pdfs directory to html
        output directory."""
        if not self.pdfs_dir.exists():
            return []

        copied_images = []
        html_images_dir = self.html_dir / "images"
        html_images_dir.mkdir(exist_ok=True)

        # Get all image files that start with the PDF name (without .pdf extension)
        image_files = [
            f
            for f in self.pdfs_dir.glob(f"{pdf_name}-*")
            if f.is_file()
            and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        ]
        image_files.sort(key=lambda x: x.name.lower())

        for image_file in image_files:
            dest_path = html_images_dir / image_file.name
            shutil.copy2(image_file, dest_path)
            copied_images.append(f"images/{image_file.name}")

        return copied_images

    def generate_html_from_svg_group(self, svg_files, output_name):
        """Generate HTML from a group of SVG files."""
        self.create_default_template()

        template = self.env.get_template("base.html")
        svg_contents = []

        for svg_file in svg_files:
            svg_content = self.process_svg(svg_file)
            svg_contents.append(svg_content)

        # Copy images with matching PDF prefix and pass them to the template
        copied_images = self.copy_images_to_html_dir(output_name)

        html_content = template.render(
            title=output_name.replace("_", " ").title(),
            svg_contents=svg_contents,
            photo_filenames=copied_images,
        )

        output_path = self.html_dir / f"{output_name}.html"
        with open(output_path, "w", encoding="utf-8") as f:
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
            pdf_name = svg_file.stem.rsplit("_page_", 1)[0]
            if pdf_name not in svg_groups:
                svg_groups[pdf_name] = []
            svg_groups[pdf_name].append(svg_file)

        generated_files = []
        for pdf_name, svg_files in svg_groups.items():
            # Sort by page number numerically instead of alphabetically
            svg_files.sort(
                key=lambda x: int(x.stem.split("_page_")[1])
                if "_page_" in x.stem
                else 0
            )
            output_file = self.generate_html_from_svg_group(svg_files, pdf_name)
            generated_files.append(output_file)

        return generated_files


def main():
    generator = HTMLGenerator()
    generated_files = generator.generate_all_html()
    print(f"Generated {len(generated_files)} HTML files")


if __name__ == "__main__":
    main()
