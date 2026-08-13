# HANDOFF — 2026-08-14 00:05

**Temat:** porządek w wersjach projektów — **R4 odebrany: REQUEST_CHANGES, 12 blokerów.** Spec NIE wchodzi w implementację. To jest ta umówiona pauza — następny odcinek to import z Fabryki/Redaktora.

## Co zrobione w tym wątku

Jedna rzecz, ta z poprzedniego handoffu: **doręczenie promptu R4 do Codexa bez limitu 10 minut.**

```
printf '%s' "$(cat docs/specs/porzadek-wersji/_review/.R4-prompt.md)" | codex exec -s workspace-write \
  -C "<root repo>" -o "docs/specs/porzadek-wersji/_review/.R4-codex-last-msg.md" -
```
odpalone przez `run_in_background: true`. **Bieg trwał ~16 minut, EXIT=0.** Log: `_review/.R4-codex-run2.log` (1,29 MB).
Poprzedni bieg (`.R4-codex-run.log`, 725 KB) padł na `Exit 143` — twardy limit narzędzia, nie błąd Codexa. Potwierdzone.

Odbiór zweryfikowany: `R4-codex.md` istnieje (15 165 B), `rg -c '^\**Werdykt:...'` → **1**. Kontrakt spełniony.

## Werdykt R4 — REQUEST_CHANGES

> „Kanał S ma zapisany, realny dowód działania, ale nowy protokół nadal nie jest wykonywalnym kontraktem
> od początku do końca." — sprawdzone 12/12 kategorii checklisty (1 × N/A: bundling/mutation targets,
> bo spec nie definiuje pure-logic testów `it()`).

**Dobra wiadomość:** główna niewiadoma po R3 — czy kanał dowodowy w ogóle działa — **zamknięta na TAK.**
Blokery są o jakości protokołu, nie o jego istnieniu.

### Blokery — pełna dwunastka

