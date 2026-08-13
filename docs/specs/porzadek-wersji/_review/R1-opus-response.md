# R1-opus-response — REQUEST_CHANGES

**Data:** 2026-08-13
**Werdykt Codexa:** REQUEST_CHANGES (parser: 1 dopasowanie, kanoniczny format)
**Spec:** `SPEC-PORZADEK-WERSJI-MASTER.md` v0.2 → **v0.3**
**Risk:** HIGH → MAX_ROUNDS = 3. `N=1`, `reset-po-spike=0`, `rundy-rdzenia=0` → **N_EFF = 1 < 3**.

**Bilans:** 9 uwag — **9 ZAAKCEPTOWANE, 0 ODRZUCONE.** Codex nie postawił ani jednej uwagi,
która nie broniłaby się wobec kodu.

---

## Weryfikacja faktów Codexa — wszystkie potwierdzone niezależnie

Nie przyjmuję ustaleń recenzenta na słowo (LESSONS#20). Każdy fakt nośny sprawdzony w kodzie
2026-08-13, przed napisaniem odpowiedzi:

| Twierdzenie Codexa | Wynik weryfikacji |
|---|---|
| `EditorPage.handleUpdateProject` — drugi write-path | **POTWIERDZONE**, `EditorPage.jsx:224-236`, `supabase.from('projects').update(...)` wprost w komponencie |
| `get_project` nie sprawdza właściciela, `_user` nieużywany | **POTWIERDZONE**, `projects.py:71-78` — brak jakiegokolwiek użycia `_user` w ciele |
| `_assert_project_access` istnieje i jest wołany gdzie indziej | **POTWIERDZONE**, `projects.py:394`, wołany w `chapters.py`, `snapshots.py`, `export_import.py` — brak wyłącznie w `get_project` |
| eksport `.tiolibri` — 7 pól, bez nowych | **POTWIERDZONE**, `export_import.py:87-97` |
| import — inna podlista, bez nowych | **POTWIERDZONE**, `export_import.py:385-400` |
| `_build_snapshot` — 8 pól, bez nowych | **POTWIERDZONE**, `snapshots.py:176-196` |
| restore — węższa allowlista (5 pól) | **POTWIERDZONE**, `snapshots.py:97-107`; pomija także `cover_image_url` i `status`, choć snapshot je zapisuje |
| trigger kasuje bez warunku `pinned` | **POTWIERDZONE**, `20260421_spec1.sql:61-79` |
| `list_snapshots` bez pola nazwy | **POTWIERDZONE**, `snapshots.py:37-41` |
| `Badge.jsx` z gotowymi wariantami | **POTWIERDZONE** — `draft/in_progress/completed/gray/blue/green/yellow/red/indigo`, rozmiary `sm`/`md` |

**Ustalenie własne, poza review:** repo **nie ma żadnego harnessu testowego** — `tiolibri-frontend`
nie ma zależności testowych ani skryptu `test`, `tiolibri-api` nie ma `tests/` ani `pytest`
w `requirements.txt`. To zmienia odpowiedź na uwagi #1 i #8: nie da się „dobudżetować plików
testów", bo wprowadzenie runnera to faza bootstrapowa (LESSONS#7). Stąd protokół owner-attested §6.

⚠️ **Zgrzyt do drenu:** `.claude/spec-config.json` deklaruje `test_cmd: "… pytest"`, którego
w tym repo nie ma. Konfiguracja kłamie o możliwościach — każda komenda ufająca temu polu dostanie
fałszywy obraz.

---

## Uwagi — decyzje

Klasyfikacja L-C: **[P]** produkt (kontrakt, logika), **[A]** aparatura (bramki, pomiar, protokół
dowodu), **[D]** docs/proza.

### 1. Sizing nie mierzy pełnego scope i pomija cztery osie — **[P]**

**Decyzja: ZAAKCEPTOWANE.** Uwaga trafna i niedoszacowana przez Codexa — osi brakowało nie trzech,
tylko czterech: §4.5 wymaga **7** (pliki, LOC, czas, **testy**, **domeny**, **migracje**,
**decyzje architektoniczne**), a v0.2 pokazywała 3. Oś „decyzje architektoniczne = 0" jest przy tym
limitem TWARDYM i v0.2 go łamała: uwagi #3, #4 i #5 to dokładnie decyzje zostawione implementacji.

**Zmiana:** §5 przepisane — pełna tabela 7 osi per faza + jawna lista plików z LOC, w tym pliki
dowodowe wliczone do tej samej sumy (LESSONS#17 pkt 2). Braki, które Codex wskazał, domknięte:
`EditorPage.jsx` w PHASE-1B, `export_import.py` i `snapshots.py` w PHASE-1A, artefakty `PROOF-*`
we wszystkich fazach. Czas PHASE-1A 50→75 min, PHASE-1B 65→80 min, PHASE-2A 55→70 min.

**Dodane ponad uwagę:** PHASE-1B ląduje na 80/90 min — przy suficie w rozumieniu LESSONS#17.
Zapisane jawnie wraz z **przygotowanym cięciem** (`1B-i` karta / `1B-ii` dashboard), żeby split
nie był wymyślany w trakcie implementacji.

### 2. Niespójność ze źródłem i stale references — **[P]** (footer: [D])

**Decyzja: ZAAKCEPTOWANE w całości.** Trzy osobne rzeczy, każda realna:

- **8 vs 10 kasowanych** — sprzeczność wewnątrz jednego pliku. §7 rozpisane na 2 + 9 + 1 = 12,
  §4 mówi „9-10". Zero pozycji bez klasyfikacji.
- **Utracony scope z HANDOFF-u** — sprawdziłem źródło (`HANDOFF-porzadek-wersji-projektow.md:70-95`).
  Codex ma rację: HANDOFF mówi dosłownie „Edycja **inline z karty i z edytora**" oraz o `role`,
  że „to ona daje **sortowanie i filtr**". Master v0.2 zgubił edytor i filtr. **To są decyzje
  właściciela już podjęte 2026-08-11 — przywracam je, nie pytam o nie ponownie.** PHASE-1B dostaje
  `EditorPage.jsx` i filtr po roli oraz po książce.
- **Stale footer** — v0.2 kierowała do `/spec-fill`, co jest tą samą pomyłką, którą `STATE.md`
  już raz oznaczył jako stale. Footer przepisany, skrócony do jednego zdania.

### 3. `AKTUALNA` bez inwariantu i niepełna logika duplikatu — **[P]**

**Decyzja: ZAAKCEPTOWANE.** To był najpoważniejszy bloker merytoryczny: cel §2 obiecuje „widzę,
który jest aktualny", a schemat pozwalał na dowolną liczbę `AKTUALNA`. **Decyzja właściciela D2
(2026-08-13): twardy inwariant w bazie.**

**Zmiana:** §3.1.2 — **dwa** indeksy częściowe.

⚠️ **Wkład ponad uwagę Codexa.** Sam indeks na `(user_id, lower(book)) WHERE role='AKTUALNA'`
byłby **pozorną ochroną**: nie obejmuje wierszy z `book IS NULL`, a w dniu migracji **wszystkie 12
projektów mają tam NULL**. Inwariant nie obowiązywałby w jedynym stanie, w którym baza faktycznie
startuje. Stąd drugi indeks `WHERE role='AKTUALNA' AND book IS NULL`.

Dopisany też tryb awarii: zapis idzie z przeglądarki, więc **nie ma transakcji** obejmującej
„zdejmij starą + nadaj nową". Kolejność jest wymuszona (najpierw zdjąć), a awaria w środku daje
stan „zero AKTUALNA" — widoczny i naprawialny jednym kliknięciem, w przeciwieństwie do cichego
„dwie AKTUALNE".

**Logika duplikatu:** §3.3 dostała pełną tabelę wejście → wynik dla `AKTUALNA`/`ROBOCZA`/`ARCHIWUM`/
`NULL` (reguła jednolita: zawsze `ROBOCZA`), format `<data>` = `YYYY-MM-DD` w `Europe/Warsaw`
generowany w backendzie, ucięcie `<tytuł>` do 120 znaków pod limit 300, oraz kolejność sortowania.

### 4. `book` martwym polem po „nie" dla PHASE-3 — **[P]**

**Decyzja: ZAAKCEPTOWANE co do diagnozy, rozstrzygnięte przez właściciela (D1).**

Codex ma rację, że uzasadnienie v0.2 było **fałszywym kosztem alternatywy**: „żeby nie robić
drugiego uzupełniania" — odłożenie kolumny nullable do PHASE-3 dałoby jedną migrację i jedno
uzupełnianie, nie dwa. Zapisałem tę korektę wprost w §3.1.1, zamiast po cichu podmienić argument.

**Rozstrzygnięcie D1: `book` zostaje w 1A/1B, ale dostaje własną widoczną funkcję** — nazwa na
karcie + filtr/sortowanie po książce, niezależnie od PHASE-3. Prawdziwe uzasadnienie jest inne
niż to z v0.2 i wystarczające: `book` jest **jedynym kluczem**, który czyni inwariant z uwagi #3
wykonalnym.

**Kontrakt normalizacji** (§3.1.1) w trzech warstwach: helper front kanonizuje, CHECK w DB odrzuca
niekanoniczne (`book = btrim(book)`), porównania idą po `lower(book)`.

### 5. „Jedna ścieżka zapisu" nie pokrywa UI + rozszerzenie IDOR — **[P]**

**Decyzja: ZAAKCEPTOWANE, obie warstwy.**

**Write-pathy:** twierdzenie v0.2 było po prostu nieprawdziwe wobec kodu. §3.2 wymienia teraz
**trzy** realne ścieżki z kotwicami i wprowadza wspólny helper `normalizeProjectMeta` wołany przez
wszystkie trzy, plus **identyczne mapowanie błędów** `23514`/`23505` na komunikaty.

**IDOR:** potwierdzony samodzielnie. `get_project` przyjmuje JWT i go nie używa, klient jest
service-role, więc RLS nie broni. Dopisanie trzech pól do `Project` **poszerzyłoby istniejącą
dziurę o nowe dane właściciela** — i to jest właściwy powód, dla którego domknięcie należy do
PHASE-1A, a nie do osobnego speca. Koszt jest niski: `_assert_project_access` już istnieje w tym
samym pliku.

**Widoczność dla współdzielonych** rozstrzygnięta wprost (§3.2.1): pola są **widoczne** dla osób
z udziałem (opisują wersję, którą taka osoba redaguje), ale **edytowalne tylko przez właściciela**,
egzekwowane przez RLS `UPDATE`, nie przez UI.

### 6. Nowe metadane wypadają z backupu i restore — **[P]**

**Decyzja: ZAAKCEPTOWANE, rozstrzygnięte przez właściciela (D3).** Nowa §3.6 z tabelą czterech
miejsc, gdzie kod ręcznie wylicza pola projektu.

**Reguła: backup i snapshot zapisują, restore nie cofa.** Uzasadnienie nie jest arbitralne —
**to zastosowanie wzorca, który w kodzie już jest**: restore dziś celowo pomija `cover_image_url`
i `status`, choć `_build_snapshot` oba zapisuje. Asymetria „snapshot łapie szerzej niż restore
oddaje" jest istniejącą decyzją tego kodu, nie wyjątkiem wymyślonym tutaj.

**Import zeruje `role`** — tą samą logiką co duplikat; inaczej import uderzałby w indeks z uwagi #3.

**Ryzyko sprzątania** przyjęte w całości: §3.5 mówi teraz wprost, że `.tiolibri` **nie niesie**
historii wersji, snapshotów ani assetów, a DELETE kasuje je kaskadowo — więc „eksport → usuń" to
backup podzbioru, nie pełna odwracalność. **„Żyje wiecznie" zawężone do „dopóki istnieje projekt"**
w §2 i §3.4.2. Ta sama uwaga wprost uzasadniła decyzję D4 o `19c4a5fe` (oględziny przed kasacją).

### 7. Kontrakt `label`/`pinned` i endpointów — **[P]**

**Decyzja: ZAAKCEPTOWANE.** Uwaga o `DEFAULT false` jest celna: nazwany snapshot tworzony jako
nieprzypięty **nie spełnia** miary sukcesu z §2 („jeden klik, ma nazwę, żyje"), bo dalej podlega
retencji.

**Zmiana** (§3.4.2, §3.4.3): nazwa **wymagana** przy ręcznym snapshocie (1-120 po `btrim`, CHECK
w DB), ręczny tworzony od razu `pinned = true`, `DEFAULT false` zostaje dla auto-snapshotów.
Endpointy rozpisane: metody, body, walidacja, kody odpowiedzi, autoryzacja **owner-only** przez
nowy `_assert_project_owner` (istniejący `_assert_project_access` przepuszcza współdzielonych),
sprawdzenie przynależności `snapshot_id` do `project_id` → `404`, idempotencja `PATCH`,
`select` w `list_snapshots` rozszerzony o `label, pinned`.

**Zachowanie retencji po unpin** (§3.4.4): trigger jest `AFTER INSERT`, więc nadmiar żyje do
następnego INSERT-u. **Przyjęte świadomie i zapisane w kryteriach**, z odrzuceniem alternatywy
`AFTER UPDATE OF pinned` — kasowanie pięciu snapshotów w reakcji na odpięcie jednego jest
zachowaniem zaskakującym.

### 8. Test mutacyjny bez uruchamialnego kontraktu — **[A]**

**Decyzja: ZAAKCEPTOWANE.** Codex słusznie **nie** postawił tego jako bramki R1 (LESSONS#15 —
trigger dopiero powstaje), tylko jako brak wykonywalnego protokołu.

**Ustalenie, które zmienia kształt odpowiedzi:** repo nie ma **żadnego** harnessu — ani frontowego,
ani backendowego. Dobudżetowanie „plików testów" byłoby więc wpisaniem do fazy feature roboty
bootstrapowej (LESSONS#7). Zamiast tego **§6 — protokół owner-attested z realnymi EXIT**, legalny
w tym workflow.

§6.2 rozpisuje mutację triggera: fixture (16 nieprzypiętych + 1 przypięty), **kontrola pozytywna
przed mutacją** (bez niej każdy FAIL może być awarią połączenia), zapis produkcyjnej deklaracji
przez `pg_get_functiondef`, mutacja **wyłącznie gałęzi `DELETE`**, oczekiwany RED, rewert
z **weryfikacją bajtową przez ponowny odczyt** (LESSONS#14: `CREATE OR REPLACE` kończy się sukcesem
także wtedy, gdy nic nie zmienił), postflight.

**Wkład ponad uwagę:** §3.4.1 twierdzi, że **oba** warunki są nośne — więc protokół wymaga **dwóch**
mutacji, także tej na podzbiorze keep-setu przy nietkniętym `DELETE`. Twierdzenie o dwóch warunkach
dowiedzione jedną mutacją byłoby dowodem połowicznym.

§6.1 dokłada analogiczny protokół dla CHECK-ów i indeksów (9 kroków, z kontrolą pozytywną
i postflightem), §6.3 nazywa klik-test **wprost słabszym dowodem** — „przeklikane, wynik poniżej",
nie „testy przechodzą".

### 9. UI bez kontraktu a11y, błędów i tokenów — **[P]**

**Decyzja: ZAAKCEPTOWANE.** Nowa §9: zachowanie inline edit (Enter/Escape/blur — z decyzją, że
**blur zapisuje**, bo anulowanie po kliknięciu obok gubi pracę bez ostrzeżenia), powrót fokusu,
zachowanie po odrzuceniu przez DB (`aria-live`, wartość zostaje do poprawki), mapowanie ról
i `pinned` na **istniejące** warianty `Badge` (sprawdzone: `green`/`yellow`/`gray`/`indigo`),
`aria-pressed` i opisowa nazwa dostępna dla pin/unpin, wymagane pole nazwy snapshotu.

**Reguła „stan nie tylko kolorem"** zapisana jako wymóg — każda plakietka niesie tekst.

---

## Sweep przeprowadzony (LESSONS#3 pkt 1)

Zmiana >100 LOC w masterze → sweep po starych frazach:

| Szukane | Wynik |
|---|---|
| `/spec-fill` w masterze | 0 trafień (był stale footer) |
| `usunięcie 8 projektów` / `8 projektów` | 0 trafień |
| `**Wersja:** 0.2` | 0 trafień |
| `3 osie` w §5 | 0 trafień |
| `żyje wiecznie` bez zawężenia | 0 trafień niezawężonych |
| `36/36` | 0 trafień |

---

## Audyt C/M/E — luki zamknięte, nie przemilczane

Codex zgłosił dwa zdania nośne bez wykonanego E i zgodnie z instrukcją nie policzył ich jako
blokera. Zamykam je mimo to, bo twierdzenie bez dowodu w specu Risk HIGH dojrzewa do blokera
w kolejnej rundzie:

- **„ani jeden snapshot nie jest ręczny"** — **wycofane** z twierdzeń nośnych (E nie zawiera
  rozkładu `triggered_by`). Zostaje wersja zweryfikowana w kodzie: snapshot nie ma nazwy
  i nie przeżywa retencji.
- **„żaden rozdział nie zgadza się hashem"** — **oznaczone jawnie** jako tło motywacyjne bez
  wykonanego E w tym specu, z zapisem, że żadna bramka się o nie nie opiera.

---

## Zakaz rundy potwierdzającej (Krok 4a) — nie dotyczy

`diff .base-R1.md ↔ master` = **niezerowa** (przepisane §3.1-§3.6, nowe §6, §8, §9, przebudowane
§4, §5, §7, footer). Runda R2 dostaje inny tekst, więc może wnieść nową informację.

## STOP-and-SPIKE (Krok 4) — nie dotyczy

`N = 1`; bramka jest sensowna od `N ≥ 2`. Brak poprzedniej rundy do porównania rdzenia.

## L-C — klasa uwag

**8 × [P]**, **1 × [A]**, 1 element klasy [D] wewnątrz uwagi #2 (stale footer).
Uwagi klasy PRODUKT dominują i **uzasadniają rundę R2** — reguła stopu L-C nie ma zastosowania.

---

## Następny krok

`spec: R1-opus-pending` → `/spec-handoff porzadek-wersji` generuje R2 (`N_EFF = 1 < MAX_ROUNDS = 3`).

---

## Dla Piotrka — jedno zdanie

Codex miał rację we wszystkich 9 punktach — master v0.3 domyka scope, wprowadza twardy inwariant
jednej AKTUALNEJ i protokół dowodu bez harnessu; spec idzie na rundę R2.

**Kopiuj dalej — w tym samym wątku:**
```
/spec-handoff porzadek-wersji
```
