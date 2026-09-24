#!/usr/bin/env python3
"""Pliki 1.0 Grzybow z wydawca Wydawnictwo XpertLab na produkcji (api.tiolibri.com). Kopia generuj.py z 23.09.

Payload jak z przycisku „Generate E-Book" (GenerateBooks.jsx): typografia z
projects.typography_settings na DEFAULT_SETTINGS z useTypography.js, okladka
z projects.cover_image_url (GET /projects/{id} jej nie zwraca), preset z projektu.
Pliki laduja w ~/Downloads pod nazwa z aplikacji: <tytul>-v<wersja>.pdf/.epub.

Uzycie: python3 generuj.py bozena
"""
import hashlib
import json
import pathlib
import re
import subprocess
import unicodedata
import sys
import urllib.request

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
API = "https://api.tiolibri.com"
PROJEKT = {"ewa": "1f23458e-b63a-4b29-a912-cced19ce3e47", "bozena": "fe9cba47-9760-4a40-8030-d5bc5e70b512"}[sys.argv[1]]
OWNER = "a4aee672-c223-480e-9a0c-b12c1fc697a4"
OUT = pathlib.Path.home() / "Downloads" / "xpertlab-wydawca-2026-09-24"
OUT.mkdir(exist_ok=True)

# useTypography.js DEFAULT_SETTINGS
DEFAULTS = {"textAlign": "left", "fontSize": 16, "lineHeight": 1.7, "marginTop": 2, "marginBottom": 2,
            "marginLeft": 1.5, "marginRight": 1.5, "chapterSpacing": 2, "tocEnabled": False,
            "tocDepth": 2, "hideOpenerTitle": True}

env = {}
for line in (REPO / "tiolibri-api/.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
SB, SERVICE, ANON = env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_KEY"], env["SUPABASE_ANON_KEY"]


def call(url, body=None, headers=None, timeout=900):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def book_filename(title, ext, version):
    """Odpowiednik bookFilename() z tiolibri-frontend/src/lib/filename.js."""
    lat = {"ł": "l", "Ł": "L"}
    t = unicodedata.normalize("NFKD", "".join(lat.get(c, c) for c in unicodedata.normalize("NFC", title)))
    stem = re.sub(r"[^a-z0-9]+", "-", "".join(c for c in t if not unicodedata.combining(c)).lower()).strip("-")
    v = re.sub(r"[^a-z0-9.]+", "-", version.strip().lower()).strip("-.")
    return f"{stem}{'-v' + v if v else ''}.{ext}"


svc = {"apikey": SERVICE, "Authorization": f"Bearer {SERVICE}"}
proj = call(f"{SB}/rest/v1/projects?id=eq.{PROJEKT}&select=title,style_preset,typography_settings,cover_image_url,imprint",
            headers=svc)[0]
t = {**DEFAULTS, **(proj["typography_settings"] or {})}
payload = {
    "project_id": PROJEKT, "formats": ["epub", "pdf"], "style_preset": proj["style_preset"] or "classic",
    "text_align": t["textAlign"], "font_size": t["fontSize"], "line_height": t["lineHeight"],
    "margin_top": t["marginTop"], "margin_bottom": t["marginBottom"], "margin_left": t["marginLeft"],
    "margin_right": t["marginRight"], "chapter_spacing": t["chapterSpacing"],
    "cover_image_url": proj["cover_image_url"], "toc_enabled": t["tocEnabled"], "toc_depth": t["tocDepth"],
    "hide_opener_title": t.get("hideOpenerTitle") is not False,
}
print("payload:", json.dumps({k: v for k, v in payload.items() if k != "cover_image_url"}, ensure_ascii=False))
print("okladka:", bool(payload["cover_image_url"]), "| imprint:", json.dumps(proj["imprint"], ensure_ascii=False))

owner = call(f"{SB}/auth/v1/admin/users/{OWNER}", headers=svc)
link = call(f"{SB}/auth/v1/admin/generate_link", {"type": "magiclink", "email": owner["email"]}, svc)
token_hash = link.get("properties", {}).get("hashed_token") or link["hashed_token"]
jwt = call(f"{SB}/auth/v1/verify", {"type": "magiclink", "token_hash": token_hash}, {"apikey": ANON})["access_token"]

res = call(f"{API}/generate", payload, {"Authorization": f"Bearer {jwt}"})
print("response.version:", res.get("version"), "| stats:", res["stats"])

for fmt in ("pdf", "epub"):
    name = book_filename(proj["title"], fmt, res.get("version") or "")
    path = OUT / name
    urllib.request.urlretrieve(res["files"][fmt], path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"{fmt}: {path}  {path.stat().st_size} B  sha256 {sha}")
    print(f"     storage: {res['files'][fmt]}")

pdf = OUT / book_filename(proj["title"], "pdf", res.get("version") or "")
info = subprocess.run(["pdfinfo", "-custom", str(pdf)], capture_output=True, text=True).stdout
print("\n".join(l for l in info.splitlines() if l.split(":")[0].strip().lower() in {"title", "author", "isbn", "version", "pages", "page size"}))

# Sprawdzian: brak linijki o wspolpracy, brak "Wydawnictwo TIOLI", napis XpertLab dalej jest.
# "Tioli Piotr Michalski" (nazwa z rejestru) zostaje z decyzji Piotrka 24.09.
import re as _re
epub = OUT / book_filename(proj["title"], "epub", res.get("version") or "")
txt = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
meta = subprocess.run(["pdfinfo", "-meta", str(pdf)], capture_output=True, text=True).stdout + info
fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout
ep = subprocess.run(["unzip", "-p", str(epub)], capture_output=True).stdout.decode("utf-8", "replace")
opf = subprocess.run(["unzip", "-p", str(epub), "EPUB/content.opf"], capture_output=True, text=True).stdout
for nazwa, tekst in (("PDF tekst", txt), ("PDF metadane", meta), ("EPUB calosc", ep)):
    trafienia = sorted(set(m.group(0) for m in _re.finditer(r".{0,25}tioli.{0,25}", tekst, _re.I)))
    print(f"{nazwa}: 'We współpracy' {'We współpracy z XpertLab' in tekst} | 'Wydawnictwo XpertLab' {'Wydawnictwo XpertLab' in tekst} | tioli: {trafienia}")
print("PDF kroj Hanken:", "Hanken" in fonts, "| EPUB napis:", "xlab-logo" in ep)
print("EPUB dc:publisher:", _re.findall(r"<dc:publisher[^>]*>[^<]*</dc:publisher>", opf))
