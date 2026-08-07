# R2 — review speca MD-EXPORT

**Spec:** `docs/specs/md-export/SPEC-MD-EXPORT.md` v0.3.1  
**Zakres:** review przed implementacją, light, Risk STANDARD  
**Data:** 2026-08-07

## Werdykt

**Werdykt:** REQUEST_CHANGES

Sprawdziłem **11/11 kategorii** checklisty. Jedyna kategoria N/A: **SQL/RLS/migracja** — endpoint
jest read-only wobec danych książki, korzysta z istniejącej kontroli dostępu i nie wymaga migracji
ani zmiany polityk. To ostatnia runda budżetu, ale wątpliwość nadal oznacza REQUEST_CHANGES: preflight
ma fałszywie zaliczony audyt dowodu, a kontrakt implementacyjny zawiera sprzeczność oraz dwie luki,
które zmuszają implementatora do zgadywania.

## Co wymaga zmiany

### 1. BLOCKER — rekordy pomiarów Ewy mają `C ⊄ E`, mimo `werdykt=PASS`

Oba rekordy wskazane szczególnie w handoffie uczciwie mówią, że materiał pochodził z Google Docs,
nie z naszego eksportu, ale ich werdykty nie wynikają z zapisanych zbiorów:

- `pomiar-bloba-w-rozdziale-ewy`: `C` obejmuje twierdzenie speca, że blob przy pełnym przebiegu
  „poleciałby do modelu” (`SPEC:358-361`), podczas gdy `E` obejmuje wyłącznie `--tylko-w1`, a pole
  `poza` wprost wyłącza zachowanie W2. To twierdzenie może być poprawną inferencją z kodu, lecz nie
  należy do wykonanego zbioru tego dowodu. W obecnym rekordzie `C ⊄ E`.
- `przebieg-w1-na-rozdziale-8-ewy`: `C` obejmuje „215 chunków [...] oznacza setki cykli
  stop-wypełnij-wznów” (`SPEC:624-630`), a `E` mierzy wyłącznie liczbę chunków i wprost nie mierzy
  liczby wywołań W2 ani czasu operatora. Znów rekord sam wyłącza z `E` część własnego `C`.

Naprawa nie wymaga kwestionowania liczb 3,44× ani 215 i nie wymaga nowego przebiegu: trzeba zawęzić
`C` do tego, co rzeczywiście wykonano, a wnioski o W2 oznaczyć osobno jako inferencję z kontraktu
transportu plikowego. Reguła 1 (brak `CME-MANIFEST.md`) czyni sam audyt nieblokującym, ale nie czyni
fałszywego `PASS` prawdziwym; handoff wymaga sprawdzenia prawdziwości `C ⊆ E`.

### 2. BLOCKER — bramka strukturalna C/M/E nie jest spełniona przez rekord CONTRACTED

Rekord `kontrakt-redaktora-KONTRAKT-md-v1` w `R2-opus-preflight.md` nie ma pola `E`; ma zamiast
niego `mierzalne-od`. Master §4.9 i opis żywej bramki `/spec-handoff` wymagają kompletnego rekordu
`dowod|C|M|E|poza|werdykt`. Brak kanonicznego `CME-MANIFEST.md` znosi bloker audytu manifestu,
ale handoffowa **bramka strukturalna nadal obowiązuje** zgodnie z treścią zadania. W tej postaci
nie da się też sprawdzić `M == E`. Rekord musi dostać rzeczywiste `E` albo zostać wyłączony z listy
„cytowanych uruchomionych dowodów” i opisany jako kontrakt do zmierzenia po implementacji.

### 3. BLOCKER — G2 jednocześnie dopuszcza listy i nazywa je zerem

Spec wspiera `<ul>/<ol>/<li>` (`SPEC:234`, `:274-283`), przykład manifestu ma `"lista": 2`
(`:458`), a G2 wymaga „zero chunków typu `kod`, `lista` i `tabela` ponad zadeklarowane w `blocks`”,
po czym mówi, że „te są zerami, bo `<pre>`/`<table>` są poza zakresem” (`:606`). Dla realnego
rozdziału z listą nie wiadomo, czy G2 ma zaakceptować liczbę równą `blocks.lista`, czy wymagać zera.
To jest sprzeczność kryterium akceptacji, nie typo: implementator bramki może uzyskać przeciwne
werdykty na tym samym `chunks.json`. Trzeba jawnie rozdzielić: `kod=tabela=0`, a `lista` równa
zadeklarowanemu licznikowi (albo usunąć listę z G2 jako już pokrytą przez G1).

### 4. MAJOR — brak ciała requestu nie ma egzekwowalnej sygnatury endpointu

Tabela endpointu rozróżnia brak body, `null`, `[]` i listę UUID (`SPEC:488-505`), ale podaje tylko
model `ExportMdRequest`, nie sygnaturę parametru route. W FastAPI samo
`request: ExportMdRequest` czyni brak body błędem 422; wymagane zachowanie potrzebuje opcjonalnego
parametru body i jawnego mapowania `None → wszystkie`. Bez sygnatury implementator może poprawnie
zaimplementować model, a mimo to złamać pierwszy wiersz tabeli. Spec ma przypiąć konkretną sygnaturę
zgodną z Pythonem 3.9, np. `request: Optional[ExportMdRequest] = None`, i wskazać test czterech
rozłącznych wejść.

