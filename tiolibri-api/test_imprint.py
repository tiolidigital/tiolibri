"""Testy wersji wydania z `projects.imprint.version`.

Runner: `pip install pytest` lokalnie — NIE dopisujemy go do requirements.txt
(ta sama konwencja co test_md_exporter.py).
"""

from datetime import date

from app.services.imprint import (
    edition_version,
    inject_version_line,
    rights_with_version,
    version_line,
)

COLOPHON = (
    "<p>Copyright © 2026 Bożena Muszyńska</p>"
    "<p>Wydanie pierwsze elektroniczne. Szczecin 2026.</p>"
    "<p><strong>Redakcja, korekta i skład:</strong> Piotr Michalski</p>"
)


def test_edition_version_reads_imprint():
    assert edition_version({"imprint": {"version": " 1.0 "}}) == "1.0"


def test_edition_version_missing():
    assert edition_version({}) == ""
    assert edition_version({"imprint": None}) == ""
    assert edition_version({"imprint": {"isbn_pdf": "978"}}) == ""


def test_version_line_uses_polish_month_and_en_dash():
    assert version_line("1.0", date(2026, 9, 15)) == "Wersja 1.0 – wrzesień 2026"
    assert version_line("1.1", date(2027, 2, 1)) == "Wersja 1.1 – luty 2027"
    assert "—" not in version_line("1.0", date(2026, 9, 15))


def test_rights_with_version_before_rights_sentence():
    note = "© 2026 Bożena Muszyńska · Wydawnictwo TIOLI. Wszelkie prawa zastrzeżone."
    assert rights_with_version(note, "1.0") == (
        "© 2026 Bożena Muszyńska · Wydawnictwo TIOLI · wersja 1.0. Wszelkie prawa zastrzeżone."
    )
    assert rights_with_version(note, "") == note


def test_rights_with_version_skips_abbreviations():
    note = "© 2026 prof. dr hab. Jan Kowalski. Wszelkie prawa zastrzeżone."
    assert rights_with_version(note, "1.0") == (
        "© 2026 prof. dr hab. Jan Kowalski · wersja 1.0. Wszelkie prawa zastrzeżone."
    )


def test_rights_with_version_single_sentence():
    assert rights_with_version("© 2026 Ewa.", "1.0") == "© 2026 Ewa · wersja 1.0."
    assert rights_with_version("© 2026 Ewa", "1.0") == "© 2026 Ewa · wersja 1.0"


def test_inject_version_line_under_edition_paragraph():
    out = inject_version_line(COLOPHON, "Wersja 1.0 – wrzesień 2026")
    assert (
        "<p>Wydanie pierwsze elektroniczne. Szczecin 2026.</p>"
        "<p>Wersja 1.0 – wrzesień 2026</p>"
        "<p><strong>Redakcja"
    ) in out
    assert out.count("Wersja 1.0") == 1


def test_inject_version_line_does_not_span_paragraphs():
    html = "<p>Copyright</p><p>Wydanie pierwsze</p>"
    out = inject_version_line(html, "Wersja 1.0")
    assert out == "<p>Copyright</p><p>Wydanie pierwsze</p><p>Wersja 1.0</p>"


def test_inject_version_line_without_edition_paragraph():
    out = inject_version_line("<p>Copyright</p>", "Wersja 1.0")
    assert out == "<p>Wersja 1.0</p><p>Copyright</p>"
