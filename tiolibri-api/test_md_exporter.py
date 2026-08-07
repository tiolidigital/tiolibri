"""Testy konwertera HTML -> Markdown (spec md-export v0.4.1, krok 1 planu wdrozenia).

Runner: `pip install pytest` lokalnie — NIE dopisujemy go do requirements.txt
(obraz Railway ma zostac chudy; ta sama konwencja co test_polish_pdf.py).
"""

import base64
import re
import unicodedata

import pytest
from bs4 import BeautifulSoup

import app.services.md_exporter as md_exporter
from app.services.md_exporter import (
    ImageTooLargeError,
    build_book_key,
    chapter_to_markdown,
    count_blocks,
    escape_line,
    sha256_nfc,
    slugify,
)

BOOK_KEY = "osteoporoza-a1b2c3d4"

PNG_1PX = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def conv(html, position=1, pad=2):
    return chapter_to_markdown(html, BOOK_KEY, position, pad)


def md(html):
    return conv(html).md


def norm(s):
    # ta sama normalizacja co bramka G3: NFC, biale znaki zwiniete, case-insensitive
    s = unicodedata.normalize("NFC", s).replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().casefold()


def blocks(**kw):
    base = {"naglowek": 0, "akapit": 0, "lista": 0, "blockquote": 0, "kod": 0, "tabela": 0}
    base.update(kw)
    return base


# --- tabela reguł konwersji ------------------------------------------------

def test_naglowki_atx_nigdy_setext():
    assert md("<h1>Wstep</h1><h3>Podrozdzial</h3>") == "# Wstep\n\n### Podrozdzial\n"


def test_naglowek_pusty_pomijany_w_calosci():
    assert md("<h2>   </h2><p>tresc</p>") == "tresc\n"


def test_akapit_pusty_pomijany():
    assert md("<p></p><p>  </p><p>a</p>") == "a\n"


def test_bold_italic_i_zagniezdzenie():
    assert md("<p><strong>a</strong> i <em>b</em></p>") == "**a** i *b*\n"
    assert md("<p><strong><em>x</em></strong></p>") == "***x***\n"


def test_whitespace_wychodzi_na_zewnatrz_znacznikow():
    assert md("<p><strong>tekst </strong>dalej</p>") == "**tekst** dalej\n"


def test_puste_znaczniki_nie_sa_emitowane():
    assert md("<p>a<strong> </strong>b</p>") == "a b\n"
    assert md("<p>a<em></em>b</p>") == "ab\n"


def test_divider_ze_stylem_z_atrybutu_data_divider_style():
    res = conv('<p>a</p><div data-divider data-divider-style="dots" style="text-align:center"></div><p>b</p>')
    assert res.md == "a\n\n---\n\nb\n"
    assert res.dividers == ["dots"]


def test_divider_bez_stylu_domyslnie_stars():
    assert conv("<div data-divider></div>").dividers == ["stars"]


def test_hr_daje_separator_ale_nie_wchodzi_do_dividers():
    res = conv("<p>a</p><hr><p>b</p>")
    assert res.md == "a\n\n---\n\nb\n"
    assert res.dividers == []


def test_lista_nieuporzadkowana_i_uporzadkowana_rosnaco():
    assert md("<ul><li>a</li><li>b</li></ul>") == "- a\n- b\n"
    assert md("<ol><li>a</li><li>b</li><li>c</li></ol>") == "1. a\n2. b\n3. c\n"


def test_ol_start_od_n():
    assert md('<ol start="4"><li>a</li><li>b</li></ol>') == "4. a\n5. b\n"


def test_lista_zagniezdzona_wciecie_dwie_spacje():
    assert md("<ul><li>a<ul><li>b</li></ul></li></ul>") == "- a\n  - b\n"


def test_li_puste_pomijane():
    assert md("<ul><li></li><li>a</li></ul>") == "- a\n"


def test_blockquote_prefiks_na_kazdej_linii():
    assert md("<blockquote><p>a</p><p>b</p></blockquote>") == "> a\n> b\n"


