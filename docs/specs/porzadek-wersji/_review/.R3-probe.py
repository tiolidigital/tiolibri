"""R3 preflight probe — read-only. Sprawdza:
1) stan bazy (kolumny projects / project_snapshots, liczby) — czy fakty §3.1/§3.4.1/§7 nadal aktualne
2) czy kanal PostgREST (venv/bin/python + supabase-py) dosiega pg_catalog (pg_policies) — potrzebne w §6.1 R1/R4
3) czy istnieje jakikolwiek RPC-owy escape hatch do surowego SQL (potrzebny w §6.2)
Sekrety nie sa drukowane.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

ROOT = "/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI"
load_dotenv(os.path.join(ROOT, "tiolibri-api", ".env"))

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_KEY"]
sb = create_client(url, key)

fails = 0

# --- 1. stan bazy ---
projects = sb.table("projects").select("*").execute().data
print(f"STEP=db-projects EXPECT=12 GOT={len(projects)} "
      f"RESULT={'PASS' if len(projects) == 12 else 'FAIL'}")
if len(projects) != 12:
    fails += 1
cols = sorted(projects[0].keys()) if projects else []
new_cols = [c for c in ("note", "role", "book", "deleted_at") if c in cols]
print(f"STEP=db-projects-cols EXPECT=brak(note,role,book,deleted_at) GOT={new_cols or 'brak'} "
      f"RESULT={'PASS' if not new_cols else 'FAIL'}")
if new_cols:
    fails += 1
print(f"       kolumny projects: {cols}")

snaps = sb.table("project_snapshots").select("id,project_id,triggered_by,created_at").execute().data
print(f"STEP=db-snapshots-count EXPECT=liczba GOT={len(snaps)} RESULT=PASS")
one = sb.table("project_snapshots").select("*").limit(1).execute().data
scols = sorted(one[0].keys()) if one else []
snew = [c for c in ("label", "pinned") if c in scols]
print(f"STEP=db-snapshots-cols EXPECT=brak(label,pinned) GOT={snew or 'brak'} "
      f"RESULT={'PASS' if not snew else 'FAIL'}")
if snew:
    fails += 1
print(f"       kolumny project_snapshots: {scols}")
from collections import Counter
print(f"       triggered_by: {dict(Counter(s['triggered_by'] for s in snaps))}")

# --- 2. pg_catalog przez PostgREST? ---
try:
    r = sb.table("pg_policies").select("*").limit(1).execute()
    print(f"STEP=postgrest-pg_policies EXPECT=blad GOT=zwrocilo {len(r.data)} wierszy RESULT=FAIL")
    fails += 1
except Exception as e:  # noqa: BLE001
    msg = str(e).replace("\n", " ")[:220]
    print(f"STEP=postgrest-pg_policies EXPECT=blad GOT={msg} RESULT=PASS")

# --- 3. RPC escape hatch do surowego SQL? ---
for fn in ("exec_sql", "execute_sql", "sql", "query"):
    try:
        sb.rpc(fn, {}).execute()
        print(f"STEP=rpc-{fn} EXPECT=brak-funkcji GOT=ISTNIEJE RESULT=FAIL")
        fails += 1
    except Exception as e:  # noqa: BLE001
        msg = str(e).replace("\n", " ")[:120]
        print(f"STEP=rpc-{fn} EXPECT=brak-funkcji GOT={msg} RESULT=PASS")

print(f"EXIT={1 if fails else 0}")
sys.exit(1 if fails else 0)
