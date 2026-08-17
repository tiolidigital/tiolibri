#!/usr/bin/env python3
"""Bramka fail-closed dostawy + inwentarz blokow + pobranie wzorca processed_html.

1. Iteruje po DOSTAWA-ewa-2026-08-15.json["pliki"] (NIE po ls, NIE po MANIFEST)
2. sha256 + rozmiar bajtowy kazdego pliku
3. count_blocks() z naszego eksportera na pliku dostawy i na naszym eksporcie
4. zrzuca processed_html z bazy do wzorzec-html/ (odczyt, service key)
"""
import hashlib, json, os, pathlib, re, sys, urllib.request, urllib.parse

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
sys.path.insert(0, str(REPO / "tiolibri-api"))
from app.services.md_exporter import count_blocks  # noqa: E402

SCRATCH = pathlib.Path(__file__).parent
DOSTAWA_DIR = REPO / "docs/dostawy/ewa-2026-08-15"
EKSPORT = SCRATCH / "eksport" / "kosci-na-cale-zycie-4-0-d73dcc3b"
PROJECT = "d73dcc3b-74ed-4d23-8cbb-d600c8f5306f"

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

# --- 1-2. bramka integralnosci --------------------------------------------
dostawa = json.loads((DOSTAWA_DIR / "DOSTAWA-ewa-2026-08-15.json").read_text())
wpisy = {p["dokument"]: p for p in dostawa["pliki"]}
assert dostawa["plikow"] == len(wpisy) == 12, "manifest dostawy nie ma 12 wpisow"

bledy = []
suma = 0
for dok, wpis in wpisy.items():
    p = DOSTAWA_DIR / dok
    if not p.exists():
        bledy.append(f"{dok}: BRAK PLIKU")
        continue
    raw = p.read_bytes()
    suma += len(raw)
    if len(raw) != wpis["bajtow"]:
        bledy.append(f"{dok}: bajtow {len(raw)} != {wpis['bajtow']}")
    got = hashlib.sha256(raw).hexdigest()
    if got != wpis["sha256"]:
        bledy.append(f"{dok}: sha256 {got[:16]}... != {wpis['sha256'][:16]}...")

print("=== BRAMKA DOSTAWY ===")
print(f"plikow: {len(wpisy)}  bajtow razem: {suma} (manifest: {dostawa['bajtow_razem']})")
if bledy or suma != dostawa["bajtow_razem"]:
    print("FAIL:")
    for b in bledy:
        print("  " + b)
    sys.exit(1)
print("OK — 12/12 sha256 i rozmiary zgodne, iteracja po manifescie dostawy")
print()

# --- 3. inwentarz blokow ---------------------------------------------------
pliki_eksportu = {p.name.split("-d73dcc3b-")[1][:2]: p for p in sorted(EKSPORT.glob("*.md"))}
KLUCZE = ["naglowek", "akapit", "lista", "blockquote", "kod", "tabela"]

print("=== INWENTARZ BLOKOW (count_blocks z md_exporter) ===")
print(f"{'NN':<3} {'dokument':<40} {'naszsz':>26}   {'dostawa':>26}  zgodne")
print("-" * 108)
inwentarz = {}
for nn, dok in PARY:
    md_nasz = pliki_eksportu[nn].read_text()
    md_dost = (DOSTAWA_DIR / dok).read_text()
    bn, bd = count_blocks(md_nasz), count_blocks(md_dost)
    inwentarz[nn] = {"dokument": dok, "nasz": bn, "dostawa": bd}
    fn = " ".join(f"{k[:3]}{bn[k]}" for k in KLUCZE)
    fd = " ".join(f"{k[:3]}{bd[k]}" for k in KLUCZE)
    print(f"{nn:<3} {dok:<40} {fn:>26}   {fd:>26}  {'=' if bn == bd else 'X'}")
(SCRATCH / "inwentarz-blokow.json").write_text(json.dumps(inwentarz, ensure_ascii=False, indent=1))
print()

# --- 4. wzorzec processed_html z bazy --------------------------------------
env = {}
for line in (REPO / "tiolibri-api/.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
SB = env["SUPABASE_URL"].rstrip("/")

q = urllib.parse.urlencode({
    "project_id": f"eq.{PROJECT}",
    "deleted_at": "is.null",
    "select": "id,title,sort_order,processed_html",
    "order": "sort_order.asc,id.asc",
})
req = urllib.request.Request(f"{SB}/rest/v1/chapters?{q}", headers={
    "apikey": env["SUPABASE_SERVICE_KEY"],
    "Authorization": "Bearer " + env["SUPABASE_SERVICE_KEY"],
})
with urllib.request.urlopen(req, timeout=120) as r:
    rozdzialy = json.loads(r.read())

out = SCRATCH / "wzorzec-html"
out.mkdir(exist_ok=True)
print("=== WZORZEC processed_html Z BAZY ===")
for i, ch in enumerate(rozdzialy, 1):
    html = ch.get("processed_html") or ""
    (out / f"{i:02d}.html").write_text(html)
    print(f"{i:02d}  {(ch['title'] or '')[:52]:<52} {len(html):>7} B  sort={ch['sort_order']}")
(SCRATCH / "rozdzialy-meta.json").write_text(json.dumps(
    [{k: ch[k] for k in ("id", "title", "sort_order")} for ch in rozdzialy],
    ensure_ascii=False, indent=1))
print(f"\nrozdzialow: {len(rozdzialy)}")
