#!/usr/bin/env python3
"""Grzyby lecznicze (Bozena): wydawca Wydawnictwo TIOLI -> Wydawnictwo XpertLab.
Zmienia imprint.publisher, imprint.rights_note i linijke "Wydawnictwo TIOLI" w kolofonie.
Nazwa firmy z rejestru ("Tioli Piotr Michalski") zostaje, decyzja Piotrka 24.09.
Backup stanu przed zmiana: backup-przed.json.
Cofniecie: python3 zmien_wydawce.py --cofnij"""
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
STARY, NOWY = "Wydawnictwo TIOLI", "Wydawnictwo XpertLab"
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
nowy_imprint = {**imprint, "publisher": imprint["publisher"].replace(STARY, NOWY),
                "rights_note": imprint["rights_note"].replace(STARY, NOWY)}
assert kolofon.count(f"<p>{STARY}</p>") <= 1
nowy_kolofon = kolofon.replace(f"<p>{STARY}</p>", f"<p>{NOWY}</p>")
w = call(f"{SB}/rest/v1/projects?id=eq.{PROJEKT}", {"imprint": nowy_imprint}, "PATCH"); assert len(w) == 1
w2 = call(f"{SB}/rest/v1/chapters?id=eq.{KOLOFON}", {"processed_html": nowy_kolofon}, "PATCH"); assert len(w2) == 1
print(json.dumps(w[0]["imprint"], ensure_ascii=False, indent=1))
print(w2[0]["processed_html"].replace("</p>", "</p>\n"))
