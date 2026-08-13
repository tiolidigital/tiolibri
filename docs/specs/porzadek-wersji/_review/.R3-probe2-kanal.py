#!/usr/bin/env python3
"""SPIKE R3 czesc 2 — pomiar kanalu Management API /database/query.

Wszystkie zapytania sa albo czysto odczytowe, albo dotykaja wylacznie TEMP TABLE
i koncza sie ROLLBACK-iem. Nic nie zmienia danych produkcyjnych.
"""
import json
import os
import sys
import urllib.error
import urllib.request

REF = "klhnyagtobgtxnexdsls"
ENV = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")


def load_token():
    path = ("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/"
            "SaaS Factory/TIOLIBRI/tiolibri-api/.env")
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("SUPABASE_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("brak SUPABASE_ACCESS_TOKEN w .env")


TOKEN = load_token()


def query(sql, read_only=False):
    """Zwraca (http_status, payload). payload to lista wierszy albo dict bledu."""
    suffix = "/read-only" if read_only else ""
    url = f"https://api.supabase.com/v1/projects/{REF}/database/query{suffix}"
    req = urllib.request.Request(
        url,
        data=json.dumps({"query": sql}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            # bez tego Cloudflare odrzuca Python-urllib: HTTP 403 "error code: 1010"
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
            return exc.code, {"raw": body[:400]}


def show(label, status, payload, limit=3):
    print(f"\n### {label}")
    print(f"    HTTP {status}")
    if isinstance(payload, list):
        print(f"    wierszy: {len(payload)}")
        for row in payload[:limit]:
            print(f"      {row}")
    else:
        print(f"    {json.dumps(payload, ensure_ascii=False)[:400]}")


print("=" * 72)
print("Q0 — czy kanal w ogole odpowiada")
print("=" * 72)
st, pl = query("select current_user, current_database(), version();")
show("select current_user/version", st, pl)

print()
print("=" * 72)
print("Q1 — czy sesja/transakcja trwa MIEDZY wywolaniami")
print("=" * 72)
st1, p1 = query("select pg_backend_pid() as pid;")
st2, p2 = query("select pg_backend_pid() as pid;")
show("wywolanie 1: pg_backend_pid", st1, p1)
show("wywolanie 2: pg_backend_pid", st2, p2)
pid1 = p1[0]["pid"] if isinstance(p1, list) and p1 else None
pid2 = p2[0]["pid"] if isinstance(p2, list) and p2 else None
print(f"\n    PID rowne? {pid1 == pid2}  ({pid1} vs {pid2})")

# proba jawnego BEGIN rozciagnietego na dwa wywolania
st3, p3 = query("begin; create temp table _spike_probe(x int);")
show("wywolanie A: begin + create temp table", st3, p3)
st4, p4 = query("select count(*) as n from _spike_probe;")
show("wywolanie B: czy temp table zyje", st4, p4)

print()
print("=" * 72)
print("Q2 — czy JEDNO wywolanie uniesie caly protokol BEGIN..ROLLBACK")
print("=" * 72)
st, pl = query(
    "begin;"
    "create temp table _spike_fix(x int);"
    "insert into _spike_fix values (1),(2),(3);"
    "select count(*) as widziane_przed_rollback from _spike_fix;"
    "rollback;"
)
show("begin/create/insert/select/rollback w jednym wywolaniu", st, pl)

print()
print("=" * 72)
print("Q3 — czy widac pg_policies (R1/R4 z §6.1)")
print("=" * 72)
st, pl = query(
    "select schemaname, tablename, policyname, cmd "
    "from pg_policies where schemaname='public' order by tablename, policyname;"
)
show("pg_policies w schema public", st, pl, limit=8)

print()
print("=" * 72)
print("Q4 — endpoint read-only")
print("=" * 72)
st, pl = query("select count(*) as n from public.projects;", read_only=True)
show("read-only: count(*) z public.projects", st, pl)
st, pl = query("create temp table _spike_ro(x int);", read_only=True)
show("read-only: proba zapisu (ma odmowic)", st, pl)

print()
print("=" * 72)
print("Q5 — czy da sie czytac katalog systemowy potrzebny do §6.2")
print("=" * 72)
st, pl = query(
    "select p.proname, md5(pg_get_functiondef(p.oid)) as md5 "
    "from pg_proc p join pg_namespace n on n.oid=p.pronamespace "
    "where n.nspname='public' order by p.proname;"
)
show("md5(pg_get_functiondef) funkcji w public", st, pl, limit=10)

st, pl = query(
    "select tgname, tgrelid::regclass::text as tabela, tgenabled "
    "from pg_trigger where not tgisinternal order by tgname;"
)
show("triggery nie-wewnetrzne", st, pl, limit=10)
