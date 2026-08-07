# R1-opus-response — REQUEST_CHANGES przerobione

**Data:** 2026-08-07
**Werdykt Codexa:** REQUEST_CHANGES (8 blokerów + 5 major, 11/11 kategorii)
**Spec:** `SPEC-MD-EXPORT.md` v0.2 → **v0.3**
**Runda:** N=1, MAX_ROUNDS=2 (Risk STANDARD), N_EFF=1, `rundy-rdzenia`=0, `reset-po-spike`=brak
→ została jedna runda.

**L-C klasyfikacja:** 11 uwag klasy **P** (produkt: kontrakt, logika, decyzje), 2 klasy **D**
(proza/kosmetyka), 0 klasy A. Runda R2 uzasadniona klasą P — stop L-C nie ma tu zastosowania.

---

## Decyzje właściciela (AskUserQuestion, 2026-08-07)

Codex słusznie odmówił wyboru za właściciela (guardrail 4.4b). Zadane trzy pytania, wszystkie
odpowiedziane rekomendacją:

| Pytanie | Wybór | Skutek w specu |
|---|---|---|
| **Zakres** (bloker 1) | Bez modala — jeden przycisk „eksportuj całą książkę" | modal, wybór rozdziałów i filtr zmian odcięte; §Sizing przeliczony; bloker 12 rozpuszczony |
| **Klucz książki** (bloker 2) | `slug(tytuł)-<8 hex z project_id>` | nowa §`book_key`; dawne D1 zamknięte |
| **Filtr zmian** (bloker 7) | Wypada z tej fazy | §Ograniczenia; dawne D2 zamknięte |

Odcięcie modala jest **decyzją cross-fazową właściciela podjętą spec-time**, nie awaryjną
decyzją implementatora — to była dokładnie treść zastrzeżenia Codexa w blokerze 1.

---

## Uwagi Codexa — decyzje

### 1. BLOCKER — Sizing liczy nie ten zbiór i przekracza limit — **[P] ZAAKCEPTOWANE**

