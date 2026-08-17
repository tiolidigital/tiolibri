#!/usr/bin/env python3
"""DRY-RUN importu: 12 plikow dostawy -> processed_html, do plikow. BEZ DOTYKANIA BAZY.

Sprawdzian odbiorczy (round-trip): wyprodukowany HTML wraca przez chapter_to_markdown()
z naszego eksportera i musi dac Markdown zgodny z plikiem dostawy. Dla 11 rozdzialow
oczekujemy zgodnosci CO DO BAJTU (po NFC); dla R8 — zgodnosci prozy, bo tam zrodlem
jest Google Docs (escape'y \\= \\! \\- i obrazek data:).
"""
import json, pathlib, re, sys, unicodedata, difflib

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
sys.path.insert(0, str(REPO / "tiolibri-api"))
SCRATCH = pathlib.Path(__file__).parent
sys.path.insert(0, str(SCRATCH))

from app.services.md_exporter import chapter_to_markdown, count_blocks, build_book_key  # noqa: E402
from md2html import md_to_html  # noqa: E402

DOSTAWA_DIR = REPO / "docs/dostawy/ewa-2026-08-15"
WZORZEC = SCRATCH / "wzorzec-html"
WYNIK = SCRATCH / "dry-run"
PROJECT = "d73dcc3b-74ed-4d23-8cbb-d600c8f5306f"
TYTUL = "Kości na całe życie 4.0"
# URL obrazka R8 ze SWIEZEGO eksportu produkcji (zastepuje data:base64 z Google Docs)
OBRAZ_R8 = ("https://klhnyagtobgtxnexdsls.supabase.co/storage/v1/object/public/assets/"
            "17adb766-c0e2-481b-8201-5248c6fae490/images/1775154332943-rozdzial-8.png")

PARY = [
    ("01", "WSTEP_Historia-z-osteoporoza.md"),
    ("02", "ROZDZIAL-1_Osteoporoza-co-to-oznacza.md"),
    ("03", "ROZDZIAL-2_Fakty-naukowe.md"),
    ("04", "ROZDZIAL-3_Skladniki-budulcowe.md"),
    ("05", "ROZDZIAL-4_Sojusznicy-zdrowych-kosci.md"),
    ("06", "ROZDZIAL-5_Mikrobiota-jelitowa.md"),
    ("07", "ROZDZIAL-6_Co-przeszkadza-kosciom.md"),
    ("08", "ROZDZIAL-7_Mapa-drogowa-dieta.md"),
    ("09", "ROZDZIAL-8_Suplementacja-4_1.md"),
    ("10", "ROZDZIAL-9_Ruch.md"),
    ("11", "ROZDZIAL-10_Sen-slonce-stres.md"),
    ("12", "ZAKONCZENIE_Co-teraz.md"),
]
GDOCS = {"09"}
BOOK_KEY = build_book_key(TYTUL, PROJECT)

RE_OBRAZ = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def proza(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    t = RE_OBRAZ.sub(" ", t)
    t = re.sub(r"!\[[^\]]*\]\[[^\]]+\]", " ", t)   # forma referencyjna ![][image1] (Google Docs)
    t = re.sub(r"^\[[^\]]+\]:\s*<?[^\n]*>?$", " ", t, flags=re.M)
    t = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>~=])", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"^[ \t]*#{1,6}[ \t]*", " ", t, flags=re.M)
    t = re.sub(r"^[ \t]*([-*+]|\d+\.)[ \t]+", " ", t, flags=re.M)
    t = t.replace("**", "").replace("__", "").replace("`", "")
    t = re.sub(r"(?<!\w)[*_](?!\s)", "", t)
    t = re.sub(r"(?<!\s)[*_](?!\w)", "", t)
    return re.sub(r"\s+", " ", t).strip()


WYNIK.mkdir(exist_ok=True)
raport = {"projekt_zrodlowy": PROJECT, "book_key": BOOK_KEY, "rozdzialy": []}
awarie = []

