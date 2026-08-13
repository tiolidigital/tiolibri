# R1 — preflight L5 (Opus), spec `porzadek-wersji` (Stadium A, master)

**Data:** 2026-08-13
**Runda generowana:** R1 (`spec: master-draft` → TARGET=1)
**Plik pod review:** `docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md` (v0.2)
**Odczyt bazy:** `tiolibri-api/venv/bin/python` + klient z `tiolibri-api/.env`
(TIOLIBRI nie jest w koncie Supabase pod MCP — kanał jak w handoffie).

## Fakty nośne

- FACT: VERIFIED | kind=sizing | source=wc -l na 8 plikach z §5 | note=wszystkie 8 zadeklarowanych LOC zgadzają się co do linii (ProjectCard 259, DashboardPage 153, useProjects 125, projects.py 431, snapshots.py 258, ProjectSnapshots 158, useSnapshots 40, schemas.py 99)
- FACT: VERIFIED | kind=path-existing | source=tiolibri-frontend/src/features/projects/NewProjectModal.jsx | note=plik cytowany w §5 jako 4. plik PHASE-1B istnieje; katalog projects/ ma dokładnie 4 pliki i nie ma w nim żadnego Dashboard.jsx (stale-ref z handoffu potwierdzony jako nieaktualny)
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/projects/useProjects.js:62-75 | note=updateProject dokładnie w tym zakresie; supabase-js .update().eq().select().single() — pułapka supabase-py z §3.5 faktycznie NIE dotyczy tej ścieżki
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/projects/useProjects.js:77-87 | note=deleteProject to gołe supabase.from('projects').delete().eq('id') bez endpointu API — twierdzenie §3.5 o twardym DELETE z przeglądarki potwierdzone
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/models/schemas.py:75 | note=class Project(BaseModel) stoi w linii 75; pola to id/user_id/title/author/language/status/style_preset/custom_styles/created_at/updated_at — brak note/role/book
- FACT: VERIFIED | kind=export | source=tiolibri-api/app/routers/projects.py:72 | note=@router.get("/{project_id}", response_model=Project) — mechanizm cichego ucinania pól z §3.2 potwierdzony u źródła
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/projects.py:98-99 | note=@router.post("/{project_id}/duplicate") + async def duplicate_project — miejsce wpięcia reguły z §3.3 zgadza się
- FACT: CORRECTED | kind=anchor | source=tiolibri-api/app/routers/snapshots.py:37-41 | note=stare=zwraca `triggered_by` i `created_at` (kotwica 36-41) nowe=zwraca `id, project_id, triggered_by, created_at` (brak pola nazwy)
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/export_import.py:169-176 | note=zapytanie o chapters z select processed_html i is_("deleted_at","null") stoi dokładnie w tym zakresie
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/projects/ProjectCard.jsx:96-106 | note=przycisk "Eksportuj backup (.tiolibri)" dokładnie 96-106 — bezpieczna ścieżka sprzątania z §3.5 realnie istnieje w kebabie
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/docs/migrations/20260421_spec1.sql:61-79 | note=funkcja prune_project_snapshots 61-74 plus trigger AFTER INSERT FOR EACH ROW 76-79; keep-set to ORDER BY created_at DESC LIMIT 15 bez jakiegokolwiek warunku pinned
- FACT: VERIFIED | kind=arg | source=tiolibri-api/app/main.py:35-37 | note=export_import(35) przed snapshots(36) przed projects(37) — kolejność rejestracji z §3.5 zgodna ze stanem repo
- FACT: CORRECTED | kind=execution | source=venv/bin/python scratchpad/probe.py EXIT=0 | note=stare=30 sztuk w bazie: Ewa 4.0 — 9, Bożena 507b3ee4 — 10 nowe=31 snapshotów, pomiar 2026-08-13: Ewa 4.0 — 10, Bożena 507b3ee4 — 10
- FACT: VERIFIED | kind=execution | source=venv/bin/python scratchpad/probe2.py EXIT=0 | note=tabela projects nie ma kolumn note/role/book ani deleted_at (kolumny realne: author, cover_image_url, created_at, custom_styles, id, language, status, style_preset, title, typography_settings, updated_at, user_id) — migracja z §3.1 jest faktycznie nowa, a brak "cofnij" z §3.5 potwierdzony
- FACT: VERIFIED | kind=execution | source=venv/bin/python scratchpad/probe.py EXIT=0 | note=tabela project_snapshots ma wyłącznie created_at/id/project_id/snapshot/triggered_by — brak label i pinned, więc obie kolumny z §3.4 są nowe; projektów w bazie 12
- FACT: CORRECTED | kind=execution | source=venv/bin/python scratchpad/probe3.py EXIT=0 | note=stare=Do backupu i usunięcia (8) nowe=Do backupu i usunięcia (10 z 12 — komplet)

## Rozstrzygnięcia Opusa PRZED handoffem (nie flagowane Codexowi)

Zgodnie z regułą „sporne kwestie egzekwowalności Opus rozstrzyga przed handoffem" — dwie
rzeczy rozstrzygnięte w masterze v0.2, nie zostawione recenzentowi jako pytanie:

