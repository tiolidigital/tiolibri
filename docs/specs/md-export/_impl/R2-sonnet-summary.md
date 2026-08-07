# Implementation R2 — Sonet

**Data:** 2026-08-07
**Faza:** `SPEC-MD-EXPORT.md` (light spec, brak `PHASE-*.md`)
**Wersja speca implementowana:** **0.4.2** (podbita w tej rundzie — patrz „Co zmieniłem")
**Commit:** brak — `/spec-impl` nie commituje. HEAD nadal `1871f07`, zmiany w worktree.

## Co zmieniłem od R1

Dwa blokery z `_impl/R1-codex-review.md`, oba domknięte. Trzeci punkt to uwaga nieblokująca,
którą też zamknąłem, bo Codex prosił o nią „w R2".

### BLOCKER 1 (G3) — wdrożone (B), po pomiarze rozszerzone do (B′)

Codex zarządził **(B)**: nie emitować markerów emfazy, gdy obejmuje **całą** znaczącą treść
nagłówka; częściową zostawić. Zaimplementowałem dokładnie to, przepuściłem bramkę — i **(B)
dało 11/12**, nie 12/12. Sprawca jest realny i pochodzi z produkcji, rozdz. 1 Ewy:

```html
<h1><img/>WSTĘP: <strong>Jak zaczęła się moja historia z osteoporozą.</strong></h1>
   → # WSTĘP: **Jak zaczęła się moja historia z osteoporozą.**
```

Emfaza nie obejmuje prefiksu „WSTĘP: ", więc wg litery (B) markery zostają. Ale to **ten sam
artefakt Google Docs** i **ta sama mina pod K-NAG**, przed którą (B) miało chronić: nagłówek
jest chunkiem edytowalnym (`chunkuj.ts:13` daje `nietykalny` tylko `kod`/`tabela`, a te są
u nas twardymi zerami przez G2), więc idzie do W2 i zgubiona para gwiazdek wywala `apply`.

**W R1 tego nagłówka nie było widać** — diagnostyczne `strip_em` w harnessie zdejmowało markery
po obu stronach porównania. Dokładnie to, przed czym ostrzegał Risk flag Codexa
w `PROACTIVE-INBOX.md`: narzędzie dowodu po (B) staje się maskownicą.

Zapytałem właściciela. **Decyzja z 2026-08-07: (B′)** — w `<h1>`…`<h6>` nie emitujemy żadnych
markerów emfazy, także przy częściowej. Poza nagłówkiem emfaza działa jak dotąd.
**To jest zmiana wobec litery werdyktu Codexa i wymaga jego akceptacji w R3.**

Argument za (B′) ponad wygodę: G3 ma **zerową** tolerancję, więc (B) czyni ją prawdziwą tylko
przypadkiem — dopóki żaden nagłówek nie ma emfazy częściowej. (B′) czyni ją prawdziwą
**z konstrukcji**. Koszt jest bliski zeru: informacja „ta część nagłówka była pogrubiona"
w nagłówku, który i tak jest wyróżniony w całości.

Implementacja jest o **jedną linię prostsza** niż (B): `_emit_heading` woła `_inline(...,
emphasis=False)`. Wersja (B) potrzebowała rekurencyjnego `_emphasis_covers_all()` (~25 LOC,
z przechodzeniem przez `<span>` Google Docs) — usunięte razem z (B).

### BLOCKER 2 (sizing) — decyzja właściciela, dyspensa rozszerzona

Codex: „recenzent nie może sam rozszerzyć autoryzacji". Zapytałem. **Decyzja z 2026-08-07:
rozszerzyć dyspensę do zmierzonego rozmiaru, jedna kohezywna faza zamiast splitu** — bo kod
istniał i był zielony, 509 z tych LOC to testy (LESSONS#17: w tej samej sumie), a split po
fakcie znaczyłby dwie pełne rundy review nad tym samym kodem.

Zapisane w specu — §Sizing niesie teraz **zmierzone** liczby, oba źródła autoryzacji
(aktualne i historyczne dla audytu) oraz **dokładną liczbę przypadków: 162**, ze ścieżką
wzrostu 110 → 162 i rozbiciem, skąd te +52 (LESSONS#17 pkt 5). Zdanie „każdy dalszy wzrost
macierzy wymaga ponownego jawnego potwierdzenia" jest w specu wprost.

### Uwaga nieblokująca: parytet parserów — zamknięta pomiarem, nie deklaracją

Codex: „brak dowodu parytetu parserów na uszkodzonym HTML-u, warto dołożyć małą próbę".
Dołożyłem — i **próba wykazała, że parytetu na uszkodzonym markupie NIE MA**. Na niedomkniętym
`<li>` i niedomkniętym `<hN>` lxml domyka inaczej niż `html.parser` i wyjścia się różnią.

Nie zamiatam tego pod dywan i nie udaję zielonego parytetu: rozdzieliłem na dwa testy —
**parytet obiecany i dowiedziony na markupie domkniętym** (7 kształtów realnie wychodzących
z TipTapa, `md` i `blocks` identyczne) oraz **`test_parsery_roznia_sie_na_markupie_uszkodzonym`,
który tę granicę asertuje jako zmierzoną**. Nas to nie dotyka, bo wejściem jest
`processed_html` z TipTapa, czyli markup domknięty — ale granica jest teraz w kodzie, nie
w domyśle. Do lxml **nie wracam**, zgodnie z zaleceniem.

Dołożyłem też `test_fallback_faktycznie_przelacza_parser` — bez niego test parytetu byłby
zielony także wtedy, gdyby `monkeypatch` nic nie zmienił (LESSONS#13 pkt 4: pusty wkład
narzędzia daje fałszywy PASS).

## Co zrobione

1. **`md_exporter.py`** — `_inline()` dostał parametr `emphasis`; `_emit_heading()` woła go
   z `emphasis=False`. Poza nagłówkiem zero zmian zachowania.
2. **`test_md_exporter.py`** — **110 → 162** przypadków. Nowe: 8 kształtów emfazy pełnej,
   5 częściowej (w tym **kształt wzięty z produkcji**, rozdz. 1 Ewy), kontrakt
   `tekst nagłówka == get_text() źródła` na wszystkich 13 (lokalne odbicie G3 z zerową
   tolerancją), „żaden nagłówek nie niesie `*` ani `_`", regresje trzymające emfazę
   w akapicie/`<li>`/blockquote nietkniętą, 7 próbek parytetu parserów + 2 rozjazdu
   + test, że fallback faktycznie przełącza parser.
3. **`harness/bramka_all.py`** — usunięte diagnostyczne `strip_em`; G3 stoi na porównaniu
   literalnym. **Domyka Risk flag z `PROACTIVE-INBOX.md`.**
4. **Bramka przepuszczona ponownie** na żywym endpoincie — `R2-bramka-G1-G4.md`.
5. **Spec 0.4.1 → 0.4.2** — §Sizing (dyspensa + 162 przypadki), nowa §Emfaza w nagłówku,
   dwa wiersze w §Tabela reguł z odsyłaczem do wyjątku, §Decyzje właściciela (impl R2).

## Pliki zmienione

| Plik | R1 | R2 | Rodzaj |
|---|---|---|---|
| `tiolibri-api/app/services/md_exporter.py` | 540 | **547** | NOWY (niezacommitowany) |
| `tiolibri-api/test_md_exporter.py` | 368 | **509** | NOWY (niezacommitowany) |
| `tiolibri-api/app/routers/export_import.py` | +203 | **+201 −2** | zmiana |
| `tiolibri-frontend/src/features/editor/EditorPage.jsx` | +47 | **+47** | zmiana |
| `tiolibri-frontend/src/features/editor/activityLabels.js` | +1 | **+1** | zmiana |
| **razem (churn)** | ~1159 | **~1307** | 5 plików, oś plików PASS |

Artefakty review (`_impl/*`, `harness/*`) nie wchodzą do osi sizingu — tak samo jak w R1.
`gate/`, `gate_all/`, `chunks*.json` **skasowane po przebiegu**, są regenerowalne.

**`.DS_Store` (dwa) — nie wpuszczać do commita** (uwaga Codexa z R1, nadal aktualna; oba pliki
są *tracked*, więc `.gitignore` ich nie zdejmie — trzeba je po prostu pominąć przy `git add`).

## Testy

- **`pytest -q test_md_exporter.py` → 162 passed** (0.58 s). R1: 110.
- **Mutacja reguły (B′)** — LESSONS#6/#14, uruchomiona na PRODUKCJI z rewertem bajtowym
  (`cmp` OK): podmiana `emphasis=False` → `emphasis=True` w `_emit_heading` daje
  **16 czerwonych** (8 oczekiwanych wyjść pełnej emfazy + 8 kontraktu `== get_text()`).
  Reguła jest dowiedziona, nie zadeklarowana.
- **Bramka G1–G4, rozdz. 8 Ewy: PASS 4/4** — G3 domknięte, pierwsza różnica: brak.
- **Bramka szeroka 12/12 rozdziałów, 1141 chunków: G1–G4 PASS na każdym**,
  **280 nagłówków, zero różnic**, G3 **literalne** (bez normalizacji diagnostycznej).
- **`npm run build`: PASS**, exit 0.
- **Regresja stackowa** (`stack_regression_checks`): kolejność routerów w `main.py` nietknięta;
  zero `.select()` po `.update().eq()`; zmiana nie dotyka TipTapa ani
  `addProseMirrorPlugins()` — jedyny plik frontendu (`EditorPage.jsx`) bez zmian od R1.
- **Baseline-relatywnie:** fail@teraz = fail@HEAD = {`test_polish_pdf.py` — collection error,
  brak `libgobject-2.0-0`}. Bez zmian od R1.

## Decyzje implementacyjne

1. **(B′) zamiast (B)** — powyżej. Świadome odstępstwo od litery werdyktu Codexa, oparte na
   pomiarze, który w R1 był zamaskowany, i zatwierdzone przez właściciela. LESSONS#21 pkt 5:
   naprawa u źródła przenosi atak recenzenta warstwę niżej — (B) naprawiało konwerter, ale
   pytanie „czy na pewno KAŻDY nagłówek?" zostawało otwarte; (B′) je zamyka.
2. **Parytet parserów rozdzielony na obiecany i zmierzony rozjazd** — LESSONS#13: bramka,
   która nie ma wkładu FAIL, nie jest dowiedziona. Zielony parytet na uszkodzonym HTML-u
   byłby nieprawdą, więc granica jest zaasertowana, nie przemilczana.
3. **Diagnostyczne `strip_em` usunięte, nie „poprawione"** — po (B′) każde zdejmowanie markerów
   po stronie bramki maskuje prawdziwy `_` w tekście nagłówka.
4. **Spec podbity do 0.4.2 mimo `spec: GREEN`** — bo obie zmiany to **zapis decyzji właściciela**
   (LESSONS#17 pkt 5 wymaga jawnego śladu sizingu; wyjątek emfazy zmienia kontrakt konwersji
   i bez wpisu w §Tabela reguł spec zostałby wewnętrznie sprzeczny — czyli dokładnie ten sam
   błąd, który wyprodukował bloker G3).

## Co odłożone

- **Wiersz „projekt bez rozdziałów"** — bez zmian od R1: żaden projekt właściciela nie ma zera
  nieusuniętych rozdziałów, odpalenie wymaga atrapy w **produkcyjnej** bazie. Gałąź jest w kodzie
  (`export_import.py:177-178`), przed filtrem `chapter_ids`. Codex w R1 uznał to za nieblokujące.
- **Prawdziwy K-NAG przy `apply`** — z definicji poza fazą (§Krok 4).
- **`.DS_Store` w indeksie git** — realny brud repo, ale to nie zakres tej fazy.

## Proactive suggestions

- **Workflow:** normalizacja diagnostyczna w harnessie bramki przeżyła rundę i zamaskowała
  realny przypadek — narzędzie dowodu musi mieć datę ważności zapisaną razem z nim.
- **Risk flag:** `.DS_Store` jest *tracked* w tym repo, więc `.gitignore` go nie zdejmie —
  każdy commit fazy wymaga ręcznego pominięcia; `git rm --cached` to osobna decyzja.
- **Praise:** wymuszenie przez Codexa przebiegu bramki na materiale produkcyjnym, a nie na
  fixture'ach, złapało kształt `WSTĘP: <strong>…</strong>`, którego żaden wymyślony test by nie miał.

---

## Dla Piotrka — jedno zdanie

Bramka jest zielona na całej książce: 12 rozdziałów, 1141 kawałków, 280 nagłówków i **zero
różnic** — po tym, jak zdjęliśmy pogrubienia z nagłówków (Google Docs wstawia je mechanicznie,
a Redaktorowi wysadzają publikację), i po Twojej zgodzie na rozmiar tej fazy.

**Kopiuj dalej — w tym samym wątku:**
```
(nic — raport wraca do wątku dyrektora, on doręcza Codexowi /spec-review)
```
