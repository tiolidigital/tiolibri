"""HTML -> Markdown dla mostu TIOLIBRI -> Redaktor (spec md-export v0.4.1).

Reguly podzialu na bloki i escapingu sa przepisane z konsumenta —
FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts:12-20 @ 134f8e4 — a nie z CommonMarka.
Konsument jest parserem regexowym pracujacym na poczatkach linii; kolejnosc sprawdzania
galezi jest czescia kontraktu, bo wzorce nie sa rozlaczne.

Skladnia typow: Optional[X], nigdy X | None — lokalny venv to Python 3.9.6.
"""

import base64
import binascii
import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup, NavigableString, Tag

# --- regexy konsumenta (segmentuj.ts:12-17) --------------------------------

RE_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
RE_ATX = re.compile(r"^ {0,3}#{1,6}(\s|$)")
RE_TABLE_SEP = re.compile(r"^ {0,3}\|?[ :|-]*-[ :|-]*\|?\s*$")
RE_BQ = re.compile(r"^ {0,3}> ?")
RE_MARKER = re.compile(r"^ {0,3}([-*+]|\d{1,9}[.)])\s")
RE_BLANK = re.compile(r"^\s*$")

INDENT_MIN = 2  # segmentuj.ts:20

_STRUCTURAL = (RE_FENCE_OPEN, RE_ATX, RE_TABLE_SEP, RE_BQ, RE_MARKER)

MAX_IMAGE_BYTES = 10 * 1024 * 1024
_LXML_TEXT_LIMIT = 10 * 1000 * 1000  # XML_MAX_TEXT_LENGTH w libxml2

_MIME_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/avif": ".avif",
}

_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
_EMPHASIS = {"strong": "**", "b": "**", "em": "*", "i": "*"}
_BLOCK_CONTAINERS = {
    "div", "section", "article", "main", "header", "footer", "aside", "nav",
    "figure", "table", "thead", "tbody", "tfoot", "tr", "pre", "dl",
}
_TEXT_BLOCKS = {"p", "figcaption", "li", "td", "th", "dt", "dd"}

# U+00A0/2009/202F/2007 wypisane jawnie — kontrakt wymaga ich zwiniecia do spacji.
_WS = re.compile("[\\s\u00a0\u2009\u202f\u2007]+")
_LEAD_WS = re.compile(r"\s*")

# NFKD nie rozklada l z kreska ani kilku innych liter — osobna mapa.
_LATIN_MAP = str.maketrans({
    "ł": "l", "Ł": "L", "đ": "d", "Đ": "D", "ø": "o", "Ø": "O",
    "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "ß": "ss", "þ": "th", "Þ": "TH",
})


class ImageTooLargeError(Exception):
    """Obraz po zdekodowaniu przekracza MAX_IMAGE_BYTES — endpoint zamienia na 413."""

    def __init__(self, chapter_position: int, order: int, size_bytes: int):
        self.chapter_position = chapter_position
        self.order = order
        self.size_bytes = size_bytes
        super().__init__(
            f"obraz #{order} w rozdziale {chapter_position} ma {size_bytes} B "
            f"(limit {MAX_IMAGE_BYTES} B)"
        )


@dataclass
class ExportImage:
    order: int
    kind: str
    filename: Optional[str]
    data: Optional[bytes]
    mime: Optional[str]
    alt: str
    src: Optional[str] = None
    skipped: bool = False
    reason: Optional[str] = None
    # Pole ponad sygnature ze speca: manifest ma udokumentowany klucz "mime_unknown",
    # a bez nosnika nie da sie go wyprodukowac.
    mime_unknown: bool = False


@dataclass
class ChapterResult:
    md: str
    images: list
    blocks: dict
    dividers: list
    chars: int


@dataclass
class _Ctx:
    book_key: str
    position: int
    pad: int
    images: list = field(default_factory=list)
    dividers: list = field(default_factory=list)


@dataclass
class _Blk:
    lines: list
    is_image: bool = False


# --- funkcje pomocnicze ----------------------------------------------------

def slugify(text: str, fallback: str = "rozdzial") -> str:
    s = unicodedata.normalize("NFC", text or "").translate(_LATIN_MAP)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:40].strip("-") or fallback


def build_book_key(project_title: str, project_id: str) -> str:
    return "{}-{}".format(
        slugify(project_title, fallback="ksiazka"),
        (project_id or "").replace("-", "")[:8],
    )


def sha256_nfc(text: str) -> str:
    digest = hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8"))
    return "sha256:" + digest.hexdigest()