def test_br_daje_pojedynczy_newline_w_jednym_akapicie():
    res = conv("<p>pierwsza<br>druga</p>")
    assert res.md == "pierwsza\ndruga\n"
    assert res.blocks == blocks(akapit=1)


def test_nbsp_i_waskie_spacje_zwijane_do_zwyklej_spacji():
    assert md("<p>w\u00a0lesie\u2009i\u202fw\u2007polu</p>") == "w lesie i w polu\n"


def test_nfc_na_wyjsciu():
    # "ą" w NFD (a + U+0328) ma wyjsc jako pojedynczy znak NFC.
    assert md("<p>m\u0105\u0328ka</p>") != ""
    assert md("<p>a\u0328</p>") == "\u0105\n"


def test_unwrap_nieznanego_tagu():
    assert md("<p><span>a</span> <mark>b</mark></p>") == "a b\n"


def test_svg_script_style_decompose_wraz_z_trescia():
    assert md("<p>a</p><svg><text>ukryte</text></svg><script>zle()</script><style>p{}</style>") == "a\n"


def test_tekst_top_level_poza_p_nie_ginie():
    assert md("goly tekst<p>a</p>") == "goly tekst\n\na\n"


def test_encje_zdekodowane():
    assert md("<p>a &amp; b &lt;c&gt;</p>") == "a & b <c>\n"


def test_figcaption_jako_akapit_po_obrazie():
    res = conv(
        '<figure><img src="data:image/png;base64,{}" alt="wykres">'
        "<figcaption>Ryc. 1</figcaption></figure>".format(PNG_1PX)
    )
    assert res.md == "![wykres](_media/{}-01-img-01.png)\n\nRyc. 1\n".format(BOOK_KEY)


def test_plik_konczy_sie_dokladnie_jednym_newline():
    out = md("<p>a</p><p>b</p>")
    assert out.endswith("\n") and not out.endswith("\n\n")


# --- escaping wyprowadzony z segmentuj.ts:12-17 ----------------------------

STRUKTURALNE = [
    "```python",
    "~~~",
    "# tytul",
    "###### tytul",
    "---",
    "| :-- |",
    "> cytat",
    "- punkt",
    "* punkt",
    "+ punkt",
    "1. punkt",
    "9) punkt",
]


@pytest.mark.parametrize("wzorzec", STRUKTURALNE)
@pytest.mark.parametrize("wciecie", ["", " ", "  ", "   "])
def test_escaping_kazdego_wzorca_strukturalnego(wzorzec, wciecie):
    linia = wciecie + wzorzec
    out = escape_line(linia)
    assert out == wciecie + "\\" + wzorzec
    # jedno wstawienie neutralizuje kazdy z pieciu wzorcow
    assert count_blocks(out + "\n") == blocks(akapit=1)


@pytest.mark.parametrize("wzorzec", ["#hasztag", "-myslnik", "1.5 mg", "*kursywa* w srodku"])
def test_przypadki_negatywne_nie_dostaja_backslasha(wzorzec):
    assert escape_line(wzorzec) == wzorzec


def test_escaping_obejmuje_kazda_linie_bloku_nie_tylko_pierwsza():
    res = conv("<p>proza<br># nie naglowek<br>- nie lista</p>")
    assert res.md == "proza\n\\# nie naglowek\n\\- nie lista\n"
    assert res.blocks == blocks(akapit=1)


def test_wlasny_separator_nigdy_nie_jest_escapowany():
    res = conv("<p>a</p><hr><p>b</p>")
    assert "\\---" not in res.md
    assert res.blocks == blocks(akapit=3)


def test_backslashy_w_prozie_nie_sa_podwajane():
    assert md("<p>C:\\temp</p>") == "C:\\temp\n"


# --- blocks: fixture per konsekwencja (kazdy asertuje CALY slownik) --------

def test_blocks_lista_wieloelementowa_to_jeden_blok():
    assert conv("<ul><li>a</li><li>b</li><li>c</li><li>d</li><li>e</li></ul>").blocks == blocks(lista=1)


