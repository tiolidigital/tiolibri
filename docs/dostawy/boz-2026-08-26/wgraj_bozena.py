#!/usr/bin/env python3
"""Wgranie ksiazki Bozeny PO REDAKCJI do projektu `Grzyby lecznicze` (fe9cba47).

Bez argumentu: PODGLAD (nic nie pisze do bazy).
Z `--wykonaj`: podmienia rozdzialy w istniejacym projekcie, potem czyta z powrotem
i weryfikuje co do znaku.

Zrodlo: FABRYKA-redaktor/redaktor/bozena-biezaca/ + DOSTAWA-bozena-2026-08-26.json
(29 plikow: 24 rozdzialy + strony redakcyjne + nota + 2 przekladki czesci + bibliografia).

Bramka fail-closed PRZED jakimkolwiek zapisem:
  1. iteracja po `kolejnosc` z DOSTAWY (NIE po ls), 29 pozycji
  2. sha256 i rozmiar kazdego pliku == wpis w dostawie
  3. dokladnie jeden <h1> na plik, po konwersji <h1> jest w HTML i da sie z niego
     wyciagnac tytul (`extract_first_heading`)
  4. proza md == proza HTML (NFC, zwiniete biale znaki, zdjety markup) 29/29
  5. zero `data:` i zero resztek markdownu w HTML
  6. projekt docelowy istnieje i ma tytul „Grzyby lecznicze"

Rollback: rozdzialy sprzed podmiany ida do `backup-rozdzialy-przed.json`; gdy insert
albo weryfikacja padnie, stan zostaje odtworzony z tego pliku.
"""
import hashlib
import json
import pathlib
import re
import sys
import unicodedata
import urllib.error
import urllib.request

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
sys.path.insert(0, str(REPO / "tiolibri-api"))
sys.path.insert(0, str(REPO / "docs/dostawy/_import-ewa"))
from app.services.epub_generator import extract_first_heading  # noqa: E402
from md2html import md_to_html  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

SCRATCH = pathlib.Path(__file__).parent
RED = pathlib.Path("/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/redaktor")
PACZKA = RED / "bozena-biezaca"
DOSTAWA = RED / "DOSTAWA-bozena-2026-08-26.json"
PROJEKT = "fe9cba47-9760-4a40-8030-d5bc5e70b512"
TYTUL_PROJEKTU = "Grzyby lecznicze"
BACKUP = SCRATCH / "backup-rozdzialy-przed.json"

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


# --- kursywa przez lamanie linii ------------------------------------------
def _pojedyncze(linia: str) -> int:
    """Ile w linii markerow kursywy `*` (gwiazdki z `**` sie nie licza)."""
    return sum(1 for i, c in enumerate(linia)
               if c == "*" and (i == 0 or linia[i - 1] != "*") and (i == len(linia) - 1 or linia[i + 1] != "*"))


def domknij_kursywe(md: str, licznik: list) -> str:
    """`*Katedra …\nUniwersytet …*` (kursywa przez lamanie linii) -> kursywa domknieta
    w kazdej linii z osobna. md2html._inline odrzuca `*…*` z `\n` w srodku, wiec bez
    tego w HTML zostaje gola gwiazdka. Renderuje sie tak samo, proza bez zmian."""
    bloki = md.split("\n\n")
    out_bloki = []
    for blok in bloki:
        linie, otwarta = [], False
        for linia in blok.split("\n"):
            if otwarta:
                linia = "*" + linia
                licznik.append(linia[:40])
            if _pojedyncze(linia) % 2:
                linia = linia + "*"
                otwarta = True
                if len(licznik) == 0 or licznik[-1] != linia[:40]:
                    licznik.append(linia[:40])
            else:
                otwarta = False
            linie.append(linia)
        out_bloki.append("\n".join(linie))
    return "\n\n".join(out_bloki)


# --- proza ------------------------------------------------------------------
RE_MD_MARKUP = re.compile(r"[#*_`>]|^\s*[-+]\s+", re.M)


def proza_md(t: str) -> str:
    """Markup na SPACJE, nie na pustke — `get_text(" ")` po stronie HTML tez wstawia
    spacje na granicy <em>/<strong>, wiec obie strony musza rozdzielac tak samo."""
    t = unicodedata.normalize("NFC", t)
    t = re.sub(r"^\s*(#{1,6}\s+|[-*+]\s+|\d+[.)]\s+)", " ", t, flags=re.M)
    t = t.replace("*", " ")
    return re.sub(r"\s+", " ", t).strip()