def escape_line(line: str) -> str:
    """Backslash przed pierwszym nie-bialym znakiem, gdy linia wyglada na strukture."""
    if not any(p.match(line) for p in _STRUCTURAL):
        return line
    cut = _LEAD_WS.match(line).end()
    return line[:cut] + "\\" + line[cut:]


def _lead_spaces(line: str) -> int:
    # segmentuj.ts liczy WYLACZNIE spacje (/^ */), nie dowolny whitespace.
    return len(line) - len(line.lstrip(" "))


def _starts_block(line: str) -> bool:
    # segmentuj.ts:29-30 — bez tabeli.
    return bool(
        RE_FENCE_OPEN.match(line)
        or RE_ATX.match(line)
        or RE_BQ.match(line)
        or RE_MARKER.match(line)
    )


def count_blocks(md: str) -> dict:
    """Odtworzenie granic blokow konsumenta na FINALNYM Markdownie (segmentuj.ts:53-146)."""
    counts = {"naglowek": 0, "akapit": 0, "lista": 0, "blockquote": 0, "kod": 0, "tabela": 0}
    lines = unicodedata.normalize("NFC", md).split("\n")
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]

        if RE_FENCE_OPEN.match(line):
            indent = _lead_spaces(line)
            fence_char = line[indent]
            fence_len = 0
            while indent + fence_len < len(line) and line[indent + fence_len] == fence_char:
                fence_len += 1
            close_re = re.compile(
                r"^ {0,3}" + re.escape(fence_char) + r"{" + str(fence_len) + r",}\s*$"
            )
            j = i + 1
            while j < n and not close_re.match(lines[j]):
                j += 1
            if j >= n:
                j = n - 1
            counts["kod"] += 1
            i = j + 1
            continue

        if RE_ATX.match(line):
            counts["naglowek"] += 1
            i += 1
            continue

        if "|" in line and i + 1 < n and RE_TABLE_SEP.match(lines[i + 1]):
            j = i + 1
            while j + 1 < n and "|" in lines[j + 1]:
                j += 1
            counts["tabela"] += 1
            i = j + 1
            continue

        if RE_BQ.match(line):
            j = i
            while j + 1 < n and RE_BQ.match(lines[j + 1]):
                j += 1
            counts["blockquote"] += 1
            i = j + 1
            continue

        if RE_MARKER.match(line):
            j = i
            while j + 1 < n:
                nxt = lines[j + 1]
                if RE_MARKER.match(nxt) or _lead_spaces(nxt) >= INDENT_MIN:
                    j += 1
                    continue
                if RE_BLANK.match(nxt):
                    k = j + 1
                    while k < n and RE_BLANK.match(lines[k]):
                        k += 1
                    if k < n and (RE_MARKER.match(lines[k]) or _lead_spaces(lines[k]) >= INDENT_MIN):
                        j = k
                        continue
                break
            counts["lista"] += 1
            i = j + 1
            continue

        if RE_BLANK.match(line):
            i += 1
            continue

        j = i
        while j + 1 < n and not RE_BLANK.match(lines[j + 1]) and not _starts_block(lines[j + 1]):
            j += 1
        counts["akapit"] += 1
        i = j + 1

    return counts


# --- obrazy ----------------------------------------------------------------

def _escape_alt(alt: str) -> str:
    out = (alt or "").replace("\\", "\\\\").replace("]", "\\]")
    return re.sub(r"[\r\n]+", " ", out)


def _wrap_url(url: str) -> str:
    return "<{}>".format(url) if any(c in url for c in " ()") else url


