#!/usr/bin/env python3
"""Nota „O autorce" i wersja 1.0 w projekcie Ewy `Kości na całe życie` (1f23458e).

Bez argumentu: PODGLAD (nic nie pisze do bazy).
Z `--wykonaj`:
  1. backup stanu (imprint + sort_order dotknietych rozdzialow) -> backup-przed.json
  2. „Literatura i zrodla naukowe" 14 -> 15, „Strona redakcyjna" 15 -> 16
  3. nowy rozdzial „O autorce" na sort_order 14 (po Zakonczeniu, przed Literatura —
     tak jak u Bozeny)
  4. imprint.version = "1.0"
  5. weryfikacja odczytem; gdy cos padnie, rollback z backupu

Tekst noty zatwierdzila Ewa 2026-09-15 (przez Piotrka), z jedna zmiana: bez stazu
na Uniwersytecie Jagiellonskim.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
HERE = pathlib.Path(__file__).parent
PROJEKT = "1f23458e-b63a-4b29-a912-cced19ce3e47"
TYTUL_PROJEKTU = "Kości na całe życie"
BACKUP = HERE / "backup-przed.json"
WERSJA = "1.0"
WYKONAJ = "--wykonaj" in sys.argv

NOTA_HTML = (
    "<h1>O autorce</h1>"
    "<p><strong>Prof. dr hab. n. med. Ewa Stachowska</strong> – dietetyczka, badaczka i nauczycielka "
    "akademicka. Kieruje Katedrą Żywienia Człowieka i Metabolomiki na Pomorskim Uniwersytecie "
    "Medycznym w Szczecinie i jest pełnomocniczką kierunku Dietetyka. Wpływem żywienia na zdrowie "
    "zajmuje się od blisko 30 lat.</p>"
    "<p>Naukowe szlify zdobywała na stażach w Polsce, na Uniwersytecie Warmińsko-Mazurskim "
    "w Olsztynie, oraz za granicą, na University of Strathclyde. Jest współautorką ponad 260 "
    "publikacji w międzynarodowych czasopismach naukowych z impact factorem, poświęconych głównie "
    "żywieniu. Wiele z nich dotyczy żywienia w chorobach jelit i wątroby oraz zaburzeń mikrobioty "
    "jelitowej. Wypromowała kilkunastu doktorów, otrzymała nagrodę Ministra Zdrowia I stopnia.</p>"
    "<p>Od początku przenosi wyniki badań do praktyki. Ma na koncie:</p>"
    "<ul>"
    "<li><p>patent na test z obszaru nutrigenetyki,</p></li>"
    "<li><p>licencję na wypiek batonu dla osób prowadzących siedzący tryb życia i zagrożonych "
    "otyłością – nagrodzonego brązowym medalem na Międzynarodowej Wystawie Własności "
    "Intelektualnej, Wynalazków i Innowacji IPITEX 2019 w Bangkoku,</p></li>"
    "<li><p>licencję na wypiek medycznego pieczywa, pomocnego w terapii osób z niealkoholowym "
    "stłuszczeniem wątroby (NAFLD).</p></li>"
    "</ul>"
    "<p>Jest redaktorką podręcznika „Żywienie w zaburzeniach mikrobioty jelitowej” (PZWL 2021) "
    "i współautorką podręczników „Dietetyka sportowa” (PZWL 2019), „Żywienie w chorobach serca” "
    "(PZWL 2022), „Probiotykoterapia w praktyce” (Edra 2026) i „Kardiodietetyka” (PZWL 2026).</p>"
    "<p>Wiedzę o żywieniu popularyzuje na Instagramie (@profesor.stachowska), na YouTube "
    "(Profesor Ewa Stachowska) i na stronie profesorstachowska.pl.</p>"
    "<p>Prywatnie miłośniczka kawy, dobrej książki i „ciężkiej” muzyki rockowej.</p>"
)

# Oczekiwany uklad PRZED zmiana: (sort_order, poczatek tytulu)
PRZED = {13: "Zakończenie", 14: "Literatura i źródła naukowe", 15: "Strona redakcyjna"}

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


def zywe_rozdzialy():
    return rest("GET", f"chapters?project_id=eq.{PROJEKT}&deleted_at=is.null"
                       "&select=id,title,sort_order,role,processed_html&order=sort_order.asc")


# --- bramka -----------------------------------------------------------------
bledy = []
proj = rest("GET", f"projects?id=eq.{PROJEKT}&select=id,title,imprint")
if not proj or proj[0]["title"] != TYTUL_PROJEKTU:
    print("FAIL: projekt nie istnieje albo ma inny tytul")
    sys.exit(1)
imprint = proj[0]["imprint"] or {}
rozdzialy = zywe_rozdzialy()
po_sort = {c["sort_order"]: c for c in rozdzialy}

if any("o autorce" in (c["title"] or "").lower() for c in rozdzialy):
    bledy.append("rozdzial „O autorce” juz istnieje")
if imprint.get("version"):
    bledy.append(f"imprint.version juz ustawione: {imprint['version']!r}")
if len(rozdzialy) != 15 or max(po_sort) != 15:
    bledy.append(f"oczekiwane 15 rozdzialow z sort_order 1..15, jest {len(rozdzialy)}")
for so, poczatek in PRZED.items():
    if so not in po_sort or not po_sort[so]["title"].startswith(poczatek):
        bledy.append(f"sort_order {so}: oczekiwany „{poczatek}…”, jest {po_sort.get(so, {}).get('title')!r}")
if po_sort.get(15, {}).get("role") != "colophon":
    bledy.append("sort_order 15 nie ma roli colophon")
if "—" in NOTA_HTML:
    bledy.append("myslnik em w tekscie noty")

print("=== BRAMKA ===")
if bledy:
    for b in bledy:
        print("FAIL: " + b)
    sys.exit(1)
print("OK — 15 rozdzialow, Zakonczenie/Literatura/Strona redakcyjna na 13/14/15, bez noty, bez wersji\n")

literatura, kolofon = po_sort[14], po_sort[15]
print("=== PLAN ===")
print(f"  14 -> 15  {literatura['title']}")
print(f"  15 -> 16  {kolofon['title']} (colophon)")
print(f"  nowy 14   O autorce ({len(NOTA_HTML)} znakow HTML)")
print(f"  imprint   {json.dumps(imprint, ensure_ascii=False)}  +  version={WERSJA!r}\n")

if not WYKONAJ:
    print("PODGLAD — nic nie zapisano. Zeby wgrac: python3 wgraj_o_autorce.py --wykonaj")
    sys.exit(0)

# --- zapis ------------------------------------------------------------------
BACKUP.write_text(json.dumps({
    "imprint": imprint,
    "sort_order": {literatura["id"]: 14, kolofon["id"]: 15},
}, ensure_ascii=False, indent=1))
print(f"=== ZAPIS ===\nbackup -> {BACKUP.name}")
nowy_id = None


def rollback(powod):
    print(f"\nROLLBACK ({powod})")
    try:
        if nowy_id:
            rest("DELETE", f"chapters?id=eq.{nowy_id}")
        rest("PATCH", f"chapters?id=eq.{literatura['id']}", {"sort_order": 14})
        rest("PATCH", f"chapters?id=eq.{kolofon['id']}", {"sort_order": 15})
        rest("PATCH", f"projects?id=eq.{PROJEKT}", {"imprint": imprint})
        print("rollback OK — stan sprzed zmiany")
    except Exception as exc:  # noqa: BLE001
        print(f"ROLLBACK NIE PRZESZEDL: {exc} — stan do odtworzenia z {BACKUP}")
    sys.exit(1)


try:
    # Kolejnosc: najpierw zwolnij miejsce od konca, potem wstaw.
    rest("PATCH", f"chapters?id=eq.{kolofon['id']}", {"sort_order": 16})
    rest("PATCH", f"chapters?id=eq.{literatura['id']}", {"sort_order": 15})
    wynik = rest("POST", "chapters", {
        "project_id": PROJEKT, "title": "O autorce", "sort_order": 14,
        "processed_html": NOTA_HTML, "status": "draft",
    }, prefer="return=representation")
    nowy_id = wynik[0]["id"]
    rest("PATCH", f"projects?id=eq.{PROJEKT}", {"imprint": {**imprint, "version": WERSJA}})
except urllib.error.HTTPError as exc:
    print(f"zapis padl: HTTP {exc.code} {exc.read().decode()[:400]}")
    rollback("zapis")
except Exception as exc:  # noqa: BLE001
    print(f"zapis padl: {exc}")
    rollback("zapis")

# --- weryfikacja odczytem ---------------------------------------------------
print("\n=== WERYFIKACJA (odczyt z bazy) ===")
po = zywe_rozdzialy()
imprint_po = rest("GET", f"projects?id=eq.{PROJEKT}&select=imprint")[0]["imprint"]
zle = []
if [c["sort_order"] for c in po] != list(range(1, 17)):
    zle.append(f"sort_order po zmianie: {[c['sort_order'] for c in po]}")
if po[13]["title"] != "O autorce" or po[13]["processed_html"] != NOTA_HTML:
    zle.append("pozycja 14 to nie nota albo HTML rozni sie od zapisanego")
if po[14]["id"] != literatura["id"] or po[15]["id"] != kolofon["id"] or po[15]["role"] != "colophon":
    zle.append("Literatura/Strona redakcyjna nie stoja na 15/16")
if imprint_po != {**imprint, "version": WERSJA}:
    zle.append(f"imprint po zmianie: {imprint_po}")
if zle:
    for z in zle:
        print("  " + z)
    rollback("weryfikacja odczytem")

for c in po[11:]:
    print(f"{c['sort_order']:>3}  {c['title'][:60]}")
print(f"imprint: {json.dumps(imprint_po, ensure_ascii=False)}")
print("\nOK — nota na 14, kolofon ostatni, imprint.version = 1.0; HTML noty co do znaku")
