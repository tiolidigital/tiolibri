#!/usr/bin/env python3
"""Grzyby lecznicze (Bozena), wersja 1.1: w kolofonie wiersz o projekcie okladki (Magda, blad, to wiersz z Kosci)
zastapiony wierszem "Zdjecie na okladce: Pawel Muszynski". imprint.version 1.0 -> 1.1. Decyzja Piotrka 29.09.
Backup stanu przed zmiana: backup-przed.json.
Cofniecie: python3 zmien_kolofon.py --cofnij"""
import json, pathlib, sys, urllib.request
REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
HERE = pathlib.Path(__file__).parent
env = {}
for l in (REPO / "tiolibri-api/.env").read_text().splitlines():
    l = l.strip()
    if l and not l.startswith("#") and "=" in l:
        k, v = l.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
SB, KEY = env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_KEY"]
PROJEKT = "fe9cba47-9760-4a40-8030-d5bc5e70b512"
KOLOFON = "0ba90032-be95-43f0-98fd-bc7bddb14356"
STARY = "<p><strong>Projekt okładki:</strong> Magda Kapinos-Michalska</p>"
NOWY = "<p><strong>Zdjęcie na okładce:</strong> Paweł Muszyński</p>"
def call(url, body=None, method="GET"):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method)
    for k, v in {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}.items():
        r.add_header(k, v)
    return json.loads(urllib.request.urlopen(r, timeout=60).read())
BK = HERE / "backup-przed.json"
if "--cofnij" in sys.argv:
    przed = json.loads(BK.read_text())
    w = call(f"{SB}/rest/v1/projects?id=eq.{PROJEKT}", {"imprint": przed["imprint"]}, "PATCH"); assert len(w) == 1
    w = call(f"{SB}/rest/v1/chapters?id=eq.{KOLOFON}", {"processed_html": przed["kolofon"]}, "PATCH"); assert len(w) == 1
    print("przywrocono imprint i kolofon"); sys.exit()
imprint = call(f"{SB}/rest/v1/projects?id=eq.{PROJEKT}&select=imprint")[0]["imprint"]
kolofon = call(f"{SB}/rest/v1/chapters?id=eq.{KOLOFON}&select=processed_html")[0]["processed_html"]
if not BK.exists():
    BK.write_text(json.dumps({"imprint": imprint, "kolofon": kolofon}, ensure_ascii=False, indent=1))
assert kolofon.count(STARY) == 1 and imprint["version"] == "1.0"
w = call(f"{SB}/rest/v1/projects?id=eq.{PROJEKT}", {"imprint": {**imprint, "version": "1.1"}}, "PATCH"); assert len(w) == 1
w2 = call(f"{SB}/rest/v1/chapters?id=eq.{KOLOFON}", {"processed_html": kolofon.replace(STARY, NOWY)}, "PATCH"); assert len(w2) == 1
print(json.dumps(w[0]["imprint"], ensure_ascii=False))
print(w2[0]["processed_html"].replace("</p>", "</p>\n"))
