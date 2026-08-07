# R1 — bramka kontraktowa G1–G4 (§Krok 4)

**Data:** 2026-08-07
**Materiał wymagany przez spec:** rozdz. 8 Ewy — „ROZDZIA8SuplementacjaCodziaaconieijaktorobido"
(`54929ca6-d18b-43a9-8052-808d29196e0f`), 35 337 znaków HTML → 32 406 znaków MD.
Najgęstszy od liczb i dawek w książce, zgodnie z ODPOWIEDZ ERRATA E3.
**Bramkę przepuszczono ponadto przez wszystkie 12 rozdziałów** — patrz §Przebieg szeroki.

## Narzędzie — prawdziwy chunker, nie reimplementacja

`segmentuj()` z **`FABRYKA-redaktor`, gałąź `redaktor`, HEAD `134f8e4`** (ten sam, który
HANDOFF notuje jako kanon konsumenta — zweryfikowany `git rev-parse` w tym wątku),
plik `src/redaktor/chunker/segmentuj.ts`, odpalony przez
`node v24.12.0 --experimental-strip-types`, import po ścieżce bezwzględnej.
**Zero pythonowej reimplementacji w torze bramki** — `count_blocks()` z `md_exporter.py`
jest tu stroną **porównywaną** (przez `manifest.chapters[i].blocks`), nie stroną mierzącą.

Wejściem jest **nasz własny plik `.md` wyjęty z ZIP-a endpointu**, nie plik pośredni.

**Rozdz. 8 → 210 chunków.** (Rząd wielkości zgadza się ze ZWIAD-EWA-R8: 215 chunków na pliku
źródłowym z Google Docs; nasz eksport daje 210 na tym samym rozdziale.)

## Wynik — rozdz. 8

| # | Asercja | Tolerancja | Wynik |
|---|---|---|---|
| **G1** | rozkład typów chunków == `manifest.chapters[i].blocks`, dla każdego typu | zero | **PASS** |
| **G2** | `blocks.kod == 0` ∧ `blocks.tabela == 0` ∧ zero chunków tych typów | zero | **PASS** |
| **G3** | ciąg nagłówków w `chunks.json` == ciąg `<h1..h6>` w źródłowym HTML | zero | **FAIL** — patrz niżej |
| **G4** | żaden chunk nie jest frontmatterem ani metadanymi | zero | **PASS** |

**G1 — dane:**
`manifest = {naglowek: 30, akapit: 170, lista: 10, blockquote: 0, kod: 0, tabela: 0}`
`chunks   = {naglowek: 30, akapit: 170, lista: 10, blockquote: 0, kod: 0, tabela: 0}`
Typów spoza manifestu: **brak**. Równość na każdym typie, w tym `lista` — czyli dokładnie to,
czego R2 zażądał, rozdzielając `lista` z G2 do G1.

**G2 — dane:** manifest `kod=0 tabela=0`; chunków `kod=0 tabela=0`. Zero przecięcia z G1.

**G4 — dane:** zero chunków, których pierwsza linia pasuje do separatora YAML/TOML (`---`, `+++`)
albo do klucza metadanych (`title:`, `chapter_id:`, `book_key:`, `position:`, `hash:`, `blocks:` …).
Manifest siedzi w `_tiolibri/manifest.json` **obok** plików prozy i nie wchodzi do żadnego chunka —
dowód, że A3 zadziałało.

## G3 — FAIL: jedna przyczyna, w pełni scharakteryzowana

**Objaw:** 29 z 30 nagłówków rozdz. 8 różni się tekstem. **Liczba nagłówków (30 = 30)
i ciąg poziomów zgadzają się co do jednego** — rozjeżdża się wyłącznie tekst.

**Przyczyna:** Google Docs owija treść każdego nagłówka w `<strong>`:

```html
<h2><strong>WAPŃ - Fundament, ale nie taki prosty.</strong></h2>
```

Konwerter — **zgodnie z §Tabela reguł**, wiersz `<strong>`, `<b>` → `**…**` — emituje:

```markdown
## **WAPŃ - Fundament, ale nie taki prosty.**
```

G3 porównuje to z `get_text()` źródłowego `<hN>`, czyli z tekstem **bez** markerów. Normalizacja,
którą G3 dopuszcza, to wyłącznie białe znaki i wielkość liter — markery emfazy zostają i psują
równość.