def proza_html(h: str) -> str:
    t = BeautifulSoup(h, "lxml").get_text(" ")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t)).strip()


# --- 1-5. bramka na materiale ----------------------------------------------
dostawa = json.loads(DOSTAWA.read_text())
kolejnosc = dostawa["kolejnosc"]
wpisy = {w["dokument"]: w for w in dostawa["pliki"]}
bledy = []
material = []
kursywa_lamana = []

if len(kolejnosc) != 29 or len(wpisy) != 29:
    bledy.append(f"dostawa: kolejnosc={len(kolejnosc)}, pliki={len(wpisy)} (oczekiwane 29/29)")
if [w["dokument"] for w in dostawa["pliki"]] != kolejnosc:
    bledy.append("dostawa: tablica `pliki` w innym porzadku niz `kolejnosc`")

for i, dok in enumerate(kolejnosc, 1):
    p = PACZKA / dok
    w = wpisy.get(dok)
    if w is None:
        bledy.append(f"{dok}: brak wpisu w dostawie")
        continue
    if not p.exists():
        bledy.append(f"{dok}: BRAK PLIKU")
        continue
    surowe = p.read_bytes()
    if len(surowe) != w["bajtow"]:
        bledy.append(f"{dok}: {len(surowe)} B != dostawa {w['bajtow']} B")
    sha = hashlib.sha256(surowe).hexdigest()
    if sha != w["sha256"]:
        bledy.append(f"{dok}: sha256 {sha[:12]}… != dostawa {w['sha256'][:12]}…")
    md = surowe.decode("utf-8")
    domkniete = []
    md_do_konwersji = domknij_kursywe(md, domkniete)
    if domkniete:
        kursywa_lamana.append((dok, len(domkniete)))
    if len(re.findall(r"^# ", md, re.M)) != 1:
        bledy.append(f"{dok}: liczba H1 != 1")
    wynik = md_to_html(md_do_konwersji)
    html = wynik.html
    tytul = extract_first_heading(html)
    if "<h1" not in html or not tytul:
        bledy.append(f"{dok}: brak <h1> / brak tytulu po konwersji")
    if "data:" in html:
        bledy.append(f"{dok}: `data:` w HTML")
    if "](" in html or "*" in html:
        bledy.append(f"{dok}: resztka markdownu w HTML")
    a, b = proza_md(md), proza_html(html)
    if a != b:
        i1 = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        bledy.append(f"{dok}: PROZA sie rozjezdza @{i1}: md…{a[max(0,i1-40):i1+40]!r} vs html…{b[max(0,i1-40):i1+40]!r}")
    material.append({"i": i, "dok": dok, "html": html, "tytul": tytul,
                     "rola": w["rola"], "numer": w["numer"], "tytul_dostawy": w["tytul"]})

# --- 6. projekt docelowy ----------------------------------------------------
proj = rest("GET", f"projects?id=eq.{PROJEKT}&select=*")
if not proj:
    bledy.append("projekt docelowy nie istnieje")
    stare = []
else:
    if proj[0]["title"] != TYTUL_PROJEKTU:
        bledy.append(f"projekt ma tytul {proj[0]['title']!r}, oczekiwane {TYTUL_PROJEKTU!r}")
    stare = rest("GET", f"chapters?project_id=eq.{PROJEKT}&select=*&order=sort_order.asc")

print("=== BRAMKA ===")
if bledy:
    print("FAIL:")
    for b in bledy:
        print("  " + b)
    sys.exit(1)
print(f"OK — 29/29 plikow zgodnych z {DOSTAWA.name} (sha256 + bajty), po jednym H1,")
print("     proza md == proza HTML 29/29, `data:` 0, resztek markdownu 0")
if kursywa_lamana:
    print("     kursywa lamana przez koniec linii, domknieta per linia: "
          + ", ".join(f"{d} ({n})" for d, n in kursywa_lamana))
print()

# --- plan -------------------------------------------------------------------
wiersze = [{"project_id": PROJEKT, "title": m["tytul"], "sort_order": m["i"],
            "processed_html": m["html"], "status": "draft"} for m in material]

