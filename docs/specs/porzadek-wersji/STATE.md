spec: R4-codex-pending (2026-08-13)
impl: not-started
reset-po-spike: R3

---

## Decyzja właściciela — 2026-08-13

**KONTYNUUJ.** Pauza z 12.08 zamknięta, plan faz z mastera §4 potwierdzony bez zmian
(1A → 1B → sprzątanie balastu → warunkowa decyzja o PHASE-3).

Master zbumpowany 0.1 → 0.2 na preflighcie L5 (`_review/R1-opus-preflight.md`):
3 fakty CORRECTED (liczba snapshotów, select w `list_snapshots`, pokrycie listy §7)
+ domknięcie kontraktu triggera prune + uzupełnienie §7 do pełnych 12 projektów.

Kod i baza NADAL NIETKNIĘTE — powstały wyłącznie dokumenty.

**Wznowienie:** czekamy na `_review/R1-codex.md`, potem `/spec-apply-review porzadek-wersji`.

---

## R1 przerobione — 2026-08-13

Codex: **REQUEST_CHANGES**, 8 BLOCKER + 1 MAJOR. **9/9 uwag ZAAKCEPTOWANE** — wszystkie fakty
mechaniczne Codexa zweryfikowane niezależnie w kodzie i potwierdzone co do jednej.
Odpowiedź: `_review/R1-opus-response.md`. Master **0.2 → 0.3** (delta 607 linii wobec `.base-R1.md`).

Decyzje właściciela D1-D4 (master §8): `book` zostaje z własną funkcją · twardy inwariant jednej
`AKTUALNA` w bazie (DWA indeksy częściowe) · backup i snapshot zapisują metadane, restore ich nie
cofa · `19c4a5fe` do oględzin przed kasacją.

Budżet rund: `N=1`, `rundy-rdzenia=0`, `reset-po-spike=0` → `N_EFF=1 < MAX_ROUNDS=3` (Risk HIGH).
Bramka 4a (zakaz rundy potwierdzającej): delta ≠ 0 → NIE dotyczy. STOP-and-SPIKE: N=1 → NIE dotyczy.
L-C: 8×[P], 1×[A] → uwagi PRODUKT dominują, runda R2 uzasadniona.

**Wznowienie R2:** `/spec-handoff porzadek-wersji` (TARGET=R2 wylicza sam handoff).

---

## R2 wysłane do Codexa — 2026-08-13

Preflight L5: `_review/R2-opus-preflight.md` — 26 faktów (6 CORRECTED, 0 BLOCKED), audyt C/M/E
5 rekordów, parser self-test z realnym wkładem FAIL. Master **0.3 → 0.3.1**.