**Dowód, że to jedyna przyczyna:** po zdjęciu markerów emfazy (`**`, `*`, `__`, `_`) z tekstu
nagłówka chunkowego różnic jest **0/30**. Nie ma drugiej klasy rozjazdu — ani gubionego
nagłówka, ani przestawionego poziomu, ani uciętego tekstu.

**Struktura jest nietknięta:** `## **tekst**` jest przez `RE_ATX` łapane normalnie i daje chunk
`typ: naglowek` — dlatego G1 przechodzi z zerową tolerancją. Szkoda jest czysto tekstowa.

### To jest sprzeczność wewnątrz speca, nie błąd implementacji

§Tabela reguł mówi `<strong>` → `**…**` **bez wyjątku dla nagłówka**. §Krok 4 G3 wymaga
równości tekstu nagłówka z `get_text()` HTML-a przy zerowej tolerancji. Na realnym materiale
z Google Docs — gdzie **każdy** nagłówek jest `<strong>` — **oba zapisy nie mogą być prawdziwe
naraz**. Implementacja spełnia pierwszy i dlatego łamie drugi.

Skąd luka: G3 jest opisane jako „lokalna symulacja K-NAG", a K-NAG (ODPOWIEDZ A4) porównuje
**md do md** — obie strony jego porównania niosą te same `**`, więc u niego markery nigdy nie
trafiają w różnicę, i normalizacja „białe znaki + wielkość liter" mu wystarcza. Spec przeniósł
tę listę normalizacji do porównania **md do HTML**, gdzie strony nie są symetryczne, i przy tym
przeniesieniu nikt nie dopisał emfazy. **Prawdziwemu K-NAG przy `apply` ten rozjazd nie grozi.**

### Dwa wyjścia — do werdyktu Codexa i decyzji Piotrka. Nie wybrałem sam

- **(A) Poprawka w G3:** normalizacja G3 zdejmuje też markery emfazy — porównujemy tekst
  z tekstem. Nie rusza wyjścia dla redaktora. Ryzyko: bramka przestaje widzieć emfazę dodaną
  w nagłówku przez konwerter.
- **(B) Poprawka w konwerterze:** gdy `<strong>`/`<em>` obejmuje **całą** treść nagłówka,
  markery są redundantne (nagłówek i tak jest wyróżniony) i nie są emitowane; emfaza
  **częściowa** w nagłówku zostaje. G3 przechodzi wtedy dosłownie. Ryzyko: zmiana §Tabeli reguł,
  dotyka **każdego nagłówka każdej książki**, i przyszły `md-import` nie odtworzy `<strong>`.

**Nie zaimplementowałem żadnego z nich.** Oba są zmianą kontraktu — (A) rozluźnia bramkę,
którą sam bym potem zdał, (B) przepisuje wiersz §Tabeli reguł. Po tym, jak sizing i tak wyszedł
2× ponad dyspensę, cichy wybór po stronie implementatora byłby nadużyciem.

### Rekomendacja Sonnetu: **(B)** — dowód z kodu konsumenta, dopisany po napisaniu raportu

Trzy fakty z gałęzi `redaktor` @ `134f8e4`, które przesądzają sprawę na korzyść (B):

1. **Nagłówki są chunkami EDYTOWALNYMI.** `chunker/chunkuj.ts:13` —
   `nietykalny: blok.typ === "kod" || blok.typ === "tabela"`. Nietykalne są **wyłącznie** te dwa
   typy, a w naszym eksporcie oba są twardymi zerami (to właśnie stwierdza G2). Czyli wszystkie
   **30 nagłówków rozdz. 8 idzie do W2 jako materiał do przepisania przez model.**
2. **K-NAG normalizuje tylko białe znaki i wielkość liter** (ODPOWIEDZ A4) — markery `**` są
   dla niego **częścią tekstu** nagłówka, tak samo jak dla G3.
3. **FAIL K-NAG rzuca wyjątek PRZED fazą publikacji** (`cli/apply.ts` krok 7) — `output.md`
   w ogóle nie powstaje.