def test_blocks_lista_zagniezdzona_to_jeden_blok():
    assert conv("<ul><li>a<ul><li>b</li></ul></li></ul>").blocks == blocks(lista=1)


def test_blocks_li_z_drugim_akapitem_to_jeden_blok():
    assert conv("<ul><li><p>a</p><p>b</p></li></ul>").blocks == blocks(lista=1)


def test_blocks_blockquote_na_cztery_linie_to_jeden_blok():
    html = "<blockquote><p>a</p><p>b</p><p>c</p><p>d</p></blockquote>"
    assert conv(html).blocks == blocks(blockquote=1)


def test_blocks_obraz_liczy_sie_jako_akapit():
    html = '<p><img src="data:image/png;base64,{}" alt=""></p>'.format(PNG_1PX)
    assert conv(html).blocks == blocks(akapit=1)


def test_blocks_separator_liczy_sie_jako_akapit():
    assert conv("<hr>").blocks == blocks(akapit=1)


def test_blocks_figcaption_liczy_sie_jako_akapit():
    html = '<figure><img src="https://x/y.png" alt=""><figcaption>Ryc.</figcaption></figure>'
    assert conv(html).blocks == blocks(akapit=2)


def test_blocks_dwie_listy_rozdzielone_akapitem():
    html = "<ul><li>a</li></ul><p>proza</p><ol><li>b</li></ol>"
    assert conv(html).blocks == blocks(lista=2, akapit=1)


def test_blocks_naglowek_to_jeden_blok_jednoliniowy():
    assert conv("<h2>Tytul</h2><p>a</p>").blocks == blocks(naglowek=1, akapit=1)


def test_blocks_kod_i_tabela_zawsze_zerami_dla_naszego_wyjscia():
    html = "<pre><code>x = 1</code></pre><table><tr><td>a</td><td>b</td></tr></table>"
    res = conv(html)
    assert res.blocks["kod"] == 0 and res.blocks["tabela"] == 0


# --- obrazy (ERRATA E4) ----------------------------------------------------

def test_data_uri_ladują_w_media_i_krotka_linia_w_prozie():
    res = conv('<p><img src="data:image/png;base64,{}" alt="rys"></p>'.format(PNG_1PX))
    assert res.md == "![rys](_media/{}-01-img-01.png)\n".format(BOOK_KEY)
    img = res.images[0]
    assert (img.kind, img.mime, img.skipped) == ("embedded", "image/png", False)
    assert img.filename == "_media/{}-01-img-01.png".format(BOOK_KEY)
    assert img.data[:8] == b"\x89PNG\r\n\x1a\n"


def test_mime_z_parametrami_ignoruje_parametry():
    res = conv('<p><img src="data:image/png;charset=utf-8;base64,{}" alt=""></p>'.format(PNG_1PX))
    assert res.images[0].filename.endswith(".png")


def test_mime_spoza_allowlisty_dostaje_bin():
    res = conv('<p><img src="data:image/tiff;base64,{}" alt=""></p>'.format(PNG_1PX))
    assert res.images[0].filename.endswith(".bin")
    assert res.images[0].mime_unknown is True


def test_svg_xml_tez_trafia_w_bin():
    payload = base64.b64encode(b"<svg/>").decode()
    res = conv('<p><img src="data:image/svg+xml;base64,{}" alt=""></p>'.format(payload))
    assert res.images[0].filename.endswith(".bin")


def test_brak_base64_pomijany_bez_bloku_obrazu():
    res = conv('<p><img src="data:image/png,%89PNG" alt="x"></p>')
    assert res.md == ""
    assert (res.images[0].skipped, res.images[0].reason) == (True, "not_base64")


def test_malformed_base64_pomijany():
    res = conv('<p><img src="data:image/png;base64,!!!nie-base64!!!" alt=""></p>')
    assert (res.images[0].skipped, res.images[0].reason) == (True, "base64_decode_failed")


def test_pusty_payload_pomijany():
    res = conv('<p><img src="data:image/png;base64," alt=""></p>')
    assert (res.images[0].skipped, res.images[0].reason) == (True, "empty_payload")


