**Temat:** obrazy w książce Bożeny — pobieranie EPUB-a, środkowanie grafik i podpisy pod nimi — bo Piotrek wgrywa teraz zdjęcia grzybów do testów i chce, żeby każde zdjęcie miało pod sobą nazwę grzyba, a nic się przy tym nie rozsypało

# HANDOFF — 2026-08-20 19:29 · HEAD 8a0ce4b

## STAN: wszystko LEŻY W WORKING TREE, NIC NIE WYPCHNIĘTE

Właściciel świadomie wstrzymał deploy („będzie jeszcze kilka rzeczy"). Zmienione pliki:

- `tiolibri-frontend/src/features/editor/GenerateBooks.jsx` — naprawione pobieranie EPUB-a
- `tiolibri-api/app/services/epub_generator.py` — okładka bez duplikatu + `img` na środku + figury
- `tiolibri-api/app/services/pdf_generator.py` — figury, plansze, alt z podpisu
- `tiolibri-frontend/src/features/editor/extensions/Figure.js` — NOWY węzeł TipTap
- `tiolibri-frontend/src/features/editor/ChapterEditor.jsx` — rejestracja Figure
- `tiolibri-frontend/src/features/editor/EditorToolbar.jsx` — wgranie wstawia figurę + guzik „Plansza"
- `tiolibri-frontend/src/features/editor/editor.css` — figura w edytorze i w podglądzie

Build frontu przechodzi (`npm run build`). Backend sprawdzony realnym generowaniem PDF-a
i EPUB-a (poniżej, sekcja „Jak to sprawdzono").

## Co zrobione — wcześniejszy wątek (czeka na deploy)

1. **Guzik EPUB nie pobierał pliku.** `handleDownload` robił `fetch → blob → sztuczny <a>`;
   Chromium unieważniał gest użytkownika, zanim CDN odesłał plik. Teraz guziki to zwykłe
   `<a href={url}?download=nazwa>` — Supabase odsyła `Content-Disposition: attachment`.
2. **Zdublowana okładka w EPUB.** `set_cover(..., create_page=False)` + zostaje nasza
   strona okładki. 12 plików zamiast 14, jedna okładka w manifeście.
3. **Obraz w EPUB przy lewej krawędzi.** Presety nie miały reguły dla `img`; doklejona
   do `css_final` w `epub_generator.py`.

## Co zrobione w TYM wątku — podpisy pod obrazami

### Decyzje właściciela (jego słowa, 20.08)

- numeracja „Ryc. 1" — **NIE robimy**. Jeden do trzech obrazów na rozdział, numer byłby
  robotą bez zysku.
- kursywa w podpisie — **nie domyślnie, ale na fragmencie**. Nazwa łacińska pochylona,
  reszta prosto.
- numer strony na planszy — **zdjąć**, tak jak przy grafice otwierającej rozdział.
- podpis do `alt` — **tak**, automatem, bez dodatkowego pola w interfejsie.

### Jak to zbudowane

**Front — węzeł TipTap `Figure`** (`extensions/Figure.js`). Podpis jest TREŚCIĄ węzła
(`content: 'inline*'`), nie atrybutem — dlatego działa w nim Ctrl+I na zaznaczonym
fragmencie. Grafika i podpis są jednym blokiem, więc łamanie strony ich nie rozdzieli.

- wgranie obrazu („Media") wstawia figurę i **stawia kursor w podpisie** — autor pisze od razu
- Enter w podpisie wychodzi akapitem pod figurę (bez tego `isolating` zamyka w podpisie)
- guzik **„Plansza"** pojawia się w pasku, gdy kursor stoi w figurze; przełącza
  `data-full-page`. Stan czytany przez `useEditorState` — TipTap 3 nie przerenderowuje
  paska na samą zmianę zaznaczenia (reszta guzików w pasku ma ten problem do dziś)
- zapisany HTML jest czysty i przenośny: `<figure><img src><figcaption>…</figcaption></figure>`,
  bez atrybutów pod edytor. Plansza to `<figure data-full-page>`
- **stare rozdziały nietknięte** — goły `<img>` w akapicie nadal parsuje się jak dawniej

**PDF** (`pdf_generator.py`):
- `.chapter figure` — środek, `page-break-inside: avoid`; `figcaption` 0.85em, wyśrodkowany,
  bez wcięcia akapitowego
- plansza: `page: figure-page` (własny `@page` **bez numeru strony**), łamanie przed i po,
  grafika z podpisem wyśrodkowana w pionie (flex)
- `CAPTION_RESERVE_LINES = 6.0` — zapas wysokości pod podpisem, liczony ze stopnia pisma;
  `FIGURE_PAGE_SHAVE_PT = 6.0` — luz, bez którego WeasyPrint wypycha podpis na kolejną stronę
- `fill_alt_from_caption()` — podpis do `alt`, gdy `alt` pusty; własny `alt` nietknięty

**EPUB** (`epub_generator.py`): te same reguły w `css_final` (`figure`, `figcaption`,
`figure[data-full-page]` z `max-height: 85vh`) + ta sama `fill_alt_from_caption()`.

### Jak to sprawdzono (pomiar, nie wiara)

- PDF z trzema rozdziałami: figura w tekście, plansza pozioma, plansza pionowa z podpisem
  na dwie linijki. Rasteryzacja stron + `pdftotext`: **plansze bez numeru strony**, podpis
  na tej samej stronie co grafika, kursywa na fragmencie podpisu wychodzi, tekst po planszy
  wraca na stronę z numerem, **żadnej pustej strony**
- przemiatanie 240 kombinacji (marginesy 1–3 cm × stopień pisma 12–24 px × interlinia
  1.4–2.0 × podpisy 1–5 linijek × grafika pionowa/pozioma): **0 nieudanych**.
  Przy `CAPTION_RESERVE_LINES = 46pt` na sztywno wysypywało się 25 kombinacji — stąd wzór
- EPUB: `figure` w CSS-ie, `alt` uzupełniony z podpisu, `<img/>` domknięty przez ebooklib
- front: test bez przeglądarki (jsdom + TipTap): wstawienie, podpis, kursywa na fragmencie,
  plansza, **round-trip zapis→odczyt→zapis stabilny**, stary `<img>` przeżywa, figura bez
  `<figcaption>` parsuje się bez wywrotki. jsdom instalowany `--no-save`, `package.json` czysty

## NASTĘPNY KROK — jeden

**Kliknąć to w przeglądarce na projekcie *test book*** (`70e90efb-230b-428f-85dd-dd6dffb63beb`):
wgrać zdjęcie, wpisać podpis, pochylić nazwę łacińską, włączyć „Planszę", wygenerować PDF
i EPUB. Testy bez przeglądarki przeszły, ale kursora w podpisie i guzika „Plansza" nikt
jeszcze nie dotknął ręką.

Potem: **deploy całości** (punkty 1–4 razem) — push na `main`.

## Kolejka od właściciela

1. ~~EPUB się nie pobiera~~ — zrobione, czeka na deploy
2. ~~zdublowana okładka~~ — zrobione, czeka na deploy
3. ~~obraz w EPUB nie na środku~~ — zrobione, czeka na deploy
4. ~~podpisy pod obrazami + plansze na całą stronę~~ — zrobione, czeka na klik i deploy
5. deploy dopiero jak zbierzemy całość

## Czego właściciel NIE kupił

- **numeracji „Ryc. 1"** — świadomie odrzucona, nie wracać bez jego słowa
- kursywy na całym podpisie domyślnie — ma być narzędziem, nie domyślnym stylem

## Rozmiar zdjęć — ustalone liczby (pytanie z 20.08)

Kolumna tekstu w A5 przy domyślnych marginesach 1,5 cm to **11,8 cm ≈ 4,65 cala**.
Przy 300 dpi wychodzi **~1400 px szerokości** — więcej drukarnia i tak wyrzuci.
Plansza na całą stronę: pole 11,8 × 17 cm → **~1400 × 2000 px**.
Generatory **nie zmniejszają grafik** — PDF wkleja plik bajt w bajt jako data URI, EPUB
kopiuje go do środka. Ile waży plik, tyle waży książka.

## Wskaźniki

- projekt testowy: *test book* `70e90efb-230b-428f-85dd-dd6dffb63beb`
- kanon Bożeny: `507b3ee4-a07d-4a69-b6a8-f88b53dc2ba6`
- deploy frontu: push na `main` → Vercel projekt `tiolibri` (NIE `tiolibri-frontend`, to zombie)
- lokalny PDF: `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib venv/bin/python` (inaczej
  WeasyPrint nie znajdzie `libgobject`)
- model docelowy: Opus
