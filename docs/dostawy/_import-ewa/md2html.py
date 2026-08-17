#!/usr/bin/env python3
"""Markdown Redaktora -> processed_html TIOLIBRI (odwrocenie md_exporter.py).

Ksztalt wyjscia jest przepisany z tego, co REALNIE lezy w bazie (wzorzec-html/),
nie z CommonMarka:
  - brak wciec i nowych linii miedzy blokami
  - <li><p>tekst</p></li> (TipTap)
  - obrazek rozdzialu jako PIERWSZE dziecko <h1>, nie osobny blok
  - naglowki owiniete w <strong> (tak trzyma je edytor)

Czego markdown nie unosi, a co bylo w zrodle — <a>, <u>, czesciowy <strong>
w naglowku — odtwarzamy z STAREGO html rozdzialu, ale WYLACZNIE jako markup:
tekst pochodzi zawsze z pliku dostawy. Gdy Redaktor zmienil tekst naglowka,
markup budujemy regula i raportujemy to jako `naglowek przebudowany`.
"""
import html as html_mod
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup

RE_ATX = re.compile(r"^ {0,3}(#{1,6})(?:\s+(.*))?$")
RE_MARKER = re.compile(r"^( *)([-*+]|\d{1,9}[.)])\s+(.*)$")
RE_BQ = re.compile(r"^ {0,3}> ?(.*)$")
RE_HR = re.compile(r"^ {0,3}-{3,}\s*$")
RE_OBRAZ = re.compile(r"^!\[([^\]]*)\]\((?:<([^>]*)>|([^)]*))\)$")
# obrazek moze stac W SRODKU linii (Google Docs wstawia go na poczatku naglowka R8)
RE_OBRAZ_INLINE = re.compile(r"!\[([^\]]*)\]\((?:<([^>]*)>|([^)]*))\)")
RE_OBRAZ_REF = re.compile(r"!\[([^\]]*)\]\[([^\]]+)\]")
RE_DEF_REF = re.compile(r"^\[([^\]]+)\]:\s*<?([^\s>]+)>?\s*$", re.M)
RE_URL = re.compile(r"(?<![\w/])(https?://[^\s<>\"')\]]+[^\s<>\"')\].,;:])")
# backslash wstawiony przez escape_line() — tylko przed PIERWSZYM nie-bialym znakiem
RE_ESC_WIODACY = re.compile(r"^(\s*)\\(?=\S)")
# escape'y Google Docs (tylko R8) — w srodku linii, przed interpunkcja
RE_ESC_GDOCS = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~=<>&$%^\"'])")

_WS = re.compile("[\\s    ]+")


@dataclass
class Wynik:
    html: str
    naglowki_odtworzone: int = 0
    naglowki_przebudowane: list = field(default_factory=list)
    linki_odtworzone: list = field(default_factory=list)
    obrazki: list = field(default_factory=list)
    utracone: list = field(default_factory=list)
    bloki: dict = field(default_factory=dict)


def _norm(t: str) -> str:
    return _WS.sub(" ", unicodedata.normalize("NFC", t or "")).strip()


def _esc(t: str) -> str:
    return html_mod.escape(t, quote=False)


# --- inline ----------------------------------------------------------------

def _inline(tekst: str, linki: list) -> str:
    """**bold**, *italic*, gole URL-e -> <a>. Reszta to tekst."""
    out = []
    i = 0
    n = len(tekst)
    while i < n:
        if tekst.startswith("**", i):
            j = tekst.find("**", i + 2)
            if j != -1 and tekst[i + 2:j].strip():
                out.append("<strong>" + _inline(tekst[i + 2:j], linki) + "</strong>")
                i = j + 2
                continue
        if tekst[i] == "*":
            j = tekst.find("*", i + 1)
            if j != -1 and tekst[i + 1:j].strip() and "\n" not in tekst[i + 1:j]:
                out.append("<em>" + _inline(tekst[i + 1:j], linki) + "</em>")
                i = j + 1
                continue
        m = RE_URL.match(tekst, i)
        if m:
            url = m.group(1)
            linki.append(url)
            out.append(
                '<a target="_blank" rel="noopener noreferrer nofollow" href="{}">{}</a>'.format(
                    html_mod.escape(url, quote=True), _esc(url))
            )
            i = m.end()
            continue
        j = i
        while j < n and tekst[j] not in "*h" :
            j += 1
        if j == i:
            j = i + 1
        out.append(_esc(tekst[i:j]))
        i = j
    return "".join(out)


