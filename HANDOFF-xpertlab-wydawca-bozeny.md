# Zadanie dla TIOLIBRI: w „Grzybach leczniczych” wydawcą jest Wydawnictwo XpertLab, Tioli znika

**Nadawca:** Baza, 2026-09-24 rano, z rozmowy z Piotrkiem.
**Termin: dziś, 24.09, zanim wyjdą linki przedpremierowe do zapisanych** (Piotrek ustala godzinę
wysyłki z Fabryką; jeśli nie zdążymy przed nią, podmiana idzie wieczorem albo po premierze, nigdy
w trakcie wysyłki). Premiera w piątek 25.09.

## Decyzja Piotrka (24.09)
Buduje markę wydawnictwa pod nazwą XpertLab i przedstawia się wszędzie jako Wydawnictwo XpertLab.
Nazwa „Wydawnictwo TIOLI” ma zniknąć z książki Bożeny. U Ewy bez zmian: tam wydawczynią jest Ewa,
a XpertLab zostaje jako „We współpracy z XpertLab”, tak jak jest od 23.09.

## Zakres (tylko Bożena, projekt `fe9cba47-9760-4a40-8030-d5bc5e70b512`)
1. `imprint.publisher`: `Wydawnictwo TIOLI` → `Wydawnictwo XpertLab`.
2. `imprint.rights_note`: `© 2026 Bożena Muszyńska · Wydawnictwo TIOLI. Wszelkie prawa zastrzeżone.`
   → `© 2026 Bożena Muszyńska · Wydawnictwo XpertLab. Wszelkie prawa zastrzeżone.`
3. Linijka „We współpracy z XpertLab” w kolofonie **nie może się pokazać**, skoro XpertLab jest wydawcą
   (brzmiałoby jak współpraca z samym sobą). Napis-logo XpertLab na stronie tytułowej zostaje.
   Dziś `xpertlab = true` włącza oba naraz (`app/services/imprint.py`, `colophon_lines`), więc potrzebna
   jest drobna zmiana: linijka pomijana, gdy `publisher` zawiera „XpertLab”. Test na obu przypadkach
   (Ewa: linijka jest, Bożena: nie ma).
4. **Przeszukać całą treść książki pod kątem „TIOLI” / „Tioli”** (kolofon pisany ręcznie, strona
   praw autorskich, metadane EPUB `dc:publisher`, metadane PDF). Każde wystąpienie jako wydawcy →
   „Wydawnictwo XpertLab”. Numery ISBN zostają bez zmian.
5. Eksport PDF i EPUB, wgranie do XpertHuba tą samą drogą co 23.09 (`docs/dostawy/xpertlab-2026-09-23/`,
   `wgraj_xperthub.py`), z kopią zapasową stanu przed zmianą i skryptem cofnięcia. Nowy podfolder
   wersji, żeby dało się wrócić jednym ruchem.

## Czego nie ruszać
Treści, okładki, numeracji, ISBN, książki Ewy. Tioli zostaje tam, gdzie wymaga go prawo, czyli poza
książką: regulamin, faktury, polityka prywatności (to nie jest zadanie dla TIOLIBRI).

## Gotowe, gdy
- nowy PDF i EPUB Bożeny w XpertHubie, produkty przepięte, stempel egzemplarza nadal stoi pod napisem,
- „Wyślij ponownie” na zamówieniu testowym daje nowe pliki (Piotrek albo sesja sprawdza jednym zakupem
  testowym lub ponowną wysyłką),
- w obu plikach nie ma słowa „TIOLI” (sprawdzone wyszukiwaniem w tekście, nie na oko),
- meldunek dla Piotrka: dwa zrzuty metryki (PDF i EPUB).

## Uwaga dla Piotrka (poza zakresem TIOLIBRI)
Pula numerów ISBN jest zapisana w Bibliotece Narodowej na firmę Tioli. Żeby dane się zgadzały, warto
później dopisać tam markę XpertLab w profilu wydawcy (system e-ISBN). To robota na spokojny tydzień,
dzisiejszej podmiany nie blokuje.
