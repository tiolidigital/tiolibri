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


def fix_polish_orphans(html_content: str) -> str:
    """
    Zamienia zwykłe spacje po jednoliterowych spójnikach/przyimkach
    na non-breaking spaces (&nbsp;) zgodnie z polskimi zasadami typografii.
    
    Obsługuje:
    - Jednoliterowe: a, i, o, u, w, z (+ wielkie litery)
    - Dwuliterowe: do, na, po, od, ze, we, ku
    - Trzyliterowe: bez, pod, nad, dla
    - Partykuły: by, czy, aż, no
    
    Args:
        html_content: HTML string z treścią rozdziału
        
    Returns:
        HTML string z poprawionymi spacjami
    """
    # Lista polskich spójników i przyimków
    orphans_one = ['a', 'i', 'o', 'u', 'w', 'z', 'A', 'I', 'O', 'U', 'W', 'Z']
    orphans_two = ['do', 'na', 'po', 'od', 'ze', 'we', 'ku', 'Do', 'Na', 'Po', 'Od', 'Ze', 'We', 'Ku']
    orphans_three = ['bez', 'pod', 'nad', 'dla', 'Bez', 'Pod', 'Nad', 'Dla']
    orphans_particles = ['by', 'czy', 'aż', 'no', 'By', 'Czy', 'Aż', 'No']
    
    all_orphans = orphans_one + orphans_two + orphans_three + orphans_particles
    
    # Regex pattern: word boundary + orphan + space (not already &nbsp;)
    # Negative lookahead (?!nbsp;) ensures we don't replace already fixed spaces
    pattern = r'\b(' + '|'.join(re.escape(word) for word in all_orphans) + r') (?!nbsp;)'
    
    # Replace space with &nbsp;
    result = re.sub(pattern, r'\1&nbsp;', html_content)
    
    return result


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


def extract_first_heading(html: str) -> Optional[str]:
    """
    Wyciąga tekst z pierwszego nagłówka H1 lub H2 w HTML.
    Używane do pobierania prawdziwego tytułu rozdziału z treści.

    Args:
        html: HTML string z treścią rozdziału

    Returns:
        Tekst nagłówka lub None jeśli brak
    """
    match = re.search(r'<h[12][^>]*>(.*?)</h[12]>', html, re.IGNORECASE | re.DOTALL)
    if match:
        # Usuń tagi HTML z tekstu nagłówka (np. <strong>, <em>)
        heading_html = match.group(1)
        clean = re.sub(r'<[^>]+>', '', heading_html).strip()
        return clean if clean else None
    return None


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


