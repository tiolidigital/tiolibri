#!/usr/bin/env python3
"""Preflight L5 rundy R4 — pomiar KSZTALTOW, ktore wprowadzila v0.5.

Spike (R3) zmierzyl WLASCIWOSCI kanalu S1-S7. Nie zmierzyl KSZTALTOW, na ktorych
stoi przepisana §6:
  - blok DO ... EXCEPTION ... GET STACKED DIAGNOSTICS constraint_name (cale §6.1)
  - `select json_agg(_wynik) as wynik from _wynik` jako OSTATNIA instrukcja (S4)
  - zachowanie json_agg przy PUSTEJ tabeli (regula 3: "brak wierszy = FAIL")
  - oczekiwania R1/R4 z §6.1r wobec pg_policies (R1: DOKLADNIE 1 wiersz)
  - md5(pg_get_functiondef('public.prune_project_snapshots'::regproc)) (§6.2 krok 1)

Wszystko jest albo czysto odczytowe, albo w transakcji zakonczonej ROLLBACK-iem.
Zero trwalych zapisow. EXIT=0 <=> wszystkie kroki PASS.
"""
import json
import os
import sys
import urllib.error
import urllib.request

REF = "klhnyagtobgtxnexdsls"
RUN_ID = "R4PF" + os.urandom(4).hex()
ENV_PATH = ("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/"
            "SaaS Factory/TIOLIBRI/tiolibri-api/.env")

STEPS = []


