# R4 — preflight L5 (Opus), spec `porzadek-wersji` (Stadium A, master)

**Data:** 2026-08-13
**Runda generowana:** R4 (`spec: R3-opus-pending` → TARGET=4). Budżet liczony od nowa
po `reset-po-spike: R3`.
**Plik pod review:** `docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md` (v0.5 → **v0.5.1**)
**Kanał pomiaru:** kanał **S** ze speca — `POST https://api.supabase.com/v1/projects/klhnyagtobgtxnexdsls/database/query[/read-only]`,
autoryzacja PAT-em z `tiolibri-api/.env`, wołany z `tiolibri-api/venv/bin/python`.

**Bramka decyzji źródłowych:** `STATE.md` nie ma linii `decyzje-zrodlowe:`, a `TARGET>1` → PASS bez
blokady. Spec sprzed bramki decyzji źródłowych — test kierunku zrobił recenzent w R1; bramki nie
doklejam wstecz.

Zakres tej rundy jest inny niż w R1-R3. Spike (R3) zmierzył **właściwości** kanału (S1-S7). Ten
preflight mierzy **kształty, które wprowadziła dopiero v0.5** i których nikt nie uruchomił: blok
`DO … EXCEPTION … GET STACKED DIAGNOSTICS`, `json_agg` jako ostatnia instrukcja, oczekiwania
§6.1r wobec `pg_policies`, hash deklaracji triggera. Kod nie był dotykany (HEAD `5f25c62`,
`git status`: zmiany wyłącznie w `docs/` i `.DS_Store`/`.gitignore`).

## Fakty nośne

- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python docs/specs/porzadek-wersji/_review/.R4-probe-ksztalt.py (surowe wyjście: _review/.R4-probe-out.txt) | note=11 kroków P1-P11, KROKOW=11 PASS=11 FAIL=0, EXIT=0 — cały pomiar tego preflightu pochodzi z jednego biegu na żywej bazie, odczytowego albo zakończonego ROLLBACK-iem
- FACT: CORRECTED | kind=execution | source=tiolibri-api/venv/bin/python docs/specs/porzadek-wersji/_review/.R4-probe-selftest.py (EXIT=0, surowe wyjście: _review/.R4-selftest-out.txt) | note=stare=brak wierszy w odpowiedzi = `FAIL` nowe=`wynik` równy `NULL` albo brak klucza `wynik` = `FAIL`
- FACT: VERIFIED | kind=execution | source=krok P4 z .R4-probe-ksztalt.py: `select json_agg(_wynik) as wynik from _wynik` nad PUSTĄ tabelą, EXIT=0 | note=odpowiedź to `rows=1` z `wynik=None`, a nie zero wierszy — asercja licząca WIERSZE nie odróżnia pustego zbioru asercyjnego od zbioru pełnego, co jest dokładnie klasą LESSONS#18
- FACT: VERIFIED | kind=execution | source=krok P3 z .R4-probe-ksztalt.py: blok `DO … EXCEPTION … GET STACKED DIAGNOSTICS constraint_name` w `begin … rollback`, jedno wywołanie, EXIT=0 | note=zwraca parę `23514/pf_named_check` oraz kontrolę pozytywną `OK` w tym samym `json_agg` — kształt, na którym stoi CAŁE §6.1, jest wykonalny w kanale S i mieści się w jednym wywołaniu (S2)
- FACT: VERIFIED | kind=execution | source=krok P5 z .R4-probe-ksztalt.py: `pg_policies` dla `projects` z `cmd='UPDATE'`, endpoint read-only, EXIT=0 | note=DOKŁADNIE 1 polityka `Users can update own projects`, `PERMISSIVE`, `roles={public}`, `qual` ORAZ `with_check` = `(auth.uid() = user_id)` — oczekiwanie R1 z §6.1r trafione co do pola, łącznie z asercją na `with_check` dołożoną w 0.5
- FACT: VERIFIED | kind=execution | source=krok P6 z .R4-probe-ksztalt.py: `pg_policies` dla `project_snapshots`, endpoint read-only, EXIT=0 | note=istnieją WYŁĄCZNIE `INSERT` i `SELECT`, zero polityk `cmd='UPDATE'` — asercja „na braku" z kroku R4 §6.1r ma co mierzyć na ŻYWEJ bazie, nie tylko w pliku migracji
- FACT: VERIFIED | kind=execution | source=krok P7 z .R4-probe-ksztalt.py: `md5(pg_get_functiondef('public.prune_project_snapshots'::regproc))` + `pg_trigger`, endpoint read-only, EXIT=0 | note=hash `568fef8488179dc83f2e1d69622aaf9e` (32 znaki), `tgenabled='O'` — krok 1 §6.2 jest wykonalny i ma wartość odniesienia dla kroków 6 i 8
- FACT: VERIFIED | kind=execution | source=kroki P1 i P8 z .R4-probe-ksztalt.py, EXIT=0 | note=S1 odtworzone (wywołanie bez `User-Agent` → HTTP 403 z treścią `error code: 1010`) i S5 odtworzone (`create table` na `/query/read-only` → `25006`) — dwa bezpieczniki §6.0 działają dziś tak, jak opisał je spike
- FACT: VERIFIED | kind=execution | source=krok P10 z .R4-probe-ksztalt.py: `set local role authenticated` + `set_config('request.jwt.claims', …)` w `begin … rollback`, EXIT=0 | note=właściciel widzi 8 projektów, obcy uuid 0 — podstawianie tożsamości (S6) działa bez zdobywania JWT-ów, czyli §6.1r R2/R3/R5 ma czym mierzyć RLS
- FACT: VERIFIED | kind=execution | source=kroki P9 i P11 z .R4-probe-ksztalt.py, EXIT=0 | note=skład bazy bez zmian od spike'u: 12 projektów, 3 właścicieli, 31 snapshotów; postflight 0 śladów `RUN_ID` w `projects` — protokół pomiaru nie zostawił ani jednego trwałego wiersza
- FACT: VERIFIED | kind=execution | source=krok P2 z .R4-probe-ksztalt.py (pierwszy bieg asertował `st==200` i dał 6 kroków FAIL, EXIT=1; poprawiony na `st in (200,201)` → EXIT=0) | note=endpoint zwraca **HTTP 201**, nie 200 — §6.0a C2 mówi „HTTP 200/201", więc spec ma rację i korekty NIE wymaga; odnotowane, bo to jedyny realny wkład FAIL w tym biegu i on udowadnia, że asercje probe'a nie są dekoracją
- FACT: VERIFIED | kind=sizing | source=wc -l na 12 plikach cytowanych w §5 (ProjectCard.jsx, DashboardPage.jsx, useProjects.js, projects.py, snapshots.py, ProjectSnapshots.jsx, useSnapshots.js, schemas.py, EditorPage.jsx, export_import.py, NewProjectModal.jsx, Badge.jsx) | note=259/153/125/431/258/158/40/99/766/450/106/75 — 12 z 12 baz zgadza się z §5 co do jednej linii, kod nietknięty od R2; zero rozjazdów do skorygowania
- FACT: VERIFIED | kind=path-existing | source=test -f docs/specs/porzadek-wersji/_review/.R4-probe-ksztalt.py oraz .R4-probe-out.txt oraz .R4-probe-selftest.py oraz .R4-selftest-out.txt | note=reguła 5 z §6.0 („artefakt = surowe wyjście PLUS skrypt") zastosowana do samego preflightu — oba pomiary mają skrypt i wyjście obok siebie
- FACT: VERIFIED | kind=state-machine | source=docs/specs/porzadek-wersji/STATE.md:1-3 | note=`spec: R3-opus-pending` → TARGET=4, plik nazwany R4-opus-preflight.md; `reset-po-spike: R3` → `N_EFF` liczone od nowa, więc R4 NIE wchodzi w próg eskalacji; delta 0.5 → 0.5.1 ≠ 0, więc bramka „zakaz rundy potwierdzającej" nie dotyczy
- FACT: VERIFIED | kind=parser | source=awk U9 z /spec-health-check na SPEC-PORZADEK-WERSJI-MASTER.md (Krok 1 tego handoffu) | note=tabela zbiorcza §5 (10 faz × 7 osi) stoi nadal PRZED podsekcjami `###`, a edycje 0.5.1 dotknęły wyłącznie nagłówka i §6.0/§6.1 — layout, na którym U9 przestał być ślepy, jest nienaruszony
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/docs/migrations/20260421_spec1.sql:61-79 | note=`prune_project_snapshots()` (61) i `trg_prune_project_snapshots AFTER INSERT` (77) — nazwy z §6.2 zgadzają się z plikiem migracji ORAZ z żywą bazą (P7), czyli mutacja §6.2 celuje w byt, który istnieje przed fazą (LESSONS#15)
- FACT: VERIFIED | kind=path-new | source=docs/specs/porzadek-wersji/_review/R4-codex.md (rodzic `_review/` istnieje, plik jeszcze NIE) | note=miejsce docelowe review R4 wolne; `.base-R4.md` powstaje w Kroku 5 tego samego handoffu

## Rozstrzygnięcia Opusa PRZED handoffem (nie flagowane Codexowi)

1. **Asercja S4 była cichym false-PASS i została poprawiona, a nie zgłoszona.** To sprawa
   EGZEKWOWALNOŚCI bramki, więc nie idzie do Codexa jako pytanie. Wersja 0.5 mówiła w trzech
   miejscach „brak wierszy w odpowiedzi = `FAIL`". Pomiar (P4 + self-test niżej) pokazuje, że
   `json_agg` nad pustą tabelą zwraca **jeden wiersz z `wynik = null`** — więc bramka licząca
   wiersze przepuszcza dokładnie ten przypadek, przed którym miała bronić: blok `DO`, który nie
   wstawił do `_wynik` ani jednego wiersza (np. cała asercja została wycięta), zostałby odczytany
   jako „przeszło". Poprawka wpisana do mastera w trzech miejscach (tabela S4, reguła 3 w §6.0,
   zdanie pod blokiem SQL w §6.1), bump 0.5 → 0.5.1. Klasa: LESSONS#18.

2. **HTTP 201 NIE jest korektą speca.** Endpoint kanału S odpowiada `201` na `POST`, a §6.0a C2
   oczekuje „HTTP 200/201" — spec był ostrożniejszy niż mój pierwszy probe i to probe się mylił.
   Zostawiam bez zmian; odnotowane wyżej jako fakt, bo to jedyny wkład FAIL w tym biegu.

3. **Kotwice LOC nie wymagały żadnej korekty.** 12 z 12 baz sizingu zgadza się co do jednej linii —
   pierwsza runda tego specu bez ani jednego CORRECTED z klasy „stale reference" (LESSONS#20).

## Parser self-test

**Master nie deklaruje własnej bramki mechanicznej** — §6 to protokół dowodu wykonywany w
PHASE-0/1A/2A na obiektach, które te fazy dopiero tworzą (LESSONS#15: kryteria akceptacji, nie
bramki rundy spec). Dry-runowi podlegają więc dwie rzeczy, które ten plik REALNIE uruchamia.

### 1. Bramka S4 — kontrpróba do faktu CORRECTED

Skrypt: `_review/.R4-probe-selftest.py`, kanał S, endpoint `/read-only` (zero zapisów).
Dwa wkłady × dwie reguły, wszystko na żywej bazie:

```
WKLAD=FAIL REGULA=stara HTTP=201 rows=1 tresc=[{"wynik": null}]      EXPECT=PASS GOT=PASS RESULT=PASS
WKLAD=FAIL REGULA=nowa  HTTP=201 rows=1 tresc=[{"wynik": null}]      EXPECT=FAIL GOT=FAIL RESULT=PASS
WKLAD=PASS REGULA=stara HTTP=201 rows=1 tresc=[{"wynik": [{"x": 1}]}] EXPECT=PASS GOT=PASS RESULT=PASS
WKLAD=PASS REGULA=nowa  HTTP=201 rows=1 tresc=[{"wynik": [{"x": 1}]}] EXPECT=PASS GOT=PASS RESULT=PASS
BLEDOW=0
EXIT=0
```

Czyta się to tak: **wkład FAIL przechodzi przez starą regułę i wywraca się na nowej.** To jest
realny wkład FAIL, nie deklaracja — i **koliduje z dozwolonym wzorcem** (LESSONS#13), bo pusty
zbiór asercyjny jest odpowiedzią *tego samego kształtu* co zbiór pełny (`rows=1`, klucz `wynik`
obecny), różniącą się wyłącznie zawartością. Kontrpróba innego kształtu (np. odpowiedź bez klucza)
niczego by tu nie obaliła, bo stara reguła i tak by ją odrzuciła.

### 2. Protokół §6.1 — czy asercje probe'a w ogóle potrafią sczerwienić

Skrypt: `_review/.R4-probe-ksztalt.py`, wyjście `_review/.R4-probe-out.txt`.

- **Wkład FAIL** (pierwszy bieg, asercja `st == 200`): 6 z 11 kroków `RESULT=FAIL`, `EXIT=1` —
  bo endpoint zwraca `201`. Bieg zatrzymał się na tym i nie zaraportował żadnego pomiaru.
- **Wkład PASS** (bieg po poprawieniu asercji na `st in (200, 201)`):
  `EXIT=0` (`KROKOW=11 PASS=11 FAIL=0`).

Krok P3 niesie własną kontrolę pozytywną w tym samym `json_agg` (wiersz `B: legalny zapis
przechodzi = OK`), więc `FAIL` na kroku A nie może się schować za awarią połączenia.

## Audyt C/M/E

Kanon `docs/specs/spec-workflow/CME-MANIFEST.md` **nie istnieje** ani w tym repo, ani w kopii
kanonicznej w FABRYCE (`ls` na `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`
→ brak pliku). Zgodnie z regułą 1 („kanon przed egzekucją") audyt nie jest tu blokerem werdyktu;
bramka strukturalna preflightu obowiązuje i rekordy są wypełnione normalnie.

- CME: typ=MEASURED | dowod=probe-ksztaltow-v05-2026-08-13 | C=§6.0 tabela S1-S7 i §6.0a C1-C7 twierdzą, że kanał S ma zmierzone właściwości; §6.1 twierdzi, że blok `DO … EXCEPTION … GET STACKED DIAGNOSTICS constraint_name` z `json_agg` jako ostatnią instrukcją jest wykonalny w JEDNYM wywołaniu; §6.1r R1/R4 twierdzą, ile polityk zobaczą w `pg_policies`; §6.2 krok 1 twierdzi, że `md5(pg_get_functiondef(…))` i `tgenabled` są czytelne | M=`_review/.R4-probe-ksztalt.py`, 11 kroków P1-P11, surowe wyjście w `_review/.R4-probe-out.txt` | E=R3 2026-08-13 (spike, `_review/.R3-probe2-kanal.py` + `.R3-probe3-rls.py`): S1-S7 zmierzone, EXIT=0 · R4 2026-08-13: P1 403/`1010` · P2 HTTP 201 `current_user=postgres` · P3 `23514/pf_named_check` + kontrola pozytywna OK · P4 `rows=1 wynik=None` · P5 1 polityka UPDATE z `qual`+`with_check` · P6 `{INSERT, SELECT}`, 0 UPDATE · P7 `568fef8488179dc83f2e1d69622aaf9e`, `tgenabled=O` · P8 `25006` · P9 12 projektów/3 właścicieli · P10 właściciel 8, obcy 0 · P11 0 śladów RUN_ID, total=12 · KROKOW=11 PASS=11 FAIL=0 EXIT=0 (pierwszy bieg: 6 FAIL, EXIT=1, asercja `st==200`) | poza=P3 mierzy blok `DO` na constraincie ZAŁOŻONYM przez probe (`pf_named_check`) w rolniętej transakcji, NIE na CHECK-ach z §3.1 — te nie istnieją przed migracją; zmierzona jest więc WYKONALNOŚĆ kształtu, nie treść bramek §6.1 krok 2-7; proporcjonalne, bo treść bramek jest kryterium akceptacji PHASE-1A-db (LESSONS#15), a artefaktem będzie `PROOF-1A-db.md`; poza dowodem zostaje też kanał H (§6.1a/§6.1b) — nieuruchamiany w tej rundzie, pokryty smoke-testem §6.0a i fazą PHASE-0-kanal | werdykt=PASS
- CME: typ=MEASURED | dowod=selftest-bramki-S4-2026-08-13 | C=§6.0 reguła 3 i tabela S4 oraz zdanie pod blokiem SQL §6.1 twierdzą, przy jakiej odpowiedzi kanału bramka ma powiedzieć `FAIL` | M=`_review/.R4-probe-selftest.py` — macierz 2 wkłady (pusty/niepusty `json_agg`) × 2 reguły (brzmienie 0.5 i 0.5.1), surowe wyjście w `_review/.R4-selftest-out.txt` | E=R4 2026-08-13: wkład pusty → `rows=1`, `[{"wynik": null}]`; reguła 0.5 GOT=PASS (false-PASS), reguła 0.5.1 GOT=FAIL · wkład niepusty → `[{"wynik": [{"x": 1}]}]`; obie reguły GOT=PASS · BLEDOW=0, EXIT=0 | poza=mierzone jest zachowanie REGUŁY na odpowiedzi kanału, NIE to, że przyszłe skrypty dowodowe §6 poprawnie ją zaimplementują — to kryterium akceptacji PHASE-0-kanal (§6.0a) i każdego artefaktu `PROOF-*.md`; proporcjonalne, bo spec zapisuje regułę, a nie kod, który ją stosuje | werdykt=PASS
- CME: typ=MEASURED | dowod=wc-l-sizing | C=§5 twierdzi, że estymaty 10 faz stoją na zmierzonych bazach 12 plików | M=`wc -l` na 12 plikach z §5 — preflighty R1 (8 plików), R2 (4 pliki), R4 (wszystkie 12 ponownie) | E=R1 2026-08-12/13: ProjectCard 259, DashboardPage 153, useProjects 125, projects.py 431, snapshots.py 258, ProjectSnapshots 158, useSnapshots 40, schemas.py 99 · R2 2026-08-13: EditorPage 766, export_import 450, NewProjectModal 106, Badge 75 · R3 2026-08-13: nie mierzone ponownie (kod nietknięty) · R4 2026-08-13: wszystkie 12 zmierzone jednym `wc -l`, 12/12 zgodne z §5 co do linii | poza=zmierzone są WYŁĄCZNIE bazy plików, NIE estymaty przyrostu — te są prognozą sprzed kodu i §5 nazywa je prognozą (LESSONS#17); pokryte przez checkpoint sizingu po napisaniu kodu w `/spec-impl` | werdykt=PASS
- CME: typ=CONTRACTED | dowod=protokol-dowodu-§6 | C=§6 twierdzi, że CHECK-i, oba indeksy częściowe, polityki RLS, kontrakt importu i oba warunki triggera prune są dowodliwe bez harnessu testowego | M=derywacja z kontraktu: `23514`+`constraint_name` dla naruszeń CHECK, `23505` dla indeksów, `pg_policies` dla polityk, `md5(pg_get_functiondef)` dla rewertu DDL, transakcyjność DDL w Postgresie dla izolacji mutanta; wykonalność KAŻDEGO z tych kształtów zmierzona w rekordzie probe-ksztaltow-v05 | mierzalne-od=kroki 1-10 i R1-R5 §6.1, I1-I6 §6.1b, kroki 1-10 §6.2, krok: PHASE-0-kanal (§6.0a), PHASE-1A-db, PHASE-1A-api, PHASE-1A-import, PHASE-2A-db (artefakty PROOF-*.md) | poza=w rundzie SPEC dowodu treści NIE ma i mieć nie może — CHECK-i, indeksy, zawężona polityka INSERT i przepisany trigger nie istnieją przed migracją (LESSONS#15); zweryfikowane są wyłącznie nieobecność obiektów docelowych, nazwy obiektów istniejących i WYKONALNOŚĆ kanału oraz kształtów | werdykt=PASS
- CME: typ=CONTRACTED | dowod=sha256-md-roundtrip-2026-08-11 | C=wybór dwóch projektów kanonicznych (d73dcc3b, 507b3ee4) jako AKTUALNA | M=pamięć project-kanoniczne-projekty-w-bazie, zapis z 2026-08-11 wykonany poza tym specem | mierzalne-od=md_exporter.chapter_to_markdown na projekcie z bazy plus porównanie sha256 NFC z input.md z przebiegów Redaktora, krok: przed sprzątaniem balastu | poza=ten spec NIE powtarza tego pomiaru i nie opiera na nim żadnej bramki; proporcjonalne, bo §7 opisuje czynność właściciela wykonywaną ręcznie wg protokołu §7.1 z backupem i wierszem w SPRZATANIE-LOG.md przed każdą kasacją; pokryte dodatkowo przez wymóg oględzin `19c4a5fe` (D4) | werdykt=PASS
