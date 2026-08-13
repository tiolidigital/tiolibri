# R2 — preflight L5 (Opus), spec `porzadek-wersji` (Stadium A, master)

**Data:** 2026-08-13
**Runda generowana:** R2 (`spec: R1-opus-pending` → TARGET=2)
**Plik pod review:** `docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md` (v0.3 → **v0.3.1**)
**Odczyt bazy:** `tiolibri-api/venv/bin/python` + klient z `tiolibri-api/.env`
(TIOLIBRI nie jest w koncie Supabase pod MCP — kanał jak w R1).

Zakres tego preflightu: **fakty nośne, które pojawiły się dopiero w v0.3** (§3.1.2, §3.2, §3.2.1,
§3.6, §5 przepisane na 7 osi, §6, §9), plus ponowny pomiar bazy pod §7. Fakty zweryfikowane w R1
i niezmienione (`ProjectCard` 259, `projects.py` 431, trigger prune, kolejność routerów) nie są tu
powtarzane — kod i baza nie były w międzyczasie dotykane (`git status`: zmiany wyłącznie w `docs/`).

## Fakty nośne

- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/editor/EditorPage.jsx:224-236 | note=handleUpdateProject to `supabase.from('projects').update({[field]: value, updated_at}).eq('id', projectId)` napisany wprost w komponencie — druga realna ścieżka zapisu z §3.2 istnieje dokładnie w tej kotwicy
- FACT: CORRECTED | kind=anchor | source=tiolibri-frontend/src/features/projects/useProjects.js:38-52 | note=stare=wiersz 3 tabeli §3.2 miał w kolumnie „Kotwica" słowo INSERT bez pliku i linii (LESSONS#20) nowe=useProjects.js:38-52
- FACT: VERIFIED | kind=signature | source=tiolibri-frontend/src/features/projects/useProjects.js:38 | note=createProject destrukturyzuje DOKŁADNIE `{ title, author = '', language = 'pl' }`, a NewProjectModal:25 woła `onSubmit({ title, author, language })` i sam nie dotyka Supabase — dopisanie `book` wymaga dwóch dotknięć, co §3.2 teraz nazywa
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/projects.py:71-78 | note=`async def get_project(project_id: str, _user: dict = Depends(verify_supabase_jwt))` robi `select("*").eq("id", project_id)` i zwraca wiersz — `_user` nie występuje w ciele; IDOR z §3.2.1 potwierdzony u źródła
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/services/supabase_client.py:4-16,37-38 | note=`get_supabase_client` bierze SUPABASE_SERVICE_KEY (linia 11) i z niego tworzy singleton `supabase` (linia 38) — twierdzenie §3.2.1 „backend omija RLS" jest wobec kodu prawdziwe
- FACT: CORRECTED | kind=export | source=rg -n '_assert_project_access' tiolibri-api/app | note=stare=§3.2.1 sugerowało jeden wspólny helper wołany z czterech plików nowe=cztery niezależne lokalne definicje
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/projects.py:394 | note=`_assert_project_access(project_id, user_id)` istnieje w tym samym pliku co `get_project` i jest wołany w projects.py:358 — wpięcie z §3.2.1 jest realnie tanie
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/export_import.py:87-97 | note=`project_export` ma DOKŁADNIE 7 pól (title, author, language, style_preset, typography_settings, cover_image_url, status) — wiersz „Eksport" w §3.6 zgadza się co do liczby
- FACT: CORRECTED | kind=anchor | source=tiolibri-api/app/routers/export_import.py:388-397 | note=stare=Import `.tiolibri` — 8 pól, kotwica 385-400 nowe=9 pól
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/snapshots.py:176-196 | note=`_build_snapshot` selectuje 8 pól projektu (id, title, author, language, style_preset, typography_settings, cover_image_url, status) — wiersz „_build_snapshot" w §3.6 zgadza się
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/snapshots.py:97-107 | note=allowlist restore'u to 5 pól (title, author, language, style_preset, typography_settings) — `cover_image_url` i `status` faktycznie wypadają, czyli asymetria „snapshot łapie szerzej niż restore oddaje" z §3.6 jest w kodzie, nie wymyślona
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/snapshots.py:50-58 | note=`create_snapshot(project_id, user)` nie przyjmuje body — §3.4.3 słusznie mówi „zmiana istniejącego endpointu", nie nowy
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/snapshots.py:160-172 | note=`_assert_project_access` w snapshots.py przepuszcza właściciela LUB udział (drugie zapytanie po `shared_with_user_id`) — uzasadnienie dla nowego `_assert_project_owner` z §3.4.3 jest realne
- FACT: VERIFIED | kind=export | source=rg -n '_assert_project_owner' tiolibri-api/app | note=zero trafień — helper owner-only z §3.4.3 jest faktycznie nowy, nie duplikuje istniejącego
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/components/ui/Badge.jsx:50-64 | note=warianty to dokładnie draft/in_progress/completed/gray/blue/green/yellow/red/indigo, rozmiary sm/md — mapowanie plakietek z §9.2 (green/yellow/gray/indigo) mieści się bez nowych wariantów
- FACT: CORRECTED | kind=sizing | source=wc -l tiolibri-frontend/src/features/editor/EditorPage.jsx | note=stare=EditorPage.jsx baza 620+ LOC nowe=baza 766 LOC
- FACT: CORRECTED | kind=sizing | source=wc -l tiolibri-frontend/src/features/projects/NewProjectModal.jsx | note=stare=NewProjectModal.jsx baza nie mierzona nowe=baza 106 LOC
- FACT: VERIFIED | kind=sizing | source=wc -l tiolibri-api/app/routers/export_import.py tiolibri-frontend/src/components/ui/Badge.jsx | note=export_import.py 450 LOC (§5 pisze „~450") i Badge.jsx 75 LOC — obie bazy zgodne z tym, co spec zakłada przy modyfikacji
- FACT: VERIFIED | kind=path-new | source=tiolibri-frontend/docs/migrations/20260813_porzadek_wersji_1a.sql | note=rodzic `tiolibri-frontend/docs/migrations/` istnieje (dwa pliki 20260421_*), plik migracji PHASE-1A jeszcze nie — ścieżka z §5 jest do utworzenia, nie stale-ref
- FACT: VERIFIED | kind=path-new | source=tiolibri-frontend/docs/migrations/20260813_porzadek_wersji_2a.sql | note=jak wyżej dla PHASE-2A; katalog migracji jest w `tiolibri-frontend/docs/`, nie w `tiolibri-api/` — spec cytuje właściwy
- FACT: VERIFIED | kind=arg | source=literal PostgreSQL SQLSTATE class 23 | note=23514 = check_violation, 23505 = unique_violation — kody oczekiwane w §3.2 i w krokach 2-6 §6.1 są przypisane do właściwych naruszeń
- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python scratchpad/probe_r2.py EXIT=0 | note=12 projektów; kolumny `projects` bez note/role/book/deleted_at; `project_snapshots` bez label/pinned; 31 snapshotów — wszystkie kolumny z §3.1 i §3.4.1 są nowe, `book IS NULL` dla wszystkich 12 (podstawa drugiego indeksu §3.1.2) potwierdzone przez BRAK kolumny
- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python scratchpad/probe_r2.py EXIT=0 | note=podział §7 pokrywa bazę bez reszty: 2 kanoniczne + 9 do usunięcia + 1 do oględzin = 12, zero prefiksów ID w bazie poza listą, zero pozycji listy nieobecnych w bazie
- FACT: CORRECTED | kind=parser | source=awk U9 z /spec-health-check na SPEC-PORZADEK-WERSJI-MASTER.md | note=stare=§5 miała wyłącznie tabele per faza pod nagłówkami ### — parser U9 kończy sekcję na pierwszym podnagłówku, więc widział rows=0 i dawał vacuous PASS (LESSONS#18) nowe=Ta zbiorcza tabela stoi **przed** podsekcjami celowo
- FACT: VERIFIED | kind=execution | source=awk U9 na docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md EXIT=0 | note=po dołożeniu tabeli zbiorczej parser widzi layout A z limitami w nagłówku: rows=5, viol=0 — U9 mierzy realnie wszystkie 5 faz × 7 osi
- FACT: VERIFIED | kind=state-machine | source=docs/specs/porzadek-wersji/STATE.md:1 | note=`spec: R1-opus-pending` → TARGET=2, plik preflightu nazwany R2-opus-preflight.md; N_EFF=1 < MAX_ROUNDS=3 (Risk HIGH), delta v0.2→v0.3 = 607 linii ≠ 0, więc bramka „zakaz rundy potwierdzającej" nie blokuje

## Rozstrzygnięcia Opusa PRZED handoffem (nie flagowane Codexowi)

1. **Ścieżka zapisu #3 dostała kotwicę i pełny opis kosztu.** v0.3 zostawiała w tabeli §3.2 słowo
   „INSERT" bez pliku i linii. Sondaż pokazał, że `NewProjectModal` w ogóle nie dotyka bazy, a
   `createProject` destrukturyzuje trzy pola w sygnaturze — dopisanie `book` tylko w modalu byłoby
   ciche i bezskuteczne. To jest doprecyzowanie faktu, nie decyzja produktowa, więc idzie do speca,
   a nie do promptu recenzenta (LESSONS#20).

2. **`_assert_project_access` NIE jest wspólnym helperem.** Cztery pliki mają własne, identyczne
   definicje. v0.3 dawała się czytać jako „jest jeden, zaimportuj go", co w PHASE-1A prowadziłoby
   albo do zbędnej ekstrakcji modułu (zmiana architektoniczna poza zakresem fazy), albo do pytania
   w rundzie. Rozstrzygnięte w specu: PHASE-1A wpina lokalną kopię z `projects.py` i **niczego nie
   centralizuje**.

3. **§5 przebudowana tak, żeby bramka U9 w ogóle ją widziała.** Health-check zwracał PASS przy
   `rows=0` — nie dlatego, że estymaty mieszczą się w limitach, tylko dlatego, że parser nie
   doczytał do żadnej tabeli. Dołożona tabela zbiorcza (5 faz × 7 osi, limity w nagłówku) daje
   `rows=5 viol=0`, a kontrpróba z `Pliki=9` przy limicie ≤8 wywraca gate na `EXIT=1`. To jest
   kwestia EGZEKWOWALNOŚCI, więc rozstrzygnięta przed handoffem, nie oddana Codexowi.

4. **Kotwica importu przesunięta na realny słownik.** `385-400` obejmowało też `raise` i `insert`;
   sam `new_project_row` stoi w `388-397` i ma 9 kluczy, nie 8. Liczba jest nośna, bo §3.6 mówi
   „dziś N pól, po zmianie + note, book" — zła liczba w tabeli to gotowy bloker.

## Parser self-test

**Master sam nie deklaruje żadnej bramki mechanicznej ani parsera.** Nowe w v0.3 `§6` to
**protokół dowodu owner-attested**, wykonywany w PHASE-1A/2A na obiektach, które te fazy dopiero
tworzą (CHECK, dwa indeksy częściowe, przepisany trigger). Zgodnie z LESSONS#15 są to **kryteria
akceptacji fazy, nie bramki rundy spec** — i tak są w specu nazwane i umiejscowione.

Dry-runowi podlega natomiast **bramka U9 z `/spec-health-check`**, która na TYM specu okazała się
ślepa — i to jest jedyne ustalenie tego preflightu, które zmieniło strukturę speca.

**Wkład PASS** (`SPEC-PORZADEK-WERSJI-MASTER.md` po dołożeniu tabeli zbiorczej):
```
layoutA_haslim=1 rows=5 viol=0
EXIT=0
```

**Wkład FAIL** (kopia w scratchpadzie, wiersz `PHASE-2A` z `Pliki` podbitym 3 → 9 przy limicie ≤8):
```
rows=5 viol=1
SIZING-FAIL
  wiersz PHASE-2A: estymata 9 > limit 8
EXIT=1
```

**Stan PRZED poprawką** (dla porządku — tak wyglądał vacuous PASS): `layoutB=0 rows=0 viol=0`,
`EXIT=0`. Zero wierszy, zero naruszeń, zielono — gate nie sprawdził niczego, bo wszystkie tabele
sizingu leżały pod nagłówkami `###`, a parser kończy sekcję na pierwszym podnagłówku. To jest
dokładnie rodzina z LESSONS#18 („kłamiąca bramka jest gorsza od milczącej"), złapana w tym
preflighcie, nie w rundzie Codexa.

Jedyne mechanizmy egzekwujące, które ISTNIEJĄ dziś i są cytowane (trigger `prune_project_snapshots`,
kolejność routerów w `main.py`), zostały zweryfikowane odczytem w R1 i nie zmieniły się.

## Audyt C/M/E

Kanon `docs/specs/spec-workflow/CME-MANIFEST.md` **nie istnieje** ani w tym repo, ani w kopii
kanonicznej w FABRYCE (`/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`
zawiera LESSONS, RETRO, RETRO-LAST-REVIEW, SPEC-WORKFLOW-MASTER, STAND-IN-REVIEWER, `_review/`).
Zgodnie z regułą 1 („kanon przed egzekucją") audyt nie jest tu blokerem werdyktu; bramka strukturalna
preflightu obowiązuje i rekordy poniżej są wypełnione normalnie.

- CME: typ=MEASURED | dowod=probe-db-2026-08-13 | C=twierdzenia §1/§3.1/§3.1.2/§3.4/§7 o stanie bazy: 12 projektów, brak kolumn note/role/book/deleted_at w projects, brak label/pinned w project_snapshots, liczba snapshotów, pełne pokrycie listy §7 | M=skrypty odczytu w scratchpadach sesji (R1: probe.py, probe2.py, probe3.py; R2: probe_r2.py), wszystkie EXIT=0 | E=R1 2026-08-13: projects 12 wierszy z 12 kolumnami · project_snapshots 31 wierszy z 5 kolumnami · rozkład per projekt d73dcc3b 10, 507b3ee4 10, 11c96cd4 6, 17adb766 2, 72609fef 1, b0841702 1, 70e90efb 1 · liczby rozdziałów dla 4 projektów · R2 2026-08-13: projects 12 wierszy, kolumny bez note/role/book/deleted_at · project_snapshots 31 wierszy, kolumny bez label/pinned · 12 prefiksów ID w bazie = 2 KEEP + 9 DELETE + 1 LOOK z §7, zero nieklasyfikowanych, zero pozycji §7 spoza bazy | poza=NIE zmierzono treści rozdziałów ani rozkładu `triggered_by`, więc twierdzenia „ani jeden snapshot nie jest ręczny" i „żaden rozdział nie zgadza się hashem" pozostają wycofane z warstwy nośnej (§1 mówi to wprost); proporcjonalne, bo żadna bramka ani kryterium akceptacji się o nie nie opiera; treść pokrywa osobny dowód sha256 opisany w rekordzie CONTRACTED niżej | werdykt=PASS
- CME: typ=MEASURED | dowod=wc-l-sizing | C=§5 twierdzi, że estymaty stoją na zmierzonych bazach 12 plików | M=`wc -l` w preflightach R1 (8 plików) i R2 (4 pliki), plus potwierdzenie Codexa w R1 z EXIT=0 | E=R1 2026-08-12/13: ProjectCard 259, DashboardPage 153, useProjects 125, projects.py 431, snapshots.py 258, ProjectSnapshots 158, useSnapshots 40, schemas.py 99 · R2 2026-08-13: EditorPage 766, export_import 450, NewProjectModal 106, Badge 75 | poza=zmierzone są WYŁĄCZNIE bazy plików, NIE estymaty przyrostu (~250, ~330, ~230, ~165 LOC) — te są prognozą sprzed kodu i §5 nazywa je prognozą (LESSONS#17); pokryte przez checkpoint sizingu po napisaniu kodu w `/spec-impl` | werdykt=PASS
- CME: typ=MEASURED | dowod=find-praca-redaktor-2026-08-13 | C=§7 twierdzi, że wybór kanonu został zweryfikowany po treści na przebiegach Redaktora | M=find po katalogu FABRYKA-redaktor/redaktor/praca, EXIT=0 | E=R1 2026-08-13: 14 katalogów ewa-*, 24 katalogi boz-*, łącznie 109 plików input.md | poza=liczba katalogów NIE odtwarza zbioru porównanych rozdziałów (14 katalogów ewa-* wobec 12 rozdziałów kanonu Ewy), więc pokrycie 36/36 zostało z §7 USUNIĘTE zamiast podparte; proporcjonalne, bo §7 to wejście do ręcznej czynności właściciela, nie kryterium akceptacji żadnej fazy; kto chce oprzeć na tym decyzję, powtarza porównanie sha256 wg metody z pamięci project-kanoniczne-projekty-w-bazie | werdykt=PASS
- CME: typ=CONTRACTED | dowod=sha256-md-roundtrip-2026-08-11 | C=wybór dwóch projektów kanonicznych (d73dcc3b, 507b3ee4) jako AKTUALNA | M=pamięć project-kanoniczne-projekty-w-bazie, zapis z 2026-08-11 wykonany poza tym specem | mierzalne-od=md_exporter.chapter_to_markdown na projekcie z bazy plus porównanie sha256 NFC z input.md z przebiegów Redaktora, krok: przed sprzątaniem balastu | poza=ten spec NIE powtarza tego pomiaru i nie opiera na nim żadnej bramki ani kryterium akceptacji; proporcjonalne, bo §7 opisuje czynność właściciela wykonywaną ręcznie z backupem .tiolibri przed każdą kasacją; pokryte przez wymóg jawnego potwierdzenia właściciela dla 19c4a5fe (D4) | werdykt=PASS
- CME: typ=CONTRACTED | dowod=protokol-dowodu-§6 | C=§6 twierdzi, że CHECK, oba indeksy częściowe i oba warunki triggera prune są dowodliwe bez harnessu testowego | M=derywacja z kontraktu: SQLSTATE 23514/23505 dla naruszeń, `pg_get_functiondef` dla rewertu DDL, kanał `venv/bin/python` + klient z `.env` wykonany z EXIT=0 w R1 i R2 | mierzalne-od=kroki 1-9 §6.1 i 1-7 §6.2, krok: PHASE-1A i PHASE-2A impl (artefakty PROOF-1A.md, PROOF-2A-mutacja.md) | poza=w rundzie SPEC dowodu NIE ma i mieć nie może — CHECK, indeksy i przepisany trigger nie istnieją przed migracją (LESSONS#15); zweryfikowany jest wyłącznie KANAŁ wykonania i to, że obiekty docelowe są dziś nieobecne (rekord probe-db wyżej) | werdykt=PASS