def load_token():
    with open(ENV_PATH, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("SUPABASE_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("brak SUPABASE_ACCESS_TOKEN w .env")


TOKEN = load_token()


def query(sql, read_only=False, user_agent="curl/8.7.1"):
    suffix = "/read-only" if read_only else ""
    url = f"https://api.supabase.com/v1/projects/{REF}/database/query{suffix}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }
    if user_agent is not None:
        headers["User-Agent"] = user_agent
    req = urllib.request.Request(
        url, data=json.dumps({"query": sql}).encode("utf-8"),
        headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"raw": body[:300]}
    except Exception as exc:                      # transport = FAIL, nie "pominiete"
        return -1, {"transport_error": repr(exc)[:300]}


def step(sid, expect, got, ok):
    STEPS.append(ok)
    print(f"STEP={sid} EXPECT={expect} GOT={got} RESULT={'PASS' if ok else 'FAIL'}")


print(f"RUN_ID={RUN_ID}")
print("=" * 78)

# ---------------------------------------------------------------- S1 (kontrola)
st, pl = query("select 1 as x;", user_agent=None)
blob = json.dumps(pl, ensure_ascii=False)
step("P1-S1-brak-UA", "403 + '1010'", f"HTTP {st} {blob[:80]}",
     st == 403 and "1010" in blob)

st, pl = query("select current_user as u, version() as v;")
cu = pl[0]["u"] if isinstance(pl, list) and pl else None
step("P2-kanal-zyje", "200 + current_user=postgres", f"HTTP {st} user={cu}",
     st in (200, 201) and cu == "postgres")

# ---------------------------------- KSZTALT §6.1: DO + GET STACKED DIAGNOSTICS
# Deterministyczny dowod mechanizmu: NAZWANY CHECK na tabeli TEMP, naruszony
# wewnatrz bloku DO. Jesli constraint_name nie wraca — cale §6.1 jest nieegzekwowalne.
sql_shape = """
begin;
  create temp table _pf_t(v text constraint pf_named_check check (char_length(v) <= 3));
  create temp table _wynik(step text, expect text, got text);
  do $$
  declare s text; c text;
  begin
    begin
      insert into _pf_t(v) values ('xxxx');
      insert into _wynik values ('A', '23514/pf_named_check', 'BRAK ODRZUCENIA');
    exception when others then
      get stacked diagnostics s = returned_sqlstate, c = constraint_name;
      insert into _wynik values ('A', '23514/pf_named_check', s || '/' || coalesce(c, 'NULL'));
    end;
    begin
      insert into _pf_t(v) values ('ok');
      insert into _wynik values ('B', 'legalny zapis przechodzi', 'OK');
    exception when others then
      get stacked diagnostics s = returned_sqlstate;
      insert into _wynik values ('B', 'legalny zapis przechodzi', 'ODRZUCONY ' || s);
    end;
  end $$;
  select json_agg(_wynik) as wynik from _wynik;
rollback;
"""
st, pl = query(sql_shape)
wynik = None
if isinstance(pl, list) and pl and isinstance(pl[0], dict):
    wynik = pl[0].get("wynik")
step("P3-DO-diagnostics", "23514/pf_named_check w json_agg",
     f"HTTP {st} wynik={json.dumps(wynik, ensure_ascii=False)[:160]}",
     st in (200, 201) and isinstance(wynik, list)
     and any(r.get("got") == "23514/pf_named_check" for r in wynik)
     and any(r.get("step") == "B" and r.get("got") == "OK" for r in wynik))

# ------------------------------- S4 edge: json_agg nad PUSTA tabela = jeden NULL
st, pl = query("begin; create temp table _pf_e(x int);"
               " select json_agg(_pf_e) as wynik from _pf_e; rollback;")
empty_val = pl[0].get("wynik", "BRAK-KLUCZA") if isinstance(pl, list) and pl else "BRAK-WIERSZY"
step("P4-json_agg-pusty", "1 wiersz z wynik=None (nie 0 wierszy)",
     f"HTTP {st} rows={len(pl) if isinstance(pl, list) else 'n/a'} wynik={empty_val!r}",
     st in (200, 201) and isinstance(pl, list) and len(pl) == 1 and empty_val is None)

# ------------------------------------------------ §6.1r R1 — pg_policies projects
st, pl = query(
    "select policyname, cmd, permissive, roles::text as roles, qual, with_check "
    "from pg_policies where schemaname='public' and tablename='projects' "
    "and cmd='UPDATE';", read_only=True)
n_upd = len(pl) if isinstance(pl, list) else -1
detail = json.dumps(pl, ensure_ascii=False)[:300] if isinstance(pl, list) else str(pl)[:200]
step("P5-R1-projects-UPDATE", "dokladnie 1 polityka", f"HTTP {st} n={n_upd} :: {detail}",
     st in (200, 201) and n_upd == 1)

# ------------------------------------- §6.1r R4 — pg_policies project_snapshots
st, pl = query(
    "select policyname, cmd, with_check from pg_policies "
    "where schemaname='public' and tablename='project_snapshots' order by cmd;",
    read_only=True)
cmds = [r["cmd"] for r in pl] if isinstance(pl, list) else []
step("P6-R4-snapshots-polityki", "0 polityk cmd=UPDATE",
     f"HTTP {st} cmds={cmds} :: {json.dumps(pl, ensure_ascii=False)[:260]}",
     st in (200, 201) and "UPDATE" not in cmds)

# ------------------------------------------------------- §6.2 krok 1 — hash + trigger
st, pl = query(
    "select md5(pg_get_functiondef('public.prune_project_snapshots'::regproc)) as h, "
    "(select tgenabled from pg_trigger where tgname='trg_prune_project_snapshots') as tg;",
    read_only=True)
h = pl[0]["h"] if isinstance(pl, list) and pl else None
tg = pl[0]["tg"] if isinstance(pl, list) and pl else None
step("P7-hash-regproc", "32 znaki md5 + tgenabled='O'", f"HTTP {st} h={h} tg={tg}",
     st in (200, 201) and isinstance(h, str) and len(h) == 32 and tg == "O")

# ------------------------------------- S5 — read-only endpoint odmawia zapisu
st, pl = query("create temp table _pf_ro(x int);", read_only=True)
blob = json.dumps(pl, ensure_ascii=False)
step("P8-read-only-odmawia", "25006", f"HTTP {st} {blob[:120]}", "25006" in blob)

# ------------------------------------ S6 — podstawienie tozsamosci (§6.1r R2/R3)
st, pl = query("select user_id, count(*) as n from public.projects "
               "group by user_id order by n desc;", read_only=True)
owners = pl if isinstance(pl, list) else []
total = sum(r["n"] for r in owners) if owners else 0
step("P9-sklad-bazy", "12 projektow / 3 wlascicieli",
     f"HTTP {st} projektow={total} wlascicieli={len(owners)}",
     st in (200, 201) and total == 12 and len(owners) == 3)

if owners:
    own = owners[0]["user_id"]
    obcy = "00000000-0000-0000-0000-0000000000ff"
    sql_rls = f"""
begin;
  set local role authenticated;
  select set_config('request.jwt.claims',
                    '{{"sub":"{own}","role":"authenticated"}}', true);
  create temp table _pf_rls(kto text, n int);
  insert into _pf_rls select 'wlasciciel', count(*) from public.projects;
  select set_config('request.jwt.claims',
                    '{{"sub":"{obcy}","role":"authenticated"}}', true);
  insert into _pf_rls select 'obcy', count(*) from public.projects;
  select json_agg(_pf_rls) as wynik from _pf_rls;
rollback;
"""
    st, pl = query(sql_rls)
    w = pl[0].get("wynik") if isinstance(pl, list) and pl else None
    m = {r["kto"]: r["n"] for r in w} if isinstance(w, list) else {}
    step("P10-RLS-podstawienie", "wlasciciel>0 ∧ obcy=0",
         f"HTTP {st} {m}",
         st in (200, 201) and m.get("wlasciciel", 0) > 0 and m.get("obcy", -1) == 0)
else:
    step("P10-RLS-podstawienie", "wlasciciel>0 ∧ obcy=0", "brak wlascicieli", False)

# ------------------------------------------------------------------- postflight
st, pl = query(
    f"select (select count(*) from public.projects where title like '%{RUN_ID}%') as p, "
    "(select count(*) from public.project_snapshots) as s, "
    "(select count(*) from public.projects) as total;", read_only=True)
row = pl[0] if isinstance(pl, list) and pl else {}
step("P11-postflight", "0 sladow RUN_ID w projects, total=12",
     f"HTTP {st} {row}",
     st in (200, 201) and row.get("p") == 0 and row.get("total") == 12)

print("=" * 78)
ok = all(STEPS)
print(f"KROKOW={len(STEPS)} PASS={sum(STEPS)} FAIL={len(STEPS) - sum(STEPS)}")
print(f"EXIT={0 if ok else 1}")
sys.exit(0 if ok else 1)
