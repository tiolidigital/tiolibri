**Temat:** książka Ewy — podtytuł na stronie tytułowej wdrożony na produkcję — bo Ewa ogląda 2026-08-18 i ma zobaczyć komplet: tytuł, podtytuł, autora, a pliki mają się nazywać po ludzku

# HANDOFF — 2026-08-17

## NASTĘPNY KROK — jeden

**Klik-test na produkcji: wejść na projekt Ewy, wygenerować PDF i EPUB, sprawdzić dwie rzeczy naraz.**

https://app.tiolibri.com/editor/1f23458e-b63a-4b29-a912-cced19ce3e47

1. Strona tytułowa niesie **trzy** linijki: `Kości na całe życie` /
   `Przewodnik żywieniowy po diagnozie osteoporozy` / `Prof. dr hab. n. med. Ewa Stachowska`.
2. Pobrany plik nazywa się **`kosci-na-cale-zycie.pdf`**, a nie `ko-ci-na-ca-e-ycie.pdf`.

Wszystkie warstwy są wdrożone i sprawdzone osobno (kod na produkcji, kolumna w bazie,
wartość wpisana, generator przetestowany lokalnie na tym samym kodzie). Czego NIE ma:
jednego przebiegu end-to-end na produkcji — wymagał JWT, a wątek dobijał do progu kontekstu.
To jest jedno kliknięcie „Generuj".

## Co zrobiono w tym wątku

### 1. Podtytuł książki — commit `40c8ffb`

Tabela `projects` nie miała pola na podtytuł. Doszło przez wszystkie cztery warstwy:

- **Migracja** [20260817_add_subtitle.sql](tiolibri-frontend/docs/migrations/20260817_add_subtitle.sql)
  — `ALTER TABLE projects ADD COLUMN IF NOT EXISTS subtitle text`, nullable, bez defaultu.
  **Wykonana na produkcji**, zweryfikowana przez `information_schema`.
