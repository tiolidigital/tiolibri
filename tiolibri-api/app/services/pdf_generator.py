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
    orphans: 2;        /* 🆕 Min 2 linie dla headings */
    widows: 2;
}

h1 {
    font-size: 18pt;
    margin-top: 2em;
}

.chapter {
    /* Stable container for chapter content */
    /* page-break-before is set inline for chapters after first */
}

p {
    margin: 0 0 0.8em 0;
    text-indent: 0;
    orphans: 3;        /* 🆕 Min 3 linie na dole strony przed page break */
    widows: 3;         /* 🆕 Min 3 linie na górze nowej strony */
}

p:first-of-type,
h1 + p,
h2 + p {
    text-indent: 0;
}

img:not(.cover-page img) {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1.5em auto;
    page-break-inside: avoid;
}

.cover-page {
    page: cover-page;
    page-break-after: always;
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
}

.cover-page img {
    width: 100%;
    height: 100vh;
    object-fit: cover;
    object-position: center;
    display: block;
    margin: 0;
    padding: 0;
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


def extract_first_heading(html: str) -> Optional[str]:
    """Wyciąga tekst z pierwszego nagłówka H1 lub H2 w HTML."""
    match = re.search(r'<h[12][^>]*>(.*?)</h[12]>', html, re.IGNORECASE | re.DOTALL)
    if match:
        clean = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return clean if clean else None
    return None


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
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
        anchor = id_match.group(1) if id_match else None
        headings.append({'level': level, 'text': text, 'anchor': anchor})

    return headings


def inject_heading_ids(html: str, chapter_idx: int = 0) -> str:
    """
    Dodaje atrybut id="" do nagłówków H1/H2/H3 które go nie mają.
    Umożliwia wewnętrzne linki w PDF (TOC → rozdział).

    Używa prefiksu chapter_idx żeby IDs były unikalne w całym dokumencie.

    Args:
        html: HTML string z treścią rozdziału
        chapter_idx: Indeks rozdziału (do generowania unikalnych IDs)

    Returns:
        HTML z dodanymi id na nagłówkach
    """
    counter = [0]

    def add_id(match):
        tag = match.group(1)
        attrs = match.group(2)
        content = match.group(3)
        if 'id=' not in attrs.lower():
            counter[0] += 1
            heading_id = f'ch{chapter_idx}-h{counter[0]}'
            return f'<{tag}{attrs} id="{heading_id}">{content}</{tag}>'
        return match.group(0)

    return re.sub(r'<(h[123])([^>]*)>(.*?)</\1>', add_id, html, flags=re.IGNORECASE | re.DOTALL)


def build_pdf_toc_html(chapters: List[Dict], title: str = "Spis treści", toc_depth: int = 1) -> str:
    """
    Generuje HTML strony spisu treści dla PDF.

    Args:
        chapters: Lista rozdziałów z treścią (muszą mieć id na nagłówkach)
        title: Tytuł sekcji TOC
        toc_depth: Głębokość nagłówków (1=tylko H1, 2=H1+H2, 3=H1+H2+H3)

    Returns:
        HTML string strony TOC
    """
    items_html = []
    for chapter in chapters:
        content = chapter.get("content") or chapter.get("processed_html", "")
        if not content or not content.strip():
            continue

        headings = extract_headings(content, max_depth=toc_depth)
        for h in headings:
            level_class = f'toc-item toc-h{h["level"]}'
            if h['anchor']:
                link = f'<a href="#{h["anchor"]}">{h["text"]}</a>'
            else:
                link = h['text']
            items_html.append(f'<li class="{level_class}">{link}</li>')

    if not items_html:
        return ""

    return f'''
    <div class="toc-page">
        <h2 class="toc-title">{title}</h2>
        <ul class="toc-list">
            {"".join(items_html)}
        </ul>
    </div>
    '''


TOC_CSS = """
.toc-page {
    page-break-after: always;
    padding-top: 2em;
}

.toc-title {
    font-size: 18pt;
    margin-bottom: 1.5em;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.5em;
}

.toc-list {
    list-style: none;
    margin: 0;
    padding: 0;
}

.toc-item {
    padding: 0.3em 0;
    border-bottom: 1px dotted #ddd;
}

.toc-item a {
    color: inherit;
    text-decoration: none;
}

.toc-h1 {
    font-size: 11pt;
    font-weight: bold;
    padding-left: 0;
}

.toc-h2 {
    font-size: 10pt;
    font-weight: normal;
    padding-left: 1.5em;
    color: #444;
}

.toc-h3 {
    font-size: 9pt;
    font-weight: normal;
    padding-left: 3em;
    color: #666;
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
    cover_image_url: Optional[str] = None,
    toc_enabled: bool = False,
    toc_depth: int = 2
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

    @page cover-page {{
        size: A5 portrait;
        margin: 0;

        @bottom-center {{
            content: none;
        }}
    }}

    @page:first {{
        @bottom-center {{
            content: none;
        }}
    }}
    """
    
    css_final = page_margins + css_final
    
    # Zbuduj HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        f'<title>{project["title"]}</title>',
        '<meta charset="UTF-8">',
        '<style>',
        BASE_CSS,
        css_final,
        TOC_CSS if toc_enabled else '',
        '</style>',
        '</head>',
        '<body>',
    ]
    
    # Cover page (jeśli istnieje cover_image_url)
    if cover_image_url:
        # Download and convert to base64 data URI
        cover_data_uri = download_and_encode_image(cover_image_url)
        if cover_data_uri:
            html_parts.append('<div class="cover-page">')
            html_parts.append(f'<img src="{cover_data_uri}" alt="Cover" />')
            html_parts.append('</div>')
    
    # Title page
    html_parts.append('<div class="title-page">')
    html_parts.append(f'<h1>{project["title"]}</h1>')
    if project.get("author"):
        html_parts.append(f'<p class="author">{project["author"]}</p>')
    html_parts.append('</div>')

    # Pre-process chapters: orphans, heading IDs, images
    # Robimy to przed budowaniem TOC żeby IDs w TOC i w treści były spójne
    processed_contents = []
    chapter_render_idx = 0
    for chapter in chapters:
        raw = chapter.get("content") or chapter.get("processed_html", "")
        if not raw or not raw.strip():
            processed_contents.append(None)
            continue

        c = fix_polish_orphans(raw)

        # Inject heading IDs z unikalnym prefiksem per rozdział
        if toc_enabled:
            c = inject_heading_ids(c, chapter_idx=chapter_render_idx)

        # Convert image URLs to base64 data URIs
        for img_url in extract_image_urls(c):
            if img_url.startswith('http'):
                data_uri = download_and_encode_image(img_url)
                if data_uri:
                    c = c.replace(f'src="{img_url}"', f'src="{data_uri}"')

        processed_contents.append(c)
        chapter_render_idx += 1

    # TOC page (po stronie tytułowej, przed rozdziałami)
    # Budujemy z pre-przetworzonych treści żeby linki (#ch0-h1 itp.) były poprawne.
    # Nadpisujemy 'content' i 'processed_html' bo build_pdf_toc_html preferuje 'content'.
    if toc_enabled:
        chapters_for_toc = []
        for chapter, proc_content in zip(chapters, processed_contents):
            if proc_content:
                chapters_for_toc.append({**chapter, 'content': proc_content, 'processed_html': proc_content})
        toc_html = build_pdf_toc_html(chapters_for_toc, title="Spis treści", toc_depth=toc_depth)
        if toc_html:
            html_parts.append(toc_html)

    # Chapters
    html_parts.append('<div class="book-content">')

    render_idx = 0
    for i, (chapter, content) in enumerate(zip(chapters, processed_contents)):
        if content is None:
            continue

        # 🆕 STABLE PAGE BREAKS - wrap chapter in div with conditional page-break-before
        # First chapter: no page-break-before
        # All subsequent chapters: page-break-before: always
        if render_idx == 0:
            html_parts.append(f'<div class="chapter">{content}</div>')
        else:
            html_parts.append(f'<div class="chapter" style="page-break-before: always;">{content}</div>')
        render_idx += 1

    html_parts.append('</div>')
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    html_string = '\n'.join(html_parts)
    
    # Generate PDF
    font_config = FontConfiguration()
    html_obj = HTML(string=html_string)
    
    html_obj.write_pdf(
        output_path,
        stylesheets=[CSS(string=css_final, font_config=font_config)],
        font_config=font_config
    )
    
    return output_path
