**Temat:** obrazy w książce — podpisy, plansze i tytuł rozdziału spod grafiki otwierającej — bo u Ewy grafika ma tytuł w sobie i ten sam tytuł stał w książce drugi raz jako nagłówek, a Piotrek chce klikać gotowe na produkcji

# HANDOFF — 2026-08-20 · HEAD b03f6b4 (na produkcji)

## STAN: NA PRODUKCJI — **WYPCHNIĘTE 20.08**

Właściciel powiedział „pushnij". `2e43099..b03f6b4` poszło na `origin/main`, więc
ukrywanie tytułu spod grafiki jest na Vercelu (projekt `tiolibri`) i Railwayu razem
z resztą. Nikt tego jeszcze nie klikał ręką na produkcji — patrz NASTĘPNY KROK.

Wcześniejsze trzy commity (`2b1ed95`, `6d645ef`, `493a098` + fix `2e43099`) są na
produkcji od 20.08 wieczorem: pobieranie EPUB-a, podpisy pod obrazami, plansze na
całą stronę, znikanie niepobranej grafiki.

## Co zrobione w TYM wątku — ukrywanie tytułu spod grafiki

### Decyzja właściciela (jego słowa, 20.08 wieczorem)

Pytanie brzmiało: automat czy przełącznik. Odpowiedź: **przełącznik, ale tak
ustawiony, żeby u Ewy nie trzeba było klikać rozdział po rozdziale** — „chciałbym,
żeby już były wyłączone". Powód, dla którego przełącznik w ogóle ma być: grafika
może kiedyś nieść co innego niż nagłówek (inny tytuł, sam obraz, podtytuł obok).

Zbudowane więc dwa piętra, bo to jedno bez drugiego nie robi tego, o co prosił:

1. **Ustawienie książki** — `hideOpenerTitle` w typografii, suwak „Ukryj tytuł pod
   grafiką rozdziału", **domyślnie WŁĄCZONY**. Ewa dostaje efekt bez klikania,
   u Bożeny nic się nie rusza (jej rozdziały otwiera zwykły `<h1>` bez grafiki).
2. **Wyjątek per rozdział** — guzik **„Tytuł"** w pasku edytora, widoczny tylko
   wtedy, gdy kursor stoi w nagłówku otwierającym grafiką. Zapisuje
   `data-chapter-title="visible"` albo `"hidden"` na `<h1>`. Bez kliknięcia żaden
   atrybut nie dochodzi — zapisany HTML zostaje czysty, stare rozdziały nietknięte.

### Jak to zbudowane

**PDF** (`pdf_generator.py`): `split_chapter_opener(html, hide_title=)` dokleja
nagłówkowi klasę `.opener-title-hidden`. Reguła to `visibility: hidden` + zerowa
wysokość, **nie `display: none`** — element bez pudełka nie ma pozycji w dokumencie,
więc link ze spisu treści nie miałby dokąd skoczyć. `opener_title_hidden()` czyta
wyjątek z atrybutu, `add_class()` dokleja klasę nie gubiąc tego, co już w tagu jest.

**EPUB** (`epub_generator.py`): `hide_opener_title()` chowa sam **TEKST** nagłówka,
zawijając go w `<span class="opener-title-hidden">`. Powód rozjazdu z PDF-em: w EPUB-ie
grafika siedzi w środku `<h1>` (nie ma wydzielania strony otwierającej), więc ukrycie
całego nagłówka zabrałoby ją razem z tytułem. Wołane PO `extract_first_heading()` —
wyżej tytuł jest jeszcze potrzebny jako nazwa rozdziału w spisie treści.

