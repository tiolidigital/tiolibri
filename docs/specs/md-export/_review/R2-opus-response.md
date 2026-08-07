# R2-opus-response — REQUEST_CHANGES przetworzony

**Data:** 2026-08-07
**Werdykt Codexa:** REQUEST_CHANGES (3 BLOCKER + 2 MAJOR, 11/11 kategorii sprawdzonych)
**Spec:** `SPEC-MD-EXPORT.md` v0.3.1 → **v0.4**

**Budżet:** N=2, `reset-po-spike`=0, `rundy-rdzenia`=0 → **N_EFF=2**, MAX_ROUNDS=2 (Risk STANDARD).
`DELTA_ROUND=0`. Czyli próg osiągnięty → Krok 6 (konwergencja) rozstrzyga, nie Krok 5 pkt 5.

**Convergence-ext:** przyznane w R2 (blokery maleją: R1 **8 BLOCKER + 5 MAJOR** → R2 **3 BLOCKER
+ 2 MAJOR**, i to blokery innej klasy — R1 obalał wykonalność rdzenia („algorytm HTML→MD nie jest
implementowalny bez zgadywania"), R2 nie tknął już ani konwersji, ani escapingu, ani endpointu
jako takich, tylko trzy punktowe luki i audyt dowodu). Rejestr zapisany w `STATE.md` linią
`convergence-ext: R2`. **R3 jest twardym końcem** — kolejnego przedłużenia nie ma.

**STOP-and-SPIKE: nie kwalifikuje się.** Centralny bloker R1 (#4, wykonalność algorytmu konwersji)
NIE wraca w R2 — checklist Codexa zalicza „Logika + edge/nullish" jako sprawdzone. R2 #5 dotyka
sąsiedniego, węższego kontraktu (jak LICZYĆ `blocks`, nie jak konwertować), a nie tego samego
rdzenia drugi raz. Rekurencja klasy C/M/E (R1 #11 MAJOR → R2 #1/#2 BLOCKER) jest realna, ale to
**aparatura dowodu, nie rdzeń projektowy** — spike na realnych danych niczego by tam nie
rozstrzygnął, bo problem był w tym, co rekordy o sobie twierdziły, nie w tym, co zmierzono.

---

## Uwagi Codexa — decyzje

### 1. BLOCKER — rekordy pomiarów Ewy mają `C ⊄ E` mimo `werdykt=PASS` — **[A]**

**Decyzja: ZAAKCEPTOWANE w całości.** Zarzut jest trafny i dokładnie tak, jak Codex go stawia:
liczby (3,44×, 215) są poprawne i nie były kwestionowane — nieprawdziwe było `PASS` przy `C`,
które sięgało poza wykonany zbiór. Oba rekordy same wyłączały w polu `poza` to, co obejmowały
w `C`; to jest sprzeczność wewnątrz rekordu, nie kwestia interpretacji.

**Naprawione bez nowego przebiegu** (Codex sam wskazuje, że nie jest potrzebny):
- `pomiar-bloba-w-rozdziale-ewy` — `C` zawężone do: ~70% pliku, iloraz 3,44×, `nietykalny=false`.
  Wypchnięte poza `C`: „blob poleciałby do modelu" i „Redaktor nie ma strażnika na ładunek
  binarny" — oznaczone jako **inferencja z kontraktu** (chunk edytowalny idzie do W2, ODPOWIEDZ §C).
- `przebieg-w1-na-rozdziale-8-ewy` — `C` zawężone do: 215 chunków. Wypchnięte: „setki cykli
  stop-wypełnij-wznów" → inferencja z kontraktu transportu plikowego (ODPOWIEDZ P1).

**Sweep po tej samej klasie (LESSONS#3 pkt 1) — znaleziony TRZECI rekord, którego Codex nie
wskazał:** `przebieg-redaktora-na-rozdziale-bozeny` miał w `C` „27 chunków, **czyli blisko
trzydzieści wywołań W2**", a własne `E` przyznawało, że liczba wywołań jest **wyprowadzona
z liczby chunków edytowalnych**, bo skrzynka niesie 59 kluczy z trzech przebiegów. Ta sama
konstrukcja, ten sam defekt. Zawężone z własnej inicjatywy — inaczej R3 znalazłby to jako
czwarty bloker tej samej klasy.

Spec v0.4 rozdziela pomiar od inferencji w trzech miejscach: §`_media/`, §Krok 4 (Ewa),
§Krok 4 (Bożena). Rekordy poprawione **w miejscu, pod jawnym znacznikiem KOREKTA PO R2** —
nie przepisane po cichu.

### 2. BLOCKER — bramka strukturalna C/M/E niespełniona przez rekord CONTRACTED — **[A]**

**Decyzja: ZAAKCEPTOWANE.** `kontrakt-redaktora-KONTRAKT-md-v1` miał `mierzalne-od` **zamiast**
`E`, a nie **obok** — więc rekord nie spełniał `dowod|C|M|E|poza|werdykt` i nie dało się
sprawdzić `M == E`. Wybrałem pierwszy z dwóch wariantów Codexa (dać rzeczywiste `E`), bo część
`C` tego rekordu **została w R2 faktycznie uruchomiona** i wyłączenie go z listy cytowanych
dowodów zgubiłoby ten fakt:

- `E` dopisane: (1) byte-diff `segmentuj.ts` `4ebec8c..d7087bd` — pusty, EXIT=0; (2) sześć
  regexów `:12-17` przepisanych i odpalonych na 78 przypadkach, PASS=78 FAIL=0, EXIT=0 — to
  dowodzi wykonaniem tej części `C`, która mówi, czym chunker rozpoznaje bloki.
- `mierzalne-od` **zostaje jako pole dodatkowe** i obejmuje teraz wyłącznie **nieuruchomioną
  resztę** `C` (K-NAG przy apply, exact-match kotwic, NFC).

### 3. BLOCKER — G2 jednocześnie dopuszcza listy i nazywa je zerem — **[P]**

**Decyzja: ZAAKCEPTOWANE.** To była sprzeczność kryterium akceptacji, nie proza: dwaj
implementatorzy bramki dostawali przeciwne werdykty na tym samym `chunks.json` dla rozdziału
z listą (a przykład manifestu ma `"lista": 2`). Rozdzielone dokładnie tak, jak proponuje Codex:

- **G2** = `blocks.kod == 0` **i** `blocks.tabela == 0` i zero takich chunków w `chunks.json`.
- **`lista`** wypada z G2 i zostaje wyłącznie w **G1**, gdzie jest zwykłym typem porównywanym
  z licznikiem. G2 nie ma już żadnego przecięcia z G1.

Powiązane, poprawione razem: „zastąpione **trzema** asercjami" przy tabeli G1–G4 → **czterema**
(Codex nazwał to NIT-em do naprawy przy okazji). Plus sweep tej samej sprzeczności w §Bramki,
gdzie uzasadnienie Risk wymieniało „przypadkowym chunkiem `kod`/`lista`/`tabela`" — przepisane
na `kod`/`tabela` + rozjazd licznika `lista`.

### 4. MAJOR — brak ciała requestu nie ma egzekwowalnej sygnatury endpointu — **[P]**

**Decyzja: ZAAKCEPTOWANE.** Zarzut jest w pełni trafny: przy `request: ExportMdRequest` FastAPI
zwraca **422 na brak body**, czyli dokładnie odwrotnie niż pierwszy wiersz tabeli §Endpoint.
Implementator mógł zrobić poprawny model i złamać kontrakt.

Wpisana konkretna sygnatura, **zwalidowana wobec produkcji** (`export_import.py:34-38`), a nie
napisana z głowy — bo pierwsza wersja tej poprawki użyła `Depends(get_current_user)` i `UUID`,
podczas gdy repo ma `Depends(verify_supabase_jwt)`, `project_id: str` i prefiks routera
`/projects` (LESSONS#20: każda nazwa zewnętrznego bytu przez `rg` przed handoffem):

```python
@router.post("/{project_id}/export-md")
async def export_md(project_id: str,
                    request: Optional[ExportMdRequest] = None,
                    user: dict = Depends(verify_supabase_jwt)):
    chapter_ids = request.chapter_ids if request is not None else None
```

**Sprawdzenie czterech rozłącznych wejść — ręczne (curl), nie `TestClient`.** Odstępstwo od
literalnej sugestii Codexa i jest ono świadome: automatyzacja wymaga zamockowania klienta
Supabase, czyli **szóstego pliku testowego i nowego harnessu** — oś plików (5/5 PASS) zamieniłaby
się w FAIL, a dyspensa właściciela z R1 obejmowała LOC, nie liczbę plików (LESSONS#17 pkt 6:
jedno obejście limitu, nie drugie). Reszta endpointu też nie ma dziś testów automatycznych
w tym specu — sprawdzian jest na tym samym poziomie rygoru, nie niżej. Wariant „bez `-d`" jest
w tabeli nazwany jako **jedyny, który wykrywa brak `Optional`**.

### 5. MAJOR — manifest `blocks` nie definiuje liczenia złożonych bloków — **[P]**

**Decyzja: ZAAKCEPTOWANE.** G1 ma **zerową tolerancję**, a kontrakt mówił tylko „licznik
wyemitowanych bloków per typ chunkera" — implementator musiał odtwarzać granice bloków
intuicyjnie. Dodany §„Jak liczymy `blocks` — algorytm, nie intuicja" z rozstrzygnięciem
kierunku, którego spec wcześniej nie miał:

> `blocks` liczy się **z finalnego Markdowna**, przez odtworzenie granic bloków konsumenta —
> nie z drzewa HTML i nie z licznika wywołań emitera.

Uzasadnienie jest wymuszone przez samą bramkę: `chunks.json` powstaje z `segmentuj()` na naszym
`.md`, więc licząc po stronie HTML-a porównywalibyśmy dwa różne języki i zerowa tolerancja byłaby
nieosiągalna **z definicji**. Algorytm zapisany krokami na tych samych sześciu regexach
+ `INDENT_MIN=2` + lookahead, plus tabela dziewięciu konsekwencji — w tym trzy, które Codex
wskazał wprost: lista wieloelementowa/zagnieżdżona = **1** blok `lista`, ciąg blockquote = **1**
blok, obraz i `---` = **`akapit`** (`---` pasuje do `RE_TABLE_SEP`, ale reguła tabeli wymaga `|`
w linii poprzedniej, a tam jest pusta).

Fixture'y dopisane do kroku 1 planu — **8 przypadków, każdy asertujący cały słownik `blocks`**,
nie pojedynczy klucz (inaczej przeciek do sąsiedniego typu przechodzi).

---

## Klasyfikacja L-C i decyzja o rundzie

| Uwaga | Klasa | Dlaczego |
|---|---|---|
| #1 `C ⊄ E` | **A** | aparatura dowodu / protokół review |
| #2 rekord bez `E` | **A** | bramka strukturalna preflightu |
| #3 sprzeczność G2 | **P** | kryterium akceptacji bramki produktu |
| #4 sygnatura endpointu | **P** | kontrakt API |
| #5 semantyka `blocks` | **P** | kontrakt danych wejściowych bramki |

**3× P, 2× A, 0× D → runda R3 jest uzasadniona** (stop L-C nie ma zastosowania; on obejmuje
werdykty, w których WSZYSTKIE przyjęte uwagi są klasy A/D).

## Zmiany w specu (v0.3.1 → v0.4)

1. §Sizing — test file ~150 → ~165 LOC, razem ~567 → **~582**, dyspensa ~67 → **~82 LOC**,
   z jawnym powodem i **zapisaną liczbą nowych przypadków (8)**. LESSONS#17 pkt 5: wzrost
   macierzy nie może być cichym rozciągnięciem. Osie plików (5/5) i czasu (~90 min) bez zmian.
2. §Bramki — uzasadnienie Risk: `kod`/`lista`/`tabela` → `kod`/`tabela` + rozjazd licznika `lista`.
3. §Kontrakt konwersji — **nowy podrozdział „Jak liczymy `blocks`"** (algorytm + tabela
   9 konsekwencji).
4. §`_media/` — rozdzielone: zmierzone (`nietykalny=false`) vs inferencja (W2 zjadłby blob).
5. §Endpoint — **sygnatura route'u** + mapowanie `None → wszystkie` + powód `Optional[...]`.
6. §Krok 4 — G2 przepisane (`kod`/`tabela` = 0), akapit „dlaczego `lista` wypadła z G2",
   „trzema" → „czterema" asercjami, Ewa i Bożena rozdzielone na pomiar vs inferencja.
7. §Plan wdrożenia krok 1 — 8 fixture'ów `blocks`.
8. §Plan wdrożenia krok 2 — sygnatura route'u + tabela czterech wejść body (curl) z powodem,
   dlaczego ręcznie.

## Zmiany w preflighcie R2

`_review/R2-opus-preflight.md` §Audyt C/M/E — nagłówek KOREKTA PO R2 + trzy rekordy z zawężonym
`C` (dwa z review, trzeci ze sweepu) + rekord CONTRACTED z dopisanym `E`. Liczby nietknięte.

## Proactive drain

`Brak proactive suggestions.` — brak akcji. Drain: 0 obserwacji (workflow=0, inne=0).

## ZADANIE KOŃCOWE — RETRO

Nic ponad to, co już drenuje master 4.6. Obserwacja o trzecim rekordzie tej samej klasy jest
instancją LESSONS#3 pkt 1 (sweep po klasie po batchu edycji), nie nową regułą.

---

## Dla Piotrka — jedno zdanie

Codex nie zatwierdził speca, ale blokery spadły z ośmiu do trzech i zeszły z „to się nie da
zaimplementować" na „doprecyzuj trzy miejsca" — poprawiłem wszystkie pięć uwag plus jedną,
której Codex nie znalazł, i spec dostaje jedną dodatkową rundę R3 jako twardy koniec.

**Kopiuj dalej — w tym samym wątku:**
```
/spec-handoff md-export
```
