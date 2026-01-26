"""
EPUB Generator Service
Generuje pliki EPUB z projektu i rozdziałów.
"""

from ebooklib import epub
from typing import List, Dict, Optional, Tuple
import os
from pathlib import Path
import urllib.request
import tempfile
import re
import uuid


def load_css_preset(preset_name: str) -> str:
    """
    Wczytuje CSS preset z pliku.

    Args:
        preset_name: Nazwa presetu (classic/modern/minimal)

    Returns:
        Zawartość pliku CSS

    Raises:
        FileNotFoundError: Gdy preset nie istnieje
    """
    # Użyj Path dla cross-platform compatibility
    base_path = Path(__file__).parent.parent / "presets"
    preset_path = base_path / f"{preset_name}.css"

    if not preset_path.exists():
        raise FileNotFoundError(f"CSS preset '{preset_name}' not found at {preset_path}")

    with open(preset_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_image_urls(html: str) -> List[str]:
    """Extract all image URLs from HTML."""
    img_pattern = r'<img[^>]+src="([^"]+)"'
    urls = re.findall(img_pattern, html)
    return urls


def download_image(url: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Download image and return (data, extension).

    Returns:
        Tuple of (image_data, file_extension) or (None, None) on failure
    """
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read()

            # Detect extension from URL
            path_part = url.split('?')[0]  # Remove query params
            ext = path_part.split('.')[-1].lower()

            # Map jpg to jpeg for consistency
            if ext == 'jpg':
                ext = 'jpeg'

            # Validate extension
            if ext not in ['jpeg', 'png', 'gif']:
                ext = 'jpeg'  # default

            return data, ext
    except Exception as e:
        print(f"Failed to download image {url}: {e}")
        return None, None


def generate_epub(
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
    Generuje EPUB z projektu i rozdziałów.

    Args:
        project: Dict z danymi projektu (id, title, author, language)
        chapters: Lista rozdziałów (title, content/processed_html)
        output_path: Ścieżka zapisu pliku (np. "/tmp/book.epub")
        style_preset: Nazwa presetu CSS (classic/modern/minimal)
        text_align: Wyrównanie tekstu (left/justify)
        font_size: Rozmiar czcionki w px (12-24)
        line_height: Interlinia
        margin_top: Margines górny (em)
        margin_bottom: Margines dolny (em)
        margin_left: Margines lewy (em)
        margin_right: Margines prawy (em)

    Returns:
        output_path: Ścieżka do wygenerowanego pliku

    Raises:
        ValueError: Gdy brak rozdziałów z treścią
        FileNotFoundError: Gdy preset CSS nie istnieje
    """
    # Stwórz obiekt książki
    book = epub.EpubBook()

    # Metadata
    book.set_identifier(str(project["id"]))
    book.set_title(project["title"])
    book.set_language(project.get("language", "pl"))

    if project.get("author"):
        book.add_author(project["author"])

    # Wczytaj CSS preset
    base_css = load_css_preset(style_preset)

    # Replace CSS variables with actual values (EPUB reader compatibility)
    margin_value = f"{margin_top}em {margin_right}em {margin_bottom}em {margin_left}em"
    css_final = base_css
    css_final = css_final.replace('var(--text-align, left)', text_align)
    css_final = css_final.replace('var(--font-size, 16px)', f'{font_size}px')
    css_final = css_final.replace('var(--line-height, 1.7)', str(line_height))
    css_final = css_final.replace('var(--margin, 2em 1.5em)', margin_value)
    css_final = css_final.replace('var(--chapter-spacing, 2em)', f'{chapter_spacing}em')

    # Dodaj CSS jako item
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=css_final.encode('utf-8')
    )
    book.add_item(nav_css)

    # Dodaj cover image (jeśli istnieje)
    cover_item = None
    if cover_image_url:
        try:
            # Download cover image
            with urllib.request.urlopen(cover_image_url) as response:
                cover_data = response.read()

                # Determine image type from URL
                image_ext = cover_image_url.lower().split('.')[-1].split('?')[0]
                if image_ext == 'jpg':
                    image_ext = 'jpeg'

                media_type = f'image/{image_ext}'

                # Create cover image item
                cover_item = epub.EpubItem(
                    uid="cover_image",
                    file_name=f"images/cover.{image_ext}",
                    media_type=media_type,
                    content=cover_data
                )
                book.add_item(cover_item)

                # Set as cover
                book.set_cover(f"images/cover.{image_ext}", cover_data)

                # Create cover page HTML
                cover_page = epub.EpubHtml(
                    title='Cover',
                    file_name='cover.xhtml',
                    lang=project.get("language", "pl")
                )
                cover_page.content = f'''
                    <div style="text-align: center; padding: 0; margin: 0;">
                        <img src="images/cover.{image_ext}" alt="Cover" style="max-width: 100%; height: auto;"/>
                    </div>
                '''
                book.add_item(cover_page)
        except Exception as e:
            print(f"Warning: Failed to add cover image: {e}")
            cover_item = None

    # Dodaj rozdziały
    epub_chapters = []
    spine = ['nav']

    # Add cover to spine if it exists
    if cover_item:
        spine.insert(0, 'cover')

    # Track downloaded images globally to avoid duplicates
    image_map = {}  # {original_url: local_filename}

    for idx, chapter in enumerate(chapters, start=1):
        # Użyj processed_html jeśli istnieje, w przeciwnym razie content
        content = chapter.get("processed_html") or chapter.get("content", "")

        if not content:
            continue

        # Extract and download images from chapter content
        img_urls = extract_image_urls(content)

        for img_url in img_urls:
            if img_url in image_map:
                continue  # Already downloaded

            img_data, img_ext = download_image(img_url)
            if not img_data:
                continue  # Skip failed downloads

            # Generate unique filename
            img_filename = f"images/img_{uuid.uuid4().hex[:8]}.{img_ext}"

            # Determine media type
            media_type = f'image/{img_ext}'

            # Add image to EPUB
            img_item = epub.EpubItem(
                uid=f"image_{uuid.uuid4().hex[:8]}",
                file_name=img_filename,
                media_type=media_type,
                content=img_data
            )
            book.add_item(img_item)

            # Map original URL to local path
            image_map[img_url] = img_filename

        # Replace image URLs with local paths in HTML
        for original_url, local_path in image_map.items():
            content = content.replace(f'src="{original_url}"', f'src="{local_path}"')

        # Stwórz rozdział EPUB
        c = epub.EpubHtml(
            title=chapter["title"],  # For TOC only
            file_name=f'chapter_{idx}.xhtml',
            lang=project.get("language", "pl")
        )

        # Only add content - no auto-generated heading
        # User already has <h1> titles inside the content from TipTap editor
        c.content = content
        c.add_item(nav_css)

        book.add_item(c)
        epub_chapters.append(c)
        spine.append(c)

    if not epub_chapters:
        raise ValueError("No chapters with content found")

    # Dodaj TOC (Table of Contents)
    book.toc = tuple(epub_chapters)

    # Dodaj domyślne NCX i Nav
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Spine (kolejność rozdziałów)
    book.spine = spine

    # Upewnij się że folder docelowy istnieje
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    # Zapisz EPUB
    epub.write_epub(output_path, book, {})

    return output_path