1. **Kontrakt triggera prune był samosprzeczny.** v0.1 mówiła tylko „prune liczy limit 15
   wyłącznie z `pinned = false`". Przy literalnym wdrożeniu (zmiana samego podzapytania
   keep-set, `DELETE` nietknięty) przypięte snapshoty wypadają ze zbioru do zachowania
   i trigger kasuje dokładnie te, które mają żyć wiecznie — odwrotność celu fazy, na danych
   właściciela, bez ścieżki cofnięcia. v0.2 wymaga OBU warunków naraz plus testu mutacyjnego
   na gałęzi `DELETE` (LESSONS#6/#21: mutacja deklaracji, nie guardu). To domknięcie już
   podjętej decyzji („przypięty żyje wiecznie"), nie nowa decyzja architektoniczna.

2. **Zbiór do sprzątania nie pokrywał bazy.** v0.1 dawała 2 kanoniczne + 8 do usunięcia = 10
   przy 12 projektach; `72609fef` i `19c4a5fe` nie miały żadnej klasyfikacji. v0.2 domyka
   listę do 12 z jawnym zastrzeżeniem, że kasacja `19c4a5fe` wymaga „tak" właściciela
   (nie ma go w żadnym wcześniejszym zapisie) — klasyfikacja to fakt, kasacja to decyzja
   właściciela i tak zostaje oznaczona.

## Parser self-test

**N/A — master Stadium A nie deklaruje żadnej bramki mechanicznej ani parsera.** Master
opisuje migrację, kontrakt kolumn i plan faz; jedyny mechanizm egzekwujący (`CHECK` na
`note`/`role`, przepisany trigger prune) powstaje dopiero w PHASE-1A/2A i jest tam
kryterium akceptacji, nie bramką rundy spec (LESSONS#15 — bramka celująca w obiekt,
który faza dopiero tworzy, jest nieuruchamialna w rundzie spec i nie ma prawa się w niej
znaleźć). Testu regexu nie ma na czym wykonać; sekcja zostaje jawnie zadeklarowana pusta
zamiast pominięta.

## Audyt C/M/E

Kanon `docs/specs/spec-workflow/CME-MANIFEST.md` **nie istnieje** ani w tym repo, ani
w kopii kanonicznej w FABRYCE — zgodnie z regułą 1 („kanon przed egzekucją") audyt nie
jest tu blokerem werdyktu, ale bramka strukturalna preflightu obowiązuje i rekordy poniżej
są wypełnione normalnie.

- CME: typ=MEASURED | dowod=probe-db-2026-08-13 | C=twierdzenia §1/§3.1/§3.4/§7 o stanie bazy: 12 projektów, brak kolumn note/role/book/deleted_at w projects, brak label/pinned w project_snapshots, liczba snapshotów | M=trzy skrypty odczytu w scratchpadzie sesji (probe.py, probe2.py, probe3.py), wszystkie EXIT=0 | E=R1 2026-08-13: projects 12 wierszy z pełną listą 12 kolumn · project_snapshots 31 wierszy z 5 kolumnami · rozkład per projekt d73dcc3b 10, 507b3ee4 10, 11c96cd4 6, 17adb766 2, 72609fef 1, b0841702 1, 70e90efb 1 · liczby rozdziałów dla 4 projektów (507b3ee4 24, d73dcc3b 12, 72609fef 24, 19c4a5fe 2) | poza=NIE zmierzono treści rozdziałów ani zgodności z Redaktorem, bo do decyzji fazy 1A wystarcza kształt schematu i liczność kafelków; treść pokrywa osobny dowód sha256 z 2026-08-11 opisany w rekordzie niżej | werdykt=PASS
- CME: typ=MEASURED | dowod=find-praca-redaktor-2026-08-13 | C=§7 twierdzi, że wybór kanonu został zweryfikowany po treści na przebiegach Redaktora | M=find po katalogu FABRYKA-redaktor/redaktor/praca, EXIT=0 | E=R1 2026-08-13: 14 katalogów ewa-*, 24 katalogi boz-*, łącznie 109 plików input.md | poza=liczba katalogów NIE odtwarza zbioru porównanych rozdziałów (14 katalogów ewa-* wobec 12 rozdziałów kanonu Ewy), więc pokrycie 36/36 zostało z §7 USUNIĘTE zamiast podparte; proporcjonalne, bo §7 to wejście do ręcznej czynności właściciela, nie kryterium akceptacji żadnej fazy; kto chce oprzeć na tym decyzję, powtarza porównanie sha256 wg metody z pamięci project-kanoniczne-projekty-w-bazie | werdykt=PASS
- CME: typ=CONTRACTED | dowod=sha256-md-roundtrip-2026-08-11 | C=wybór dwóch projektów kanonicznych (d73dcc3b, 507b3ee4) jako AKTUALNA | M=pamięć project-kanoniczne-projekty-w-bazie, zapis z 2026-08-11 wykonany poza tym specem | mierzalne-od=md_exporter.chapter_to_markdown na projekcie z bazy plus porównanie sha256 NFC z input.md z przebiegów Redaktora, krok: przed sprzątaniem balastu | poza=ten spec NIE powtarza tego pomiaru i nie opiera na nim żadnej bramki ani kryterium akceptacji; proporcjonalne, bo §7 opisuje czynność właściciela wykonywaną ręcznie z backupem .tiolibri przed każdą kasacją; pokryte przez wymóg jawnego potwierdzenia właściciela dla 19c4a5fe | werdykt=PASS