def _build_image(tag: Tag, ctx: _Ctx) -> Optional[str]:
    """Rejestruje obraz w ctx.images; zwraca linie Markdowna albo None (pominiety)."""
    order = len(ctx.images) + 1
    alt = _escape_alt(tag.get("alt") or "")
    src = (tag.get("src") or "").strip()

    def skip(kind: str, reason: str) -> None:
        ctx.images.append(ExportImage(
            order=order, kind=kind, filename=None, data=None, mime=None,
            alt=alt, src=src or None, skipped=True, reason=reason,
        ))

    lowered = src.lower()

    if lowered.startswith("http://") or lowered.startswith("https://"):
        ctx.images.append(ExportImage(
            order=order, kind="remote", filename=None, data=None, mime=None,
            alt=alt, src=src,
        ))
        return "![{}]({})".format(alt, _wrap_url(src))

    if not lowered.startswith("data:"):
        skip("remote", "unsupported_scheme")
        return None

    head, sep, payload = src[len("data:"):].partition(",")
    if not sep:
        skip("remote", "unsupported_scheme")
        return None

    params = head.split(";")
    mime = params[0].strip().lower()
    if not any(p.strip().lower() == "base64" for p in params[1:]):
        skip("embedded", "not_base64")
        return None

    ext = _MIME_EXT.get(mime)
    mime_unknown = ext is None

    try:
        data = base64.b64decode(re.sub(r"\s+", "", payload), validate=True)
    except (binascii.Error, ValueError):
        skip("embedded", "base64_decode_failed")
        return None

    if not data:
        skip("embedded", "empty_payload")
        return None

    if len(data) > MAX_IMAGE_BYTES:
        raise ImageTooLargeError(ctx.position, order, len(data))

    filename = "_media/{}-{:0{}d}-img-{:02d}{}".format(
        ctx.book_key, ctx.position, ctx.pad, order, ext or ".bin"
    )
    ctx.images.append(ExportImage(
        order=order, kind="embedded", filename=filename, data=data, mime=mime or None,
        alt=alt, mime_unknown=mime_unknown,
    ))
    return "![{}]({})".format(alt, filename)


# --- skladanie blokow ------------------------------------------------------

def _is_divider(node: Tag) -> bool:
    return node.name == "div" and node.has_attr("data-divider")


def _divider_style(node: Tag) -> str:
    return (node.get("data-divider-style") or "stars").strip() or "stars"


def _inline(nodes, ctx: _Ctx, image_lines: list, emphasis: bool = True) -> str:
    out = []
    for node in nodes:
        if isinstance(node, NavigableString):
            out.append(str(node))
            continue
        if not isinstance(node, Tag):
            continue
        name = node.name.lower()
        if name == "br":
            out.append("\n")
            continue
        if name == "img":
            line = _build_image(node, ctx)
            if line:
                image_lines.append(line)
            continue
        if name in _EMPHASIS:
            inner = _inline(list(node.children), ctx, image_lines, emphasis)
            core = inner.strip()
            if not core or not emphasis:
                out.append(inner)
                continue
            mark = _EMPHASIS[name]
            lead = inner[: len(inner) - len(inner.lstrip())]
            trail = inner[len(inner.rstrip()):]
            out.append("{}{}{}{}{}".format(lead, mark, core, mark, trail))
            continue
        out.append(_inline(list(node.children), ctx, image_lines, emphasis))
    return "".join(out)



def _to_lines(text: str) -> list:
    lines = []
    for raw in text.split("\n"):
        line = _WS.sub(" ", raw).strip()
        if line:
            lines.append(line)
    return lines


def _emit_paragraph(nodes, ctx: _Ctx, blocks: list) -> None:
    image_lines = []
    text = _inline(nodes, ctx, image_lines)
    lines = [escape_line(l) for l in _to_lines(text)]
    if lines:
        blocks.append(_Blk(lines))
    for line in image_lines:
        blocks.append(_Blk([line], is_image=True))


def _emit_heading(tag: Tag, ctx: _Ctx, blocks: list) -> None:
    image_lines = []
    # Wyjscie (B') z blokera G3 R1: w NAGLOWKU nie emitujemy markerow emfazy — ani pelnej,
    # ani czesciowej. Google Docs owija tresc naglowka w <strong> (czasem bez prefiksu, patrz
    # rozdz. 1 Ewy: `WSTEP: <strong>Jak zaczela...</strong>`), wiec marker nic nie rozroznia,
    # a K-NAG liczy go jako czesc tekstu i wysadza `apply`, gdy model zgubi pare gwiazdek.
    # Dzieki temu G3 (tekst naglowka == get_text() zrodla) jest prawdziwe Z KONSTRUKCJI.
    # Poza naglowkiem emfaza zostaje nietknieta.
    parts = _to_lines(_inline(list(tag.children), ctx, image_lines, emphasis=False))
    if parts:
        blocks.append(_Blk(["{} {}".format("#" * _HEADINGS[tag.name.lower()], " ".join(parts))]))
    for line in image_lines:
        blocks.append(_Blk([line], is_image=True))


def _emit_blockquote(tag: Tag, ctx: _Ctx, blocks: list) -> None:
    lines = []
    images = []
    for blk in _blocks_from(tag, ctx):
        if blk.is_image:
            images.append(blk)
        else:
            lines.extend(blk.lines)
    if lines:
        blocks.append(_Blk(["> " + l for l in lines]))
    blocks.extend(images)


