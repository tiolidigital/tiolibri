#!/usr/bin/env python3
"""Wgrywa Grzyby 1.0 z wydawca Wydawnictwo XpertLab do Storage XpertHuba (bucket ebooks, nowy podfolder
v1.0-wydawca-xpertlab, bez nadpisywania) i przepina file_path/epub_path w produktach Bozeny. Kopia skryptu z 23.09.
Klucze czytane z XpertHub/.env.local. Backup produktow: backup-produkty-xperthub-przed.json (stan sprzed 24.09).
Uzycie: python3 wgraj_xperthub.py            (wgranie + weryfikacja, bez przepiecia)
        python3 wgraj_xperthub.py --przepnij (przepiecie produktow)
        python3 wgraj_xperthub.py --cofnij   (przywraca sciezki z backupu tej rundy; pliki w Storage zostaja)"""
import hashlib, json, pathlib, sys, urllib.request, urllib.error
HERE = pathlib.Path(__file__).parent
env = {}
for l in (pathlib.Path.home() / "Documents/SaaS_Factory2026/App_Factory/XpertHub/.env.local").read_text().splitlines():
    l = l.strip()
    if l and not l.startswith("#") and "=" in l:
        k, v = l.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
URL, KEY = env["NEXT_PUBLIC_SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_ROLE_KEY"]
SRC = pathlib.Path.home() / "Downloads/xpertlab-wydawca-2026-09-24"
# Druga runda 24.09: bez wiersza "Wydawnictwo XpertLab" na stronie tytulowej (logo zostaje).
# Pierwsza runda: "bozena-muszynska/v1.0-xpertlab/..." -> v1.0-wydawca-xpertlab, backup-produkty-xperthub-przed.json.
RUNDA = "-2"
KSIAZKI = {  # stary file_path -> (nowy katalog, nazwa pliku)
    "bozena-muszynska/v1.0-wydawca-xpertlab/grzyby-lecznicze-v1.0.pdf": ("bozena-muszynska/v1.0-wydawca-xpertlab-2", "grzyby-lecznicze-v1.0"),
}
TYPY = {"pdf": "application/pdf", "epub": "application/epub+zip"}

def call(url, data=None, method="GET", headers=None):
    r = urllib.request.Request(url, data=data, method=method)
    for k, v in {"apikey": KEY, "Authorization": f"Bearer {KEY}", **(headers or {})}.items():
        r.add_header(k, v)
    return urllib.request.urlopen(r, timeout=300).read()

def produkty(stary_pdf):
    q = urllib.parse.quote(stary_pdf, safe="")
    return json.loads(call(f"{URL}/rest/v1/products?file_path=eq.{q}&select=id,slug,file_path,epub_path"))

import urllib.parse
BK = HERE / f"backup-produkty-xperthub-przed{RUNDA}.json"

if "--cofnij" in sys.argv:
    for p in json.loads(BK.read_text()):
        w = json.loads(call(f"{URL}/rest/v1/products?id=eq.{p['id']}", json.dumps({"file_path": p["file_path"], "epub_path": p["epub_path"]}).encode(),
                            "PATCH", {"Content-Type": "application/json", "Prefer": "return=representation"}))
        assert len(w) == 1; print("przywrocono", p["slug"], w[0]["file_path"])
    sys.exit()

if "--przepnij" in sys.argv:
    wszystkie = []
    for stary, (katalog, nazwa) in KSIAZKI.items():
        wszystkie += produkty(stary)
    if not BK.exists():
        BK.write_text(json.dumps(wszystkie, ensure_ascii=False, indent=1))
    for stary, (katalog, nazwa) in KSIAZKI.items():
        for p in produkty(stary):
            nowe = {"file_path": f"{katalog}/{nazwa}.pdf", "epub_path": f"{katalog}/{nazwa}.epub"}
            w = json.loads(call(f"{URL}/rest/v1/products?id=eq.{p['id']}", json.dumps(nowe).encode(), "PATCH",
                                {"Content-Type": "application/json", "Prefer": "return=representation"}))
            assert len(w) == 1 and w[0]["file_path"] == nowe["file_path"] and w[0]["epub_path"] == nowe["epub_path"]
            print("przepieto", p["slug"], "->", nowe["file_path"])
    sys.exit()

for stary, (katalog, nazwa) in KSIAZKI.items():
    for ext, typ in TYPY.items():
        plik = SRC / f"{nazwa}.{ext}"
        b = plik.read_bytes(); assert len(b) <= 10_485_760, f"{plik} za duzy"
        cel = f"{katalog}/{nazwa}.{ext}"
        try:
            call(f"{URL}/storage/v1/object/ebooks/{cel}", b, "POST", {"Content-Type": typ})
            print("wgrano", cel)
        except urllib.error.HTTPError as e:
            print("NIE wgrano", cel, e.code, e.read()[:200]); continue
        z = call(f"{URL}/storage/v1/object/ebooks/{cel}")
        ok = hashlib.sha256(z).hexdigest() == hashlib.sha256(b).hexdigest()
        print(f"   pobrane z powrotem: {len(z)} B, sha256 {hashlib.sha256(z).hexdigest()} {'ZGODNE' if ok else 'NIEZGODNE'}")