Ustalenie preflightu, które zmieniło strukturę speca: bramka **U9 health-checku była ślepa** na §5
(wszystkie tabele sizingu pod `###`, parser kończy sekcję na pierwszym podnagłówku → `rows=0`,
vacuous PASS — LESSONS#18). Dołożona tabela zbiorcza 5 faz × 7 osi przed podsekcjami:
`rows=5 viol=0`, kontrpróba `Pliki=9 > 8` daje `SIZING-FAIL EXIT=1`.

Baseline pomiaru NITS-EXT: `_review/.base-R2.md` (678 linii).

Kontekst „skąd to się wzięło": `HANDOFF-porzadek-wersji-projektow.md` w korzeniu repo.
⚠️ Jego „NASTĘPNY KROK: /spec-fill" jest BŁĘDNY wobec kanonu — `/spec-fill` to etap
Stadium B (wymaga fazy + sondażu R0). Ze `spec: master-draft` idzie się `/spec-handoff`.

---

## R2 przerobione — 2026-08-13

Codex: **REQUEST_CHANGES**, 8 BLOCKER + 3 MAJOR + 1 OBSERVATION + 1 MINOR.
**11/11 uwag merytorycznych ZAAKCEPTOWANE.** Odpowiedź: `_review/R2-opus-response.md`.
Master **0.3.1 → 0.4**.

Rdzeń rundy: CHECK `book = btrim(book)` nie egzekwował kanonizacji (podwojna spacja w srodku →
dwa klucze `lower(book)` → dwie AKTUALNA); dowod mutacyjny triggera kazal podmienic funkcje
WSPOLNA dla wszystkich projektow na zywej bazie — przepisany na jedna transakcje z ROLLBACK.

Bramki: STOP-and-SPIKE **nie dotyczy** (R2 atakuje warstwe nizej niz R1, LESSONS#21 pkt 5;
8/11 uwag na powierzchni powstalej dopiero w v0.3). Zakaz rundy potwierdzajacej **nie dotyczy**
(delta != 0). Risk **HIGH bez zmian**, stempel `plan faz: 5` → `plan faz: 8`.

Budzet: `N=2`, `rundy-rdzenia=0`, `reset-po-spike=0` → `N_EFF=2 < MAX_ROUNDS=3`.
L-C: 8x[P], 4x[A], 1x[D] → PRODUKT dominuje, runda R3 uzasadniona.

**Plan faz 5 → 8** (ciecie po granicy domen, nie nowy zakres): `1A-db`/`1A-api`,
`1B-karta`/`1B-dashboard`, `2A-db`/`2A-api`, `2B`, `3`. Najwyzsze wykorzystanie osi czasu 78%.

**Nowe decyzje wlasciciela do potwierdzenia (weto jedna linia):**
- **D5** — restore snapshotu staje sie **owner-only** (dzis przepuszcza udzialowca). Jedyna
  decyzja mastera, ktora ZABIERA istniejaca mozliwosc.
- **D6** — przypiecie snapshotu bez nazwy dostaje **nazwe zastepcza z serwera**, nie odmowe.

**Wznowienie R3:** `/spec-handoff porzadek-wersji` (TARGET=R3 wylicza sam handoff).

---

## R3 wyslane do Codexa — 2026-08-13

Preflight L5: `_review/R3-opus-preflight.md` — 22 fakty (4 CORRECTED, 0 BLOCKED), audyt C/M/E
5 rekordow, parser self-test U9 z realnym wkladem FAIL (`rows=8 viol=1`, EXIT=1). Master **0.4 → 0.4.1**.

Ustalenie preflightu, ktore zmienilo strukture speca: **deklarowany kanal dowodu nie wykonywal
polowy wlasnego protokolu**. §6.0 mowila „kazdy krok §6.1 i §6.2 wykonuje skrypt `venv/bin/python`",
a §6.1 R1/R4 pyta `pg_policies` i cale §6.2 wymaga BEGIN/DISABLE TRIGGER/CREATE OR REPLACE/ROLLBACK.
Zmierzone (`probe_r3.py`, EXIT=0): PostgREST → `PGRST205` na `pg_policies`, `PGRST202` na cztery
kandydatury funkcji SQL; brak `psql`; venv bez psycopg2/asyncpg; `.env` bez URL-a polaczenia.
§6.0 dostala DWA nazwane kanaly (A: skrypt asercyjny; B: Supabase SQL Editor — ten sam, ktorym
repo stosuje migracje, `20260421_spec1.sql:3`) z wiazacym przypisaniem krokow (LESSONS#15).

Dwie dalsze poprawki egzekwowalnosci: §6.2 liczy `md5(pg_get_functiondef(...))` POZA transakcja
(ROLLBACK skasowalby wartosc odniesienia razem z mutantem) oraz fixture dostal kolumny NOT NULL
(`snapshot='{}'::jsonb`, `triggered_by='auto'`). §1 odzyskal wycofane twierdzenie: **31 z 31
snapshotow ma `triggered_by='auto'`** — jako pomiar z data, bez bramki.

Baseline pomiaru NITS-EXT: `_review/.base-R3.md` (1129 linii).

Budzet: `N=3` po tej rundzie → `N_EFF=3 = MAX_ROUNDS`. **To ostatnia runda przed progiem eskalacji.**

---

## R3 przerobione — 2026-08-13 — **ESCALATED: STOP-and-SPIKE**

Codex: **REQUEST_CHANGES**, 8 BLOCKER + 1 MINOR + 1 OBSERVATION. **10/10 uwag ZAAKCEPTOWANE**,
wszystkie fakty mechaniczne zweryfikowane niezaleznie w zrodle. Odpowiedz: `_review/R3-opus-response.md`.

**Master NIE zbumpowany — tresc merytoryczna zamrozona na v0.4.1** (zmieniona wylacznie linia
`**Status:**`). Powod: 5 z 10 uwag to ten sam rdzen (protokol dowodu §6), a przepisanie go po raz
TRZECI bez ustalenia realnego kanalu utrwalioby wariant, ktory juz dwa razy przegral. Uwagi
produktowe (#4 sizing, #5 `pinned`→`label`, #7 dowod importu) sa z §6 sprzezone — kazda dokłada
krok dowodowy albo przelicza sizing. Kierunki naprawy 10/10 sa zapisane w odpowiedzi.

**STOP-and-SPIKE:** rdzen — **wykonalny dowod §6: bramka SQL/RLS z realnym kodem wyjscia w kanale,
ktory na tej maszynie istnieje**. Pada 3x z rzedu: R1 #8 (brak kontraktu dowodu), R2 #6/#7
(niebezpieczny na zywej bazie, brak funkcji PASS/FAIL), R3 #1/#2/#3 (kanal B = recznie wpisany
`EXIT`; krok 8 §6.2 niewykonalny po `ROLLBACK`; `DISABLE TRIGGER` blokuje zapisy produkcyjne;
kanal A bez tozsamosci).

Budzet: `N=3`, `rundy-rdzenia=0`, `reset-po-spike=0` → `N_EFF=3 = MAX_ROUNDS=3` (Risk HIGH).
**Convergence-ext NIE przyznane** — warunek „blokery maleja" niespelniony: 8 → 8 → 8 blokerow
przy specu rosnacym 678 → 1129 linii. Bramka 4a: delta prozy wobec `.base-R3.md` = 0.
L-C: 3x[P], 6x[A], 1x[D].

**Brief dla arbitra (D13):** `_review/FABLE-BRIEF-R3.md` — pytanie brzmi, czy przy Risk HIGH
owner-attested transcript z SQL Editora jest dowodem, czy trzeba zdobyc kanal (spike), czy zle
jest samo WYMAGANIE.

**Kod i baza NADAL NIETKNIETE.**

**Wznowienie — trzy legalne wyjscia (decyzja wlasciciela):**
1. `/spec-greenlight porzadek-wersji spec --reason "..."` — do GREEN mimo uwag
2. spike SZEROKI (zakres w `R3-opus-response.md`, sekcja „Co ma rozstrzygnac spike") → po WYKONANIU
   dopisz `reset-po-spike: R3`, `spec:` wraca na `R3-opus-pending`, potem `/spec-handoff porzadek-wersji`
3. reset zakresu speca — zmiana STATE.md

---

## SPIKE — czesc 1 wykonana, 2026-08-13 — **decyzja wlasciciela: SPIKE, kanal = Supabase MCP**

Zapis: `_review/SPIKE-R3-kanal.md`.

Zmierzone 4 kandydatury kanalu. **Znaleziony:** konektor **Supabase MCP** (`execute_sql`,
`apply_migration`, `list_tables`) — wykonuje SQL programowo i **zwraca wynik**, wiec asercja moze
sama liczyc PASS/FAIL. To znosi podstawe R3 #1 (recznie wpisany `EXIT`), #2 (fixture ginie
z `ROLLBACK`-iem) i wieksza czesc #3 (`DISABLE TRIGGER` trzymany przez recznà sesje SQL Editora).

**Zablokowane na autoryzacji — TRZY tozsamosci, zadna nie widzi TIOLIBRI:** konektor MCP siedzi
na orgu `ncpycfjugfxbbiqbefco` (`QuoteFLOW`, `fabryka`); `supabase` CLI **jest zalogowane**, ale
na orgu `hcwydriuwapyzxugxgrv` (`xperthub`, `tavlo`); baza TIOLIBRI to ref **`klhnyagtobgtxnexdsls`**
— gdzie indziej. `.env` **nie ma** `DATABASE_URL` ani hasla DB, `psql` brak.

**Uscislenie kanalu (po pytaniu wlasciciela „a przez CLI?"):** samo CLI by nie wystarczylo — 2.75
nie ma `db execute`/`db query`, a `push`/`dump` chca hasla do bazy. Kanalem jest **Management API
`POST /v1/projects/{ref}/database/query`** (to samo, co MCP wola pod spodem), autoryzowane
**samym Personal Access Tokenem**, bez hasla DB — wolalne z Pythona, czyli **kanal A z §6.0
doslownie tak, jak spec go definiuje**. Wklad wlasciciela zmienia sie z autoryzacji konektora
na **jeden PAT** (przez `SUPABASE_ACCESS_TOKEN`, zeby nie nadpisac zalogowania CLI na tavlo).
Trop na pytanie o transakcje: **temporary access (JIT)** pozwala uzyc PAT jako hasla roli Postgresa
→ prawdziwe `BEGIN`/`ROLLBACK` przez `psql`/pooler (wymaga PG >= 17.6.1.081).

**Spike NIE jest domkniety** — czesc 2 (po autoryzacji) ma odpowiedziec, czy `execute_sql` trzyma
`BEGIN`/`ROLLBACK` miedzy wywolaniami (jesli nie — §6.2 wymaga PRZEPROJEKTOWANIA, nie przepisania),
czy widac `pg_policies`, i skad wziac JWT wlasciciela i udzialowca do asercji RLS.

Dlatego: `spec:` **zostaje ESCALATED**, `reset-po-spike` **nie dopisany**, master **zamrozony
na v0.4.1**. Bumpy naleza sie dopiero po czesci 2.

**Kod i baza NADAL NIETKNIETE.**

---

## SPIKE DOMKNIETY — 2026-08-13 — **kanal zdobyty, `spec:` → R3-opus-pending**

Wlasciciel dostarczyl Personal Access Token (`tiolibri-api/.env`, `SUPABASE_ACCESS_TOKEN`).
Konto okazalo sie **czwarte**: widzi `klhnyagtobgtxnexdsls` (TIOLIBRI, ACTIVE_HEALTHY, pg 17.6.1.063)
i `hcmeofmaedhlmdotviyh`. Pomiar: `_review/.R3-probe2-kanal.py` + `_review/.R3-probe3-rls.py`,
pelny zapis w `_review/SPIKE-R3-kanal.md`.

**Kanal: Management API `POST /v1/projects/{ref}/database/query`**, autoryzacja samym PAT-em,
`current_user = postgres`. Pulapka wejsciowa: Cloudflare odrzuca `urllib` (HTTP 403 `error code: 1010`)
— **konieczny naglowek `User-Agent`**; to musi trafic do §6.0.

**Zmierzone, wiazace dla przepisania §6:**
- sesja **NIE trwa** miedzy wywolaniami (`pg_backend_pid` 547415 vs 547416; temp table ginie)
- ale **jedno wywolanie unosi caly `BEGIN..ROLLBACK`** i zwraca `SELECT` sprzed rollbacku
  (`{'widziane_przed_rollback': 3}`) → protokol musi byc pisany jako **transakcja w jednym wywolaniu**
- `pg_policies` **widoczne** (23 polityki) — tam, gdzie PostgREST dawal `PGRST205`
- `/database/query/read-only` dziala i odmawia zapisu (`25006`) — realny bezpiecznik
- `md5(pg_get_functiondef(...))` i `pg_trigger` czytelne → §6.2 mierzalne
- **RLS bez zdobywania JWT-ow**: `set local role authenticated` + `set_config('request.jwt.claims',…)`
  → wlasciciel widzi 8, obcy 0, `anon` 0, asercja zwraca doslowne `PASS`

**Skutek dla uwag R3:** #1 i #2 **znikaja**. #3 **maleje, nie znika** — okno `DISABLE TRIGGER`
skraca sie z sesji czlowieka do jednego wywolania, ale lock nadal idzie na zywa baze.

**Ograniczenie, ktore zostaje:** temporary access (JIT) **niedostepny** — wymaga PG >= 17.6.1.081,
TIOLIBRI ma 17.6.1.063. Wielowywolaniowej sesji `psql` nie bedzie bez upgrade'u.

Przy okazji do §7: 12 projektow ma **trzech** wlascicieli — `a4aee672…` (8), `f521bd58…` (2),
`0079c43d…` (2).

**Master NADAL zamrozony na v0.4.1.** Przepisanie §6 to nastepny krok, nie ten.
**Kod i baza NIETKNIETE** — pomiar byl odczytowy albo konczyl sie `ROLLBACK`-iem.

**Wznowienie:** przepisac §6 pod zmierzony kanal + doniesc pozostale 7 uwag R3 z
`_review/R3-opus-response.md`, bump mastera 0.4.1 → 0.5, potem `/spec-handoff porzadek-wersji`
(TARGET=R4, budzet po `reset-po-spike: R3` → `N_EFF` liczone od nowa).

---

## §6 PRZEPISANA — 2026-08-13 — master **0.4.1 → 0.5**, 10/10 uwag R3 domkniete

Pierwszy bump od R3. Tresc merytoryczna odmrozona, bo spike dostarczyl to, czego brakowalo:
**zmierzony kanal**. §6 napisana RAZ, pod pomiar, nie pod zalozenie.

**Rdzen (uwagi #1, #2, #3, #6, #7 — piec razy ten sam protokol):**
- kanal „owner-attested SQL Editor" **zniesiony w calosci** — zaden krok §6 nie ma juz linii
  wpisywanej recznie; `EXIT` liczy proces (#1)
- §6.0 dostala siedem **zmierzonych** wlasciwosci kanalu S (S1-S7) z wiazacym skutkiem dla ksztaltu
  protokolu: `User-Agent` (Cloudflare 1010), sesja nie trwa → bramka w JEDNYM wywolaniu, wynik
  wraca z ostatniej instrukcji zwracajacej wiersze (brak wierszy = FAIL), `/read-only` jako
  bezpiecznik, `current_user=postgres` → RLS trzeba przestawic jawnie, JIT niedostepny (17.6.1.063)
- §6.1 przepisana na blok `DO` z `EXCEPTION` + `GET STACKED DIAGNOSTICS` → asercja na parze
  `sqlstate` + **`constraint_name`**, nie na samym kodzie bledu
- **kanal H nazwany i zmierzony** (uvicorn :8000, GoTrue admin zaklada i **kasuje** tozsamosc
  testowa, pulapka `hashed_token` na top-levelu) — koniec zgadywania tozsamosci (#3)
- §6.1r: R1 **asertuje `with_check`** (dopuszczajac NULL jako legalny), doszedl **R5** — wykonawcza
  kontrproba `UPDATE … SET user_id=<obcy>` → `42501` (#6)
- §6.1b: import z 3 archiwow → **6**, pelne pokrycie pieciu rozstrzygniec §3.6.1 (#7)

**§6.2 — `DISABLE TRIGGER` USUNIETY z protokolu.** To bylo pytanie zostawione otwarte przez spike.
Odpowiedz: fixture (15 nieprzypietych + 1 przypiety NAJNOWSZY) buduje sie przy **aktywnym** triggerze,
bo po migracji retencja liczy limit wylacznie z `pinned=false`. Transakcja bierze juz tylko
`ROW EXCLUSIVE` → **zero blokad zapisow produkcyjnych**. Krok 6 mierzy rewert hashem wewnatrz
transakcji (zamiast „przywrocenia deklaracji z hasha", ktore bylo niewykonalne), krok 10 to swiezy
fixture w nowej transakcji (zamiast postflightu na projekcie, ktory juz nie istnial).

**Produktowe:** CHECK `snapshots_pin_named` + krok dowodowy 9 (#5) · §9.5 panel snapshotow read-only
dla udzialu, kontrolki NIE ISTNIEJA zamiast byc wyszarzone (#8) · §3.2 zawezone do writerow **nowych
pol** z pomiarem 10 trafien w 4 plikach (#9) · §6.0 regula 5: artefakt = surowe wyjscie **plus**
skrypt (#10).

**Sizing (#4): plan faz 8 → 10.** Skrypty dowodowe policzone we wszystkich fazach, ktore ich wymagaja.
Wydzielone: **PHASE-0-kanal** (bootstrap kanalu, LESSONS#7 — moduly wspolne dla 4 faz, wlasny
smoke-test §6.0a) i **PHASE-1A-import** (6 archiwow to osobny skrypt). Najwyzsze wykorzystanie osi
czasu **78%**, wszystkie 7 osi PASS.

**Kod i baza NIETKNIETE.** Delta: master 1131 → ~1420 linii wobec `.base-R3.md`.

**Wznowienie:** `/spec-handoff porzadek-wersji` (TARGET=R4; `spec: R3-opus-pending` jest legalnym
wejsciem tej komendy — `SPEC-WORKFLOW-MASTER.md:329`). Budzet po `reset-po-spike: R3` liczy sie
od nowa. ⚠️ Wlasciciel zaplanowal Fable 5 po R3 — `_review/FABLE-BRIEF-R3.md` jest **nieaktualny**
(pytal o kanal, ktory sie znalazl); przed arbitrem trzeba go przepisac pod nowe pytanie.
