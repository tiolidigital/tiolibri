#!/usr/bin/env python3
"""Swiezy eksport 12 rozdzialow Ewy z produkcji -> ZIP w scratchpadzie."""
import json, os, sys, urllib.request, pathlib

ENV = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI/tiolibri-api/.env")
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
PROJECT = "d73dcc3b-74ed-4d23-8cbb-d600c8f5306f"
API = os.environ.get("TIOLIBRI_API", "https://api.tiolibri.com")
EMAIL = "kontakt@przestudio.pl"

env = {}
for line in ENV.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

SB = env["SUPABASE_URL"].rstrip("/")


def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), dict(r.headers)


# 1. magiclink -> hashed_token
raw, _ = post(f"{SB}/auth/v1/admin/generate_link",
              {"type": "magiclink", "email": EMAIL},
              {"apikey": env["SUPABASE_SERVICE_KEY"],
               "Authorization": "Bearer " + env["SUPABASE_SERVICE_KEY"]})
r = json.loads(raw)
hashed = r.get("properties", {}).get("hashed_token") or r["hashed_token"]

# 2. verify -> access_token
raw, _ = post(f"{SB}/auth/v1/verify",
              {"type": "magiclink", "token_hash": hashed},
              {"apikey": env["SUPABASE_ANON_KEY"]})
token = json.loads(raw)["access_token"]
print("JWT OK")

# 3. export-md
req = urllib.request.Request(f"{API}/projects/{PROJECT}/export-md", data=b"{}", method="POST",
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + token})
with urllib.request.urlopen(req, timeout=300) as resp:
    data = resp.read()
    print("HTTP", resp.status, resp.headers.get("Content-Disposition"))

zp = OUT / "eksport-prod.zip"
zp.write_bytes(data)
print("ZIP", zp, len(data), "B")