def extract_headings(html: str, max_depth: int = 2) -> List[Dict]:
    """
    Wyciąga listę nagłówków (H1/H2/H3) z HTML z zachowaniem hierarchii.

    Args:
        html: HTML string z treścią rozdziału
        max_depth: Maksymalna głębokość nagłówków (1/2/3)

    Returns:
        Lista dicts: [{level: 1, text: "Tytuł", anchor: "anchor-id"}, ...]
    """
    tags = '|'.join(f'h{i}' for i in range(1, max_depth + 1))
    pattern = rf'<({tags})([^>]*)>(.*?)</\1>'
    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)

    headings = []
    for tag, attrs, content in matches:
        level = int(tag[1])
        text = re.sub(r'<[^>]+>', '', content).strip()
        if not text:
            continue
        # Sprawdź czy nagłówek ma id
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
        anchor = id_match.group(1) if id_match else None
        headings.append({'level': level, 'text': text, 'anchor': anchor})

    return headings


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
    cover_image_url: Optional[str] = None,
    toc_enabled: bool = False,
    toc_depth: int = 2
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
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head><title>Cover</title></head>
            <body style="margin: 0; padding: 0;">
                <img src="images/cover.{image_ext}" alt="Cover" style="width: 100%; height: 100vh; object-fit: cover; object-position: center; display: block;" />
            </body>
            </html>
            '''
            cover_page.add_item(nav_css)
            book.add_item(cover_page)
            
        except Exception as e:
            print(f"Warning: Could not add cover image: {e}")
            cover_item = None
    
    # Collect all image URLs from all chapters (for deduplication)
    all_image_urls = set()
    for chapter in chapters:
        content = chapter.get("content") or chapter.get("processed_html", "")
        if content:
            img_urls = extract_image_urls(content)
            all_image_urls.update(img_urls)
    
    # Download and add images to EPUB (deduplicated)
    image_map = {}  # url -> local_path mapping
    for img_url in all_image_urls:
        if not img_url.startswith('http'):
            continue
        
        img_data, img_ext = download_image(img_url)
        if not img_data:
            continue
        
        # Generate unique filename
        img_id = str(uuid.uuid4())[:8]
        local_path = f"images/{img_id}.{img_ext}"
        
        # Create EPUB image item
        img_item = epub.EpubItem(
            uid=f"image_{img_id}",
            file_name=local_path,
            media_type=f"image/{img_ext}",
            content=img_data
        )
        book.add_item(img_item)
        
        # Map URL to local path
        image_map[img_url] = local_path
    
    # Title page
    title_page = epub.EpubHtml(
        title='Title Page',
        file_name='title.xhtml',
        lang=project.get("language", "pl")
    )
    
    author_html = f'<p class="author">{project["author"]}</p>' if project.get("author") else ""
    
    title_page.content = f'''
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>Title Page</title>
        <link rel="stylesheet" href="style/nav.css" type="text/css" />
    </head>
    <body>
        <div class="title-page">
            <h1>{project["title"]}</h1>
            {author_html}
        </div>
    </body>
    </html>
    '''
    title_page.add_item(nav_css)
    book.add_item(title_page)
    
    # Chapters
    epub_chapters = []
    chapters_processed = []  # Równoległa lista rozdziałów do epub_chapters (dla TOC)
    spine_items = [title_page]

    if cover_item:
        spine_items.insert(0, cover_page)
    
    for idx, chapter in enumerate(chapters, start=1):
        content = chapter.get("content") or chapter.get("processed_html", "")
        
        if not content or not content.strip():
            continue
        
        # 🆕 FIX POLISH ORPHANS - dodaj &nbsp; po spójnikach
        content = fix_polish_orphans(content)
        
        # Replace image URLs with local paths
        for img_url, local_path in image_map.items():
            content = content.replace(f'src="{img_url}"', f'src="{local_path}"')
        
        # Pobierz prawdziwy tytuł z pierwszego H1/H2 w treści
        chapter_heading = extract_first_heading(content) or chapter.get("title", f"Chapter {idx}")

        chapter_item = epub.EpubHtml(
            title=chapter_heading,
            file_name=f'chapter_{idx}.xhtml',
            lang=project.get("language", "pl")
        )

        chapter_item.content = f'''
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
            <title>{chapter_heading}</title>
            <link rel="stylesheet" href="style/nav.css" type="text/css" />
        </head>
        <body>
            <div class="book-content">
                {content}
            </div>
        </body>
        </html>
        '''
        
        chapter_item.add_item(nav_css)
        book.add_item(chapter_item)
        
        epub_chapters.append(chapter_item)
        chapters_processed.append(chapter)
        spine_items.append(chapter_item)
    
    if not epub_chapters:
        raise ValueError("No valid chapters with content found")
    
    # TOC (Table of Contents)
    if toc_enabled and toc_depth > 1:
        # Buduj hierarchiczny TOC z nagłówkami wewnątrz rozdziałów
        toc_entries = []
        for idx, chapter_item in enumerate(epub_chapters):
            chapter = chapters_processed[idx] if idx < len(chapters_processed) else None
            if not chapter:
                toc_entries.append(chapter_item)
                continue

            content = chapter.get("content") or chapter.get("processed_html", "")
            sub_headings = extract_headings(content, max_depth=toc_depth)

            # Pomijamy pierwszego nagłówka (H1 = tytuł rozdziału - już w chapter_item.title)
            sub_entries = [
                epub.Link(
                    f'{chapter_item.file_name}#{h["anchor"]}' if h["anchor"] else chapter_item.file_name,
                    h["text"],
                    f'sub_{idx}_{i}'
                )
                for i, h in enumerate(sub_headings)
                if h["level"] > 1
            ]

            if sub_entries:
                toc_entries.append((epub.Section(chapter_item.title), [chapter_item] + sub_entries))
            else:
                toc_entries.append(chapter_item)

        book.toc = tuple(toc_entries)
    else:
        book.toc = tuple(epub_chapters)

    # Spine (reading order)
    book.spine = spine_items
    
    # Add NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Write EPUB file
    epub.write_epub(output_path, book)
    
    return output_path
