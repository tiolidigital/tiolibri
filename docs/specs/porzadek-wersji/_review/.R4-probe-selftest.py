#!/usr/bin/env python3
"""Preflight L5 rundy R4 — SELF-TEST bramki S4 (kontrproba do faktu CORRECTED).

Pytanie: czy asercja z v0.5 ("brak wierszy w odpowiedzi = FAIL") odrzuca wklad,
przed ktorym miala bronic? Mierzone na ZYWYM kanale S, endpoint /read-only
(zero zapisow, zero transakcji — sam SELECT).

Dwa wklady, dwie reguly:
  wklad FAIL  : json_agg nad PUSTYM zbiorem   -> oczekiwanie: bramka ODRZUCA
  wklad PASS  : json_agg nad NIEPUSTYM zbiorem -> oczekiwanie: bramka PRZEPUSZCZA
  regula STARA (v0.5)  : PASS <=> len(rows) > 0
  regula NOWA  (v0.5.1): PASS <=> 'wynik' in row AND row['wynik'] is not None

EXIT=0 <=> zmierzona macierz zgadza sie z oczekiwaniem, czyli: stara regula
daje FALSE-PASS na wkladzie FAIL, a nowa go odrzuca.
"""
import json
import os
import sys
import urllib.error
import urllib.request

REF = "klhnyagtobgtxnexdsls"
ENV_PATH = ("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/"
            "SaaS Factory/TIOLIBRI/tiolibri-api/.env")

SQL_PUSTY = "select json_agg(t) as wynik from (select 1 as x where false) t;"
SQL_NIEPUSTY = "select json_agg(t) as wynik from (select 1 as x) t;"


def load_token():
    with open(ENV_PATH, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("SUPABASE_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("brak SUPABASE_ACCESS_TOKEN w .env")


TOKEN = load_token()


def query(sql):
    url = f"https://api.supabase.com/v1/projects/{REF}/database/query/read-only"
    req = urllib.request.Request(
        url,
        data=json.dumps({"query": sql}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.7.1",   # S1 — bez tego Cloudflare 403/1010
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, json.loads(resp.read().decode())


def regula_stara(rows):
    return len(rows) > 0


def regula_nowa(rows):
    if not rows:
        return False
    row = rows[0]
    return "wynik" in row and row["wynik"] is not None


OCZEKIWANIE = {
    # (wklad, regula) -> czy bramka ma powiedziec PASS
    ("FAIL", "stara"): True,    # <- to jest defekt: stara regula PRZEPUSZCZA zly wklad
    ("FAIL", "nowa"): False,
    ("PASS", "stara"): True,
    ("PASS", "nowa"): True,
}

bledy = 0
print("=" * 78)
for wklad, sql in (("FAIL", SQL_PUSTY), ("PASS", SQL_NIEPUSTY)):
    st, body = query(sql)
    rows = body if isinstance(body, list) else body.get("result", body)
    for nazwa, fn in (("stara", regula_stara), ("nowa", regula_nowa)):
        got = fn(rows)
        exp = OCZEKIWANIE[(wklad, nazwa)]
        ok = got == exp
        bledy += 0 if ok else 1
        print(
            f"WKLAD={wklad:4s} REGULA={nazwa:5s} HTTP={st} rows={len(rows)} "
            f"tresc={json.dumps(rows)} EXPECT={'PASS' if exp else 'FAIL'} "
            f"GOT={'PASS' if got else 'FAIL'} RESULT={'PASS' if ok else 'FAIL'}"
        )
print("=" * 78)
print(f"BLEDOW={bledy}")
print(f"EXIT={1 if bledy else 0}")
sys.exit(1 if bledy else 0)
