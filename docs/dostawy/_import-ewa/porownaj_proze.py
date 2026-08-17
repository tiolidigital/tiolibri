#!/usr/bin/env python3
"""Porownanie prozy: nasz swiezy eksport z produkcji  <->  input.md Redaktora.

Metoda ustalona z Fabryka (HANDOFF 2026-08-15):
  - zdjac markup obrazka (![...](...)), bo R8 ma data:base64 a my URL do Storage
  - NFC + normalizacja bialych znakow
  - porownac SAMA PROZE; pelnego diff-a nie robimy (szum formatowania dwoch kanalow)

Dwa poziomy:
  A) tekst po zdjeciu obrazka + NFC + zwiniecie bialych znakow  (dokladny)
  B) sama proza: dodatkowo zdjete znaczniki markdown (#, *, _, `, >, linki)
Jesli B rozni sie -> word-level diff (difflib) z kontekstem, zeby ocenic czy to
rozjazd rewizji, czy szum kanalu.
"""
import json, pathlib, re, sys, unicodedata, difflib

SCRATCH = pathlib.Path(__file__).parent
EKSPORT = SCRATCH / "eksport" / "kosci-na-cale-zycie-4-0-d73dcc3b"
PRACA = pathlib.Path("/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/redaktor/praca")
DOSTAWA = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI/docs/dostawy/ewa-2026-08-15/DOSTAWA-ewa-2026-08-15.json")

# NN eksportu -> dokument dostawy (kolejnosc rozdzialow w projekcie)
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

RE_OBRAZ = re.compile(r"!\[[^\]]*\]\([^)]*\)")
RE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def poziom_a(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    t = RE_OBRAZ.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def poziom_b(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    t = RE_OBRAZ.sub(" ", t)
    t = RE_LINK.sub(r"\1", t)
    t = re.sub(r"^[ \t]*#{1,6}[ \t]*", " ", t, flags=re.M)   # naglowki
    t = re.sub(r"^[ \t]*>[ \t]?", " ", t, flags=re.M)        # cytaty
    t = re.sub(r"^[ \t]*([-*+]|\d+\.)[ \t]+", " ", t, flags=re.M)  # listy
    t = t.replace("**", "").replace("__", "")
    t = re.sub(r"(?<!\w)[*_](?!\s)", "", t)
    t = re.sub(r"(?<!\s)[*_](?!\w)", "", t)
    t = t.replace("`", "")
    return re.sub(r"\s+", " ", t).strip()


def znajdz_input(dokument: str, run_id: str) -> pathlib.Path:
    kat = dokument[:-3]  # bez .md
    p = PRACA / kat / run_id / "input.md"
    if p.exists():
        return p
    kandydaci = list(PRACA.glob(f"*/{run_id}/input.md"))
    if not kandydaci:
        raise SystemExit(f"BRAK input.md dla {dokument} ({run_id})")
    return kandydaci[0]


def rozne_fragmenty(a: str, b: str, limit=6):
    wa, wb = a.split(), b.split()
    sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        lewo = " ".join(wa[i1:i2])
        prawo = " ".join(wb[j1:j2])
        kontekst = " ".join(wa[max(0, i1 - 6):i1])
        out.append((tag, kontekst, lewo, prawo, i2 - i1, j2 - j1))
    return out[:limit], len(out), sm.ratio()


dostawa = json.loads(DOSTAWA.read_text())
run_by_doc = {p["dokument"]: p["run_id"] for p in dostawa["pliki"]}

pliki_eksportu = {p.name.split("-d73dcc3b-")[1][:2]: p for p in sorted(EKSPORT.glob("*.md"))}

print(f"{'NN':<3} {'dokument':<38} {'slow(nasz)':>10} {'slow(input)':>11} {'A':>3} {'B':>3}  uwagi")
print("-" * 100)

raport = []
for nn, dok in PARY:
    ep = pliki_eksportu[nn]
    ip = znajdz_input(dok, run_by_doc[dok])
    et, it = ep.read_text(), ip.read_text()
    a_ok = poziom_a(et) == poziom_a(it)
    ea, ia = poziom_b(et), poziom_b(it)
    b_ok = ea == ia
    slow_e, slow_i = len(ea.split()), len(ia.split())
    uwagi = ""
    szczegoly = []
    if not b_ok:
        frag, ile, ratio = rozne_fragmenty(ea, ia)
        uwagi = f"{ile} roznic slownych, podobienstwo {ratio:.4f}"
        szczegoly = frag
    print(f"{nn:<3} {dok:<38} {slow_e:>10} {slow_i:>11} {'=' if a_ok else 'X':>3} {'=' if b_ok else 'X':>3}  {uwagi}")
    raport.append((nn, dok, ip, a_ok, b_ok, slow_e, slow_i, uwagi, szczegoly))

print()
for nn, dok, ip, a_ok, b_ok, se, si, uwagi, szczegoly in raport:
    if b_ok:
        continue
    print("=" * 100)
    print(f"NN {nn}  {dok}")
    print(f"  input: {ip}")
    print(f"  {uwagi}")
    for tag, kontekst, lewo, prawo, nl, npr in szczegoly:
        print(f"  --- {tag}  (nasz {nl} sl. -> input {npr} sl.)")
        print(f"      kontekst: ...{kontekst[-160:]}")
        print(f"      NASZ  : {lewo[:400]}")
        print(f"      INPUT : {prawo[:400]}")
    print()
