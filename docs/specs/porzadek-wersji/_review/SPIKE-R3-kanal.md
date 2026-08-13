# SPIKE R3 — kanał dowodowy §6

**Data:** 2026-08-13 · **Stan:** ✅ **DOMKNIĘTY** — kanał zdobyty, wszystkie pytania odpowiedziane
**Decyzja właściciela:** kanał = **Supabase MCP**, autoryzowany na organizacji posiadającej projekt TIOLIBRI

Pytanie spike'u (za `R3-opus-response.md`, sekcja „Co ma rozstrzygnąć spike"): czy na tej maszynie
istnieje kanał do bazy TIOLIBRI, który wykonuje SQL **programowo** i zwraca wynik, żeby asercja
mogła sama powiedzieć PASS/FAIL — bez człowieka wpisującego `EXIT` i bez ręcznej sesji SQL Editora.

## Pomiar — 4 kandydatury

| kandydat | wynik | dowód |
|---|---|---|
| **Supabase MCP** (`execute_sql`, `apply_migration`, `list_tables`, `get_advisors`) | **DZIAŁA, zły org** | `list_projects` → `QuoteFLOW` (INACTIVE) + `fabryka` (ACTIVE). `list_tables(project_id=klhnyagtobgtxnexdsls)` → `MCP error -32600: You do not have permission to perform this action` |
| `psycopg2` + connection string | BRAK wkładu | `psycopg2` nieobecny w `tiolibri-api/venv`; w `tiolibri-api/.env` klucze to `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_KEY`, `SUPABASE_ANON_KEY`, `API_HOST`, `API_PORT` — **żadnego** `DATABASE_URL`/`POSTGRES*`/`postgresql://` |
| `supabase` CLI | **ZALOGOWANE, trzeci org** | `/opt/homebrew/bin/supabase` v2.75.0. `supabase projects list` → org `hcwydriuwapyzxugxgrv`: `xperthub`, `tavlo`. Token w Keychain (w `~/.supabase/` go nie ma), `SUPABASE_ACCESS_TOKEN` nieustawiony |
| `psql` | BRAK | `psql not found` |

**Ref bazy TIOLIBRI:** `klhnyagtobgtxnexdsls` (zgodny w `tiolibri-api/.env` i `tiolibri-frontend/.env.local`).

**TRZY tożsamości, żadna nie widzi TIOLIBRI:** konektor MCP → org `ncpycfjugfxbbiqbefco`
(`QuoteFLOW`, `fabryka`) · CLI → org `hcwydriuwapyzxugxgrv` (`xperthub`, `tavlo`) ·
TIOLIBRI `klhnyagtobgtxnexdsls` → gdzie indziej. To brak uprawnienia, nie brak narzędzia.

## Dlaczego samo CLI nie wystarczy

CLI 2.75 **nie ma** `db execute` ani `db query` — dostępne wyłącznie `diff/dump/lint/pull/push/reset/start`.
`push`/`dump`/`pull` idą bezpośrednim połączeniem do Postgresa, czyli chcą **hasła do bazy**, którego
lokalnie nie ma. CLI na właściwym koncie nadal nie byłoby kanałem dowodowym.

## Kanał właściwy: Management API

`POST /v1/projects/{ref}/database/query` (jest też `/database/query/read-only`,
`api.supabase.com`) — **to samo, co MCP woła pod spodem**. Autoryzacja: `Authorization: Bearer <PAT>`,
**bez hasła do bazy**. Wołalne z Pythona → realny skrypt `.py` z realnym kodem wyjścia,
czyli **kanał A z §6.0 dosłownie tak, jak spec go definiuje**.

Wkład od właściciela: **Personal Access Token** z konta posiadającego `klhnyagtobgtxnexdsls`
(supabase.com/dashboard/account/tokens; PAT-y da się zawęzić zakresem). Podawać przez zmienną
`SUPABASE_ACCESS_TOKEN` — **nie nadpisuje** zalogowania CLI na `tavlo`/`xperthub`.
PAT = pełna władza nad kontem → **nie trzymać w repo**.

## CZĘŚĆ 2 — pomiar na żywej bazie (wykonany)

Token dostarczony przez właściciela (`tiolibri-api/.env`, `SUPABASE_ACCESS_TOKEN`). Konto okazało
się **czwarte**: widzi `klhnyagtobgtxnexdsls` (TIOLIBRI, ACTIVE_HEALTHY, pg 17.6.1.063)
i `hcmeofmaedhlmdotviyh` (Big Picture APP). Skrypty pomiarowe: `.R3-probe2-kanal.py`, `.R3-probe3-rls.py`.

### Pułapka wejściowa (do §6.0)

`urllib` dostaje od Cloudflare **HTTP 403 `error code: 1010`** — blokada po sygnaturze klienta.
Wystarczy nagłówek `User-Agent` (np. `curl/8.7.1`) i przechodzi. Bez tego skrypt asercyjny
wygląda na „brak uprawnień", którym nie jest. **To musi być w §6.0**, inaczej pierwszy bieg
zdiagnozuje się fałszywie.

### Wyniki — 6 pomiarów