# --- bloki -----------------------------------------------------------------

def _podziel_bloki(md: str) -> list:
    bloki = []
    biezacy = []
    for linia in md.split("\n"):
        if linia.strip() == "":
            if biezacy:
                bloki.append(biezacy)
                biezacy = []
            continue
        biezacy.append(linia)
    if biezacy:
        bloki.append(biezacy)
    return bloki


def _lista_html(linie: list, linki: list, poziom: int = 0) -> str:
    """Zagniezdzenie po wcieciu 2 spacji na poziom (md_exporter._emit_list)."""
    uporzadkowana = False
    pozycje = []          # [(linie_pozycji, [podlinie])]
    for linia in linie:
        m = RE_MARKER.match(linia)
        wciecie = len(linia) - len(linia.lstrip(" "))
        if m and wciecie == poziom * 2:
            uporzadkowana = bool(re.match(r"^\d", m.group(2)))
            pozycje.append([m.group(3), []])
        elif pozycje:
            pozycje[-1][1].append(linia)
        else:
            pozycje.append([linia.strip(), []])
    czesci = []
    for glowna, ogon in pozycje:
        tresc = "<p>" + _inline(glowna, linki) + "</p>"
        if ogon:
            podlista = [l for l in ogon if RE_MARKER.match(l)]
            if podlista and len(podlista) == len(ogon):
                tresc += _lista_html(ogon, linki, poziom + 1)
            else:
                tresc += "<p>" + _inline(" ".join(l.strip() for l in ogon), linki) + "</p>"
        czesci.append("<li>" + tresc + "</li>")
    tag = "ol" if uporzadkowana else "ul"
    return "<{0}>{1}</{0}>".format(tag, "".join(czesci))


def _wyjmij_obrazki(tekst: str) -> tuple:
    """Zwraca (tekst_bez_obrazkow, [src]) — md_exporter emituje obraz z naglowka/akapitu
    jako osobny blok PO nim, wiec przy odwracaniu wyjmujemy go tak samo."""
    srcs = []

    def _zbierz(m):
        srcs.append(m.group(2) or m.group(3) or "")
        return ""

    return RE_OBRAZ_INLINE.sub(_zbierz, tekst).strip(), srcs


def _odescapuj(linia: str, gdocs: bool) -> str:
    linia = RE_ESC_WIODACY.sub(r"\1", linia)
    if gdocs:
        linia = RE_ESC_GDOCS.sub(r"\1", linia)
    return linia


# --- odtwarzanie markupu naglowkow ze starego HTML -------------------------

def _stare_naglowki(stary_html: str) -> list:
    if not stary_html:
        return []
    zupa = BeautifulSoup(stary_html, "lxml")
    out = []
    for h in zupa.find_all(re.compile(r"^h[1-6]$")):
        kopia = BeautifulSoup(str(h), "lxml").find(re.compile(r"^h[1-6]$"))
        for img in kopia.find_all("img"):
            img.decompose()
        wnetrze = "".join(str(c) for c in kopia.children)
        st = kopia.find("strong")
        pelny_strong = bool(st and _norm(kopia.get_text()) == _norm(st.get_text()))
        out.append({"tekst": _norm(kopia.get_text()), "wnetrze": wnetrze, "pelny_strong": pelny_strong})
    return out


# --- glowne ----------------------------------------------------------------