- **PDF** — reguła `.title-page .subtitle` (15pt, #333) + warunkowy render między `h1` a autorem.
- **EPUB** — analogicznie. Uwaga: w EPUB `.title-page`/`.author` **nie mają żadnego CSS**
  (nav.css to preset treści), więc strona tytułowa jedzie na domyślnych stylach czytnika.
  Podtytuł zrobiony spójnie z autorem, presetów nie ruszałem.
- **Nie ginie po drodze**: duplikacja projektu, eksport/import `.tiolibri`, snapshoty + restore.
- **Escapowany** przez `html.escape` — `&` w tym polu łamało XHTML w EPUB (czytnik odmawia).

Sprawdzone na czterech przypadkach (z podtytułem, bez, brak klucza, znaki XML), PDF + EPUB.
**Wariant bez podtytułu daje PDF identycznego rozmiaru co przed zmianą** — zero regresji
dla pozostałych projektów.

### 2. Bug skaczącego kursora — ten sam commit

Przyczyna: `handleUpdateProject` w EditorPage awaitował Supabase **przed** `setProject`,
a input jest kontrolowany przez `project.title`. Między keystrokiem a odpowiedzią bazy
React przerysowywał input starą wartością. Stąd „Życie**b**".

Rozbite na `persistProjectField` (zapis) i `handleUpdateProjectText` (stan synchronicznie,
zapis debounced 600 ms). Przy okazji koniec z jednym `UPDATE` na każdy znak. Sprawdzone,
że nic innego nie nadpisuje `project` w trakcie pisania — `fetchProject` woła się tylko
przy montowaniu i po restore snapshotu.

### 3. Nazwy plików: transliteracja zamiast wycinania — commit `1758807`

Zgłoszone przez właściciela: pobierane pliki nazywały się `ko-ci-na-ca-e-ycie…`.
Przyczyna: `[^a-z0-9]` po `toLowerCase()` — każda polska litera stawała się myślnikiem.

Nowy [lib/filename.js](tiolibri-frontend/src/lib/filename.js) (`transliterate` + `bookFilename`)
powtarza kroki `slugify()` z `md_exporter.py`, żeby front i backend nazywały pliki tak samo.
**Mapa liter jest konieczna, bo NFKD nie rozkłada `ł`** — to osobny znak, nie `l` z diakrytykiem,
i właśnie on wypadał (`całe` → `cae`).

Ten sam błąd siedział w **trzech** miejscach, nie w jednym: `GenerateBooks` (PDF/EPUB, na `-`),
`ProjectCard` (eksport `.tiolibri`, na `_`), `EditorPage` (paczka dla redaktora, na `_`).
Poprawione wszystkie + ASCII-fallback nagłówka `Content-Disposition` po stronie backendu;
`slugify()` korzysta teraz ze wspólnego `to_ascii()`.

Sprawdzone: `Kości na całe życie` → `kosci-na-cale-zycie.pdf`, `ŁÓDŹ ŹDŹBŁO` → `lodz-zdzblo`,
`ąćęłńóśźż ĄĆĘŁŃÓŚŹŻ` → `acelnoszz ACELNOSZZ`. Front i backend dają identyczny wynik.

### 4. Dane projektu Ewy

`subtitle` = `Przewodnik żywieniowy po diagnozie osteoporozy` (dosłownie z okładki).
Bez myślnika, więc sprawa półpauz vs em dashy tu nie występuje.

### 5. Deploy — zrobiony

Push `main` (4 commity: `b4613e1`, `2fa86e0`, `40c8ffb`, `1758807`). Zweryfikowane:

- **Vercel / app.tiolibri.com** — bundle zawiera „Podtytuł (opcjonalny)" i mapę transliteracji.
  Uwaga: hash bundla na produkcji ≠ hash z lokalnego builda, bo `VITE_API_URL` się różni
  — nie porównywać hashy, szukać stringów.
- **Railway / API** — `subtitle` widoczny w `Project` w `/openapi.json`. Deploy zszedł w ~30 s.

## Stan: pliki, commity

- **HEAD `1758807`**, `main` == `origin/main`, wszystko wypchnięte.
- `40c8ffb` — podtytuł + fix kursora (9 plików). `1758807` — transliteracja nazw (7 plików).
- Hook repo bumpuje wersję przy commicie: `1.0.31 → 1.0.33`.
- Projekt: `1f23458e-b63a-4b29-a912-cced19ce3e47`

## Jak wykonać SQL na tej bazie (przydało się, zapisane w pamięci)

Management API `POST https://api.supabase.com/v1/projects/{ref}/database/query`,
autoryzacja **samym `SUPABASE_ACCESS_TOKEN`, który już jest w `tiolibri-api/.env`**.
Ref: `klhnyagtobgtxnexdsls`. **Pułapka: Cloudflare odbija domyślny User-Agent `urllib`
błędem HTTP 403 / `error code: 1010`** — wygląda jak brak uprawnień, a to blokada UA.
Ustawić własny nagłówek `User-Agent`. Skrypt: `scratchpad/run_migration.py`.

## Znane, nietknięte

- **`title` i `author` NIE są escapowane w generatorach** — `&` w tytule złamie XHTML w EPUB.
  Podtytuł już jest bezpieczny, tamte dwa nie. Nie ruszałem, żeby nie dokładać regresji
  dzień przed pokazem.
- **`NewProjectModal` nie ma pola podtytułu** — ustawia się go w Project Details.
- **Błąd numeracji w treści R10**: ostatni H2 to `Podsumowanie rozdziału 11.`, a to rozdział 10.
- **Druga runda R8** — cofnięcie `e-006` (KLU) i `e-001` (WAR).
- **Bożena** — linijka do Fabryki; od tego wisi ich agregator (PHASE-22).
- **`.DS_Store` śledzony w gicie**, brak go w `.gitignore`.
- **Spec `porzadek-wersji` — ZAPARKOWANY** (R4 = REQUEST_CHANGES, 12 blokerów).
  Jego §78 o „nazwie książki" dotyka tego samego bólu co dzisiejsza robota.

## Kanon: BAZA, nie Fabryka

Kanonem treści jest projekt `1f23458e` w bazie. `docs/dostawy/_import-ewa/dry-run/` jest nieaktualny.

## Em dashe

W książce mają być **półpauzy (– U+2013), nigdy em dashe (— U+2014)**. Stan: 719 półpauz,
1 em dash — w oryginalnym angielskim tytule publikacji w R14, cytat bibliograficzny,
**zostawić**. Nie wstawiać em dashy do treści ani do pól projektu.

**Model docelowy: Opus.**