| # | Bloker | Sedno |
|---|---|---|
| **B1** | `ROLLBACK TO SAVEPOINT fixture` kasuje własne wyniki §6.2 | Postgres cofa **wszystko** po savepoincie, w tym inserty do temp table `_wynik`. Bramka S4 odrzuca tylko `NULL`/pustą listę → jeden ocalały wiersz = false-PASS. **Ta sama klasa błędu, którą złapaliśmy w 0.5.1, piętro wyżej.** |
| **B2** | Mapa kanału §6.2 sprzeczna z własnym protokołem | Tabela mówi „krok 7 read-only", a krok 7 robi `CREATE OR REPLACE FUNCTION` + `INSERT`. Kroki 8–10 pominięte. Diagram wkłada mutację #2 w zły krok. |
| **B3** | R3 nie sprawdza użytkownika **z udziałem** | Deklaruje claims udziałowca, a bierze „dowolny inny `user_id` z `projects`" — to dowodzi zachowania obcego, nie udziałowca. Dziura dokładnie tam, gdzie chodzi o dostęp redaktora. |
| **B4** | PHASE-0 nie testuje kanału H, mimo że go dostarcza | C1–C7 („kanał dowodzi sam siebie") są S-only; §6.0a oznaczone S-only. Pierwsze użycie H w 1A-api diagnozowałoby produkt i bootstrap naraz. |
| **B5** | Trwałe zapisy kanału H bez gwarantowanego cleanupu na ścieżce błędu | Cleanup tylko jako końcowy postflight, brak `finally`. Błąd HTTP między utworzeniem użytkownika a postflightem → `EXIT=1` i **śmieci w produkcji**. Przy Risk HIGH nie do zgadnięcia. |
| **B6** | Brak właścicielskiej kontrolki zmiany `role`; `book` bez przypisanej edycji na karcie | Spec obiecuje „jednym kliknięciem", plan 1B ma tylko plakietkę i notatkę. **Cel produktu nieosiągalny z opisanego UI.** |
| **B7** | Podział 1B bez wiążącej kolejności; szew integracyjny nie policzony | `normalizeProjectMeta` powstaje w 1B-dashboard, a 1B-karta go używa. `DashboardPage` nie pobiera `updateProject` z hooka — żadna rozpiska tego nie nazywa. |
| **B8** | Obowiązkowe kroki dowodu bez właściciela i budżetu | R5 poza artefaktami 1A, R4 poza artefaktami 2A, krok 9a pominięty. U9 nominalnie zielone, ale sizing nie obejmuje całego zakresu. |
| **B9** | „Pełna tabela" duplikatu ma próbę dla 1 z 4 wejść | Kontrakt §3.3 wylicza `AKTUALNA`/`ROBOCZA`/`ARCHIWUM`/`NULL`; krok 8 uruchamia tylko `AKTUALNA`. |
| **B10** | Sześć archiwów nie daje deklarowanego pokrycia złego typu | I5 sprawdza tylko `book=123`; brak kontrpróby `note` złego typu. Jedno archiwum z dwoma błędnymi polami też nie starczy — walidator może stanąć na pierwszym. |
| **B11** | Klik-proof nie pokrywa większości wymagań faz UI | Brak wyników dla: `role` set/unset, zmiany `book`, filtrów/sortowania, `NewProjectModal`; nazwy snapshotu, pin/unpin, `aria-pressed`, fokusu (§9.3–9.4); całej warunkowej PHASE-3 (grupowanie, `aria-expanded`, `localStorage`). |
| **B12** | Protokół twardego DELETE ma niemożliwy warunek kompletności | `wynik` ma zawierać liczbę kafelków **przed i po**, a wiersz ma być kompletny **przed** usunięciem. Sprzeczne. Trzeba rozdzielić stan `READY_TO_DELETE` od rekordu po akcji. |

### Uwagi nieblokujące (4)

1. Nagłówek mastera (`:11`) i footer (`:1465`) nadal mówią `/spec-handoff` — stale wobec `R4-codex-pending`.
2. Sekcja „jedno zdanie" ma **772 znaki i dwa zdania** — twardy limit workflow §4.7 to 200.
3. §3.5 i §10 nadal nazywają §6 „owner-attested", choć §6 ten kanał jawnie znosi.
4. Surowy R4 E ma w P2 `EXPECT=200`, `GOT=HTTP 201`, `RESULT=PASS` — skrypt dopuszcza oba, ale etykieta myląca.

### Co przeszło — bramki maszynowe w komplecie

| Kontrola | Wynik |
|---|---|
| U9 na realnym specu | **EXIT=0** |
| U9, mutant `PHASE-0 Pliki=9` przy limicie 8 | `SIZING-FAIL`, **EXIT=1** |
| FACT gate preflightu | 17/17 valid, corrected=1, **EXIT=0** |
| strukturalny gate C/M/E | 5/5 valid, **EXIT=0** |
| 12 baz `wc -l` z §5 | **12/12 co do linii** |
| cytowane ścieżki i kotwice `#L…` | wszystkie istnieją |
| parse AST czterech probe'ów R3/R4 | **4/4 EXIT=0** |

**Kanał S u Codexa padł lokalnie na `EXIT=1` — DNS sandboxu nie rozwiązuje `api.supabase.com`.**
Codex przyjął nasze owner-attested raw (`.R4-probe-out.txt` 11/11 PASS, `.R4-selftest-out.txt` 4/4 PASS)
na podstawie jawnego wyjątku z promptu i **sam zaznaczył**, że B1–B3 wynikają z treści protokołu,
nie z braku sieci. To nie jest powód RC.

### Audyt C/M/E — nieblokujący (reguła 1: `CME-MANIFEST.md` nie istnieje)

Warte zapamiętania na przyszłą rundę: brak surowego artefaktu pierwszego biegu z 6 FAIL/EXIT=1, choć rekord E go
deklaruje; `.R3-probe2-kanal.py` i `.R3-probe3-rls.py` tylko drukują obserwacje — **nie mają akumulatora asercji
ani `sys.exit` zależnego od wyniku**. Rekord `protokol-dowodu-§6` twierdzi, że zmierzono wykonalność każdego
kształtu, a P3 mierzy pojedynczy blok `DO`, nie wielogałęziowy kształt §6.2 z savepointem — C szersze od E.

## NASTĘPNY KROK — ale najpierw decyzja właściciela

**Umówiona pauza wypada dokładnie tutaj.** Bramka brzmiała „za R4, przed implementacją" i R4 właśnie
przyszedł. 12 blokerów to nie kosmetyka — droga to `/spec-apply-review` → poprawki mastera → najpewniej **R5**,
a dopiero potem 10 faz implementacji (~12 h + review każdej fazy).

Dwie drogi, decyzja Piotrka:

- **PAUZA (uzgodniona)** — bierzemy import z Fabryki/Redaktora. Wtedy zapisz to:
  `printf '%s\n' 'spec porzadek-wersji: R4 REQUEST_CHANGES, wracamy po imporcie z Fabryki' > .claude/parked`
  — inaczej pytanie „KONTYNUUJ / PARKUJ / ZETNIJ" wróci w KAŻDEJ sesji (Z14).
- **KONTYNUUJ** — `/spec-apply-review porzadek-wersji` i przerabiamy dwunastkę.

**Nic z R4 nie zostało zastosowane.** Master jest nietknięty od czasu bumpu 0.5.1.

## Stan: pliki

**Niezacommitowane**, HEAD nadal `5f25c62`. **Kod i baza NIETKNIĘTE** — cały pomiar odczytowy albo z `ROLLBACK`.
- `SPEC-PORZADEK-WERSJI-MASTER.md` — zmieniony, v0.5.1, 1466 linii (bez zmian w tym wątku)
- `STATE.md` — `spec: R4-codex-pending` — **poprawny, NIE bumpuj ręcznie**, zrobi to `/spec-apply-review`
- `_review/R4-codex.md` — **NOWY**, 15 165 B, werdykt REQUEST_CHANGES, 12 blokerów
- `_review/.R4-codex-last-msg.md` — **NOWY**, 800 B, podsumowanie Codexa
- `_review/.R4-codex-run2.log` — **NOWY**, 1,29 MB, pełny log udanego biegu
- `_review/.R4-codex-run.log` — 725 KB, ślad biegu zabitego limitem (diagnostyczny, można skasować)
- `_review/.base-R4.md` — baseline pomiaru NITS-EXT, **NIE nadpisywać**
- `_review/R4-opus-preflight.md`, `.R4-probe-selftest.py`, `.R4-selftest-out.txt`, `.R4-prompt.md` — bez zmian
- `_review/FABLE-BRIEF-R3.md` — nieaktualny, świadomie nietknięty

## Do decyzji właściciela — wiszą od R2, nie blokują

- **D5** — restore snapshotu staje się owner-only. Jedyna decyzja mastera, która **zabiera** istniejącą
  możliwość. Udostępniasz książkę redaktorowi w trybie „sam sobie cofa wpadki"? — powiedz, odwracam.
- **D6** — przypięcie snapshotu bez nazwy dostaje nazwę zastępczą z serwera, nie odmowę.
- **`19c4a5fe`** — otworzyć projekt i zerknąć (Bożena, 2 rozdziały, ost. edycja 2026-02-06).
