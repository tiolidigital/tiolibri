#!/usr/bin/env python3
"""PDF „na komputer" (A4, mniejsze pismo) z tej samej tresci i imprintu co pliki v1.0-xpertlab na telefon.
NIC nie zapisuje do bazy ani do Storage. Kopia boz-2026-09-22/generuj_komputer.py z dwiema zmianami:
- podmieniamy tez A5_HEIGHT_PT (wysokosc pola na plansze), inaczej zdjecia sa przyciete do wysokosci A5,
- ustawienia spoza skladu (preset, spis tresci, tytuly pod grafika) ida z projektu, jak w GenerateBooks.jsx.

Uzycie: DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib venv/bin/python generuj_komputer.py bozena|ewa <wyjscie.pdf>
"""
import json, os, pathlib, sys, time, urllib.request

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
sys.path.insert(0, str(REPO / "tiolibri-api"))

ROZMIAR, A4_HEIGHT_PT = "A4 portrait", 841.89
FONT, LINE, MARG = 14, 1.45, 2.0  # px, interlinia, cm

env = {}
for line in (REPO / "tiolibri-api/.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
for k, v in env.items():
    os.environ.setdefault(k, v)
SB, KEY = env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_KEY"]
PROJEKT = {"ewa": "1f23458e-b63a-4b29-a912-cced19ce3e47", "bozena": "fe9cba47-9760-4a40-8030-d5bc5e70b512"}[sys.argv[1]]
wyjscie = sys.argv[2]


def get(url):
    req = urllib.request.Request(url)
    req.add_header("apikey", KEY); req.add_header("Authorization", f"Bearer {KEY}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


project = get(f"{SB}/rest/v1/projects?id=eq.{PROJEKT}&select=*")[0]
chapters = [c for c in get(f"{SB}/rest/v1/chapters?project_id=eq.{PROJEKT}&select=*&order=sort_order")
            if not c.get("deleted_at")]
t = project.get("typography_settings") or {}
print(f"projekt: {project['title']} | rozdzialow: {len(chapters)} | imprint: {json.dumps(project.get('imprint'), ensure_ascii=False)}")

import weasyprint
from app.services import pdf_generator

pdf_generator.A5_HEIGHT_PT = A4_HEIGHT_PT
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
pdf_generator.CSS, pdf_generator.HTML = CSS_z_podmiana, HTML_z_podmiana

t0 = time.time()
pdf_generator.generate_pdf(
    project=project, chapters=chapters, output_path=wyjscie,
    style_preset=project.get("style_preset") or "classic",
    text_align=t.get("textAlign", "left"), font_size=FONT, line_height=LINE,
    margin_top=MARG, margin_bottom=MARG, margin_left=MARG, margin_right=MARG,
    chapter_spacing=t.get("chapterSpacing", 2.0), cover_image_url=project.get("cover_image_url"),
    toc_enabled=t.get("tocEnabled", False), toc_depth=t.get("tocDepth", 2),
    hide_opener_title=t.get("hideOpenerTitle") is not False,
)
print("podmian rozmiaru:", licznik)
print(f"gotowe w {time.time()-t0:.0f} s -> {wyjscie}")
