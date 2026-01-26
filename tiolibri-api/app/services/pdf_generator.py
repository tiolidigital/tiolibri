"""
PDF Generator Service
Generuje pliki PDF z projektu i rozdziałów używając WeasyPrint.
Pełne wsparcie UTF-8 i polskich znaków.

UWAGA: Lazy import - WeasyPrint ładuje się dopiero przy wywołaniu generate_pdf()
"""

import os
import sys
from typing import List, Dict, Optional
from pathlib import Path
import urllib.request
import base64
import re

# macOS fix - musi być PRZED jakimkolwiek importem weasyprint
if sys.platform == "darwin":
    os.environ["DYLD_LIBRARY_PATH"] = f"/opt/homebrew/lib:{os.environ.get('DYLD_LIBRARY_PATH', '')}"

def load_css_preset(preset_name: str) -> str:
    base_path = Path(__file__).parent.parent / "presets"
    preset_path = base_path / f"{preset_name}.css"

    if not preset_path.exists():
        raise FileNotFoundError(f"CSS preset '{preset_name}' not found at {preset_path}")

    with open(preset_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_image_urls(html: str) -> list:
    """Extract all image URLs from HTML."""
    img_pattern = r'<img[^>]+src="([^"]+)"'
    urls = re.findall(img_pattern, html)
    return urls

def download_and_encode_image(url: str) -> Optional[str]:
    """
    Download image and return as base64 data URI.

    Returns:
        Data URI string or None on failure
    """
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            img_data = response.read()

            # Determine MIME type from URL
            path_part = url.split('?')[0]
            ext = path_part.split('.')[-1].lower()

            if ext == 'jpg':
                ext = 'jpeg'

            # Determine content type
            if ext in ['jpeg', 'jpg']:
                content_type = 'image/jpeg'
            elif ext == 'png':
                content_type = 'image/png'
            elif ext == 'gif':
                content_type = 'image/gif'
            else:
                content_type = 'image/jpeg'  # default

            # Encode to base64
            b64_data = base64.b64encode(img_data).decode('utf-8')
            data_uri = f"data:{content_type};base64,{b64_data}"

            return data_uri
    except Exception as e:
        print(f"Failed to download image {url}: {e}")
        return None

BASE_CSS = """
body {
    font-family: "DejaVu Serif", "Liberation Serif", Georgia, serif;
    font-size: 11pt;
    line-height: 1.6;
    text-align: justify;
}
h1, h2, h3 {
    font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
    page-break-after: avoid;
}
h1 {
    font-size: 18pt;
    margin-top: 2em;
    page-break-before: always;
}
h1:first-of-type { page-break-before: avoid; }
p { margin: 0 0 0.8em 0; text-indent: 0; }  /* DISABLED for testing */
p:first-of-type, h1 + p, h2 + p { text-indent: 0; }
img:not(.cover-page img) {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1.5em auto;
    page-break-inside: avoid;
}
.cover-page {
    page-break-after: always;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
}
.cover-page img {
    max-width: 100%;
    max-height: 100vh;
    width: auto;
    height: auto;
}
.title-page {
    page-break-after: always;
    text-align: center;
    padding-top: 35%;
}
.title-page h1 {
    font-size: 24pt;
    page-break-before: avoid;
}
.title-page .author {
    font-size: 14pt;
    color: #444;
    margin-top: 1em;
}
"""

def generate_pdf(
    project: Dict,
    chapters: List[Dict],
    output_path: str,
    style_preset: str = "classic",
    text_align: str = "left",
    font_size: int = 16,
    line_height: float = 1.7,
    margin_top: float = 2.0,
    margin_bottom: float = 2.0,
    margin_left: float = 1.5,
    margin_right: float = 1.5,
    chapter_spacing: float = 2.0,
    cover_image_url: Optional[str] = None
) -> str:
    """
    Generuje PDF z projektu i rozdziałów używając WeasyPrint.

    Args:
        project: Dict z danymi projektu
        chapters: Lista rozdziałów
        output_path: Ścieżka zapisu pliku
        style_preset: Nazwa presetu CSS (classic/modern/minimal)
        text_align: Wyrównanie tekstu (left/justify)
        font_size: Rozmiar czcionki w px (12-24)
        line_height: Interlinia
        margin_top: Margines górny (em)
        margin_bottom: Margines dolny (em)
        margin_left: Margines lewy (em)
        margin_right: Margines prawy (em)
        chapter_spacing: Spacing między rozdziałami (em)
        cover_image_url: URL do cover image (opcjonalny)
    """
    # LAZY IMPORT - dopiero tutaj!
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration

    # Wczytaj CSS preset
    try:
        preset_css = load_css_preset(style_preset)
    except FileNotFoundError:
        preset_css = ""

    # Replace CSS variables with actual values (WeasyPrint compatibility)
    css_final = preset_css
    css_final = css_final.replace('var(--text-align, left)', text_align)
    css_final = css_final.replace('var(--font-size, 16px)', f'{font_size}px')
    css_final = css_final.replace('var(--line-height, 1.7)', str(line_height))
    css_final = css_final.replace('var(--chapter-spacing, 2em)', f'{chapter_spacing}em')
    
    # BODY MARGINS: Remove body margin entirely (controlled by @page instead)
    # Replace var(--margin, ...) with 0 so @page margins control everything
    css_final = css_final.replace('margin: var(--margin, 2em 1.5em);', 'margin: 0;')
    
    # @page rule for PDF page margins (this controls ACTUAL page margins)
    page_margins = f"""
@page {{
  size: A5 portrait;
  margin-top: {margin_top}cm;
  margin-bottom: {margin_bottom}cm;
  margin-left: {margin_left}cm;
  margin-right: {margin_right}cm;
  
  @bottom-center {{
    content: counter(page);
    font-size: 9pt;
    color: #666;
  }}
}}

@page:first {{
  @bottom-center {{ content: none; }}
}}

"""
    css_final = page_margins + css_final

    # Zbuduj HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="pl">',
        '<head><meta charset="UTF-8">',
        f"<title>{_escape_html(project['title'])}</title>",
        '</head><body>',
    ]

    # Add cover image if provided
    if cover_image_url:
        try:
            # Download cover image and convert to base64 for inline embedding
            with urllib.request.urlopen(cover_image_url) as response:
                cover_data = response.read()
                cover_base64 = base64.b64encode(cover_data).decode('utf-8')

                # Determine image type
                image_ext = cover_image_url.lower().split('.')[-1].split('?')[0]
                if image_ext == 'jpg':
                    image_ext = 'jpeg'

                mime_type = f'image/{image_ext}'

                # Add cover page
                html_parts.append('<div class="cover-page">')
                html_parts.append(f'<img src="data:{mime_type};base64,{cover_base64}" alt="Cover"/>')
                html_parts.append('</div>')
        except Exception as e:
            print(f"Warning: Failed to add cover image to PDF: {e}")

    # Add title page
    html_parts.append('<div class="title-page">')
    html_parts.append(f"<h1>{_escape_html(project['title'])}</h1>")

    if project.get("author"):
        html_parts.append(f'<p class="author">{_escape_html(project["author"])}</p>')
    html_parts.append("</div>")

    # Rozdziały
    chapters_added = 0
    for chapter in chapters:
        content = chapter.get("processed_html") or chapter.get("content", "")
        if not content:
            continue

        # Convert image URLs to base64 data URIs
        img_urls = extract_image_urls(content)
        for img_url in img_urls:
            img_b64 = download_and_encode_image(img_url)
            if img_b64:
                content = content.replace(f'src="{img_url}"', f'src="{img_b64}"')

        # Only add content - no auto-generated heading
        # User already has <h1> titles inside the content from TipTap editor
        html_parts.append(content)
        chapters_added += 1

    if chapters_added == 0:
        raise ValueError("No chapters with content found")

    html_parts.append("</body></html>")
    full_html = "\n".join(html_parts)

    # Folder docelowy
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Generuj PDF
    font_config = FontConfiguration()
    combined_css = BASE_CSS + "\n" + css_final

    HTML(string=full_html).write_pdf(
        output_path,
        stylesheets=[CSS(string=combined_css, font_config=font_config)],
        font_config=font_config
    )

    return output_path

def _escape_html(text: str) -> str:
    if not text:
        return ""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
