#!/usr/bin/env python3
"""Wgrywa Grzyby 1.1 (zdjecie na okladce: Pawel Muszynski) do Storage XpertHuba (bucket ebooks, nowy podfolder
bozena-muszynska/v1.1, bez nadpisywania) i przepina file_path/epub_path/desktop_path w produktach Bozeny.
Kopia skryptu z 24.09 plus plik na komputer. Backup produktow: backup-produkty-xperthub-przed.json.
Uzycie: python3 wgraj_xperthub.py            (wgranie + weryfikacja, bez przepiecia)
        python3 wgraj_xperthub.py --przepnij (przepiecie produktow)
        python3 wgraj_xperthub.py --cofnij   (przywraca sciezki z backupu; pliki w Storage zostaja)"""
import hashlib, json, pathlib, sys, urllib.request, urllib.error, urllib.parse
HERE = pathlib.Path(__file__).parent
env = {}
for l in (pathlib.Path.home() / "Documents/SaaS_Factory2026/App_Factory/XpertHub/.env.local").read_text().splitlines():
    l = l.strip()
    if l and not l.startswith("#") and "=" in l:
        k, v = l.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
URL, KEY = env["NEXT_PUBLIC_SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_ROLE_KEY"]
SRC = pathlib.Path.home() / "Downloads/boz-2026-09-29-zdjecie-okladki"
STARY_PDF = "bozena-muszynska/v1.0-wydawca-xpertlab-2/grzyby-lecznicze-v1.0.pdf"
KATALOG, NAZWA = "bozena-muszynska/v1.1", "grzyby-lecznicze-v1.1"
PLIKI = {"file_path": (f"{NAZWA}.pdf", "application/pdf"), "epub_path": (f"{NAZWA}.epub", "application/epub+zip"),
         "desktop_path": (f"{NAZWA}-komputer.pdf", "application/pdf")}
H = {"Content-Type": "application/json", "Prefer": "return=representation"}

def call(url, data=None, method="GET", headers=None):
    r = urllib.request.Request(url, data=data, method=method)
    for k, v in {"apikey": KEY, "Authorization": f"Bearer {KEY}", **(headers or {})}.items():
        r.add_header(k, v)
    return urllib.request.urlopen(r, timeout=300).read()

def produkty(pdf):
    return json.loads(call(f"{URL}/rest/v1/products?file_path=eq.{urllib.parse.quote(pdf, safe='')}&select=id,slug,file_path,epub_path,desktop_path"))

BK = HERE / "backup-produkty-xperthub-przed.json"
if "--cofnij" in sys.argv:
    for p in json.loads(BK.read_text()):
        w = json.loads(call(f"{URL}/rest/v1/products?id=eq.{p['id']}", json.dumps({k: p[k] for k in PLIKI}).encode(), "PATCH", H))
        assert len(w) == 1; print("przywrocono", p["slug"], w[0]["file_path"])
    sys.exit()

if "--przepnij" in sys.argv:
    lista = produkty(STARY_PDF)
    if not BK.exists():
        BK.write_text(json.dumps(lista, ensure_ascii=False, indent=1))
    nowe = {k: f"{KATALOG}/{n}" for k, (n, _) in PLIKI.items()}
    for p in lista:
        w = json.loads(call(f"{URL}/rest/v1/products?id=eq.{p['id']}", json.dumps(nowe).encode(), "PATCH", H))
        assert len(w) == 1 and all(w[0][k] == v for k, v in nowe.items())
        print("przepieto", p["slug"], "->", nowe["file_path"])
    sys.exit()

for n, typ in PLIKI.values():
    b = (SRC / n).read_bytes(); assert len(b) <= 10_485_760, f"{n} za duzy"
    cel = f"{KATALOG}/{n}"
    try:
        call(f"{URL}/storage/v1/object/ebooks/{cel}", b, "POST", {"Content-Type": typ}); print("wgrano", cel, len(b), "B")
    except urllib.error.HTTPError as e:
        print("NIE wgrano", cel, e.code, e.read()[:200]); continue
    z = call(f"{URL}/storage/v1/object/ebooks/{cel}")
    print(f"   pobrane z powrotem: {len(z)} B {'ZGODNE' if hashlib.sha256(z).digest() == hashlib.sha256(b).digest() else 'NIEZGODNE'}")