print(f"{'NN':<3} {'dokument':<40} {'HTML':>8} {'bloki':>6} {'round-trip':>11} {'proza':>6}  markup")
print("-" * 112)

for nn, dok in PARY:
    md_dostawy = (DOSTAWA_DIR / dok).read_text()
    stary = (WZORZEC / f"{nn}.html").read_text()
    w = md_to_html(md_dostawy, stary_html=stary,
                   podmien_obraz=OBRAZ_R8 if nn == "09" else None,
                   gdocs=nn in GDOCS)
    (WYNIK / f"{nn}-{dok[:-3]}.html").write_text(w.html)

    # sprawdzian odbiorczy: HTML -> md naszym eksporterem
    rt = chapter_to_markdown(w.html, BOOK_KEY, int(nn))
    md_rt = rt.md
    (WYNIK / f"{nn}-roundtrip.md").write_text(md_rt)

    bajt_ok = unicodedata.normalize("NFC", md_rt) == unicodedata.normalize("NFC", md_dostawy)
    # linia definicji obrazka referencyjnego ([image1]: <data:...>) to markup, nie proza —
    # count_blocks liczy ja jako akapit, wiec przy porownaniu blokow ja zdejmujemy
    md_dostawy_bloki = re.sub(r"^\[[^\]]+\]:\s*<?[^\n]*>?$\n?", "", md_dostawy, flags=re.M)
    bloki_ok = count_blocks(md_rt) == count_blocks(md_dostawy_bloki)
    proza_ok = proza(md_rt) == proza(md_dostawy)

    if not proza_ok:
        a, b = proza(md_dostawy).split(), proza(md_rt).split()
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal":
                awarie.append(f"{nn} {tag}: DOSTAWA[{' '.join(a[i1:i2])[:120]}] -> HTML[{' '.join(b[j1:j2])[:120]}]")
    if not bloki_ok:
        awarie.append(f"{nn} bloki: dostawa {count_blocks(md_dostawy_bloki)} != html {count_blocks(md_rt)}")

    markup = f"h_odtw={w.naglowki_odtworzone} h_przeb={len(w.naglowki_przebudowane)} a={len(w.linki_odtworzone)} img={len(w.obrazki)}"
    print(f"{nn:<3} {dok:<40} {len(w.html):>8} {'=' if bloki_ok else 'X':>6} "
          f"{('BAJT' if bajt_ok else ('proza' if proza_ok else 'X')):>11} {'=' if proza_ok else 'X':>6}  {markup}")

    raport["rozdzialy"].append({
        "nn": nn, "dokument": dok, "html_bajtow": len(w.html),
        "roundtrip_bajtowy": bajt_ok, "bloki_zgodne": bloki_ok, "proza_zgodna": proza_ok,
        "naglowki_odtworzone": w.naglowki_odtworzone,
        "naglowki_przebudowane": w.naglowki_przebudowane,
        "linki": w.linki_odtworzone, "obrazki": w.obrazki, "uwagi": w.utracone,
        "bloki": count_blocks(md_rt),
    })

(WYNIK / "RAPORT-dry-run.json").write_text(json.dumps(raport, ensure_ascii=False, indent=1))

print()
ok_bajt = sum(1 for r in raport["rozdzialy"] if r["roundtrip_bajtowy"])
ok_proza = sum(1 for r in raport["rozdzialy"] if r["proza_zgodna"])
print(f"round-trip bajtowy: {ok_bajt}/12    proza zgodna: {ok_proza}/12")
img_total = sum(len(r["obrazki"]) for r in raport["rozdzialy"])
data_uri = [u for r in raport["rozdzialy"] for u in r["obrazki"] if u.startswith("data:")]
print(f"obrazkow: {img_total} (oczekiwane 11)   data: pozostalych: {len(data_uri)} (musi byc 0)")
if awarie:
    print(f"\nAWARIE ({len(awarie)}):")
    for a in awarie[:25]:
        print("  " + a)
else:
    print("\nbrak awarii")
