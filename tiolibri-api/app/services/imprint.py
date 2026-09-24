"""
Wersja wydania z danych wydawniczych projektu.

Jedno pole `projects.imprint.version` (np. "1.0") zasila wszystkie miejsca,
w których wersja się pokazuje: wiersz w kolofonie, dopisek przy linijce ©
na stronie tytułowej, metadane PDF i EPUB oraz nazwę pobieranego pliku.
Trzymane w jednym module, żeby te miejsca nie mogły się rozjechać.

Projekt bez `version` generuje się dokładnie tak jak dotąd.
"""

import re
from datetime import date
from pathlib import Path
from typing import List, Optional

# Miesiące w mianowniku, małą literą — tak jak w „Wersja 1.0 – wrzesień 2026".
POLISH_MONTHS = (
    "styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec",
    "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień",
)

# Akapit kolofonu z informacją o wydaniu („Wydanie pierwsze elektroniczne.
# Szczecin 2026.") — wiersz z wersją staje bezpośrednio pod nim.
_EDITION_PARAGRAPH = re.compile(
    r'<p\b[^>]*>(?:(?!</p>).)*?\bWydanie\b(?:(?!</p>).)*?</p>',
    re.IGNORECASE | re.DOTALL,
)

# Koniec zdania w linijce ©: kropka, odstęp i wielka litera — o ile kropka
# nie zamyka skrótu, bo „prof. dr hab. Jan" to wciąż to samo zdanie.
_SENTENCE_END = re.compile(r"\.\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ])")
_ABBREVIATIONS = {"prof", "dr", "hab", "mgr", "inż", "lek", "med", "n", "wyd", "św"}


def edition_version(project: dict) -> str:
    """Wersja wydania z `imprint.version` albo pusty napis, gdy jej nie ma."""
    imprint = project.get("imprint") or {}
    return str(imprint.get("version") or "").strip()


def version_line(version: str, today: Optional[date] = None) -> str:
    """Wiersz do kolofonu: "1.0" → "Wersja 1.0 – wrzesień 2026".

    Miesiąc to miesiąc wygenerowania pliku — nowy plik z poprawkami dostaje
    nową wersję, więc data idzie razem z nią.
    """
    today = today or date.today()
    return f"Wersja {version} – {POLISH_MONTHS[today.month - 1]} {today.year}"


def rights_with_version(rights_note: str, version: str) -> str:
    """Linijka © na stronie tytułowej z krótkim dopiskiem wersji.

    Wersja staje na końcu pierwszego zdania, przed zdaniem o prawach:
    "© 2026 X · Wydawnictwo TIOLI. Wszelkie prawa zastrzeżone."
    → "© 2026 X · Wydawnictwo TIOLI · wersja 1.0. Wszelkie prawa zastrzeżone."
    Koniec zdania to kropka przed wielką literą, więc skróty w rodzaju
    „prof. dr hab." nie tną linijki w złym miejscu.
    """
    if not version:
        return rights_note
    tag = f" · wersja {version}"
    for match in _SENTENCE_END.finditer(rights_note):
        before = rights_note[:match.start()].split()
        if before and before[-1].lower() in _ABBREVIATIONS:
            continue
        return rights_note[:match.start()] + tag + rights_note[match.start():]
    if rights_note.endswith("."):
        return rights_note[:-1] + tag + "."
    return rights_note + tag


def inject_version_line(colophon_html: str, line: str) -> str:
    """Wstawia akapit z wersją pod akapitem o wydaniu.

    Kolofon bez takiego akapitu dostaje wiersz na początku — wersja ma być
    widoczna zawsze, gdy jest ustawiona.
    """
    return inject_colophon_lines(colophon_html, [line])


# --- XpertLab ---------------------------------------------------------------
# Przełącznik `projects.imprint.xpertlab = true`: linijka w kolofonie pod
# wersją i napis-logo na dole strony tytułowej. Gdy XpertLab jest też wydawcą
# (`publisher` z „XpertLab”), linijka o współpracy znika, a napis zostaje.

XPERTLAB_LINE = "We współpracy z XpertLab"
XPERTLAB_LOGO_HTML = '<div class="xlab-logo"><span class="x">Xpert</span><span class="l">Lab</span></div>'
FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
XPERTLAB_FONTS = (("HankenGrotesk-Regular.ttf", 400), ("HankenGrotesk-SemiBold.ttf", 600))


def xpertlab_enabled(project: dict) -> bool:
    imprint = project.get("imprint") or {}
    return imprint.get("xpertlab") is True


def xpertlab_is_publisher(project: dict) -> bool:
    imprint = project.get("imprint") or {}
    return "xpertlab" in str(imprint.get("publisher") or "").lower()


def xpertlab_css(font_url_prefix: str) -> str:
    """@font-face i kolory napisu. `font_url_prefix` to katalog z krojem:
    `file:///…/fonts/` w PDF, `../fonts/` w EPUB."""
    faces = "".join(
        f"@font-face {{ font-family: 'Hanken Grotesk'; font-weight: {weight}; "
        f"src: url('{font_url_prefix}{name}'); }}\n"
        for name, weight in XPERTLAB_FONTS
    )
    return faces + """
.xlab-logo { font-family: 'Hanken Grotesk', sans-serif; text-align: center; text-indent: 0; }
.xlab-logo .x { font-weight: 600; color: #3A2342; }
.xlab-logo .l { font-weight: 400; color: #A0526E; }
"""


def colophon_lines(project: dict, today: Optional[date] = None) -> List[str]:
    """Wiersze dopisywane do kolofonu pod akapitem o wydaniu: wersja, XpertLab."""
    lines = []
    version = edition_version(project)
    if version:
        lines.append(version_line(version, today))
    if xpertlab_enabled(project) and not xpertlab_is_publisher(project):
        lines.append(XPERTLAB_LINE)
    return lines


def inject_colophon_lines(colophon_html: str, lines: List[str]) -> str:
    """Wstawia akapity pod akapitem o wydaniu, a bez niego na początku kolofonu."""
    paragraph = "".join(f"<p>{line}</p>" for line in lines)
    match = _EDITION_PARAGRAPH.search(colophon_html)
    if not match:
        return paragraph + colophon_html
    return colophon_html[:match.end()] + paragraph + colophon_html[match.end():]
