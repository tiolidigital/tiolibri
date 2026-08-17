#!/usr/bin/env python3
"""R8 — izolacja realnej delty tresci od szumu kanalu Google Docs.

Szum, ktory zdejmujemy dodatkowo wobec porownaj_proze.py:
  - obrazek referencyjny  ![][image1]  + linia definicji  [image1]: <data:...>
  - backslash-escape'y Google Docs:  \-  \!  \.  \[  itd.
Po tym zostaje sama proza; co sie rozni, jest rozjazdem rewizji.
"""
import pathlib, re, sys, unicodedata, difflib

SCRATCH = pathlib.Path(__file__).parent
NASZ = next((SCRATCH / "eksport" / "kosci-na-cale-zycie-4-0-d73dcc3b").glob("*-09-*.md"))
INPUT = pathlib.Path("/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/redaktor/praca/ROZDZIAL-8_Suplementacja-4_1/2026-08-11-4e0e64/input.md")

RE_OBRAZ_INLINE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
RE_OBRAZ_REF = re.compile(r"!\[[^\]]*\]\[[^\]]*\]")
RE_DEF_REF = re.compile(r"^\[[^\]]+\]:\s*<?[^\n]*>?$", re.M)
RE_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
RE_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~])")


def proza(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    t = RE_DEF_REF.sub(" ", t)
    t = RE_OBRAZ_INLINE.sub(" ", t)
    t = RE_OBRAZ_REF.sub(" ", t)
    t = RE_LINK.sub(r"\1", t)
    t = RE_ESCAPE.sub(r"\1", t)
    t = re.sub(r"^[ \t]*#{1,6}[ \t]*", " ", t, flags=re.M)
    t = re.sub(r"^[ \t]*>[ \t]?", " ", t, flags=re.M)
    t = re.sub(r"^[ \t]*([-*+]|\d+\.)[ \t]+", " ", t, flags=re.M)
    t = t.replace("**", "").replace("__", "")
    t = re.sub(r"(?<!\w)[*_](?!\s)", "", t)
    t = re.sub(r"(?<!\s)[*_](?!\w)", "", t)
    t = t.replace("`", "")
    return re.sub(r"\s+", " ", t).strip()


a, b = proza(NASZ.read_text()), proza(INPUT.read_text())
wa, wb = a.split(), b.split()
print(f"nasz eksport : {len(wa)} slow")
print(f"input.md     : {len(wb)} slow")
print(f"delta        : {len(wb) - len(wa):+d} slow")
sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
print(f"podobienstwo : {sm.ratio():.6f}")
print()

roznice = [op for op in sm.get_opcodes() if op[0] != "equal"]
print(f"blokow roznic: {len(roznice)}")
print("=" * 100)
for tag, i1, i2, j1, j2 in roznice:
    lewo = " ".join(wa[i1:i2])
    prawo = " ".join(wb[j1:j2])
    kontekst = " ".join(wa[max(0, i1 - 8):i1])
    print(f"[{tag}] nasz {i2-i1} sl. -> input {j2-j1} sl.")
    print(f"  kontekst: ...{kontekst}")
    print(f"  NASZ  : {lewo if lewo else '(brak)'}")
    print(f"  INPUT : {prawo if prawo else '(brak)'}")
    print("-" * 100)

print()
print("BMJ / DOI w obu wersjach:")
for nazwa, t in (("nasz", a), ("input", b)):
    print(f"  {nazwa:<6} BMJ x{t.count('BMJ')}  DOI x{t.count('DOI')}  '10.1136' x{t.count('10.1136')}")
