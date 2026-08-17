**Temat:** książka Ewy — strona tytułowa, plansze rozdziałów i spis treści doprowadzone do porządku na produkcji — bo Ewa ogląda plik 2026-08-18 i ma zobaczyć złożoną książkę, a nie wydruk z generatora

# HANDOFF — 2026-08-17

## NASTĘPNY KROK — jeden

**Obejrzeć gotowy PDF własnymi oczami i powiedzieć, czy idzie do Ewy.**

Świeży plik z produkcji leży w scratchpadzie tego wątku:
`…/8a8af80e-baef-4b2f-be12-88f643f6edf5/scratchpad/ewa-final.pdf` (246 stron, z okładką,
ze spisem treści). Jeśli scratchpad zniknął — wygenerować z UI:
https://app.tiolibri.com/editor/1f23458e-b63a-4b29-a912-cced19ce3e47

Wszystko poniżej jest zmierzone maszynowo na produkcji. Czego NIE ma: oceny człowieka,
czy to ładnie wygląda jako całość.

## Co zrobiono w tym wątku

Wątek zaczął się od klik-testu z poprzedniego handoffu; testy przeszły, ale odsłoniły
cztery rzeczy do poprawy. Wszystkie naprawione i wdrożone.

### 1. Klik-test podtytułu i nazw plików — ZALICZONY

Przebieg end-to-end przez `POST https://api.tiolibri.com/generate` z prawdziwym JWT.
Strona tytułowa niesie trzy linijki w PDF i EPUB. Nazwa pliku sprawdzona **funkcją
wyciągniętą z wdrożonego bundla** (`app.tiolibri.com/assets/index-*.js`), nie ze źródeł:
`Kości na całe życie` → `kosci-na-cale-zycie.pdf`.

### 2. Tytuł na stronie tytułowej był do lewej — `2f31091`

Presety mają twarde `h1 { text-align: left }` (nagłówki rozdziałów), które wygrywa
z wyśrodkowaniem dziedziczonym po `.title-page`. Reguła `.title-page h1` jest bardziej
specyficzna — tam dopisane `text-align: center`.

### 3. Autor miał wcięcie akapitowe — `5151b9a` (PDF) + `7ff7b3a` (EPUB)

**To była nasza regresja z `40c8ffb`.** Preset ma `p { text-indent: 1.5em }` z wyjątkiem
`h1 + p { text-indent: 0 }`. Dopóki strona tytułowa miała tytuł + autora, autor łapał się
na wyjątek. Podtytuł wszedł między nie i autor zaczął brać wcięcie — na wyśrodkowanej
linijce widać to jako przesunięcie o pół wcięcia w prawo (zmierzone: 10,4 pt).

Reguła obejmuje teraz `h1` i wszystkie akapity strony tytułowej. W EPUB strona tytułowa
**dostała własny CSS po raz pierwszy** (wcześniej jechała na domyślnych stylach czytnika)
— środek, zero wcięcia, rozmiary w `em`. Decyzja właściciela: oba pliki mają wyglądać tak samo.

### 4. Numer strony na planszy otwierającej rozdział — `b36969c`

Zgłoszone przez właściciela ze zrzutu: cyfra leżąca na ilustracji. Wybrany wariant
(za zgodą): **zdjąć numer, nie zmniejszać grafiki** — konwencja składu mówi, że
całostronicowe plansze folio nie noszą.

Grafika (edytor trzyma ją jako pierwsze dziecko `H1`) idzie do `.chapter-opener`
na nazwanej stronie `@page chapter-opener` bez `@bottom-center`. **Licznik stron leci dalej**,
numer po prostu nie jest drukowany — ten sam mechanizm co przy okładce. Dodatkowo
`max-height` liczone z marginesów strony, żeby grafika nie mogła wejść w dolny margines.
Nagłówek zostaje nietknięty poza usunięciem obrazka, więc ID i tekst do spisu treści
są te same.

### 5. Spis treści drobniejszy od tekstu książki — ten sam commit

Miał **sztywne 9-11pt**, podczas gdy treść jedzie na ustawieniu użytkownika (16px = 12pt)
— czyli spis w ogóle nie brał udziału w ustaleniu „ma się czytać na telefonie".
Rozmiary są teraz w `em` (1.05 / 1 / 0.95), odstępy 0,45em, kolory ciemniejsze.

## Dowód z produkcji (nie z lokalnego builda)

Ostatni przebieg, payload wierny temu, co wysyła UI (z okładką):

- 246 stron, 13 stron z grafiką, **na żadnej nie ma numeru**, zero pustych stron
- strona tytułowa: `tytuł L=114,1 P=114,1` · `podtytuł L=56,5 P=56,4` · `autor L=102,8 P=102,8`
- numeracja ciągła: 11, [12 bez numeru], 13
- EPUB z produkcji ma blok `.title-page` w `nav.css` i trzy linijki w `title.xhtml`
- nagłówki rozdziałów nadal do lewej (`x=42,5` = lewy margines) — reguła nie wyciekła

Skrypty sprawdzianu: `scratchpad/klik_test_final.py` (produkcja), `lokalny_pdf.py`
(ten sam kod lokalnie na prawdziwych danych — szybsza iteracja niż czekanie na Railway).

## Stan: pliki, commity

- **HEAD `b36969c`**, `main` == `origin/main`, wszystko wypchnięte i wdrożone.
- `2f31091`, `5151b9a`, `7ff7b3a`, `b36969c` — cztery poprawki z tego wątku.
- Wersja repo: `1.0.34 → 1.0.38` (hook bumpuje przy commicie).
- Projekt Ewy: `1f23458e-b63a-4b29-a912-cced19ce3e47`

## Pułapka przy powtarzaniu klik-testu

`GET /projects/{id}` **nie zwraca `cover_image_url`** (nie ma go w modelu Pydantic).
Front bierze okładkę wprost z Supabase (`useCover.js`). Sprawdzian, który buduje payload
z odpowiedzi API, wygeneruje książkę **bez okładki** i będzie wyglądał na zielony.
Okładkę dociągnąć z `rest/v1/projects?select=cover_image_url`. Zapisane w pamięci.

## Znane, nietknięte

- **`title` i `author` NIE są escapowane w generatorach** — `&` w tytule złamie XHTML w EPUB.
  Podtytuł jest bezpieczny, tamte dwa nie.
- **`NewProjectModal` nie ma pola podtytułu** — ustawia się go w Project Details.
- **Błąd numeracji w treści R10**: ostatni H2 to `Podsumowanie rozdziału 11.`, a to rozdział 10.
- **Druga runda R8** — cofnięcie `e-006` (KLU) i `e-001` (WAR).
- **Bożena** — linijka do Fabryki; od tego wisi ich agregator (PHASE-22).
- **`.DS_Store` śledzony w gicie**, brak go w `.gitignore`.
- **Spec `porzadek-wersji` — ZAPARKOWANY** (R4 = REQUEST_CHANGES, 12 blokerów).

## Kanon: BAZA, nie Fabryka

Kanonem treści jest projekt `1f23458e` w bazie. `docs/dostawy/_import-ewa/dry-run/` jest nieaktualny.

## Em dashe

W książce mają być **półpauzy (– U+2013), nigdy em dashe (— U+2014)**. Stan: 719 półpauz,
1 em dash — w oryginalnym angielskim tytule publikacji w R14, cytat bibliograficzny,
**zostawić**.

**Model docelowy: Opus.**
