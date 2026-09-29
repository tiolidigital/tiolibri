# 2026-09-29 · Grzyby Bożeny: autor zdjęcia na okładce

- Paweł Muszyński (Bożena to jego ciotka) jest autorem zdjęcia użytego na okładce; w książce nie ma o tym słowa. Piotrek chce, żeby od teraz każdy egzemplarz (także wysłany ponownie) to miał.
- Stan dziś (baza, kolofon `0ba90032`): „Projekt okładki: Magda Kapinos-Michalska”, „Prawa do zdjęć: Paweł Stasiowski, Jacek Lelek, Bożena Muszyńska”. Pawła Muszyńskiego nie ma nigdzie w treści.
- Zaproponowane brzmienie: osobny wiersz pod projektem okładki „Zdjęcie na okładce: Paweł Muszyński”. Wariant: „Okładka na podstawie zdjęcia Pawła Muszyńskiego”.
- Plan po zgodzie: kolofon w bazie (z kopią i cofnięciem), wersja 1.0 → 1.1, nowe PDF i EPUB (+ PDF na komputer A4), wgranie do XpertHuba i przepięcie produktów, meldunek do XpertHuba z numerem wersji.

## Otwarte
- Czekam na zgodę Piotrka na brzmienie i pisownię nazwiska.

## Dopisek (ta sama rozmowa)
- Piotrek: „Projekt okładki: Magda Kapinos-Michalska” dotyczy Kości (Ewa), w Grzybach autora okładki ma nie być; w Grzybach chodzi wyłącznie o „Zdjęcie na okładce: Paweł Muszyński”.
- Sprawdzone: wiersz o Magdzie JEST w kolofonie Grzybów (baza) i w PDF na komputer z 24.09 (strona redakcyjna). Wszedł 2026-09-02 (patrz pamięć „strony redakcyjne”).
- Pytanie do Piotrka: wyrzucić wiersz o Magdzie z Grzybów przy tej samej wersji 1.1?

## Zrobione (Piotrek: „tak”)
- Kolofon w bazie: wiersz o Magdzie usunięty, „Zdjęcie na okładce: Paweł Muszyński” dopisany; imprint.version 1.0 → 1.1. Kopia i cofnięcie: `docs/dostawy/boz-2026-09-29-zdjecie-okladki/zmien_kolofon.py --cofnij`.
- Wygenerowane na produkcji PDF i EPUB 1.1 oraz lokalnie PDF na komputer A4; wgrane do XpertHuba (`bozena-muszynska/v1.1/`), 7 produktów przepiętych (desktop_path też). Sprawdzone wyszukiwaniem: Paweł jest we wszystkich trzech plikach, Magdy nie ma.
- Zrzut strony wysłany Piotrkowi; XpertHub (karta xperthub-80) powiadomiony o wersji 1.1.

## Otwarte
- (domknięte) XpertHub potwierdził: sumy się zgadzają, 1.1 w rejestrze wersji, stempel „Egzemplarz…” na stronie tytułowej jak w 1.0.
- Osoby, które już kupiły, mają 1.0. Nowa wersja trafi do nich tylko przy ponownej wysyłce.

## Mail do Pawła (w toku)
- Piotrek chce przeprosić Pawła mailem ze skrzynki sklepu: błąd przyznany wprost, bez kajania; wersja: „współpracownik pomylił książki” (nie mówimy o AI). Okładki Magdy nie załączamy.
- Zaproponowane: zamiast linku egzemplarz autorski z XpertHuba (`/egzemplarz grzyby <email> "Pawła Muszyńskiego"`), trzy pliki w załączniku z dedykacją. Szkic maila podany Piotrkowi.
- Zmiana: Piotrek nie chce załączników, tylko link z XpertHuba. Całość przekazana Bazie (baza-e3), plik `App_Factory/BAZA/HANDOFF-2026-09-29-mail-do-pawla-grzyby.md`. Piotrek ustala resztę z Bazą; w TIOLIBRI nic otwartego.

# Kości Ewy: odsyłacze i sprzeczności (handoff od Bazy, ta sama data)
- Baza (przez Piotrka): część odsyłaczy wskazuje złe albo nieistniejące rozdziały; na live Ewa odsyła po tytułach; poprawka w 1.1 po stronie TIOLIBRI.
- Sprawdzone w bazie: 8 złych odsyłaczy (więcej niż w handoffie: także białko, wit. D, trening siłowy w Zakończeniu i alkohol w rozdz. 4). Sprzeczne liczby są w tekście tam, gdzie Baza wskazała.
- Przygotowane: `docs/dostawy/ewa-2026-09-29-odsylacze-v1.1/POPRAWKI.md` (tabela poprawek + 7 pytań do Ewy). W bazie nic nie zmienione.

## Otwarte
- Piotrek przekazuje Ewie 7 pytań. Po odpowiedziach i jego słowie: poprawki w bazie (z kopią i cofnięciem), 1.0 → 1.1, nowe pliki, XpertHub. Bez maila do kupujących.