| pytanie | wynik |
|---|---|
| tożsamość w kanale | `current_user = postgres`, `current_database = postgres`, PostgreSQL 17.6 |
| **sesja trwa między wywołaniami?** | **NIE.** `pg_backend_pid()` = 547415 vs 547416; `begin; create temp table` w wywołaniu A → w wywołaniu B `42P01: relation "_spike_probe" does not exist` |
| **jedno wywołanie uniesie cały `BEGIN..ROLLBACK`?** | **TAK.** `begin; create temp; insert 3; select count(*); rollback;` → HTTP 201, zwrócone `{'widziane_przed_rollback': 3}` |
| `pg_policies` widoczne? | **TAK** — 23 polityki w `public` (PostgREST zwracał `PGRST205`; Management API widzi) |
| endpoint `/read-only` | działa i **odmawia zapisu**: `25006: cannot execute CREATE TABLE in a read-only transaction` |
| katalog do §6.2 | `md5(pg_get_functiondef(...))` działa — 4 funkcje w `public` (m.in. `prune_project_snapshots` = `568fef8488179dc83f2e1d69622aaf9e`); `pg_trigger` widoczne, `trg_prune_project_snapshots` na `project_snapshots`, `tgenabled='O'` |

### RLS bez zdobywania JWT-ów — pytanie #3 ROZPUSZCZONE

Wzorzec w jednym wywołaniu, bez startu API i bez generowania tokenów użytkowników:

```sql
begin;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"<uuid>","role":"authenticated"}', true);
select case when count(*) = 0 then 'PASS' else 'FAIL' end as wynik from public.projects;
rollback;
```

Zmierzone: właściciel `a4aee672…` widzi **8**, obcy uuid widzi **0**, `anon` widzi **0**,
a asercja zwraca dosłowne `{'wynik': 'PASS', 'widziane': 0}`. **Tożsamości nie trzeba zdobywać** —
podstawia się je rolą i `request.jwt.claims`.

Przy okazji, do §7: 12 projektów rozkłada się na **trzech** właścicieli — `a4aee672…` (8),
`f521bd58…` (2), `0079c43d…` (2).

### Co to robi z uwagami R3

- **#1** (kanał B każe człowiekowi wpisać `EXIT`) — **znika.** Kod wyjścia liczy skrypt `.py`.
- **#2** (krok 8 §6.2 niewykonalny, fixture ginie z `ROLLBACK`) — **znika.** Wynik `SELECT`-a
  sprzed `ROLLBACK` wraca do wołającego w odpowiedzi HTTP.
- **#3** (`DISABLE TRIGGER` blokuje zapisy produkcyjne na czas ręcznej sesji) — **maleje, nie znika.**
  Okno skraca się z sesji człowieka do jednego wywołania, ale lock nadal jest brany na żywej bazie
  i przez ten moment współbieżny zapis do `project_snapshots` zobaczy mutanta. Do rozstrzygnięcia
  w §6.2: czy dowód mutacyjny da się zrobić bez `DISABLE TRIGGER`.

### Ograniczenie, które zostaje

**Temporary access (JIT) NIEDOSTĘPNY** — wymaga PG ≥ 17.6.1.081, TIOLIBRI ma **17.6.1.063**.
Prawdziwej wielowywołaniowej sesji `psql` nie będzie bez upgrade'u. Nie jest potrzebna:
protokół musi być pisany jako **transakcja mieszcząca się w jednym wywołaniu**. To jest wiążące
ograniczenie dla przepisania §6, nie detal.

## Co to zmienia w §6

`execute_sql` przez MCP to kanał, którego §6 nie miała: zapytanie leci programowo i **wraca z wynikiem**,
więc asercja sama liczy PASS/FAIL. To trafia w trzy z pięciu uwag „rdzenia dowodu":

- **R3 #1** — kanał B kazał człowiekowi ręcznie wpisać `EXIT` → odpada, kod wyjścia liczy skrypt z odpowiedzi
- **R3 #2** — krok 8 §6.2 niewykonalny, bo fixture ginie z `ROLLBACK`-iem → odpada, wynik wraca do wołającego przed końcem transakcji
- **R3 #3** — `DISABLE TRIGGER` bierze `SHARE ROW EXCLUSIVE` na czas **ręcznej** sesji SQL Editora i blokuje zapisy produkcyjne → skraca się do czasu jednego wywołania; do rozstrzygnięcia w części drugiej spike'u, czy w ogóle da się dowód mutacyjny zrobić bez `DISABLE TRIGGER`

Nie rozstrzygnięte i **wciąż otwarte** (część druga spike'u, po autoryzacji):
- czy `execute_sql` przepuszcza `BEGIN`/`ROLLBACK` w jednej sesji, czy każde wywołanie to osobna transakcja
  (jeśli osobna — cały protokół mutacyjny §6.2 wymaga przeprojektowania, nie przepisania)
- czy widać `pg_policies` (R1/R4 §6.1) — PostgREST zwracał `PGRST205`
- tożsamości do asercji RLS: JWT właściciela i udziałowca + start API

## Blokada

Autoryzacja konektora Supabase na koncie/organizacji, która ma projekt `klhnyagtobgtxnexdsls`
(claude.ai → ustawienia konektorów). Sesja nieinteraktywna — OAuth nie przechodzi stąd.

**Po autoryzacji:** dokończyć część drugą (3 pytania wyżej), dopiero wtedy `reset-po-spike: R3`
w STATE, `spec:` → `R3-opus-pending`, `/spec-handoff porzadek-wersji`.

**Master pozostaje zamrożony na v0.4.1.** §6 nie jest przepisywana, dopóki część druga nie odpowie
na pytanie o transakcje — to jest dokładnie ten błąd, przed którym bramka STOP-and-SPIKE broni.
