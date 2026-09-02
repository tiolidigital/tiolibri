**Temat:** strony redakcyjne książki Bożeny — bo Piotrek nie wiedział, jak taka strona ma wyglądać, i chciał to zrobić porządnie przed wystąpieniem o ISBN

## Co zrobione w tym wątku

Rozmowa redaktorska + implementacja. Ustalenia spisane w pamięci projektu
(`project_strony_redakcyjne_konwencje.md`) — tam jest kanon, nie tutaj.

Skrót decyzji:
- strona tytułowa **nie jest rozdziałem** — oba generatory składają ją same
  z `projects.title/subtitle/author`; dotychczasowy rozdział był duplikatem
- strona redakcyjna (kolofon) idzie **na koniec**, w PDF i EPUB tak samo
- marka wydawnicza: **„Wydawnictwo TIOLI"** (TIOLI wersalikami — tak Piotrek
  zarejestrował wydawcę w e-ISBN BN 2026-09-02, tego nie zmieniać)
- `prof. dr hab. Bożena Muszyńska` małymi literami
- w tekstach półpauza (–), nigdy emdash

## Stan

Commit `1aebe14` (wersja 1.0.47), **niewypchnięty**:
- `tiolibri-api/migrations/003_imprint_and_chapter_role.sql` — `projects.imprint`
  (jsonb) + `chapters.role` ('colophon'). **Migracja JUŻ ZASTOSOWANA na
  produkcyjnej bazie** przez Management API (PAT z `.env`), nie tylko w pliku.
- `tiolibri-api/app/services/pdf_generator.py` — wydawca/miejsce+rok/nota praw
  na stronie tytułowej, klasa `.chapter.colophon`, CSS
- `tiolibri-api/app/services/epub_generator.py` — to samo + kolofon wyrzucony
  z nawigacji EPUB (obie gałęzie budowania `book.toc`)

Dane w bazie (projekt Bożeny `fe9cba47-9760-4a40-8030-d5bc5e70b512`):
- `author` poprawiony na małe litery, `imprint` wypełniony
- rozdział `0ba90032-be95-43f0-98fd-bc7bddb14356`: tytuł „Strona redakcyjna",
  `role='colophon'`, `sort_order=30` (ostatni), treść to gotowy kolofon
- **backup stanu sprzed zmian**: `docs/isbn/backup-strony-redakcyjne-2026-09-02.json`

Zweryfikowane renderem próbnym (strona tytułowa + kolofon na jednej stronie).
EPUB-a nie renderowałem.

## NASTĘPNY KROK

`git push` i sprawdzić, czy Railway przebudował — potem wygenerować pełny PDF
i EPUB z aplikacji, żeby Piotrek zobaczył całość na produkcji.

## Czego właściciel jeszcze nie ma

- **ISBN-y i prawa do zdjęć**: w kolofonie stoi `---`. Wniosek o pulę ISBN
  złożony w BN 2026-09-02, czeka na konto (do 2 dni roboczych).
- **„Egzemplarz dla: …" (social DRM)** — świadomie odłożone. Sprzedaż pójdzie
  przez XperHUB, więc dane nabywcy przyjdą stamtąd; to parametr `GenerateRequest`
  + pole w `GenerateBooks.jsx`. Robić przed pierwszą sprzedażą.
- **Brak UI dla `imprint`** — dane wydawnicze kolejnej książki trzeba na razie
  wpisać wprost do bazy. Świadomy dług, przy dwóch tytułach nieopłacalny do
  zamknięcia.
- **Numer strony drukuje się na stronie tytułowej i na kolofonie** — zachowanie
  sprzed tej zmiany, nie ruszane. Typograficznie nie powinno go tam być.
- **Te same reguły czekają na książkę Ewy** (osteoporoza) — u niej różni się
  tylko blok „Wydawca", bo wydaje na własną firmę.
