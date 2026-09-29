#!/usr/bin/env python3
"""Probny sklad 'na komputer' ksiazki Bozeny. NIC nie zapisuje do bazy ani do Storage.

Rozmiar strony jest w pdf_generator.py zakodowany na sztywno (A5 portrait) w 6 miejscach,
wiec na czas proby podmieniamy go w zaladowanym module, bez dotykania pliku na dysku.
"""
import os, pathlib, re, sys, time

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
sys.path.insert(0, str(REPO / "tiolibri-api"))
os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")

env = {}
for line in (REPO / "tiolibri-api/.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
for k, v in env.items():
    os.environ.setdefault(k, v)

import json, urllib.request
SB, KEY = env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_KEY"]
PROJEKT = "fe9cba47-9760-4a40-8030-d5bc5e70b512"

def get(url):
    req = urllib.request.Request(url)
    req.add_header("apikey", KEY); req.add_header("Authorization", f"Bearer {KEY}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

project = get(f"{SB}/rest/v1/projects?id=eq.{PROJEKT}&select=*")[0]
chapters = [c for c in get(f"{SB}/rest/v1/chapters?project_id=eq.{PROJEKT}&select=*&order=sort_order")
            if not c.get("deleted_at")]
print(f"projekt: {project['title']} | rozdzialow: {len(chapters)}")

from app.services import pdf_generator

ROZMIAR, FONT, MARG = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
wyjscie = sys.argv[4]

# podmiana rozmiaru strony w kodzie funkcji: przepuszczamy CSS przez wlasny filtr
import weasyprint
_CSS, _HTML = weasyprint.CSS, weasyprint.HTML
licznik = {"css": 0, "html": 0}
def CSS_z_podmiana(*a, **kw):
    if "string" in kw and "A5 portrait" in kw["string"]:
        kw["string"] = kw["string"].replace("A5 portrait", ROZMIAR); licznik["css"] += 1
    return _CSS(*a, **kw)
def HTML_z_podmiana(*a, **kw):
    if "string" in kw and "A5 portrait" in kw["string"]:
        kw["string"] = kw["string"].replace("A5 portrait", ROZMIAR); licznik["html"] += 1
    return _HTML(*a, **kw)
weasyprint.CSS, weasyprint.HTML = CSS_z_podmiana, HTML_z_podmiana

t0 = time.time()
pdf_generator.generate_pdf(
    project=project, chapters=chapters, output_path=wyjscie,
    style_preset=project.get("style_preset") or "classic",
    text_align="left", font_size=FONT, line_height=1.45,
    margin_top=MARG, margin_bottom=MARG, margin_left=MARG, margin_right=MARG,
    chapter_spacing=2.0, cover_image_url=project.get("cover_image_url"),
    toc_enabled=True, toc_depth=2, hide_opener_title=False,
)
print("podmian rozmiaru:", licznik)
print(f"gotowe w {time.time()-t0:.0f} s -> {wyjscie}")
