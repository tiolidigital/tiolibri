**Temat:** książka Ewy — czyszczenie nagłówków i strony tytułowej przed pokazaniem autorce — bo Ewa ogląda 2026-08-18 i nie może zobaczyć literówek ani rozjazdu wersalików

# HANDOFF — 2026-08-17

## NASTĘPNY KROK — jeden

**Dodać podtytuł książki na stronę tytułową: „Przewodnik żywieniowy po diagnozie osteoporozy".**

Tabela `projects` **nie ma pola na podtytuł** (kolumny: `author`, `cover_image_url`,
`created_at`, `custom_styles`, `id`, `language`, `status`, `style_preset`, `title`,
`typography_settings`, `updated_at`, `user_id`). Więc to zmiana kodu produkcyjnego,
nie danych — i dlatego jej **nie zacząłem** (kontekst wątku dobił do progu).

Zakres, gdyby robić: migracja `ALTER TABLE projects ADD COLUMN subtitle text`
→ [pdf_generator.py:468-473](tiolibri-api/app/services/pdf_generator.py#L468-L473)
(blok `title-page`, + reguła CSS koło [pdf_generator.py:183](tiolibri-api/app/services/pdf_generator.py#L183))
→ `epub_generator.py` (strona tytułowa) → input w Project Details.
**Właściciel jeszcze nie zdecydował, czy to idzie przez `/spec-draft`** — zapytać.

## Do naprawy przy okazji (zgłoszone przez właściciela)

**Bug w Project Details: przy pisaniu w polu tytułu kursor skacze na początek/koniec linii.**
Właśnie przez to w tytule wylądowało „Życie**b**" — właściciel próbował wpisać półpauzę.
Nie diagnozowałem. Podejrzenie: kontrolowany input przepisywany po każdym keystroke
(ten sam wzorzec co naprawiony `loadContent` race w EditorPage) — szukać w komponencie
ustawień projektu we `tiolibri-frontend/src/features/projects/`.

## Co zrobiono w tym wątku

### 1. Wersaliki zdjęte z nagłówków — commit `b4613e1`

`text-transform` **nie występuje** w presetach ani generatorach — wersaliki były wpisane
literalnie w treść, więc to była edycja danych, nie CSS.

- **38 nagłówków** H1/H2/H3 + **12 `chapters.title`** w 12 z 14 rozdziałów.
- **10 nagłówków z CAPS zostawionych świadomie** (słownik `ZOSTAJE` w skrypcie):
  emfaza autorki (`Czego NIE znajdziesz`, `Co zrobić PO przeczytaniu?`,
  `Czego NIE suplementować`, `Interakcje – czego NIE łączyć`) i skróty
  (`SCFA` 4×, `DHEA`, `DEXA`).
- Dwa tytuły zmielone przez stary upload naprawione: `Zastrzeeniemedyczne` → `Zanim zaczniesz`,
  `Literaturaizrodanaukowe.md` → `Literatura i źródła naukowe`.

### 2. Pola projektu poprawione (zmiana w danych, bez commita)

| pole | przed | po |
|---|---|---|
| `title` | `Kości Na Całe Życieb 4.0 — po redakcji (2026-08-15)` | `Kości na całe życie` |
| `author` | `Profesor Ewa Stachowska` | `Prof. dr hab. n. med. Ewa Stachowska` |

Zapis autora **wzięty dosłownie z okładki** (`cover.jpg`, 1200×1804) — tam jest
`Prof. dr hab. n. med. Ewa Stachowska`, z wielkiego „P". Okładka niesie też podtytuł
(pionowo, różowym): **`Przewodnik żywieniowy po diagnozie osteoporozy`** — stąd NASTĘPNY KROK.

**Uwaga: stary tytuł był jedynym miejscem z em dashem w polach projektu — już go nie ma.**

### 3. Strona tytułowa — ZOSTAJE (decyzja właściciela)

Kod nietknięty. Uwaga na przyszłość: title page jest **bezwarunkowa**, nie ma flagi
do wyłączenia, generuje się nawet przy okładce.

## Em dashe — sprawdzone, jest czysto

Właściciel pilnuje, żeby w książce były **półpauzy (– U+2013), nigdy em dashe (— U+2014)**.
Stan po policzeniu w całej treści (14 rozdziałów, odczyt z bazy):

- **719 półpauz, 1 em dash.**
- Ten jeden em dash siedzi w R14 (Literatura), w **oryginalnym angielskim tytule publikacji**:
  `The Importance of Nutrition in Menopause and Perimenopause—A Review.` (Nutrients 2024).
  To dosłowny cytat bibliograficzny i angielska konwencja — **zostawić, nie „poprawiać".**
- Zamiany wersalików nie mogły dołożyć myślnika: podmiana szła token po tokenie i zmieniała
  wyłącznie wielkość liter.

**Reguła na przyszłość: nie wstawiać em dashy do treści ani do pól projektu.**

## Kanon: BAZA, nie Fabryka

Decyzja właściciela: w TIOLIBRI doszły PNG, literatura i disclaimer, których dostawa md nie zna;
Fabryka raczej nie będzie drugi raz pracować na tym ebooku. **`docs/dostawy/_import-ewa/dry-run/`
jest nieaktualny** — kanonem treści jest projekt `1f23458e` w bazie.

## Znane, nietknięte

- **Błąd numeracji w treści R10**: ostatni H2 to `Podsumowanie rozdziału 11.`, a to rozdział 10.
- **Druga runda R8** — cofnięcie `e-006` (KLU) i `e-001` (WAR).
- **Bożena** — linijka do Fabryki; od tego wisi ich agregator (PHASE-22).
- **`.DS_Store` śledzony w gicie**, brak go w `.gitignore`.
- **Spec `porzadek-wersji` — ZAPARKOWANY.** Jego §78 („trzy nośniki poza tytułem: notatka,
  etykieta wersji, **nazwa książki**") to dokładnie ten ból: tytuł projektu musi naraz
  służyć stronie tytułowej i wyszukiwaniu w dashboardzie.

## Stan: pliki, commity

- **HEAD `b4613e1`** — wersaliki + zaległa dostawa `ewa-2026-08-15` i konwerter `_import-ewa`.
  **Nie pushowane.**
- Zmiana `title`/`author` jest **wyłącznie w bazie**, nie ma jej w żadnym commicie.
- Skrypty: `docs/dostawy/_wersaliki/` — `pobierz.py` (backup + inwentarz),
  `zdejmij_wersaliki.py` (bez argumentu podgląd, `--wykonaj` zapisuje; bramki fail-closed
  przed i po zapisie). `backup-przed.json` = pełny stan sprzed zmian, do rollbacku.
- Projekt: `1f23458e-b63a-4b29-a912-cced19ce3e47` · https://app.tiolibri.com/editor/1f23458e-b63a-4b29-a912-cced19ce3e47

**Model docelowy: Opus.**