def test_obraz_ponad_10mb_rzuca_wyjatek():
    payload = base64.b64encode(b"\0" * (10 * 1024 * 1024 + 1)).decode()
    with pytest.raises(ImageTooLargeError) as exc:
        conv('<p><img src="data:image/png;base64,{}" alt=""></p>'.format(payload), position=7)
    assert exc.value.chapter_position == 7


def test_https_zostaje_jak_jest():
    res = conv('<p><img src="https://x.supabase.co/a.png" alt="dxa"></p>')
    assert res.md == "![dxa](https://x.supabase.co/a.png)\n"
    assert (res.images[0].kind, res.images[0].filename) == ("remote", None)


def test_inny_schemat_pomijany():
    res = conv('<p><img src="file:///etc/passwd" alt=""></p>')
    assert (res.images[0].skipped, res.images[0].reason) == (True, "unsupported_scheme")


def test_alt_z_nawiasem_kwadratowym_i_newline_jest_neutralizowany():
    res = conv('<p><img src="https://x/y.png" alt="a]b&#10;c\\d"></p>')
    assert res.md == "![a\\]b c\\\\d](https://x/y.png)\n"


def test_url_ze_spacja_owiniety_w_nawiasy_katowe():
    res = conv('<p><img src="https://x/a b(1).png" alt=""></p>')
    assert res.md == "![](<https://x/a b(1).png>)\n"


def test_obraz_wsrod_tekstu_wyniesiony_do_wlasnego_bloku_zaraz_po():
    res = conv('<p>przed <img src="https://x/y.png" alt="i"> po</p>')
    assert res.md == "przed po\n\n![i](https://x/y.png)\n"


def test_regresja_zaden_ciag_data_nie_wychodzi_do_md():
    res = conv(
        '<p>tekst</p><p><img src="data:image/png;base64,{}" alt="a"></p>'.format(PNG_1PX)
    )
    assert "data:" not in res.md


# --- slug, book_key, hash --------------------------------------------------

def test_slugify_ascii_bez_diakrytykow():
    assert slugify("Gęstość kości — ĄĆĘŁŃÓŚŹŻ") == "gestosc-kosci-acelnoszz"


def test_slugify_pusty_wynik_daje_fallback():
    assert slugify("!!!") == "rozdzial"
    assert slugify("", fallback="ksiazka") == "ksiazka"


def test_slugify_obcina_do_40_znakow():
    assert len(slugify("a" * 80)) == 40


def test_book_key_bierze_osiem_hex_bez_myslnikow():
    assert build_book_key("Osteoporoza", "a1b2c3d4-1111-2222-3333-444444444444") == "osteoporoza-a1b2c3d4"


def test_book_key_nigdy_nie_zaczyna_sie_od_myslnika():
    assert build_book_key("???", "a1b2c3d4-1111-2222-3333-444444444444").startswith("ksiazka-")


def test_sha256_nfc_ma_prefiks_i_liczy_na_nfc():
    assert sha256_nfc("a\u0328") == sha256_nfc("\u0105")
    assert sha256_nfc("x").startswith("sha256:")


def test_padding_pozycji_rosnie_do_trzech_cyfr():
    res = conv('<p><img src="data:image/png;base64,{}" alt=""></p>'.format(PNG_1PX), position=7, pad=3)
    assert res.images[0].filename == "_media/{}-007-img-01.png".format(BOOK_KEY)


def test_chars_to_dlugosc_md():
    res = conv("<p>abc</p>")
    assert res.chars == len(res.md) == 4


# --- emfaza w naglowku: wyjscie (B\') z blokera G3 R1 ----------------------
#
# W naglowku NIE emitujemy markerow emfazy — ani pelnej, ani czesciowej. Google Docs owija
# tresc naglowka w <strong>, wiec marker nic nie rozroznia, a K-NAG liczy go jako czesc
# tekstu i wysadza `apply`, gdy model zgubi pare gwiazdek. Poza naglowkiem emfaza zostaje.