Uwaga trafna w całości. Master §4.5 liczy wszystkie pliki i wszystkie linie, także testy;
zapis „~495 LOC produkcyjnych + ~110 LOC testów" omijał limit przez rozdzielenie sumy
(LESSONS#17 pkt 2). Linia cięcia „gdy urośnie, odetnę UI" faktycznie nie ratowała bramki.

**Zmiana:** nagłówek ma teraz tabelę **plik → rodzaj → LOC** z jedną sumą (5 plików, ~567 LOC),
osie domen/migracji/decyzji architektonicznych, i status **`Sizing: DYSPENSA`** z **nazwanym
źródłem autoryzacji** (decyzja właściciela w tej rundzie) — LESSONS#18 punktuje marker DYSPENSA
bez źródła jako pozorną zieleń. Rozbieżność 80 vs 90 min usunięta: jedna liczba, ~90 min.

**Czego nie zaakceptowałem:** propozycji, żeby odcięcie UI wymagało promocji na full spec.
Właściciel odciął zakres decyzją spec-time, co jest legalną drogą — spec zostaje light.

**Znalezione przy okazji, czego review nie miało:** `pytest` **nie jest** w `requirements.txt`
ani w `tiolibri-api/venv` (`bs4` i `lxml` **są** — ta część speca była prawdziwa). Bez nazwania
tego implementator albo dopisze runner do obrazu Railway, albo odkryje brak w połowie fazy
(LESSONS#7). Spec ustala: `pip install pytest` lokalnie, plik testowy w korzeniu
`tiolibri-api/` obok istniejącego `test_polish_pdf.py`, **bez dopisywania do `requirements.txt`**
— dzięki temu nie ma szóstego pliku ani rippla zależności.

### 2. BLOCKER — globalna unikalność basename'ów — **[P] ZAAKCEPTOWANE**

Trafne: slug **tytułu** rozwiązuje kolizję dwóch tytułów, nie dwóch projektów o tym samym
tytule, a sufiksy `-2`/`-3` liczone w obrębie jednego ZIP-a nie wiedzą nic o poprzednich
eksportach — więc wymóg ODPOWIEDZ B2 nie był spełniony.

**Zmiana:** nowa §`book_key` — `slugify(project_title)-<pierwsze 8 hex project_id>`. Stabilny
między eksportami (UUID się nie zmienia), więc powtórny eksport trafia w ten sam katalog
przebiegu Redaktora. Sufiks `-2`/`-3` zostaje, ale wyłącznie na kolizje slugów **tytułów
rozdziałów w obrębie książki** — jego rola jest teraz nazwana wprost.

### 3. BLOCKER — T3 nie testuje języka rzeczywistego chunkera — **[P] ZAAKCEPTOWANE**

Najcenniejsza uwaga rundy. Codex obalił mój własny preflight kontrpróbą na produkcyjnym
`segmentuj.ts` (Node 24 `--experimental-strip-types`, EXIT=0) i miał rację: T3 badał **mój
regex, nie język konsumenta**.

**Zmiana:** przeczytałem `segmentuj.ts` w całości i przepisałem regułę z sześciu regexów
`:12-17`. Nowa §Kontrakt escapingu ma tabelę **regex konsumenta → linia → co produkuje bez
escapingu**, a reguła brzmi: jeśli linia pasuje do któregokolwiek z pięciu wzorców
strukturalnych, wstaw `\` przed pierwszym nie-białym znakiem.

Trzy rzeczy wyszły poza to, co wskazał Codex:

- **Escaping jest teraz WĘŻSZY, nie szerszy.** `RE_ATX` wymaga `#` z następującym białym znakiem
  lub końcem linii, `RE_MARKER` wymaga białego znaku po markerze — więc `#hasztag` i `-myślnik`
  **nie są strukturą** i nie dostają backslasha. v0.2 escape'owała je niepotrzebnie. Fixture
  ma teraz **przypadki negatywne**, które muszą zostać czyste.
- **Tabeli nie da się zneutralizować escape'owaniem pipe'ów** — `L.includes("|")`
  (`segmentuj.ts:91`) jest prawdziwe także dla `\|`. Neutralizujemy **linię separatora**:
  `\` nie należy do klasy `[ :|-]`, więc `RE_TABLE_SEP` przestaje pasować.
- **Nasze `---` nigdy nie jest escape'owane i nie może przypadkiem utworzyć tabeli** — warunek
  tabeli wymaga `|` w linii **poprzedniej**, a bloki rozdziela pusta linia.

**O1 zamknięte przy okazji** (Codex słusznie zauważył, że przestało być otwarte):
`segmentuj.ts:142` — akapit pęka tylko na pustej linii albo `startsBlock`. Pojedynczy `\n` nie
rozbija akapitu, więc `<br>` → `\n` **zostaje** — pod warunkiem, że escaping obejmuje **każdą**
linię bloku, nie tylko pierwszą. v0.2 escape'owała tylko początek bloku i to był ukryty bloker.

### 4. BLOCKER — algorytm HTML→MD nie jest implementowalny bez zgadywania — **[P] ZAAKCEPTOWANE**

Wszystkie sześć luk zamknięte, każda jawnie:

| Luka Codexa | Rozstrzygnięcie w v0.3 |
|---|---|
| zagnieżdżone listy, kontynuacja `<li>` | §Listy — 2 spacje na poziom, wyprowadzone z `INDENT_MIN = 2` (`segmentuj.ts:20`); pusta linia w liście legalna przez lookahead `:118-125`; `<ol start>`; numeracja rosnąca |
| spacje między inline nodes | §Inline — sklejanie bez wstawiania spacji, whitespace z wnętrza `<strong>` wychodzi na zewnątrz znaczników, puste znaczniki nieemitowane |
| literalne znaki MD w `alt` i URL-u | `alt`: `\`→`\\`, `]`→`\]`, newline→spacja (v0.2 mówiła „bez zmian" — błąd); URL ze spacją/nawiasem → `<…>` |
| kolejność „whitespace do jednej spacji" vs `<br> → \n` | §Kolejność operacji — 9 ponumerowanych kroków; `<br>` jest twardą granicą linii i **nie jest białym znakiem**, zwijanie działa w obrębie linii |
| puste bloki, tekst top-level poza `<p>` | puste/whitespace-only bloki i nagłówki **pomijane**; goły węzeł tekstowy pod `<body>` → własny akapit |
| atomowa konsumpcja obrazka vs tagi-rodzice | §Umiejscowienie bloku obrazu — `<img>` sam w rodzicu przejmuje blok; `<img>` wśród tekstu **wyniesiony** do bloku bezpośrednio po |

Plan testów rozszerzony dokładnie o to, co Codex wypunktował jako pominięte.

### 5. BLOCKER — kontrakt obrazów/base64 i limitów niepełny — **[P] ZAAKCEPTOWANE**

**Zmiana:** tabela przypadków `data:` URI (7 wierszy) — malformed base64, brak `;base64`,
parametry MIME, pusty payload, MIME spoza allowlisty, `image/svg+xml`, przekroczenie limitu.
Każdy ma zachowanie i, gdy pominięty, `reason` w manifeście. Allowlista rozszerzeń jest
zamknięta; wszystko poza nią (w tym SVG) → `.bin`.

Limity: **10 MB mierzone na bajtach zdekodowanych**, **80 MB jako suma wpisów PRZED kompresją**
(to ta suma ogranicza pamięć przy buforowaniu ZIP-a).

Sygnatura poprawiona — `chapter_to_markdown(html, book_key, position) -> ChapterResult`
z dataclassami `ChapterResult`/`ExportImage`, więc bajty obrazów mają kanał. **Własność limitów
rozdzielona jawnie:** limit per obraz egzekwuje konwerter (jako jedyny widzi bajty), limit ZIP-a
endpoint (jako jedyny sumuje rozdziały).

**Świadomie odrzucone:** sniffing bajtów wobec deklarowanego MIME — Redaktor obrazów nie
renderuje, rozszerzenie jest kosmetyką. Zapisane w §Co odrzucone jako decyzja, nie przeoczenie.

### 6. BLOCKER — endpoint gubi legalny stan i ma niebezpieczną semantykę pustej listy — **[P] ZAAKCEPTOWANE**

Sprawdziłem `useChapters.js:177-212` — Codex ma rację co do faktu: rozdział bez
`processed_html` jest legalnym stanem, a fallback (Storage `uploads` → `convertGoogleDocsHtml`)
żyje w JS-ie przeglądarki.

**Rozstrzygnięcie: fail-closed.** Endpoint czyta wyłącznie `processed_html`; jeśli którykolwiek
eksportowany rozdział ma je puste → **409 z listą tytułów**. Port `convertGoogleDocsHtml` do
Pythona to drugi konwerter i osobna decyzja — zapisany w §Ograniczenia. Cichy skip odrzucony
świadomie: niekompletna książka, na którą nikt się nie skarży, to ta sama klasa błędu co
kolizja katalogów z ODPOWIEDZ B2.

**Pusta lista:** model `ExportMdRequest { chapter_ids: list[UUID] | None = None }`. Brak body
albo `null` = wszystkie; **jawne `[]` = 400**. Dołożone: 404 dla ID spoza projektu (fail-closed,
nie cichy skip), 422 z Pydantica dla nie-UUID, 400 dla projektu bez rozdziałów, **tie-breaker
`order("id")`** przy równym `sort_order`.

Uwaga do tie-breakera: **nie użyłem `created_at`**, mimo że narzucał się pierwszy —
`chapters.py:211` selektuje `id, project_id, title, sort_order, deleted_at, deleted_by, status`
i kolumny `created_at` w `chapters` **nie potwierdziłem**. `id` jest pewne (LESSONS#20 — nazwa
niesprawdzona to nazwa fałszywa).

### 7. BLOCKER — filtr „zmienione" nie ma przepływu danych — **[P] ZAAKCEPTOWANE, ROZSTRZYGNIĘTE PRZEZ WŁAŚCICIELA**

Diagnoza trafna: frontend dostaje sam `Blob`, `authedFetch` nie wystawia nagłówków, nikt nie
rozpakowuje ZIP-a w JS, a hash źródłowego HTML nie jest hashem NFC `.md`. D2 wybrało miejsce
przechowania, nie zaprojektowało przepływu.

**Właściciel wybrał usunięcie filtra z tej fazy.** Hashe i tak lądują w `manifest.json`, więc
nic nie ginie trwale — temat wraca przy `md-import`, który manifest czyta z definicji.

### 8. BLOCKER — krok weryfikacyjny odwołuje się do bramki nieaktywnej na etapie `chunks.json` — **[P] ZAAKCEPTOWANE**

Sprawdziłem ODPOWIEDZ A4: K-NAG reużywa `segmentuj()`, ale wyjątek leci w kroku 7 `cli/apply.ts`
— na etapie `chunks.json` nie uruchamia się w ogóle. Kryterium było niewykonalne w opisanym
punkcie.

**Zmiana:** krok 4 to teraz **cztery asercje z zerową tolerancją** (G1–G4) uruchamialne na
samym `chunks.json`. Kluczowy jest G1: konwerter emituje `blocks` — licznik wyemitowanych
bloków per typ chunkera — a bramka porównuje go z rozkładem typów w `chunks.json`. To daje
mianownik, którego brakowało. G3 jest **lokalną symulacją K-NAG** (ciąg nagłówków, porównanie
case-insensitive z normalizacją białych znaków, wprost wg A4), z jawnym zastrzeżeniem, że
**pełny K-NAG dowodzi się dopiero przy `apply`** i jest osobnym przebiegiem poza tą fazą.

„Liczba chunków odpowiada z grubsza liczbie akapitów" **usunięta** — Codex ma rację, że bez
tolerancji i mianownika to nie było kryterium.

### 9. MAJOR — Risk STANDARD ma nieprawdziwe uzasadnienie — **[P] ZAAKCEPTOWANE**

Argument (c) z v0.2 przedstawiał K-NAG jak backstop całego serializatora. To była nieprawda.

**Zmiana:** §Bramki przepisana. Nazwane wprost, że K-NAG chroni **wyłącznie strukturę nagłówków,
i wyłącznie przy `apply`**, i że nie ochroni przed utratą treści, złym unwrapem, przypadkowym
`kod`/`lista`/`tabela`, zepsutym obrazem ani rozjazdem chunków. Realnym backstopem jest bramka
G1–G4 po naszej stronie. Dołożony uczciwy koszt błędu: plik trafia do W1/W2 i generuje ręczną
pracę operatora oraz decyzje na rozjechanych chunkach — dlatego krok 4 jest obowiązkowy przed
masowym użyciem.

**Klasyfikacja zostaje STANDARD**, ale na innych przesłankach: zero zapisów do bazy, brak zmian
w modelu dostępu, odwracalność ponownym eksportem, wejściem jest nasz własny HTML.

### 10. MAJOR — dwie decyzje produktowe zostawione właścicielowi dopiero w review — **[P] ZAAKCEPTOWANE**

D1 i D2 zadane właścicielowi (tabela na górze) i **zamknięte w specu**, nie w sekcji „do
potwierdzenia". D3 przeniesione do §Ograniczenia — Codex ma rację, że to nie była decyzja,
tylko ograniczenie narzucone przez kontrakt. O1 rozstrzygnięte na kodzie (finding 3). Sekcja
„Decyzje wymagające potwierdzenia w review" **przestała istnieć**; w jej miejsce jest
„Decyzje właściciela (zamknięte w R1)" ze śladem daty i pliku.

### 11. MAJOR — C/M/E i proza rozciągają zakres dowodów — **[P/D] ZAAKCEPTOWANE w całości**

- **„koszt zabezpieczenia zerowy"** — usunięte jako fałszywe i sprzeczne z własnym sizingiem
  tego samego dokumentu. Zastąpione liczbą: `_media/` + base64 + limity to ~+70 LOC i +10 min,
  przyjęte świadomie.
- **T1–T4** — poprawione C: to były cztery wąskie sondy na **własnych regexach**, nie „dry-run
  każdego parsera/reguły". Dowód na języku chunkera wnosi dopiero kontrpróba Codexa i to ona
  jest teraz źródłem reguły escapingu (§Kontrakt escapingu cytuje `segmentuj.ts:12-17`).
- **„27 chunków → blisko 30 wywołań"** — zostawione **literalnie jako obserwacja rozdziału
  Bożeny**, z jawnym zdaniem, że dla Ewy nie mamy oczekiwanego przedziału. Słowo „skala
  oczekiwana" usunięte.
- Brak `CME-MANIFEST.md` — zgodne z regułą 1, nieblokujące; Codex sam to potwierdził.

### 12. MAJOR — UI bez kontraktu a11y i stanów błędu — **[P] ZAAKCEPTOWANE, rozwiązane descope'em**

Po odcięciu modala zostaje jeden przycisk, więc kontrakt zmniejsza się do stanów: `disabled`
na czas żądania (blokada podwójnego submitu), `aria-busy`, komunikat błędu z `err.message`
z osobnym brzmieniem dla 409 i 413.

**Sondaż, którego Codex słusznie zażądał:** `components/ui/Modal.jsx` **istnieje** i ma
zamykanie Escape (`:64-80`) oraz kliknięcie w overlay (`:87-90`), ale **nie ma focus trapu, nie
przywraca focusu do przycisku wywołującego i nie ma `role="dialog"` ani `aria-modal`**.
Zapisane w §Frontend jako notatka dla przyszłego speca modala — żeby descope nie zgubił
ustalenia.

Sprawdzone też i zapisane w §Endpoint: `authedFetch` sprawdza `res.ok` i rzuca
`Error(err.detail)` **przed** gałęzią blobową (`lib/authedFetch.js:30` vs `:33`), więc 409/413
są widoczne dla frontendu mimo `responseType: 'blob'` — bez zmian w `authedFetch`.

### 13. MAJOR — stale/nieprecyzyjne odwołania — **[D] ZAAKCEPTOWANE w całości**

- **„ODPOWIEDZ/HANDOFF, ekran eksportu"** — Codex ma rację, że kanon nie ustanawia tego ekranu.
  Przepisane na **decyzję lokalną tego speca**, nazwaną wprost, z uzasadnieniem (u właściciela
  wszystko siedzi w `draft`, filtr po statusie odciąłby całą treść).
- **`Divider.js`** — cytaty rozdzielone wg tego, czego każdy dowodzi: definicja atrybutu
  `data-divider-style` to `:14-17` (`parseHTML`/`renderHTML` **atrybutu**), emisja w renderze
  **node'a** to `:84`. Sprawdzone w pliku; v0.2 mieszała jedno z drugim i podawała `:80-92`.
- **„Asercja `--light` potwierdzona"** — usunięte słowo „asercja". Dowodem jest pięć odpowiedzi
  NIE w tabeli bramek, nie jakaś uruchomiona komenda; v0.2 sugerowała inaczej.
- **manifest a przyszły import** — dołożony kontrakt: `version: 1`, nakaz ignorowania nieznanych
  pól i odrzucania nieznanej wersji, schemat wpisu dla obrazu pominiętego (`skipped` + `reason`,
  bez `file`/`bytes`), i zdanie, że rozdział bez treści nie trafia do manifestu, bo endpoint
  odrzuca eksport wcześniej.

---

## Sweep przeprowadzony (LESSONS#3)

Zmiana >100 LOC w jednym pliku → sweep po starych frazach:

| Komenda | Wynik |
|---|---|
| `rg -n 'D1\|D2\|D3\|O1' SPEC-MD-EXPORT.md` | **2 hits** (`:268`, `:662`) — oba to zdania „dawne O1, zamknięte". Zero wystąpień D1/D2/D3 i zero „do potwierdzenia w review" |
| `rg -n '80 min\|~80' SPEC-MD-EXPORT.md` | (empty) — rozjazd 80/90 min usunięty |
| `rg -n 'book_slug' SPEC-MD-EXPORT.md` | (empty) — wszystkie wystąpienia przemianowane na `book_key` |
| `rg -n 'koszt zabezpieczenia zerowy\|z grubsza' SPEC-MD-EXPORT.md` | **1 hit** (`:587`) — zdanie dokumentujące PORZUCENIE kryterium „z grubsza". Fraza „koszt zabezpieczenia zerowy": zero hitów |
| `rg -n 'Wersja:\*\* 0\.2' SPEC-MD-EXPORT.md` | (empty) — nagłówek na 0.3 |
| `rg -n '[Mm]odal' SPEC-MD-EXPORT.md` | **10 hits**, wszystkie w §Sizing (descope), §Ograniczenia, §Co odrzucone i notatce dla przyszłego speca — zero pozostałości w zakresie fazy |

`DELTA` względem `.base-R1.md`: **673 zmienione linie**.

---

## Proactive drain

Sekcja `## Proactive suggestions` miała 2 wpisy:

