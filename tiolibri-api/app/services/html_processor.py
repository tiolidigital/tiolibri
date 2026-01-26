"""
HTML Processor Service
Czyści HTML z Google Docs artifacts i przygotowuje do generowania e-booków.
"""

import re
from typing import Optional


def clean_html(html: str) -> str:
    """
    Czyści HTML z Google Docs artifacts.
    Usuwa style inline, niepotrzebne tagi, normalizuje whitespace.

    Args:
        html: Surowy HTML z Google Docs

    Returns:
        Wyczyszczony HTML
    """
    if not html:
        return ""

    # Usuń style inline
    html = re.sub(r' style="[^"]*"', '', html)
    html = re.sub(r' class="[^"]*"', '', html)

    # Usuń puste tagi
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'<div>\s*</div>', '', html)
    html = re.sub(r'<span>\s*</span>', '', html)

    # Usuń Google Docs specific tagi
    html = re.sub(r'<o:p>.*?</o:p>', '', html, flags=re.DOTALL)

    # Normalizuj whitespace (ale zachowaj pojedyncze spacje)
    html = re.sub(r'\s+', ' ', html)
    html = html.strip()

    return html


def wrap_chapter_html(title: str, content: str, css: str) -> str:
    """
    Opakowuje treść rozdziału w kompletny HTML dokument z CSS.

    Args:
        title: Tytuł rozdziału
        content: Treść HTML rozdziału
        css: Style CSS

    Returns:
        Kompletny dokument HTML
    """
    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
{css}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {content}
</body>
</html>"""


def extract_text_content(html: str) -> str:
    """
    Ekstrahuje czysty tekst z HTML (do statystyk, np. word count).

    Args:
        html: Dokument HTML

    Returns:
        Czysty tekst bez tagów
    """
    if not html:
        return ""

    # Usuń wszystkie tagi HTML
    text = re.sub(r'<[^>]+>', ' ', html)
    # Normalizuj whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def count_words(html: str) -> int:
    """
    Liczy słowa w dokumencie HTML.

    Args:
        html: Dokument HTML

    Returns:
        Liczba słów
    """
    text = extract_text_content(html)
    if not text:
        return 0
    return len(text.split())