print("=== PLAN ===")
print(f"projekt : {TYTUL_PROJEKTU}  ({PROJEKT})")
print(f"  w bazie teraz: {len(stare)} rozdzialow  ->  po podmianie: {len(wiersze)}")
print()
print(f"{'so':>3} {'rola':<10} {'nr':>3}  {'plik':<30} {'znakow':>7}  tytul (H1 z tresci)")
print("-" * 122)
for m in material:
    print(f"{m['i']:>3} {m['rola']:<10} {str(m['numer'] or '—'):>3}  {m['dok']:<30} {len(m['html']):>7}  {m['tytul'][:52]}")
print(f"\nrazem znakow HTML: {sum(len(m['html']) for m in material)}")
print()

if not WYKONAJ:
    print("PODGLAD — nic nie zapisano. Zeby wgrac: python3 wgraj_bozena.py --wykonaj")
    sys.exit(0)

# --- zapis ------------------------------------------------------------------
BACKUP.write_text(json.dumps(stare, ensure_ascii=False, indent=1))
print(f"=== ZAPIS ===\nbackup {len(stare)} rozdzialow -> {BACKUP.name}")


def rollback(powod):
    print(f"\nROLLBACK ({powod}) — odtwarzam stan sprzed podmiany")
    try:
        rest("DELETE", f"chapters?project_id=eq.{PROJEKT}")
        wroc = [{k: v for k, v in ch.items() if k not in ("created_at", "updated_at")} for ch in stare]
        if wroc:
            rest("POST", "chapters", wroc, prefer="return=minimal")
        print(f"rollback OK — w projekcie znowu {len(wroc)} rozdzialow")
    except Exception as exc:  # noqa: BLE001
        print(f"ROLLBACK NIE PRZESZEDL: {exc} — stan do odtworzenia z {BACKUP}")
    sys.exit(1)


rest("DELETE", f"chapters?project_id=eq.{PROJEKT}")
print(f"stare rozdzialy skasowane: {len(stare)}")
try:
    rest("POST", "chapters", wiersze, prefer="return=minimal")
except urllib.error.HTTPError as exc:
    print(f"insert padl: HTTP {exc.code} {exc.read().decode()[:400]}")
    rollback("insert rozdzialow")
except Exception as exc:  # noqa: BLE001
    print(f"insert padl: {exc}")
    rollback("insert rozdzialow")
print(f"rozdzialy wstawione: {len(wiersze)}")

# --- weryfikacja odczytem ---------------------------------------------------
print("\n=== WERYFIKACJA (odczyt z bazy) ===")
wczytane = rest("GET", f"chapters?project_id=eq.{PROJEKT}&deleted_at=is.null"
                       "&select=id,title,sort_order,processed_html&order=sort_order.asc")
zle = []
if len(wczytane) != len(material):
    zle.append(f"rozdzialow w bazie: {len(wczytane)} != {len(material)}")
for ch, m in zip(wczytane, material):
    if ch["sort_order"] != m["i"]:
        zle.append(f"{m['i']}: sort_order {ch['sort_order']}")
    if (ch.get("processed_html") or "") != m["html"]:
        zle.append(f"{m['i']}: processed_html rozni sie od {m['dok']}")
    if ch["title"] != m["tytul"]:
        zle.append(f"{m['i']}: tytul {ch['title']!r} != {m['tytul']!r}")
# test Redaktora: rozdzialy gatunkowe maja zaczynac sie nazwa gatunku, nie „Rodzina"
for dok in ("boz-08.md", "boz-12.md", "boz-15.md"):
    m = next(x for x in material if x["dok"] == dok)
    if m["tytul"].strip().lower().startswith("rodzina"):
        zle.append(f"{dok}: H1 zaczyna sie od „Rodzina” — to tekst SPRZED redakcji")
if zle:
    for z in zle:
        print("  " + z)
    rollback("weryfikacja odczytem")

for ch in wczytane:
    print(f"{ch['sort_order']:>3}  {len(ch['processed_html']):>7} znakow  {ch['title'][:64]}")
print(f"\nOK — {len(wczytane)}/{len(material)} rozdzialow w bazie, processed_html CO DO ZNAKU zgodny z paczka")
print("     boz-08/12/15 otwiera nazwa gatunku, nie „Rodzina” — przyszedl tekst PO redakcji")