def _list_item_lines(li: Tag, ctx: _Ctx, depth: int, image_lines: list) -> list:
    out = []
    buffer = []

    def flush():
        if not buffer:
            return
        for line in _to_lines(_inline(buffer, ctx, image_lines)):
            out.append(escape_line(line))
        del buffer[:]

    for child in li.children:
        if isinstance(child, NavigableString):
            if str(child).strip():
                buffer.append(child)
            continue
        if not isinstance(child, Tag):
            continue
        name = child.name.lower()
        if name in ("ul", "ol"):
            flush()
            sub = []
            _emit_list(child, ctx, sub, depth + 1)
            for blk in sub:
                if blk.is_image:
                    image_lines.extend(blk.lines)
                else:
                    out.extend(blk.lines)
        elif name == "p":
            flush()
            for line in _to_lines(_inline(list(child.children), ctx, image_lines)):
                out.append(escape_line(line))
        else:
            buffer.append(child)
    flush()

    if not out:
        return []
    cont = "  " * (depth + 1)
    return [out[0]] + [l if l.startswith(" ") else cont + l for l in out[1:]]


def _emit_list(tag: Tag, ctx: _Ctx, blocks: list, depth: int = 0) -> None:
    ordered = tag.name.lower() == "ol"
    try:
        number = int(tag.get("start", 1))
    except (TypeError, ValueError):
        number = 1
    indent = "  " * depth
    lines = []
    image_lines = []
    for li in tag.find_all("li", recursive=False):
        item = _list_item_lines(li, ctx, depth, image_lines)
        if not item:
            continue
        marker = "{}. ".format(number) if ordered else "- "
        number += 1
        lines.append(indent + marker + item[0])
        lines.extend(item[1:])
    if lines:
        blocks.append(_Blk(lines))
    for line in image_lines:
        blocks.append(_Blk([line], is_image=True))


def _blocks_from(container, ctx: _Ctx) -> list:
    blocks = []
    buffer = []

    def flush():
        if not buffer:
            return
        _emit_paragraph(list(buffer), ctx, blocks)
        del buffer[:]

    for child in container.children:
        if isinstance(child, NavigableString):
            if str(child).strip():
                buffer.append(child)
            continue
        if not isinstance(child, Tag):
            continue
        name = child.name.lower()
        if _is_divider(child):
            flush()
            ctx.dividers.append(_divider_style(child))
            blocks.append(_Blk(["---"]))
        elif name == "hr":
            flush()
            blocks.append(_Blk(["---"]))
        elif name in _HEADINGS:
            flush()
            _emit_heading(child, ctx, blocks)
        elif name in ("ul", "ol"):
            flush()
            _emit_list(child, ctx, blocks)
        elif name == "blockquote":
            flush()
            _emit_blockquote(child, ctx, blocks)
        elif name in _BLOCK_CONTAINERS:
            flush()
            blocks.extend(_blocks_from(child, ctx))
        elif name in _TEXT_BLOCKS:
            flush()
            _emit_paragraph(list(child.children), ctx, blocks)
        else:
            buffer.append(child)
    flush()
    return blocks


def chapter_to_markdown(html: str, book_key: str, position: int, pad: int = 2) -> ChapterResult:
    """Konwertuje processed_html rozdzialu na Markdown dla Redaktora.

    `pad` jest dodatkiem ponad sygnature ze speca: §book_key wymaga, zeby padding
    numeru rozdzialu urosl do 3 dla CALEGO eksportu przy >99 rozdzialach, a tej
    decyzji nie da sie podjac z samego `position`. Wywolanie 3-argumentowe
    zachowuje sie dokladnie jak w specu.
    """
    ctx = _Ctx(book_key=book_key, position=position, pad=pad)
    source = html or ""
    # libxml2 po cichu WYRZUCA atrybut dluzszy niz ~10 MB (XML_MAX_TEXT_LENGTH), czyli
    # gubi dokladnie ten `src`, ktory ma dac 413. Powyzej progu parsujemy html.parser,
    # ktory limitu nie ma — inaczej regula ">10 MB -> 413" jest nieegzekwowalna.
    parser = "lxml" if len(source) < _LXML_TEXT_LIMIT else "html.parser"
    soup = BeautifulSoup(source, parser)
    for tag in soup.find_all(["svg", "script", "style"]):
        tag.decompose()
    root = soup.body or soup

    blocks = _blocks_from(root, ctx)
    md = "\n\n".join("\n".join(b.lines) for b in blocks if b.lines)
    md = unicodedata.normalize("NFC", md)
    if md:
        md += "\n"

    return ChapterResult(
        md=md,
        images=ctx.images,
        blocks=count_blocks(md),
        dividers=ctx.dividers,
        chars=len(md),
    )
