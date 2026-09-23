#!/usr/bin/env python3
"""Wlacza imprint.xpertlab = true w ksiazkach Ewy i Bozeny. Backup imprintu w backup-imprint-przed.json.
Cofniecie: python3 wlacz_xpertlab.py --cofnij"""
import json, pathlib, sys, urllib.request
REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
HERE = pathlib.Path(__file__).parent
env = {}
for l in (REPO / "tiolibri-api/.env").read_text().splitlines():
    l = l.strip()
    if l and not l.startswith("#") and "=" in l:
        k, v = l.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
SB, KEY = env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_KEY"]
PROJEKTY = ["1f23458e-b63a-4b29-a912-cced19ce3e47", "fe9cba47-9760-4a40-8030-d5bc5e70b512"]
def call(url, body=None, method="GET"):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method)
    for k, v in {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}.items():
        r.add_header(k, v)
    return json.loads(urllib.request.urlopen(r, timeout=60).read())
BK = HERE / "backup-imprint-przed.json"
if "--cofnij" in sys.argv:
    przed = json.loads(BK.read_text())
    for pid in PROJEKTY:
        w = call(f"{SB}/rest/v1/projects?id=eq.{pid}", {"imprint": przed[pid]}, "PATCH"); assert len(w) == 1
        print("przywrocono", pid, w[0]["imprint"])
    sys.exit()
przed = {pid: call(f"{SB}/rest/v1/projects?id=eq.{pid}&select=imprint")[0]["imprint"] for pid in PROJEKTY}
if not BK.exists():
    BK.write_text(json.dumps(przed, ensure_ascii=False, indent=1))
for pid in PROJEKTY:
    w = call(f"{SB}/rest/v1/projects?id=eq.{pid}", {"imprint": {**przed[pid], "xpertlab": True}}, "PATCH"); assert len(w) == 1
    print(pid, w[0]["title"], w[0]["imprint"])