PELNA_EMFAZA = [
    ("<h2><strong>Suplementacja</strong></h2>", "## Suplementacja\n"),
    ("<h2><b>Suplementacja</b></h2>", "## Suplementacja\n"),
    ("<h3><em>Dawkowanie</em></h3>", "### Dawkowanie\n"),
    ("<h1><strong><em>Wstep</em></strong></h1>", "# Wstep\n"),
    ("<h2><span><strong>Przez span</strong></span></h2>", "## Przez span\n"),
    ("<h2>  <strong>Ze spacjami</strong>  </h2>", "## Ze spacjami\n"),
    ("<h2><strong>Wapn</strong> <strong>i witamina D</strong></h2>", "## Wapn i witamina D\n"),
    ("<h4><strong>Ryzyko</strong> <em>zlaman</em></h4>", "#### Ryzyko zlaman\n"),
]

CZESCIOWA_EMFAZA = [
    ("<h2><strong>Wapn</strong> i witamina D</h2>", "## Wapn i witamina D\n"),
    ("<h2>Ryzyko <em>zlaman</em></h2>", "## Ryzyko zlaman\n"),
    ("<h3>Dawka <strong>1000 mg</strong> na dobe</h3>", "### Dawka 1000 mg na dobe\n"),
    ("<h2><span>Zwykly </span><strong>pogrubiony</strong></h2>", "## Zwykly pogrubiony\n"),
    # Ksztalt WZIETY Z PRODUKCJI — rozdz. 1 Ewy. W R1 byl zamaskowany diagnostyczna
    # normalizacja w harnessie; to on przesadzil o (B\') zamiast (B).
    ('<h1><img src="https://x/y.png"/>WSTEP: <strong>Jak zaczela sie moja historia.</strong></h1>',
     "# WSTEP: Jak zaczela sie moja historia.\n\n![](https://x/y.png)\n"),
]


@pytest.mark.parametrize("html,oczekiwane", PELNA_EMFAZA)
def test_naglowek_pelna_emfaza_bez_markerow(html, oczekiwane):
    assert md(html) == oczekiwane


@pytest.mark.parametrize("html,oczekiwane", CZESCIOWA_EMFAZA)
def test_naglowek_czesciowa_emfaza_tez_bez_markerow(html, oczekiwane):
    assert md(html) == oczekiwane


@pytest.mark.parametrize("html,_oczekiwane", PELNA_EMFAZA + CZESCIOWA_EMFAZA)
def test_naglowek_rowny_get_text_zrodla(html, _oczekiwane):
    """Lokalne odbicie bramki G3 z ZEROWA tolerancja: tekst naglowka po konwersji ==
    get_text() zrodla, dla emfazy pelnej I czesciowej. To jest wlasnie kontrakt, ktory
    (B\') czyni prawdziwym z konstrukcji."""
    zrodlo = norm(BeautifulSoup(html, "lxml").find(re.compile(r"^h[1-6]$")).get_text())
    wynik = norm(re.match(r"^#{1,6}\s*(.*)$", md(html).strip().split("\n")[0]).group(1))
    assert wynik == zrodlo


@pytest.mark.parametrize("html,_oczekiwane", PELNA_EMFAZA + CZESCIOWA_EMFAZA)
def test_zaden_naglowek_nie_niesie_markera_emfazy(html, _oczekiwane):
    """Kazdy `**` albo `*` w chunku naglowkowym to mina pod K-NAG przy `apply`."""
    linia = md(html).strip().split("\n")[0]
    assert "*" not in linia and "_" not in linia


def test_akapit_w_calosci_pogrubiony_zachowuje_markery():
    """Regula (B) dotyczy WYLACZNIE naglowkow — akapit zostaje nietkniety."""
    assert md("<p><strong>Caly akapit</strong></p>") == "**Caly akapit**\n"
    assert md("<ul><li><strong>Caly punkt</strong></li></ul>") == "- **Caly punkt**\n"
    assert md("<blockquote><p><em>Caly cytat</em></p></blockquote>") == "> *Caly cytat*\n"


