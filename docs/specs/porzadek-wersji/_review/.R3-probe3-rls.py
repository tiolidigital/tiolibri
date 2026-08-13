#!/usr/bin/env python3
"""SPIKE R3 czesc 2b — czy asercje RLS da sie zrobic BEZ prawdziwych JWT-ow.

Wzorzec: w JEDNYM wywolaniu ustawic role `authenticated` i `request.jwt.claims`,
zmierzyc co widac, i zrobic ROLLBACK. Wszystko odczytowe + ROLLBACK.
"""
import json
import urllib.error
import urllib.request

REF = "klhnyagtobgtxnexdsls"
ENV = ("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/"
       "SaaS Factory/TIOLIBRI/tiolibri-api/.env")


def load_token():
    with open(ENV, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("SUPABASE_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("brak tokenu")


TOKEN = load_token()


def query(sql):
    req = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{REF}/database/query",
        data=json.dumps({"query": sql}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.7.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"raw": body[:300]}


def show(label, st, pl, limit=5):
    print(f"\n### {label}\n    HTTP {st}")
    if isinstance(pl, list):
        print(f"    wierszy: {len(pl)}")
        for r in pl[:limit]:
            print(f"      {r}")
    else:
        print(f"    {json.dumps(pl, ensure_ascii=False)[:300]}")


print("=" * 72)
print("A — kto jest wlascicielem ilu projektow (jako postgres, RLS omijane)")
print("=" * 72)
st, pl = query(
    "select user_id::text, count(*) as ile from public.projects "
    "group by user_id order by ile desc;"
)
show("rozklad projektow po user_id", st, pl)

owner = None
if isinstance(pl, list) and pl:
    owner = pl[0]["user_id"]
print(f"\n    wybrany user_id do proby: {owner}")

print()
print("=" * 72)
print("B — RLS pod rola `authenticated` z podstawionym request.jwt.claims")
print("=" * 72)

claims_ok = json.dumps({"sub": owner, "role": "authenticated"})
sql_ok = (
    "begin;"
    "set local role authenticated;"
    f"select set_config('request.jwt.claims', '{claims_ok}', true);"
    "select count(*) as widzi from public.projects;"
    "rollback;"
)
st, pl = query(sql_ok)
show("jako WLASCICIEL — ile projektow widzi", st, pl)

obcy = "00000000-0000-4000-8000-000000000000"
claims_obcy = json.dumps({"sub": obcy, "role": "authenticated"})
sql_obcy = (
    "begin;"
    "set local role authenticated;"
    f"select set_config('request.jwt.claims', '{claims_obcy}', true);"
    "select count(*) as widzi from public.projects;"
    "rollback;"
)
st, pl = query(sql_obcy)
show("jako OBCY (uuid z palca) — ile projektow widzi", st, pl)

print()
print("=" * 72)
print("C — czy anon widzi cokolwiek")
print("=" * 72)
st, pl = query(
    "begin;"
    "set local role anon;"
    "select count(*) as widzi from public.projects;"
    "rollback;"
)
show("jako anon", st, pl)

print()
print("=" * 72)
print("D — czy wynik ASERCJI da sie zwrocic jako PASS/FAIL jednym zapytaniem")
print("=" * 72)
st, pl = query(
    "begin;"
    "set local role authenticated;"
    f"select set_config('request.jwt.claims', '{claims_obcy}', true);"
    "select case when count(*) = 0 then 'PASS' else 'FAIL' end as wynik, "
    "count(*) as widziane from public.projects;"
    "rollback;"
)
show("asercja: obcy NIE widzi cudzych projektow", st, pl)
