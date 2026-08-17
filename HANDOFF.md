# HANDOFF — 2026-08-17 (wersaliki zdjęte, książka Ewy gotowa do oglądania)

**Temat:** książka Ewy (projekt `1f23458e`) ma spójne nagłówki — wersaliki zdjęte
z H1/H2/H3, dwa zmielone tytuły rozdziałów naprawione. Ewa ogląda 2026-08-18.

## NASTĘPNY KROK — do zrobienia przez właściciela, ZANIM Ewa spojrzy

1. **Literówka w tytule projektu.** W bazie jest
   `Kości Na Całe Życie**b** 4.0 — po redakcji (2026-08-15)` — z doklejonym „b".
   **Ten tytuł idzie prosto na stronę tytułową PDF/EPUB** ([pdf_generator.py:470](tiolibri-api/app/services/pdf_generator.py#L470)).
   Nie ruszałem, bo tytuł to twoje pole i nie wiem, jaki ma być docelowo.
   Poprawka: Project Details → Tytuł.
2. **Wygenerować EPUB/PDF** i sprawdzić okładkę + spis treści oczami.

## Co zrobiono w tym wątku

### Wersaliki — ZDJĘTE (decyzja właściciela: H1 i H2)

**Ustalenie, które zmieniło plan:** `text-transform` **nie występuje** ani w presetach,
ani w generatorach. Wersaliki były wpisane **literalnie w treść** — więc to była edycja
danych, nie jednolinijkowa zmiana CSS.

- **38 nagłówków** zmienionych w treści + **12 `chapters.title`**, w 12 z 14 rozdziałów.
- **10 nagłówków z CAPS zostawionych świadomie** (wypisane w skrypcie w słowniku `ZOSTAJE`):
  - **emfaza autorki** — `Czego NIE znajdziesz`, `Co zrobić PO przeczytaniu?`,
    `Czego NIE suplementować`, `Interakcje – czego NIE łączyć`;
  - **skróty** — `SCFA` (4×), `DHEA`, `DEXA`.
- Decyzje niebanalne: `WAPŃ – Fundament` → `Wapń – fundament` (małą po półpauzie);
  `KIEDY`/`JAK` → zdjęte (to pytanie, nie kontrast, inaczej niż `NIE`);
  `BOR, CYNK, FOSFOR` → `Bor, cynk, fosfor`; `FITOESTROGENY (IZOFLAWONY)` →
  `Fitoestrogeny (izoflawony)`; człon po dwukropku zostaje z wielkiej —
  zgodnie z `Rozdział 7:` i `Rozdział 9:`, które już wcześniej były pisane normalnie.

### Dwa zmielone tytuły rozdziałów — NAPRAWIONE

Ten sam bug starego uploadu, co `ROZDZIA1Osteoporoza…`. Poprawny wariant wzięty z H1 w treści:

- `Zastrzeeniemedyczne` → **`Zanim zaczniesz`**
- `Literaturaizrodanaukowe.md` → **`Literatura i źródła naukowe`** (miał w tytule `.md`)

### Strona tytułowa — ZOSTAJE (decyzja właściciela)

Nie jest duplikatem okładki: okładka to grafika, strona tytułowa to tekstowy rekord książki
(w EPUB standard `titlepage`). Kod nie zmieniony. Uwaga na przyszłość: title page w
[pdf_generator.py:468-473](tiolibri-api/app/services/pdf_generator.py#L468-L473) jest
**bezwarunkowa** — nie ma flagi do wyłączenia, generuje się nawet przy okładce.

## Kanon: od teraz BAZA, nie Fabryka

Decyzja właściciela z tego wątku: w TIOLIBRI doszły już PNG do rozdziału, literatura
i disclaimer, których dostawa md nie zna. **Fabryka raczej nie będzie drugi raz pracować
na tym ebooku.** Wniosek praktyczny: `docs/dostawy/_import-ewa/dry-run/` jest **nieaktualny** —
kanonem treści jest projekt `1f23458e` w bazie. Gdyby Fabryka jednak wróciła, roundtrip
trzeba będzie wymyślić od nowa.

## Znane, nietknięte

- **Błąd numeracji w treści R10**: ostatni H2 brzmi `Podsumowanie rozdziału 11.`,
  a to jest rozdział 10. Nie ruszałem — to treść merytoryczna, nie formatowanie.
- **Druga runda R8** — cofnięcie `e-006` (KLU) i `e-001` (WAR). Nadal wiszą.
- **Bożena** — jedna linijka do Fabryki; u nich „sporne, do potwierdzenia",
  od tego wisi ich zaparkowany agregator (PHASE-22).
- **`.DS_Store` jest śledzony w gicie** i nie ma go w `.gitignore`. Nie commitowałem go.
- **Spec `porzadek-wersji` — NADAL ZAPARKOWANY.** Uwaga: jego §78 („trzy nośniki poza
  tytułem: notatka, etykieta wersji, **nazwa książki") to dokładnie ten ból, przez który
  tytuł projektu musi naraz służyć stronie tytułowej i wyszukiwaniu w dashboardzie.

## Skrypty

`docs/dostawy/_wersaliki/` — odpalać z venv API (`tiolibri-api/venv/bin/python3`):

- `pobierz.py` — pobiera projekt + rozdziały, zapisuje `backup-przed.json`
  (pełny stan przed zmianą, do rollbacku) i `inwentarz-naglowkow.json`;
- `zdejmij_wersaliki.py` — bez argumentu **podgląd**, `--wykonaj` zapisuje.
  Tabela `ZAMIANY` trzyma **jawnie** pełny tekst każdego nagłówka (przed → po),
  podmiana idzie **token po tokenie tylko w segmentach tekstowych**, więc wewnętrzny
  markup (`<strong>`, `<img>`, `<a>`) i encje zostają nietknięte. Niedzielące spacje
  (`\xa0`) przeżywają — `title` R2 miał jedną i przez to początkowo umykał tabeli.
  **Bramki fail-closed:** backup musi się zgadzać z bazą co do znaku przed zapisem;
  po podmianie goły tekst musi równać się docelowemu; żaden nagłówek ani `title`
  z CAPS nie może zostać poza tabelą i poza `ZOSTAJE`; po zapisie weryfikacja odczytem.

**Weryfikacja po zapisie:** 12/12 rozdziałów zgodnych co do znaku,
0 nagłówków z CAPS nieobsłużonych, 10 zostawionych świadomie.
