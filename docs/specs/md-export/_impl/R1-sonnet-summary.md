# Implementation R1 — Sonet

**Data:** 2026-08-07
**Faza:** `SPEC-MD-EXPORT.md` (light spec, `N=1`, brak `PHASE-*.md`)
**Wersja speca implementowana:** **0.4.1**
**Commit:** brak — `/spec-impl` nie commituje. HEAD nadal `1871f07`, zmiany w worktree.

## Preflight check (TYLKO w R1)

- Spec jednoznaczny? **NIE w jednym miejscu** — §Tabela reguł i §Krok 4 G3 są wzajemnie
  sprzeczne na realnym materiale (patrz „Znaleziska" #2). Reszta jednoznaczna.
- Sizing trzyma się limitów (≤8 plików, ≤500 LOC)? **Oś plików ✓ 5/5. Oś LOC ✗** —
  ~1159 zamiast ~582 (patrz „Sizing").
- Brakujące zależności? brak. `pytest` doinstalowany lokalnie, `requirements.txt` **nietknięty**
  zgodnie ze specem.
- Czy poprzednie fazy są implemented? n/d — light spec, brak zależności fazowych.
- Backstop C/M/E: `_review/R3-opus-preflight.md` §Audyt C/M/E — **8 rekordów, wszystkie PASS** ✓
- Ripple cross-fazowy: brak wpisów w STATE.md — n/d

## Co zrobione

1. **`app/services/md_exporter.py` (NOWY, 540 LOC)** — `chapter_to_markdown()`, `slugify()`,
   `sha256_nfc()`, `escape_line()`, `build_book_key()`, dekodowanie `data:` URI, `count_blocks()`.
2. **`test_md_exporter.py` (NOWY, 368 LOC)** — **110/110 zielonych** (`python -m pytest -q`, 0.42 s,
   przebieg powtórzony w tym wątku).
3. **`POST /projects/{project_id}/export-md`** w `export_import.py` (+203) — sygnatura
   z §Endpoint, budowa ZIP-a i manifestu, asercja unikalności nazw, limit 80 MB, 409 przy braku
   `processed_html`, 413 przy obrazie >10 MB, `log_activity`.
4. **Przycisk w `EditorPage.jsx` (+47)** ze stanami z §Frontend + etykieta
   w `activityLabels.js` (+1). `npm run build` **PASS** (1m40s, 190 modułów).
5. **Sprawdzian odbiorczy wejść body** — `R1-sprawdzian-body.md`, **6/6 wykonanych PASS**.
6. **Bramka kontraktowa G1–G4** — `R1-bramka-G1-G4.md`, **3/4 PASS, G3 FAIL** (sprzeczność speca).

## Pliki zmienione

| Plik | Zmiana |
|---|---|
| `tiolibri-api/app/services/md_exporter.py` | NOWY, 540 LOC |
| `tiolibri-api/test_md_exporter.py` | NOWY, 368 LOC |
| `tiolibri-api/app/routers/export_import.py` | +203 |
| `tiolibri-frontend/src/features/editor/EditorPage.jsx` | +47 |
| `tiolibri-frontend/src/features/editor/activityLabels.js` | +1 |

`docs/specs/md-export/_impl/*` (ten plik, dwa raporty, `harness/`) to **artefakty review,
nie implementacja** — do osi plików sizingu nie wchodzą.

## Testy

- **Automatyczne:** 110/110 zielonych. Pokryte: cała tabela reguł konwersji, escaping
  (12 wzorców × 4 wcięcia + 4 negatywne), wszystkie 8 fixture'ów `blocks` (każdy asertuje
  **cały słownik**), reguły `data:` URI, `alt`, URL-e, slug/`book_key`/sha256, regresja
  „`data:` nie występuje w wyjściu".
- **`npm run build`:** PASS.
- **Ręczne (żywy backend :8000):** 6 wariantów body — a–d obowiązkowe + 404 i 422. Wszystkie PASS.
- **Bramka na żywym materiale:** prawdziwy `segmentuj()` (FABRYKA-redaktor `redaktor` @ `134f8e4`,
  Node v24.12.0) na naszym własnym `.md`. Rozdz. 8 Ewy = 210 chunków; puszczone dodatkowo
  na **wszystkich 12 rozdziałach = 1141 chunków**.

## Dwa zapytania SQL, które spec kazał wykonać przy implementacji — WYKONANE

- `chapters` z `data:image` w treści → **0**
- `processed_html` NULL albo puste (nieusunięte) → **0**

Czyli ścieżka `data:` jest dziś **czysto defensywna**, a fail-closed 409 **nie ma jak strzelić
na produkcji**. Obie ścieżki zostają — spec chce je mieć zanim wejdzie materiał, który je odpali.

## Znaleziska — trzy, wszystkie do werdyktu Codexa

### 1. lxml po cichu gubi atrybut >10 MB — reguła 413 była nieegzekwowalna

libxml2 (`XML_MAX_TEXT_LENGTH`) **wyrzuca atrybut dłuższy niż ~10 MB**. Obraz `data:` ponad
limit — dokładnie ten, który wg §Limity ma dać **413** — tracił `src` przy parsowaniu i wypadał
jako `unsupported_scheme`, **po cichu**. Reguła fail-closed była nieegzekwowalna narzędziem,
które spec wskazał. Złapane testem `test_obraz_ponad_10mb_rzuca_wyjatek` (jedyny, który padł
w pierwszym przebiegu).

**Poprawka:** przy dokumencie ≥10 MB `chapter_to_markdown` parsuje `html.parser` zamiast `lxml`
(`_LXML_TEXT_LIMIT`). Poniżej progu nic się nie zmienia. **Świadome odstępstwo od §Kontrakt
konwersji** („Parser: BeautifulSoup + lxml") — nazwane, do werdyktu.

### 2. G3 nie do przejścia razem z §Tabelą reguł — bramka stoi na tym

Google Docs owija treść **każdego** nagłówka w `<strong>`. §Tabela reguł każe `<strong>` → `**…**`,
więc emitujemy `## **Tekst**`. G3 porównuje to z `get_text()` źródłowego `<hN>` i dopuszcza
normalizację **tylko** białych znaków i wielkości liter — markery zostają i równość pada.

Na rozdz. 8: **29/30 nagłówków różnych, liczba (30=30) i ciąg poziomów zgodne co do jednego**,
a **po zdjęciu markerów emfazy różnic 0/30**. Na wszystkich 12 rozdziałach — ten sam,
jedyny rozjazd. Struktura nietknięta (`## **tekst**` daje chunk `naglowek`, stąd G1 PASS).

Źródło luki: G3 to „symulacja K-NAG", ale K-NAG porównuje **md do md** — obie strony niosą te
same `**`, więc jego lista normalizacji mu wystarcza. Spec przeniósł ją do porównania
**md do HTML**, gdzie strony nie są symetryczne, i nie dopisał emfazy. **Prawdziwemu K-NAG
przy `apply` ten rozjazd nie grozi.**

Dwa wyjścia — **(A)** normalizacja G3 zdejmuje markery emfazy; **(B)** konwerter nie emituje
markerów, gdy emfaza obejmuje **całą** treść nagłówka (częściowa zostaje). **Żadnego nie
zaimplementowałem** — oba są zmianą kontraktu.

**Rekomenduję (B), z dowodu w kodzie konsumenta** (gałąź `redaktor` @ `134f8e4`):
`chunkuj.ts:13` ustawia `nietykalny` **tylko** dla `kod` i `tabela` — a te są u nas twardymi
zerami (G2), więc **nagłówki są chunkami edytowalnymi** i wszystkie 30 idzie do W2. K-NAG
normalizuje wyłącznie białe znaki i wielkość liter (A4), więc `**` jest dla niego częścią tekstu,
a jego FAIL **rzuca wyjątek przed publikacją**. Czyli każde `**` w nagłówku to mina pod `apply`:
model gubi parę gwiazdek przy przepisywaniu i pada cały przebieg po setkach cykli operatora.
**(A) jest gorsze niż neutralne** — rozluźnia bramkę dokładnie o tę emfazę, która potem wysadza
K-NAG. Pełny wywód: `R1-bramka-G1-G4.md` §Rekomendacja.

### 3. Wiersz „projekt bez rozdziałów" nieodpalony

Żaden projekt właściciela nie ma zera nieusuniętych rozdziałów; odpalenie wymagałoby założenia
atrapy w **produkcyjnej** bazie. Gałąź jest w kodzie (`export_import.py:177-178`) i leży **przed**
filtrem `chapter_ids`. Do decyzji, czy chcemy atrapę.

## Decyzje implementacyjne

1. **`chapter_to_markdown(..., pad: int = 2)`** — dodatek ponad sygnaturę ze speca, wymuszony
   przez §`book_key`: padding `NNN` obowiązuje **cały** eksport przy >99 rozdziałach, a z samego
   `position` tej decyzji podjąć się nie da. Addytywne — wywołanie z dokumentacji działa bez zmian.
2. **`ExportImage.mime_unknown: bool = False`** — jw.; manifest ma udokumentowany klucz
   `"mime_unknown": true`, a bez nośnika nie ma go z czego wyprodukować.
3. **Parser warunkowy przy ≥10 MB** — znalezisko #1.
4. **Token do sprawdzianu ręcznego wybity przez `admin/generate_link` → `auth/v1/verify`**,
   nie wyklikany we frontendzie. `verify_supabase_jwt` waliduje go u dostawcy, więc to pełna
   ścieżka autoryzacji, nie obejście — i sprawdzian da się powtórzyć bez przeglądarki.

## Sizing — przekroczony grubo ponad dyspensę, do werdyktu właściciela

| Plik | Spec | Faktycznie |
|---|---|---|
| `md_exporter.py` (NOWY) | ~300 | **540** |
| `test_md_exporter.py` (NOWY) | ~165 | **368** |
| `export_import.py` | ~85 | **+203** |
| `EditorPage.jsx` | ~30 | **+47** |
| `activityLabels.js` | ~2 | **+1** |
| **razem** | **~582** | **~1159** |

Oś **plików trzyma: 5/5**. Oś LOC to **~2× dyspensowana liczba** — dyspensa z R1/R2 obejmowała
~82 LOC ponad limit 500, nie 659. Główny narzut: `count_blocks()` jest wierną reimplementacją
`segmentuj()` (~78 LOC samego licznika) i fixture'y `blocks` rozrosły się na wariantach wcięć.
**Nie „naprawiam" tego wycinaniem testów** — to decyzja Piotrka.

## Co odłożone

- **G3** — czeka na werdykt (A)/(B). Po decyzji domyka się jedną zmianą.
- **Wiersz „projekt bez rozdziałów"** — czeka na zgodę na atrapę w produkcji.
- **Prawdziwy K-NAG przy `apply`** — z definicji poza tą fazą (§Krok 4: osobny, ręczny przebieg
  właściciela).

## Proactive suggestions

Brak — trzy znaleziska wyżej wyczerpują to, co znalazłem.

---

## Dla Piotrka — jedno zdanie

Eksport MD działa end-to-end na Twoich prawdziwych książkach: 110/110 testów, sprawdzian
endpointu 6/6, a prawdziwy chunker Redaktora policzył 1141 chunków z 12 rozdziałów Ewy i zgodził
się z naszym manifestem **co do jednego bloku** — jedyne, co nie przeszło, to porównanie tekstu
nagłówków, bo Google Docs pogrubia każdy nagłówek, a spec w dwóch miejscach każe z tym zrobić
dwie sprzeczne rzeczy i ktoś musi wybrać którą.

**Kopiuj dalej:**
```
Sonet skończył md-export impl R1 (draft, G3 czeka na werdykt). Wygeneruj prompt Codex /spec-review dla mnie.
```