- **Workflow** — „Preflight parsera powinien generować przypadki z regexów rzeczywistego
  konsumenta, bo self-test własnego regexu może być zielony przy niepełnym kontrakcie."
  → `RETRO.md` (FABRYKA).
- **Risk flag** — „Globalna unikalność oparta na tytule książki jest pozorna; identyfikator
  przestrzeni roboczej musi przeżyć dwa projekty o identycznym tytule."
  → `PROACTIVE-INBOX.md`. Uwaga jest już **zrealizowana** w v0.3 (§`book_key`), zapisana dla
  śladu jako klasa problemu, nie jako otwarty punkt.

---

## Bramka 4a — zakaz rund potwierdzających

`DELTA` (diff `.base-R1.md` ↔ `SPEC-MD-EXPORT.md`) **znacznie > 0** — spec przepisany w ośmiu
sekcjach, dwie nowe (`book_key`, Kontrakt escapingu), jedna usunięta („Decyzje wymagające
potwierdzenia"). Bramka nie ma zastosowania, R2 wnosi nowy tekst.

## STOP-and-SPIKE

Nie dotyczy — N=1, brak poprzedniej rundy do porównania rdzenia.

---

## Następny krok

STATE `spec: R1-opus-pending` → auto-handoff R2. Została **jedna runda**: R2 musi wyjść GREEN
albo spec idzie do ESCALATED.

---

## Dla Piotrka — jedno zdanie

Przerobiłem wszystkie 13 uwag, zamknąłem trzy Twoje decyzje w specu (przycisk zamiast modala,
klucz książki z UUID-em, filtr zmian wypada) i przepisałem regułę escapingu z prawdziwego
chunkera Redaktora zamiast z głowy — spec jest w wersji 0.3 i idzie do Codexa na R2.

**Kopiuj dalej — w tym samym wątku:**
```
(nic — R2 leci automatycznie)
```
