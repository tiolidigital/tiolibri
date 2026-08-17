#!/usr/bin/env python3
"""Wgranie poprawionej ksiazki Ewy do NOWEGO projektu w bazie.

Bez argumentu: PODGLAD (nic nie pisze do bazy).
Z `--wykonaj`: tworzy projekt + 12 rozdzialow, potem czyta z powrotem i weryfikuje.

Bramka fail-closed PRZED jakimkolwiek zapisem:
  1. iteracja po dry-run/RAPORT-dry-run.json["rozdzialy"] (NIE po ls)
  2. dlugosc kazdego HTML == html_bajtow z raportu
  3. proza_zgodna == True dla 12/12
  4. zero `data:` w HTML, kazdy plik ma <h1>
  5. stary projekt istnieje i ma 12 rozdzialow (zrodlo pol projektu)

Rollback: gdy insert rozdzialow albo weryfikacja padnie, nowy projekt i jego
rozdzialy sa kasowane, zeby nie zostawic polowicznej ksiazki.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
sys.path.insert(0, str(REPO / "tiolibri-api"))
from app.services.epub_generator import extract_first_heading  # noqa: E402

SCRATCH = pathlib.Path(__file__).parent
DRY = SCRATCH / "dry-run"
STARY = "d73dcc3b-74ed-4d23-8cbb-d600c8f5306f"
NOWY_TYTUL = "Kości Na Całe Życie 4.0 — po redakcji (2026-08-15)"

WYKONAJ = "--wykonaj" in sys.argv


# --- polaczenie -------------------------------------------------------------
env = {}
for line in (REPO / "tiolibri-api/.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
SB = env["SUPABASE_URL"].rstrip("/")
KEY = env["SUPABASE_SERVICE_KEY"]
H = {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json"}


def rest(method, path, body=None, prefer=None):
    headers = dict(H)
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(f"{SB}/rest/v1/{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


# --- 1-4. bramka na materiale ----------------------------------------------
raport = json.loads((DRY / "RAPORT-dry-run.json").read_text())
rozdzialy_raportu = raport["rozdzialy"]
bledy = []
material = []

for wpis in rozdzialy_raportu:
    nn, dok = wpis["nn"], wpis["dokument"]
    p = DRY / f"{nn}-{dok[:-3]}.html"
    if not p.exists():
        bledy.append(f"{nn}: BRAK PLIKU {p.name}")
        continue
    html = p.read_text()
    if len(html) != wpis["html_bajtow"]:
        bledy.append(f"{nn}: dlugosc {len(html)} != raport {wpis['html_bajtow']}")
    if not wpis.get("proza_zgodna"):
        bledy.append(f"{nn}: proza_zgodna == False")
    if "data:" in html:
        bledy.append(f"{nn}: zostal `data:` w HTML")
    tytul = extract_first_heading(html)
    if "<h1" not in html or not tytul:
        bledy.append(f"{nn}: brak <h1> / brak tytulu")
    material.append({"nn": nn, "dokument": dok, "html": html, "tytul": tytul, "plik": p.name})

if len(material) != 12:
    bledy.append(f"rozdzialow w raporcie: {len(material)} (oczekiwane 12)")

# --- 5. stary projekt jako zrodlo pol ---------------------------------------
stary = rest("GET", f"projects?id=eq.{STARY}&select=*")
if not stary:
    bledy.append("stary projekt nie istnieje")
    stary_row = {}
else:
    stary_row = stary[0]
    ile = rest("GET", f"chapters?project_id=eq.{STARY}&deleted_at=is.null&select=id")
    if len(ile) != 12:
        bledy.append(f"stary projekt ma {len(ile)} rozdzialow, nie 12")

print("=== BRAMKA ===")
if bledy:
    print("FAIL:")
    for b in bledy:
        print("  " + b)
    sys.exit(1)
print("OK — 12/12 plikow zgodnych z RAPORT-dry-run.json, proza 12/12, `data:` 0")
print()

# --- plan -------------------------------------------------------------------
nowy_id = str(uuid.uuid4())
projekt = {
    "id": nowy_id,
    "user_id": stary_row["user_id"],
    "title": NOWY_TYTUL,
    "author": stary_row.get("author"),
    "language": stary_row.get("language", "pl"),
    "status": "draft",
    "style_preset": stary_row.get("style_preset", "classic"),
    "typography_settings": stary_row.get("typography_settings"),
    "cover_image_url": stary_row.get("cover_image_url"),
}
wiersze = [
    {
        "project_id": nowy_id,
        "title": m["tytul"],
        "sort_order": i,
        "processed_html": m["html"],
        "status": "draft",
    }
    for i, m in enumerate(material, 1)
]

print("=== PLAN ===")
print(f"projekt : {NOWY_TYTUL}")
print(f"  autor : {projekt['author']}  ·  preset: {projekt['style_preset']}  ·  jezyk: {projekt['language']}")
print(f"  okladka: {(projekt['cover_image_url'] or '—')[:96]}")
print(f"  typografia: {'skopiowana ze starego' if projekt['typography_settings'] else 'BRAK'}")
print(f"  id      : {nowy_id}")
print()
print(f"{'so':>3}  {'plik':<44} {'znakow':>7}  tytul")
print("-" * 118)
for w, m in zip(wiersze, material):
    print(f"{w['sort_order']:>3}  {m['plik']:<44} {len(m['html']):>7}  {w['title'][:56]}")
print(f"\nrazem znakow HTML: {sum(len(m['html']) for m in material)}")
print()

if not WYKONAJ:
    print("PODGLAD — nic nie zapisano. Zeby wgrac: python3 wgraj.py --wykonaj")
    sys.exit(0)


# --- zapis ------------------------------------------------------------------
def rollback(powod):
    print(f"\nROLLBACK ({powod}) — kasuje nowy projekt {nowy_id}")
    try:
        rest("DELETE", f"chapters?project_id=eq.{nowy_id}")
        rest("DELETE", f"projects?id=eq.{nowy_id}")
        print("rollback OK — baza w stanie sprzed uruchomienia")
    except Exception as exc:  # noqa: BLE001
        print(f"ROLLBACK NIE PRZESZEDL: {exc} — posprzatac recznie projekt {nowy_id}")
    sys.exit(1)


print("=== ZAPIS ===")
rest("POST", "projects", projekt, prefer="return=representation")
print(f"projekt utworzony: {nowy_id}")

try:
    rest("POST", "chapters", wiersze, prefer="return=minimal")
except urllib.error.HTTPError as exc:
    print(f"insert rozdzialow padl: HTTP {exc.code} {exc.read().decode()[:400]}")
    rollback("insert rozdzialow")
except Exception as exc:  # noqa: BLE001
    print(f"insert rozdzialow padl: {exc}")
    rollback("insert rozdzialow")
print("rozdzialy wstawione: 12")

# --- weryfikacja odczytem ---------------------------------------------------
print("\n=== WERYFIKACJA (odczyt z bazy) ===")
wczytane = rest(
    "GET",
    f"chapters?project_id=eq.{nowy_id}&deleted_at=is.null"
    "&select=id,title,sort_order,processed_html&order=sort_order.asc",
)
zle = []
if len(wczytane) != 12:
    zle.append(f"rozdzialow w bazie: {len(wczytane)} != 12")
for i, (ch, m) in enumerate(zip(wczytane, material), 1):
    if ch["sort_order"] != i:
        zle.append(f"{i}: sort_order {ch['sort_order']}")
    if (ch.get("processed_html") or "") != m["html"]:
        zle.append(f"{i}: processed_html rozni sie od {m['plik']}")
    if ch["title"] != m["tytul"]:
        zle.append(f"{i}: tytul '{ch['title']}' != '{m['tytul']}'")
if zle:
    for z in zle:
        print("  " + z)
    rollback("weryfikacja odczytem")

for ch in wczytane:
    print(f"{ch['sort_order']:>3}  {len(ch['processed_html']):>7} znakow  {ch['title'][:64]}")
print("\nOK — 12/12 rozdzialow w bazie, processed_html CO DO ZNAKU zgodny z dry-run")
print(f"PROJEKT: {nowy_id}")
print(f"URL: https://app.tiolibri.com/editor/{nowy_id}")