def test_naglowek_z_sama_emfaza_pusta_nadal_pomijany():
    assert md("<h2><strong>   </strong></h2><p>tresc</p>") == "tresc\n"


def test_naglowek_pelna_emfaza_liczy_sie_jako_jeden_blok_naglowka():
    assert conv("<h2><strong>Tytul</strong></h2><p>a</p>").blocks == blocks(naglowek=1, akapit=1)


# --- parytet parserow wokol sciezki fallbacku (uwaga Codexa R1) ------------
#
# Konwerter schodzi na html.parser dla dokumentu >=10 MB, bo lxml po cichu wyrzuca
# atrybut `src` ponad XML_MAX_TEXT_LENGTH i czyni regule „>10 MB -> 413" nieegzekwowalna.
# Wejsciem jest `processed_html` z TipTapa, czyli markup DOMKNIETY — i tylko na takim
# parytet jest obiecany. Na markupie uszkodzonym parsery roznia sie i to jest udowodnione
# nizej, a nie przemilczane.

PARYTET_PROBKI = [
    "<h2><strong>Naglowek</strong></h2><p>proza</p>",
    "<ul><li>a</li><li>b</li></ul><ol start='3'><li>c</li></ol>",
    "<div data-divider data-divider-style='dots'></div><p>po separatorze</p>",
    "<p>a<br>b</p><blockquote><p>cytat</p></blockquote>",
    "<p>encje &amp; nbsp&nbsp;i tekst</p><figure><img src='https://x/y.png' alt='i'>"
    "<figcaption>podpis</figcaption></figure>",
    "<p>zagniezdzone <strong><em>x</em></strong> dalej</p><svg><text>ukryte</text></svg>",
    "<h3>Naglowek</h3><p>tekst <span>w spanie</span> i <strong>bold</strong></p>",
]

ROZJAZD_PROBKI = [
    "<ul><li>a<li>b</ul>",           # <li> bez domkniecia
    "<h3>Bez domkniecia<p>akapit</p>",  # <hN> bez domkniecia
]


@pytest.mark.parametrize("probka", PARYTET_PROBKI)
def test_parytet_lxml_i_html_parser_na_domknietym_markupie(monkeypatch, probka):
    wzorzec = conv(probka)
    monkeypatch.setattr(md_exporter, "_LXML_TEXT_LIMIT", 0)  # wymusza html.parser
    fallback = conv(probka)
    assert fallback.md == wzorzec.md
    assert fallback.blocks == wzorzec.blocks


@pytest.mark.parametrize("probka", ROZJAZD_PROBKI)
def test_parsery_roznia_sie_na_markupie_uszkodzonym(monkeypatch, probka):
    """Zmierzona GRANICA parytetu, nie regresja. Na niedomknietym <li>/<hN> lxml domyka
    inaczej niz html.parser, wiec wyjscia sie roznia. Nie dotyka nas, bo `processed_html`
    pochodzi z TipTapa. Gdyby ten test sczerwienial (parsery sie zrownaly), granice
    mozna przesunac — ale nie wolno jej zakladac w ciemno."""
    wzorzec = conv(probka)
    monkeypatch.setattr(md_exporter, "_LXML_TEXT_LIMIT", 0)
    assert conv(probka).md != wzorzec.md


def test_fallback_faktycznie_przelacza_parser(monkeypatch):
    """Bez tego test parytetu bylby zielony takze wtedy, gdyby monkeypatch nic nie zmienil."""
    uzyte = []
    oryginal = md_exporter.BeautifulSoup
    monkeypatch.setattr(
        md_exporter, "BeautifulSoup",
        lambda src, parser, *a, **kw: (uzyte.append(parser), oryginal(src, parser, *a, **kw))[1],
    )
    conv("<p>a</p>")
    assert uzyte == ["lxml"]
    monkeypatch.setattr(md_exporter, "_LXML_TEXT_LIMIT", 0)
    conv("<p>a</p>")
    assert uzyte == ["lxml", "html.parser"]