Złożenie: **każde `**` w nagłówku jest miną pod najdroższym etapem przebiegu.** Model
przepisujący nagłówek ma trzydzieści okazji na rozdziale, żeby zgubić albo przesunąć parę
gwiazdek — a wtedy pada **cały `apply`**, po setkach cykli stop-wypełnij-wznów, które operator
ma już za sobą (§Krok 4, skala pracy operatora). To ryzyko nie jest kosmetyczne.

**Dlatego (A) jest gorsze niż neutralne:** rozluźnia bramkę dokładnie o tę emfazę, która potem
wysadza K-NAG. Bramka by przeszła i **tym samym przestałaby ostrzegać** przed jedyną rzeczą,
przed którą tu ostrzega.

**Kontrargument przeciw (B) jest słaby:** `<strong>` obejmujący **całą** treść nagłówka to
artefakt Google Docs, nie decyzja typograficzna autorki — nagłówki i tak są wyróżnione przez CSS
presetu, więc `md-import` nie odtwarzając go niczego wizualnie nie traci. Emfaza **częściowa**
w nagłówku zostaje nietknięta i dalej niesie informację.

**Zakres (B):** gdy `<strong>`/`<em>` obejmuje całą treść nagłówka (po zwinięciu białych znaków),
markery nie są emitowane. Poza nagłówkami — bez zmian. §Tabela reguł dostaje wyjątek w wierszu
`<h1>…<h6>`. Koszt: kilka LOC w `md_exporter.py` + test w obie strony (pełna i częściowa emfaza).

## Przebieg szeroki — wszystkie 12 rozdziałów (ponad wymagania speca)

Spec zamawia bramkę na jednym rozdziale. Puściłem ją na całym eksporcie, żeby odróżnić usterkę
punktową od systemowej — **1141 chunków łącznie**:

| poz | chunków | G1 | G2 | G3 dosłownie | G3 bez emfazy | G4 | nagłówki różne/wszystkie |
|---|---|---|---|---|---|---|---|
| 1 | 57 | PASS | PASS | FAIL | PASS | PASS | 9/9 |
| 2 | 127 | PASS | PASS | FAIL | PASS | PASS | 5/7 |
| 3 | 73 | PASS | PASS | FAIL | PASS | PASS | 22/23 |
| 4 | 86 | PASS | PASS | FAIL | PASS | PASS | 24/25 |
| 5 | 63 | PASS | PASS | FAIL | PASS | PASS | 21/22 |
| 6 | 82 | PASS | PASS | FAIL | PASS | PASS | 26/28 |
| 7 | 80 | PASS | PASS | FAIL | PASS | PASS | 27/27 |
| 8 | 88 | PASS | PASS | FAIL | PASS | PASS | 28/29 |
| **9 (rozdz. 8 — materiał bramki)** | **210** | **PASS** | **PASS** | **FAIL** | **PASS** | **PASS** | **29/30** |
| 10 | 79 | PASS | PASS | FAIL | PASS | PASS | 21/22 |
| 11 | 141 | PASS | PASS | FAIL | PASS | PASS | 27/28 |
| 12 | 55 | PASS | PASS | FAIL | PASS | PASS | 9/10 |

**Zbiorczo 12/12: G1 PASS · G2 PASS · G4 PASS · G3 FAIL dosłownie, PASS po normalizacji emfazy.**

Wniosek: G1/G2/G4 trzymają zerową tolerancję na całej książce, nie tylko na wybranym rozdziale.
G3 rozjeżdża się na **każdym** rozdziale i **zawsze z tej jednej przyczyny** — to potwierdza
diagnozę „sprzeczność w specyfikacji", a nie „przypadkowa usterka na trudnym rozdziale".

## Werdykt bramki

**3/4 PASS (G1, G2, G4) · G3 FAIL zablokowane sprzecznością §Tabela reguł ↔ §Krok 4 G3.**
Decyzja (A) vs (B) należy do Codexa/Piotrka; po niej G3 domyka się jedną zmianą.

## Odtwarzalność

Skrypty przebiegu (poza repo, scratchpad sesji): `chunkuj.mjs` (most do prawdziwego
`segmentuj()`), `bramka.py` (G1–G4 na rozdz. 8), `bramka_all.py` (12/12).
Wejście: ZIP-y z wariantów (a) i (d) sprawdzianu body — patrz `R1-sprawdzian-body.md`.
