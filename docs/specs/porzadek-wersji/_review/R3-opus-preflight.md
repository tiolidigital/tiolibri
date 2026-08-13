# R3 — preflight L5 (Opus), spec `porzadek-wersji` (Stadium A, master)

**Data:** 2026-08-13
**Runda generowana:** R3 (`spec: R2-opus-pending` → TARGET=3) — **ostatnia przed progiem eskalacji**
(`N_EFF` po R3 = 3 = `MAX_ROUNDS` dla Risk HIGH)
**Plik pod review:** `docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md` (v0.4 → **v0.4.1**)
**Kanał odczytu bazy:** `tiolibri-api/venv/bin/python` + klient z `tiolibri-api/.env`
(TIOLIBRI nie jest w koncie Supabase pod MCP — jak w R1/R2).

Zakres: **fakty nośne, które pojawiły się dopiero w v0.4** (§3.4.2a, §3.4.3, §3.4.3a, §3.6.1, §6.0,
§6.2, §8/D5) plus **wykonalność protokołu dowodu §6** — bo to jedyna rzecz w tym specu, która
twierdzi coś o SESJI wykonania, a nie o pliku. Fakty zweryfikowane w R1/R2 i niezmienione nie są
powtarzane; kod nie był dotykany (`git status`: zmiany wyłącznie w `docs/`, HEAD `5f25c62`).

## Fakty nośne

- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python scratchpad/probe_r3.py EXIT=0 | note=baza bez zmian od R2: `projects` 12 wierszy i 12 kolumn BEZ note/role/book/deleted_at, `project_snapshots` 31 wierszy i 5 kolumn BEZ label/pinned — wszystkie kolumny §3.1 i §3.4.1 nadal są nowe
- FACT: CORRECTED | kind=execution | source=tiolibri-api/venv/bin/python scratchpad/probe_r3.py EXIT=0 | note=stare=twierdzenie „ani jeden snapshot nie jest ręczny" wycofane w 0.3, bo E nie zawierał rozkładu `triggered_by` nowe=31 z 31 `triggered_by = 'auto'`
- FACT: CORRECTED | kind=execution | source=tiolibri-api/venv/bin/python scratchpad/probe_r3.py EXIT=0 (STEP=postgrest-pg_policies, STEP=rpc-exec_sql/execute_sql/sql/query) | note=stare=Środowisko: `tiolibri-api/venv/bin/python` + klient z `tiolibri-api/.env` jako JEDYNY kanał dowodu §6.1 i §6.2 nowe=**kanał B** (SQL Editor) dla R1 i R4
- FACT: VERIFIED | kind=execution | source=`command -v psql` (brak) + `ls tiolibri-api/venv/lib/python*/site-packages` + `rg -o '^[A-Z_]+=' tiolibri-api/.env` | note=na tej maszynie nie ma `psql`, venv ma wyłącznie `supabase`/`postgrest`/`dotenv` (zero `psycopg2`/`asyncpg`), a `.env` nie zawiera URL-a połączenia — trzy niezależne powody, dla których kanał SQL musi być nazwany osobno, a nie założony
- FACT: VERIFIED | kind=path-existing | source=tiolibri-frontend/docs/migrations/20260421_spec1.sql:3 | note=`-- Run in Supabase SQL Editor (single transaction)` — kanał B nie jest wymyślony na potrzeby dowodu, tylko tym samym, którym w tym repo stosuje się migracje (potwierdza też `20260421_spec1_fixup.sql:11`)
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/docs/migrations/20260421_spec1.sql:240-242 | note=`DROP POLICY` (240) + `CREATE POLICY "Users can insert accessible project_snapshots"` (241) + `WITH CHECK (user_has_project_access(project_id))` (242) — kotwica §3.4.3a trafia co do wiersza
- FACT: VERIFIED | kind=anchor | source=rg -n 'project_snapshots' tiolibri-frontend/docs/migrations/20260421_spec1.sql | note=na `project_snapshots` istnieją DOKŁADNIE dwie polityki (SELECT 238, INSERT 241) — brak `FOR UPDATE` z §3.4.3a jest faktem pliku, więc asercja „na braku" (krok R4 §6.1) ma co mierzyć
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/docs/migrations/20260421_spec1.sql:48-79 | note=`project_snapshots` ma `snapshot JSONB NOT NULL` i `triggered_by TEXT NOT NULL CHECK IN ('auto','manual','pre-restore')`; funkcja `prune_project_snapshots()` (61) i trigger `trg_prune_project_snapshots AFTER INSERT` (77) nazwane dokładnie tak, jak cytuje §6.2
- FACT: CORRECTED | kind=fixture | source=tiolibri-frontend/docs/migrations/20260421_spec1.sql:48-55 | note=stare=fixture §6.2 opisany wyłącznie przez `created_at` i `pinned`, bez kolumn NOT NULL nowe=snapshot = '{}'::jsonb, triggered_by = 'auto'
- FACT: CORRECTED | kind=state-machine | source=PostgreSQL: ROLLBACK cofa DDL, wiersze tabel TEMP utworzonych w transakcji oraz efekty `SET` | note=stare=**Zapis produkcyjnej deklaracji** — `pg_get_functiondef('public.prune_project_snapshots'::regproc)` do zmiennej nowe=**Zapis produkcyjnej deklaracji POZA transakcją** — `md5(pg_get_functiondef('public.prune_project_snapshots'::regproc))` wklejony do artefaktu
- FACT: VERIFIED | kind=arg | source=tiolibri-frontend/docs/migrations/20260421_spec1.sql:53 | note=słownik `triggered_by` to dokładnie `auto`/`manual`/`pre-restore` — mapowanie §3.4.2a („Automatyczny"/„Ręczny"/„Przed przywróceniem") pokrywa zbiór bez reszty i bez wartości spoza CHECK-a
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/snapshots.py:74-80 | note=`@router.post("/{project_id}/snapshots/{snapshot_id}/restore")` (74), `async def restore_snapshot` (75), `_assert_project_access(project_id, user["id"])` (80) — podstawa D5 („restore przepuszcza dziś udziałowca") jest w kodzie dokładnie tam, gdzie §8 ją wskazuje
- FACT: VERIFIED | kind=signature | source=tiolibri-frontend/src/features/editor/useSnapshots.js:23-24 | note=`createSnapshot` woła `authedFetch('/projects/${projectId}/snapshots', { method: 'POST' })` BEZ body — szew 2A→2B z §3.4.3 opisuje realnego klienta, a nie hipotezę: wymagalne `label` w 2A dałoby `422` po samym merge 2A
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/projects.py:98-99 | note=`@router.post("/{project_id}/duplicate")` (98) + `async def duplicate_project` (99) — kotwica §3.3 trafia w dekorator i sygnaturę
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/docs/supabase-schema.sql:131-135 | note=`DROP POLICY IF EXISTS "Users can update own projects"` + `CREATE POLICY … FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (…)` — polityka owner-only z §3.2.1 jest w repozytoryjnym SQL-u; spec słusznie nazywa ten plik historycznym, bo to nie jest odczyt żywej bazy (dlatego krok R1 §6.1 idzie kanałem B)
- FACT: VERIFIED | kind=export | source=tiolibri-api/app/routers/projects.py:72-73 | note=`@router.get("/{project_id}", response_model=Project)` nad `async def get_project(project_id, _user=Depends(verify_supabase_jwt))` — pułapka §3.2 („bez dopisania pól endpoint utnie je po cichu") i dziura §3.2.1 dotyczą tego samego, jednego dekoratora
- FACT: VERIFIED | kind=export | source=tiolibri-api/app/models/schemas.py:75 | note=`class Project(BaseModel)` stoi dokładnie w cytowanej linii
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/projects/useProjects.js:77-80 | note=`deleteProject` (77) woła `.delete()` (80) wprost z przeglądarki — twierdzenie §3.5 „twardy DELETE bez endpointu, bez cofnij" potwierdzone; to ono uzasadnia protokół §7.1
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/export_import.py:169-176 | note=`select("id, title, sort_order, processed_html").eq(project_id).is_("deleted_at","null")` — eksport do Redaktora czyta bieżącą treść, nigdy `chapter_versions` (§3.5)
- FACT: VERIFIED | kind=sizing | source=§6.2 kroki 2/4/6 przeliczone na deklaracji triggera z 20260421_spec1.sql:61-79 | note=GREEN 15 nieprzypiętych (keep-set 15 najnowszych z `pinned=false`, kasowany 2026-01-01); mutacja #1 keep-set bez przypiętego → DELETE bez filtra zabiera przypiętego; mutacja #2 keep-set liczy 15 najnowszych ŁĄCZNIE z przypiętym (najnowszym), więc nieprzypiętych zostaje **14** — arytmetyka trzech RED/GREEN zgadza się co do wiersza
- FACT: VERIFIED | kind=state-machine | source=docs/specs/porzadek-wersji/STATE.md:1 | note=`spec: R2-opus-pending` → TARGET=3, plik nazwany R3-opus-preflight.md; `N=2, rundy-rdzenia=0, reset-po-spike=0` → `N_EFF=2 < MAX_ROUNDS=3`; delta 0.4→0.4.1 ≠ 0, więc bramka „zakaz rundy potwierdzającej" nie blokuje
- FACT: VERIFIED | kind=parser | source=awk U9 z /spec-health-check na SPEC-PORZADEK-WERSJI-MASTER.md | note=tabela zbiorcza §5 (8 faz × 7 osi) stoi nadal PRZED podsekcjami `###`, a edycje 0.4.1 dotknęły §1 i §6 — layout, na którym U9 przestał być ślepy (LESSONS#18), jest nienaruszony

## Rozstrzygnięcia Opusa PRZED handoffem (nie flagowane Codexowi)

1. **Deklarowany kanał dowodu nie wykonywał połowy własnego protokołu.** §6.0 v0.4 mówiła
   „każdy krok §6.1 i §6.2 wykonuje skrypt asercyjny uruchamiany `venv/bin/python`", a §6.1 R1/R4
   pyta `pg_policies` i całe §6.2 wymaga `BEGIN`/`DISABLE TRIGGER`/`CREATE OR REPLACE`/`ROLLBACK`.
   Zmierzone: PostgREST odpowiada `PGRST205` na `pg_policies`, `PGRST202` na cztery kandydatury
   funkcji SQL, brak `psql`, brak sterownika libpq w venv, brak URL-a w `.env`. To jest dokładnie
   klasa LESSONS#15 (bramka nieuruchamialna w kanale, w którym ją zapisano) i sprawa
   EGZEKWOWALNOŚCI, więc rozstrzygnięta przed handoffem: §6.0 dostała **dwa nazwane kanały**
   z wiążącym przypisaniem kroków, a kanał B jest tym samym SQL Editorem, którym repo stosuje
   migracje (`20260421_spec1.sql:3`) — nie nowym narzędziem.

2. **Rewert triggera mierzony z wnętrza transakcji byłby niemierzalny.** `ROLLBACK` kasuje
   też wartość odniesienia (tabela TEMP z transakcji, `SET`, wynik SAVEPOINT-u), więc krok 7
   nie miałby z czym porównywać hasha. §6.2 liczy teraz `md5(pg_get_functiondef(…))` **przed
   `BEGIN` i po `ROLLBACK`**, oba wklejone do artefaktu. Fakt o Postgresie, nie decyzja produktowa.

3. **Fixture §6.2 nie dało się wstawić.** `project_snapshots.snapshot` i `.triggered_by` są
   `NOT NULL`, a opis fixture'u wymieniał wyłącznie `created_at`, `label` i `pinned` — szesnaście
   INSERT-ów wywróciłoby się na pierwszym. Dopisane wartości mieszczą się w CHECK-u kolumny.

4. **Pomiar `triggered_by` przywrócił twierdzenie wycofane w 0.3.** 31 z 31 snapshotów ma `auto`.
   §1 dostaje je z powrotem, ale **jako pomiar z datą**, z jawnym „żadna bramka się o to nie opiera"
   — to samo obwarowanie, które ma tam liczba snapshotów.

## Parser self-test

**Master nie deklaruje własnej bramki mechanicznej ani parsera** — §6 to protokół dowodu
wykonywany w PHASE-1A/2A na obiektach, które te fazy dopiero tworzą (LESSONS#15: kryteria
akceptacji, nie bramki rundy spec; tak są nazwane i umiejscowione).

Dry-runowi podlega **bramka U9 z `/spec-health-check`** — jedyny parser, który czyta ten plik.

**Wkład PASS** (`SPEC-PORZADEK-WERSJI-MASTER.md` v0.4.1, tabela zbiorcza §5):
```
layoutA_haslim=1 rows=8 viol=0
EXIT=0
```

**Wkład FAIL** (kopia w scratchpadzie, wiersz `PHASE-2A-db` z `Pliki` podbitym 2 → 9 przy limicie ≤8):
```
rows=8 viol=1
SIZING-FAIL
  wiersz PHASE-2A-db: estymata 9 > limit 8
EXIT=1
```

Kontrpróba **koliduje z dozwolonym wzorcem** (LESSONS#13): to legalny wiersz legalnej tabeli
z jedną wartością ponad limit, a nie wiersz-śmieć, który parser odrzuciłby kształtem.

Osobno dry-runowi podlegał w tym preflighcie **kanał dowodu** (`probe_r3.py`, `EXIT=0`) — z wkładem
oczekującym BŁĘDU: pięć kroków (`pg_policies` + cztery RPC) ma `EXPECT=blad`, a `RESULT=PASS`
zapada dopiero, gdy błąd realnie przyszedł. Gdyby PostgREST te zapytania obsłużył, skrypt
zwróciłby `EXIT=1` — i to jest jedyny powód, dla którego wniosek „potrzebny drugi kanał" jest
pomiarem, a nie przypuszczeniem.

## Audyt C/M/E

Kanon `docs/specs/spec-workflow/CME-MANIFEST.md` **nie istnieje** ani w tym repo, ani w kopii
kanonicznej w FABRYCE. Zgodnie z regułą 1 („kanon przed egzekucją") audyt nie jest tu blokerem
werdyktu; bramka strukturalna preflightu obowiązuje i rekordy są wypełnione normalnie.

- CME: typ=MEASURED | dowod=probe-db-2026-08-13 | C=twierdzenia §1/§3.1/§3.1.2/§3.4.1/§7 o stanie bazy: 12 projektów, brak kolumn note/role/book/deleted_at, brak label/pinned, liczba snapshotów, rozkład `triggered_by`, pełne pokrycie listy §7 | M=skrypty odczytu w scratchpadach sesji (R1: probe.py, probe2.py, probe3.py; R2: probe_r2.py; R3: probe_r3.py), wszystkie EXIT=0 | E=R1 2026-08-13: projects 12 wierszy z 12 kolumnami · project_snapshots 31 wierszy z 5 kolumnami · rozkład per projekt d73dcc3b 10, 507b3ee4 10, 11c96cd4 6, 17adb766 2, 72609fef 1, b0841702 1, 70e90efb 1 · R2 2026-08-13: 12 prefiksów ID w bazie = 2 KEEP + 9 DELETE + 1 LOOK z §7, zero nieklasyfikowanych · R3 2026-08-13: projects 12 wierszy, kolumny bez note/role/book/deleted_at · project_snapshots 31 wierszy, kolumny bez label/pinned · triggered_by = {auto: 31}, zero manual, zero pre-restore | poza=NIE zmierzono treści rozdziałów, więc „żaden rozdział nie zgadza się hashem" pozostaje w §1 jawnie oznaczone jako tło bez wykonanego E; proporcjonalne, bo żadna bramka się o nie nie opiera; treść pokrywa rekord CONTRACTED sha256 niżej | werdykt=PASS
- CME: typ=MEASURED | dowod=probe-kanalu-dowodu-2026-08-13 | C=§6.0 twierdzi, którym kanałem wykonuje się KAŻDY krok §6.1 i §6.2 | M=`probe_r3.py` kroki STEP=postgrest-pg_policies i STEP=rpc-{exec_sql,execute_sql,sql,query} + `command -v psql` + inwentarz site-packages venva + nazwy kluczy `.env` | E=R3 2026-08-13: `pg_policies` → PGRST205 „Could not find the table 'public.pg_policies' in the schema cache" · 4× PGRST202 dla kandydatur funkcji SQL · `psql` brak w PATH · site-packages bez psycopg2/asyncpg · `.env` bez URL-a połączenia (SUPABASE_URL + klucze) · EXIT=0 | poza=NIE zmierzono, że SQL Editor faktycznie wykona §6.2 — to zdarzy się dopiero w PHASE-2A-db; zmierzono wyłącznie, że kanał A tego NIE zrobi, plus że repo już dziś używa SQL Editora do migracji (`20260421_spec1.sql:3`); proporcjonalne, bo teza speca brzmi „potrzebne są dwa kanały", a nie „kanał B został przetestowany" | werdykt=PASS
- CME: typ=MEASURED | dowod=wc-l-sizing | C=§5 twierdzi, że estymaty stoją na zmierzonych bazach 12 plików | M=`wc -l` w preflightach R1 (8 plików) i R2 (4 pliki), plus potwierdzenie Codexa w R1 z EXIT=0 | E=R1 2026-08-12/13: ProjectCard 259, DashboardPage 153, useProjects 125, projects.py 431, snapshots.py 258, ProjectSnapshots 158, useSnapshots 40, schemas.py 99 · R2 2026-08-13: EditorPage 766, export_import 450, NewProjectModal 106, Badge 75 · R3 2026-08-13: bazy nie mierzone ponownie — kod nietknięty (`git status`: tylko `docs/`) | poza=zmierzone są WYŁĄCZNIE bazy plików, NIE estymaty przyrostu — te są prognozą sprzed kodu i §5 nazywa je prognozą (LESSONS#17); pokryte przez checkpoint sizingu po napisaniu kodu w `/spec-impl` | werdykt=PASS
- CME: typ=CONTRACTED | dowod=sha256-md-roundtrip-2026-08-11 | C=wybór dwóch projektów kanonicznych (d73dcc3b, 507b3ee4) jako AKTUALNA | M=pamięć project-kanoniczne-projekty-w-bazie, zapis z 2026-08-11 wykonany poza tym specem | mierzalne-od=md_exporter.chapter_to_markdown na projekcie z bazy plus porównanie sha256 NFC z input.md z przebiegów Redaktora, krok: przed sprzątaniem balastu | poza=ten spec NIE powtarza tego pomiaru i nie opiera na nim żadnej bramki; proporcjonalne, bo §7 opisuje czynność właściciela wykonywaną ręcznie wg protokołu §7.1 z backupem i wierszem w SPRZATANIE-LOG.md przed każdą kasacją; pokryte dodatkowo przez wymóg oględzin 19c4a5fe (D4) | werdykt=PASS
- CME: typ=CONTRACTED | dowod=protokol-dowodu-§6 | C=§6 twierdzi, że CHECK-i, oba indeksy częściowe, polityki RLS i oba warunki triggera prune są dowodliwe bez harnessu testowego | M=derywacja z kontraktu: SQLSTATE 23514/23505 dla naruszeń, `pg_policies` dla polityk, `md5(pg_get_functiondef)` dla rewertu DDL, transakcyjność DDL w Postgresie dla izolacji mutanta; kanały nazwane i zmierzone w rekordzie probe-kanalu-dowodu | mierzalne-od=kroki 1-10 i R1-R4 §6.1 oraz 1-8 §6.2, krok: PHASE-1A-db/1A-api i PHASE-2A-db (artefakty PROOF-1A-db.md, PROOF-1A-api.md, PROOF-2A-mutacja.md) | poza=w rundzie SPEC dowodu NIE ma i mieć nie może — CHECK-i, indeksy, zawężona polityka INSERT i przepisany trigger nie istnieją przed migracją (LESSONS#15); zweryfikowane są wyłącznie: nieobecność obiektów docelowych, nazwy obiektów istniejących (funkcja, trigger, polityki) i wykonalność kanałów | werdykt=PASS