def md_to_html(md: str, stary_html: str = "", podmien_obraz: Optional[str] = None,
               gdocs: bool = False) -> Wynik:
    w = Wynik(html="")
    md = unicodedata.normalize("NFC", md)

    # obrazek referencyjny Google Docs: ![][image1] + linia definicji [image1]: <data:...>
    definicje = {m.group(1): m.group(2) for m in RE_DEF_REF.finditer(md)}
    if definicje:
        md = RE_DEF_REF.sub("", md)

        def _ref(m):
            cel = definicje.get(m.group(2), "")
            if podmien_obraz and cel.startswith("data:"):
                w.utracone.append(f"data:base64 ({len(cel)} B) -> {podmien_obraz}")
                return "![{}]({})".format(m.group(1), podmien_obraz)
            return "![{}]({})".format(m.group(1), cel)

        md = RE_OBRAZ_REF.sub(_ref, md)

    stare_h = _stare_naglowki(stary_html)
    idx_h = 0
    linki = []
    czesci = []       # (rodzaj, html)

    for blok in _podziel_bloki(md):
        linie = [_odescapuj(l, gdocs) for l in blok]
        pierwsza = linie[0]

        m_obraz = RE_OBRAZ.match(pierwsza.strip())
        if m_obraz and len(linie) == 1:
            src = m_obraz.group(2) or m_obraz.group(3) or ""
            if podmien_obraz and src.startswith("data:"):
                w.utracone.append(f"data:base64 ({len(src)} B) -> {podmien_obraz}")
                src = podmien_obraz
            w.obrazki.append(src)
            czesci.append(("img", '<img class="editor-image" src="{}">'.format(
                html_mod.escape(src, quote=True))))
            continue

        m_atx = RE_ATX.match(pierwsza)
        if m_atx:
            poziom = len(m_atx.group(1))
            tekst = " ".join([(m_atx.group(2) or "")] + [l.strip() for l in linie[1:]]).strip()
            tekst, obrazki_naglowka = _wyjmij_obrazki(tekst)
            stary = stare_h[idx_h] if idx_h < len(stare_h) else None
            idx_h += 1
            if stary and stary["tekst"] == _norm(tekst):
                wnetrze = stary["wnetrze"]
                w.naglowki_odtworzone += 1
            else:
                srodek = _inline(tekst, linki)
                wnetrze = "<strong>{}</strong>".format(srodek) if (stary is None or stary["pelny_strong"]) else srodek
                if stary is not None:
                    w.naglowki_przebudowane.append({"h": poziom, "nowy": tekst[:90], "stary": stary["tekst"][:90]})
            czesci.append(("h", "<h{0}>{1}</h{0}>".format(poziom, wnetrze)))
            for src in obrazki_naglowka:
                if podmien_obraz and src.startswith("data:"):
                    w.utracone.append(f"data:base64 ({len(src)} B) -> {podmien_obraz}")
                    src = podmien_obraz
                w.obrazki.append(src)
                czesci.append(("img", '<img class="editor-image" src="{}">'.format(
                    html_mod.escape(src, quote=True))))
            continue

        if RE_HR.match(pierwsza):
            czesci.append(("hr", "<hr>"))
            continue

        if RE_BQ.match(pierwsza):
            tresc = " ".join(RE_BQ.match(l).group(1) if RE_BQ.match(l) else l.strip() for l in linie)
            czesci.append(("bq", "<blockquote><p>{}</p></blockquote>".format(_inline(tresc, linki))))
            continue

        if RE_MARKER.match(pierwsza):
            czesci.append(("list", _lista_html(linie, linki)))
            continue

        czesci.append(("p", "<p>{}</p>".format(
            "<br>".join(_inline(l.strip(), linki) for l in linie))))

    # obrazek bezposrednio po naglowku wraca DO naglowka (jak w bazie)
    zlozone = []
    for rodzaj, frag in czesci:
        if rodzaj == "img" and zlozone and zlozone[-1][0] == "h":
            poprz = zlozone[-1][1]
            zlozone[-1] = ("h", re.sub(r"^(<h[1-6]>)", r"\1" + frag.replace("\\", "\\\\"), poprz, count=1))
            continue
        zlozone.append((rodzaj, frag))

    w.html = "".join(frag for _, frag in zlozone)
    w.linki_odtworzone = linki
    return w