### 5. MAJOR — manifest `blocks` nie definiuje sposobu liczenia złożonych bloków

`ChapterResult.blocks` jest wejściem zerotolerancyjnej G1, ale kontrakt mówi tylko „licznik
wyemitowanych bloków per typ chunkera” (`SPEC:203-220`). Nie rozstrzyga, czy wieloelementowa lista
to jeden blok `lista` (tak robi `segmentuj()`), czy liczba `<li>`; analogicznie kilka kolejnych
linii blockquote to jeden chunk, a linie obrazu i `---` stają się chunkami `akapit`. Implementator
nie powinien odtwarzać tych zasad intuicyjnie, skoro G1 porównuje liczby z zerową tolerancją.
Trzeba zdefiniować liczenie zgodnie z granicami bloków konsumenta albo wyliczać `blocks` z finalnego
Markdowna tą samą, jawnie opisaną regułą i dodać fixture: lista wieloelementowa/zagnieżdżona,
ciąg blockquote, obraz oraz divider.

## Exhaustiveness checklist

- [✓ sprawdzone] **Budżet ROZMIARU:** 5 plików, ~567 LOC, 1 domena, 0 migracji; testy są w sumie.
  Dyspensa ~67 LOC ma ślad decyzji właściciela. Nie przeliczam liczby testów jako sizingu.
- [✓ sprawdzone] **Spójność z kanonem + stale references:** ERRATA E1–E4, kod konsumenta i młodszy
  ZWIAD sprawdzone; liczby 3,44×/215 mają poprawnie nazwane pochodzenie. `segmentuj.ts` jest bajtowo
  identyczny między wskazanymi rewizjami. Nie otwieram trzech zamkniętych decyzji właściciela.
- [✓ sprawdzone] **Egzekwowalność:** luki w sygnaturze body i semantyce `blocks` opisane w #4–#5.
- [✓ sprawdzone] **Logika + edge/nullish:** kolejność 9 operacji, escaping, obrazy, `null`/`[]`,
  puste `processed_html`, limity i sortowanie sprawdzone; sprzeczność G2 opisana w #3.
- [✓ sprawdzone] **Bundling / mutation targets (pure logic):** plan wymienia rozłączne gałęzie
  konwertera i negatywne fixture escapingu, ale dla krytycznych granic `blocks` brakuje rozłącznych
  przypadków mutacyjnych — objęte #5. Test endpointu czterech stanów body — #4.
- [✓ sprawdzone] **Typy/sygnatury/argi/ścieżki:** `Optional[...]`, dataclassy, Pydantic, symbole
  routera/frontendu oraz kotwice w obu repo sprawdzone; brak sygnatury route jest uwagą #4.
- [✓ sprawdzone] **Bramki maszynowe uruchomione:**
  - escaping na pięciu regexach strukturalnych z `segmentuj.ts:12-16`: 68 pozytywnych + 10
    negatywnych, `FAIL=0`, **EXIT=0**;
  - `tiolibri-api/venv/bin/python --version`: Python 3.9.6, **EXIT=0**;
  - `Optional[list[UUID]]` + `Optional[bytes]`: `OPTIONAL_OK`, **EXIT=0**;
  - PEP 604 w Pydantic na tym venv: oczekiwany `TypeError`, **EXIT=1**;
  - dwa `.order()`: `select=%2A&order=sort_order%2Cid`, **EXIT=0**;
  - byte-diff `segmentuj.ts` dla `4ebec8c..d7087bd`: pusty, **EXIT=0**.
- [✓ sprawdzone] **Manifest pokrycia dowodu:** brak `CME-MANIFEST.md` nie blokuje audytu regułą 1,
  lecz prawdziwość FAIL dla dwóch wskazanych rekordów (`C ⊄ E`) i struktura FAIL dla rekordu bez
  `E`; akapit „czego preflight NIE dowodzi” ma trzy wymagane elementy: zakres, proporcjonalność,
  miejsce późniejszego pokrycia.
- [N/A — spec jest read-only wobec danych książki, bez migracji i zmian RLS.] **SQL/RLS/migracja**
- [✓ sprawdzone] **UI/a11y/tokeny:** jeden przycisk ma disabled, `aria-busy`, błąd i instrukcję;
  brak nowego widoku/tokenów. Modal jest jawnie poza zakresem.
- [✓ sprawdzone] **Ryzyko/dane:** Risk STANDARD ma uzasadnienie i obowiązkową bramkę przed masowym
  użyciem; brak mutacji treści nie usuwa kosztu błędnego wsadu do W1/W2.
- [✓ sprawdzone] **Docs/proza:** znaleziono sprzeczność G2 oraz drobne „trzema asercjami” przy
  tabeli G1–G4 (`SPEC:600-608`). To drugie samo byłoby NIT, ale powinno zostać poprawione razem.

## Proactive suggestions (rzeczy o które nie pytano)

Brak proactive suggestions.

---

## Dla Piotrka — jedno zdanie

R2 nie może zatwierdzić speca: liczby są poprawne, ale audyt dowodu ma fałszywe PASS-y, a trzy kontrakty nadal wymagają zgadywania przed implementacją.

**Kopiuj dalej:**
```
/spec-apply-review md-export
```