**Front**: nowe rozszerzenie `extensions/ChapterTitle.js` (globalny atrybut na
`heading` + `openerTitleState()` dla paska), guzik w `EditorToolbar.jsx` na tym samym
`useEditorState` co „Plansza", suwak w `TypographyControls.jsx`, `hideOpenerTitle`
w `DEFAULT_SETTINGS` (`useTypography.js`), mapowanie na `hide_opener_title`
w `GenerateBooks.jsx` (przez `!== false`, bo brak ustawienia w starym projekcie ma
znaczyć „chowaj"). W edytorze taki nagłówek jest przygaszony i ma notkę „NIE WCHODZI
DO KSIĄŻKI" (`editor.css`) — bez tego autor patrzy na widoczny tytuł i nie ma skąd
wiedzieć, że w PDF-ie go nie będzie.

Pliki: `pdf_generator.py`, `epub_generator.py`, `schemas.py` (`hide_opener_title:
bool = True`), `routers/generate.py`, `ChapterTitle.js` (NOWY), `EditorToolbar.jsx`,
`ChapterEditor.jsx`, `TypographyControls.jsx`, `useTypography.js`, `GenerateBooks.jsx`,
`editor.css`.

### Jak to sprawdzono (pomiar, nie wiara)

- **Kanon Ewy `1f23458e`, prawdziwy PDF, 381 stron**: wszystkie **262 kotwice** na
  miejscu, każdy rozdział ląduje na tej samej stronie co przed zmianą (rozdział 1:
  strona 18, grafika na 17), tekst zaczyna się od góry strony bez śladu po nagłówku
  i bez pustego miejsca, numer strony jest. Książka schudła o 7 stron.
- **EPUB Ewy**: 12 z 14 rozdziałów z ukrytym tytułem (dwa bez grafiki nietknięte),
  nazwy w `toc.ncx` nietknięte.
- **Regresja u Bożeny `507b3ee4`**: 24 rozdziały, **0 zmienionych** w obu generatorach.
  To samo w *test book* `70e90efb`.
- **Wyjątek per rozdział**: rozdział z `data-chapter-title="visible"` drukuje tytuł
  mimo włączonego ustawienia książki (PDF syntetyczny, sprawdzone `pdftotext`).
- **Front, 11 testów bez przeglądarki** (jsdom + TipTap, instalowany `--no-save`):
  round-trip HTML bez atrybutu i z atrybutem, przełączanie w obie strony, guzik
  nie pokazuje się w `<h1>` bez grafiki ani w nagłówku, który nie otwiera rozdziału,
  figura z podpisem nietknięta. `npm run build` przechodzi.

## NASTĘPNY KROK — jeden

**Odebrać wynik klikania na produkcji** (*test book* `70e90efb-230b-428f-85dd-dd6dffb63beb`):
wgrać zdjęcie, wpisać podpis, pochylić nazwę łacińską, włączyć „Planszę", wygenerować
PDF i EPUB. Testy bez przeglądarki przeszły, ale kursora w podpisie i guzika „Plansza"
nikt jeszcze nie dotknął ręką. Po deployu doszedł do tego guzik „Tytuł" i suwak
w typografii — też nietknięte ręką.

## Pomysły zgłoszone właścicielowi, jeszcze NIEKUPIONE

- **Zmniejszanie zdjęć przy wgrywaniu** (canvas → dłuższy bok 2000 px, JPEG ~0,82,
  przed wysłaniem do Supabase). Znosi problem „jak duże ma być zdjęcie", trzyma 300 dpi
  na A5 i przestaje boleć limit 5 MB. Największy zysk z całej listy.
- **Dwie drogi do jednej rzeczy**: grafika otwierająca rozdział (`<h1><img>`) i plansza
  (`figure[data-full-page]`) robią prawie to samo, innym mechanizmem. Kiedyś scalić.
- **Podgląd w aplikacji** (`BookPreview.jsx`) nie zna ani strony otwierającej, ani
  ukrywania tytułu — dzieli tekst po liczbie słów. Kto kiedyś będzie go urealniał,
  ma tu dwie rzeczy do dołożenia.

## Czego właściciel NIE kupił

- **numeracji „Ryc. 1"** — świadomie odrzucona, nie wracać bez jego słowa
- kursywy na całym podpisie domyślnie — ma być narzędziem, nie domyślnym stylem

## Rozmiar zdjęć — ustalone liczby (pytanie z 20.08)

Kolumna tekstu w A5 przy domyślnych marginesach 1,5 cm to **11,8 cm ≈ 4,65 cala**.
Przy 300 dpi wychodzi **~1400 px szerokości** — więcej drukarnia i tak wyrzuci.
Plansza na całą stronę: pole 11,8 × 17 cm → **~1400 × 2000 px**. Generatory **nie
zmniejszają grafik** — ile waży plik, tyle waży książka.

## Wskaźniki

- kanon Ewy: `1f23458e-b63a-4b29-a912-cced19ce3e47` (12 z 14 rozdziałów otwiera grafika)
- kanon Bożeny: `507b3ee4-a07d-4a69-b6a8-f88b53dc2ba6` (zero grafik otwierających)
- projekt testowy: *test book* `70e90efb-230b-428f-85dd-dd6dffb63beb`
- deploy frontu: push na `main` → Vercel projekt `tiolibri` (NIE `tiolibri-frontend`)
- lokalny PDF: `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib venv/bin/python`
- tabela `chapters`: treść w `processed_html` (kolumny `content` nie ma), kolejność
  `sort_order` — jawna lista kolumn w `select()` wywraca skrypt
- model docelowy: Opus
