# R3 — preflight Opusa (L5) · md-export

**Spec:** `docs/specs/md-export/SPEC-MD-EXPORT.md` (wersja **0.4.1**, light, Risk STANDARD)
**Runda generowana:** R3 (STATE `spec: R2-opus-pending` → N=3, TARGET=3)
**Data:** 2026-08-07
**Środowisko dowodów:** repo TIOLIBRI @ `f0940c4`, venv `tiolibri-api/venv` (Python **3.9.6**,
FastAPI 0.115.12, Pydantic 2.12.5, httpx 0.27.2); kanon konsumenta `FABRYKA-redaktor` gałąź
`redaktor` @ **`134f8e4`**; Node **v24.12.0** (`--experimental-strip-types`).

R1 zweryfikował kotwice v0.2, R2 to, co dopisała v0.3. Ta runda weryfikuje **to, co dopisała
v0.4** — czyli obie poprawki produktowe z blokerów R2: sygnaturę endpointu (#4) i algorytm
liczenia `blocks` (#5). Oba są **uruchomione**, nie odczytane: sygnatura przez `TestClient`
z kontrpróbą, `blocks` przez porównanie z **prawdziwym `segmentuj()`** na 11 fixture'ach.

Cztery fakty wyszły błędnie i **wszystkie są już wpisane do speca** (v0.4 → v0.4.1), nie
zostawione Codexowi. Jeden z nich jest merytoryczny, nie kosmetyczny — patrz §Co poszło do speca.

---

## Fakty

- FACT: VERIFIED | kind=state-machine | source=docs/specs/md-export/STATE.md:1 | note=spec: R2-opus-pending → N=3, nazwa pliku R3-opus-preflight.md zgodna z TARGET=3, impl: not-started bez zmian, convergence-ext: R2 obecne (R3 jest twardym końcem budżetu)
- FACT: VERIFIED | kind=signature | source=tiolibri-api/app/routers/export_import.py:34-38 | note=@router.post("/{project_id}/export") + project_id: str + user: dict = Depends(verify_supabase_jwt) — trzy elementy sygnatury ze §Endpoint zgadzają się z produkcyjnym sąsiadem co do znaku
- FACT: VERIFIED | kind=arg | source=tiolibri-api/app/routers/export_import.py:21 | note=router = APIRouter(prefix="/projects", tags=["export-import"]) — prefiks /projects potwierdzony, więc ścieżka POST /projects/{project_id}/export-md jest kompletna
- FACT: VERIFIED | kind=export | source=rg -n 'def verify_supabase_jwt' tiolibri-api/app/ → app/dependencies.py:6 | note=symbol istnieje i jest importowany w export_import.py:19 — nazwa zależności nie jest zmyślona (LESSONS#20)
- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python scratchpad/t_signature.py — TestClient na dwóch aplikacjach, tabela 5 wejść body | note=PASS=6 FAIL=0 EXIT=0; Optional[ExportMdRequest]=None daje 200 na brak body, a kontrpróba bez Optional daje 422 przy identycznych b-d — wiersz 1 tabeli §Endpoint jest egzekwowalny dokładnie tą sygnaturą
- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python -c "import fastapi,pydantic,httpx" | note=fastapi 0.115.12, pydantic 2.12.5, httpx 0.27.2 na Pythonie 3.9.6, EXIT=0 — TestClient jest uruchamialny w tym venv bez instalacji czegokolwiek
- FACT: VERIFIED | kind=execution | source=node --experimental-strip-types scratchpad/blocks/real.ts fixtures.json | note=prawdziwy segmentuj() z FABRYKA-redaktor wykonany na 11 fixture'ach Markdowna, EXIT=0 — wszystkie 9 wierszy tabeli konsekwencji §Jak liczymy blocks potwierdzone co do liczby i typu
- FACT: VERIFIED | kind=parser | source=tiolibri-api/venv/bin/python scratchpad/blocks/spec_blocks.py fixtures.json real.json | note=PASS=11 FAIL=0 EXIT=0 dla kolejności konsumenta; kolejność wypisana w v0.4 rozjeżdża się na 2 z 11 — pełny wynik w §Parser self-test
- FACT: CORRECTED | kind=parser | source=segmentuj.ts:55-146 (kolejność gałęzi pętli) + pomiar F10/F11 | note=stare=kolejność ATX → MARKER → BQ → FENCE → tabela nowe=kolejność gałęzi pętli `segmentuj.ts:55-146`
- FACT: CORRECTED | kind=path-existing | source=git -C FABRYKA-redaktor diff --stat 4ebec8c..134f8e4 -- src/redaktor/chunker/segmentuj.ts (pusto, EXIT=0) oraz d7087bd..134f8e4 (pusto, EXIT=0) | note=stare=d7087bd opisany jako obecny HEAD gałęzi redaktor nowe=bajtowo identyczny w `d7087bd` i w `134f8e4`
- FACT: CORRECTED | kind=fixture | source=rg -n '~3×' SPEC-MD-EXPORT.md → §Co odrzucone (wiersz o obrazie inline) | note=stare=rozjeżdża pomiar ~3× nowe=3,44×
- FACT: CORRECTED | kind=sizing | source=rg -n '~67' SPEC-MD-EXPORT.md → §Decyzje właściciela | note=stare=Dyspensa sizingu na ~67 LOC ponad limit nowe=~82 LOC
- FACT: VERIFIED | kind=anchor | source=segmentuj.ts:91 | note=L.includes("|") && i+1<n && RE_TABLE_SEP.test(lines[i+1].text) — gałąź tabeli stoi PRZED blockquote i listą w pętli, co jest treścią korekty kolejności
- FACT: VERIFIED | kind=anchor | source=segmentuj.ts:142 | note=while (j+1<n && !isBlank(...) && !startsBlock(...)) — startsBlock nie zawiera tabeli, więc tabela jest rozpoznawana wyłącznie na początku bloku; przepisane do kroku 2.6 algorytmu
- FACT: VERIFIED | kind=anchor | source=/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/src/redaktor/model/typy.ts:48 | note=export type ChunkTyp = "akapit" | "naglowek" | "lista" | "blockquote" | "kod" | "tabela" — sześć kluczy blocks w §Sygnatura i w manifeście to dokładnie ta enumeracja, bez literówki
- FACT: VERIFIED | kind=path-new | source=test -f tiolibri-api/app/services/md_exporter.py && test -f tiolibri-api/test_md_exporter.py | note=oba pliki docelowe nadal nie istnieją, rodzice istnieją (PARENT_OK, NOT_EXISTS_OK) — spec jest wciąż przed implementacją
- FACT: VERIFIED | kind=sizing | source=docs/specs/md-export/SPEC-MD-EXPORT.md:8-24 | note=marker "Sizing: DYSPENSA" ze źródłem autoryzacji obecny, tabela 5 plików / ~582 LOC wobec limitu 500/90min/5 plików, dyspensa ~82 z jawną liczbą nowych przypadków (8) — korekty tej rundy są prozą, zero LOC produkcyjnych dołożonych
- FACT: VERIFIED | kind=fixture | source=rg -c '3,44×|~82 LOC|134f8e4|55-146' docs/specs/md-export/SPEC-MD-EXPORT.md → 7 | note=wszystkie cztery skorygowane wartości realnie obecne w pliku speca, nie tylko w tym preflighcie (U1-P2)

### Co poszło do speca z korekt

1. **Kolejność rozpoznawania bloków — jedyna korekta merytoryczna tej rundy.** v0.4 wypisywała
   gałęzie algorytmu w kolejności ATX → marker → BQ → fence → tabela. Prawdziwy `segmentuj()`
   sprawdza je w kolejności fence → ATX → **tabela** → BQ → marker (`:55-146`), a wzorce **nie
   są rozłączne**: linia `> a | b` bezpośrednio nad `---` daje u konsumenta **jeden chunk
   `tabela`**, a w kolejności ze speca `blockquote` + `akapit`. To samo dla `- a | b`. Zmierzone,
   nie wydedukowane — F10/F11 w §Parser self-test. W naszym własnym wyjściu ta klasa jest
   nieosiągalna (nasze `---` zawsze ma nad sobą pustą linię, a proza pasująca do `RE_TABLE_SEP`
   dostaje backslash w kroku 6), ale przy **zerowej tolerancji G1** algorytm ma odtwarzać
   konsumenta, nie przybliżać go. Spec ma teraz kolejność jako jawną część kontraktu
   z uzasadnieniem i z nazwanym przypadkiem rozjazdu.
2. **SHA kanonu konsumenta** — `d7087bd` przestało być HEAD-em (jest `134f8e4`). To druga runda
   z rzędu, w której ten wskaźnik się zestarzał. `segmentuj.ts` jest bajtowo identyczny we
   **wszystkich trzech** rewizjach (`4ebec8c`, `d7087bd`, `134f8e4`), więc kotwice po numerach
   linii trzymają — i spec mówi to teraz wprost, zamiast wskazywać ruchomy HEAD (LESSONS#20).
3. **`~3×` w §Co odrzucone** — przeżyło korektę R2, która podniosła tę liczbę do `3,44×`
   w §`_media/`. Klasyczny stale-ref po batchu edycji: poprawione jedno wystąpienie z dwóch
   (LESSONS#3 pkt 1). Ten sam dokument podawał dwie różne liczby dla tego samego pomiaru.
4. **`~67 LOC` w §Decyzje właściciela** — ta sama klasa. §Sizing mówi `~82` po wzroście w R2,
   §Decyzje właściciela wciąż `~67`. Poprawione z zachowaniem historii („w R1 autoryzowane ~67"),
   bo dyspensa właściciela dotyczyła tamtej liczby i ten ślad ma zostać.

Korekty 3 i 4 znalazł sweep `rg` po liczbach zmienionych w R2, nie lektura. Obie są dokładnie
tą klasą, którą LESSONS#3 przewiduje po edycji >100 LOC prozy — i obie przeszłyby do Codexa
jako NIT-y albo gorzej.

---

## Parser self-test

Spec deklaruje **dwa** egzekwowalne parsery. Escaping był dowiedziony w R2 (78 przypadków,
PASS=78 FAIL=0) i nie zmienił się w v0.4 — nie powtarzam go. Nowy jest **algorytm liczenia
`blocks`** (§Jak liczymy `blocks`, bloker #5 z R2) i to jego dotyczy ten dry-run.

Metoda jest mocniejsza niż w R2, bo tu da się porównać z oryginałem: te same fixture'y idą
przez **prawdziwy `segmentuj()`** (Node 24, `--experimental-strip-types`, import wprost
z `FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts`, EXIT=0) i przez **implementację
algorytmu ze speca** w Pythonie, w dwóch wariantach kolejności gałęzi.

```
fixture                        prawdziwy segmentuj()      kolejnosc ze SPECA v0.4    kolejnosc konsumenta
F1 lista 5 pozycji             {"lista": 1}               {"lista": 1}               {"lista": 1}
F2 lista zagniezdzona          {"lista": 1}               {"lista": 1}               {"lista": 1}
F3 li z drugim akapitem        {"lista": 1}               {"lista": 1}               {"lista": 1}
F4 dwie listy + akapit         {"lista": 2, "akapit": 1}  {"akapit": 1, "lista": 2}  {"akapit": 1, "lista": 2}
F5 blockquote 4 linie          {"blockquote": 1}          {"blockquote": 1}          {"blockquote": 1}
F6 obraz                       {"akapit": 1}              {"akapit": 1}              {"akapit": 1}
F7 divider miedzy akapitami    {"akapit": 3}              {"akapit": 3}              {"akapit": 3}
F8 obraz + figcaption          {"akapit": 2}              {"akapit": 2}              {"akapit": 2}
F9 naglowek h2                 {"naglowek": 1}            {"naglowek": 1}            {"naglowek": 1}
F10 BQ z pipe przed ---        {"tabela": 1}              {"blockquote":1,"akapit":1}  <-ROZJAZD   {"tabela": 1}
F11 marker z pipe przed ---    {"tabela": 1}              {"lista": 1, "akapit": 1}    <-ROZJAZD   {"tabela": 1}

kolejnosc konsumenta vs prawdziwy segmentuj(): PASS=11 FAIL=0   EXIT=0
kolejnosc ze SPECA v0.4 rozjezdza sie na: F10, F11
```

**F1–F9 to dokładnie dziewięć wierszy tabeli konsekwencji ze speca** — każdy zbudowany jako
Markdown, który nasz konwerter ma wyemitować dla danej konstrukcji HTML. Wszystkie dziewięć
zgadza się z prawdziwym chunkerem co do liczby i typu. To jest pierwszy raz, kiedy ta tabela
została **zmierzona**, a nie wyprowadzona z lektury `segmentuj.ts`.

**Gate odrzuca zły wkład, nie tylko istnieje.** F10 i F11 są wkładem FAIL i zostały dobrane tak,
żeby **kolidowały z dozwolonym wzorcem** (LESSONS#13 pkt 1): nie są nielegalnym Markdownem,
tylko legalnym blockquote i legalną listą, które akurat zawierają `|` nad linią separatora.
Dopiero taka kontrpróba ujawnia, że kolejność gałęzi jest kontraktem — fixture z losowo złym
tekstem przeszedłby w obu wariantach i niczego by nie obalił.

**Czego self-test NIE pokrywa.** (1) Nie pokrywa drogi HTML → Markdown — fixture'y są pisane
jako gotowy Markdown, więc dowodzą reguły LICZENIA, a nie tego, że konwerter taki Markdown
wyprodukuje; to jest treść testów jednostkowych z kroku 1 planu. (2) Nie pokrywa `kod` ani
`tabela` jako typów emitowanych przez nas — konwerter ich nie produkuje (§Ograniczenia),
a G2 traktuje ich pojawienie się jako błąd. (3) Nie pokrywa całego rozdziału Ewy przepuszczonego
przez `segmentuj()` — to jest krok 4 planu, po implementacji. Dry-run sygnatury endpointu
nie pokrywa `Depends(verify_supabase_jwt)` ani dostępu do Supabase: mierzy **semantykę parametru
body**, czyli dokładnie to, czego dotyczył bloker #4, i nic ponadto.

---

## Audyt C/M/E

Kanon `docs/specs/spec-workflow/CME-MANIFEST.md` **nie istnieje** ani w TIOLIBRI, ani w FABRYCE
(sprawdzone ponownie w tej rundzie). Zgodnie z regułą 1 audyt nie jest tu blokerem; sekcja jest
wypełniona, bo bramka strukturalna obowiązuje, a spec cytuje cudze pomiary.

Rekordy przeniesione z R2 zachowują `E` **append-only z etykietą rundy** (reguła 3) — historia
zawężeń z R2 zostaje widoczna, dopisany jest wyłącznie stan R3.

- CME: typ=MEASURED | dowod=preflight-R3-blocks-vs-prawdziwy-chunker | C=spec §Jak liczymy `blocks` twierdzi, że dziewięć wierszy tabeli konsekwencji odpowiada temu, jak konsument dzieli tekst na bloki, oraz że kolejność sprawdzania gałęzi jest częścią kontraktu (lista wieloelementowa i zagnieżdżona = 1 blok `lista`, ciąg blockquote = 1 blok, obraz i `---` i `<figcaption>` = `akapit`, dwie listy rozdzielone akapitem = 2+1) | M=sekcja Parser self-test tego pliku, 11 fixture'ów × 3 kolumny (prawdziwy chunker, kolejność v0.4, kolejność konsumenta) | E=R3: 11 fixture'ów przepuszczonych przez PRAWDZIWY segmentuj() z FABRYKA-redaktor @ 134f8e4 (Node 24 --experimental-strip-types, EXIT=0) i przez implementację algorytmu ze speca w Pythonie (EXIT=0); F1-F9 zgodne we wszystkich trzech kolumnach, F10/F11 rozjeżdżają kolejność v0.4 z konsumentem, kolejność konsumenta PASS=11 FAIL=0 | poza=poza dowodem zostaje droga HTML → Markdown (fixture'y są pisane jako gotowy Markdown, nie generowane przez konwerter, którego jeszcze nie ma) oraz zachowanie na całym rozdziale Ewy — proporcjonalne, bo pierwsze jest wprost treścią testów jednostkowych z kroku 1 planu, a drugie treścią bramki G1 z kroku 4, i obie są w specu nazwane jako kryteria akceptacji, nie jako rzeczy dowiedzione tutaj | werdykt=PASS
- CME: typ=MEASURED | dowod=preflight-R3-sygnatura-endpointu | C=spec §Endpoint twierdzi, że przy `request: Optional[ExportMdRequest] = None` brak body daje 200 i `chapter_ids is None`, że `chapter_ids: null` zbiega się w tę samą gałąź, że `[]` pozostaje rozróżnialne, że ID niebędące UUID daje 422, oraz że wariant „bez `-d`" jest JEDYNYM, który wykrywa brak `Optional` | M=skrypt scratchpad/t_signature.py — dwie aplikacje FastAPI (sygnatura ze speca oraz kontrpróba bez `Optional`), pięć wejść body plus test rozróżnienia | E=R3: PASS=6 FAIL=0 EXIT=0 na FastAPI 0.115.12 / Pydantic 2.12.5 / Python 3.9.6; A (ze speca): brak body 200 {"ids": null}, `null` 200, `[]` 200 z `[]`, `[uuid]` 200, nie-UUID 422; B (kontrpróba): brak body **422**, a b-d identycznie jak A — czyli twierdzenie o wariancie (a) jest zmierzone, nie założone | poza=poza dowodem zostaje cała reszta endpointu: `Depends(verify_supabase_jwt)`, `_assert_project_access`, budowa ZIP-a i kody 400/404/409/413, bo test biegnie na aplikacji bez Supabase — proporcjonalne, bo bloker #4 dotyczył wyłącznie tego, czy sygnatura egzekwuje pierwszy wiersz tabeli, a pozostałe kody są przedmiotem ręcznego sprawdzenia odbiorczego z kroku 2 planu, jawnie tam opisanego wraz z powodem, dlaczego jest ręczne | werdykt=PASS
- CME: typ=MEASURED | dowod=pomiar-bloba-w-rozdziale-ewy | C=(ZAWĘŻONE po R2) spec §_media/ twierdzi, że blob to ~70% pliku, że zaniża mianownik strażnika budżetu o 3,44× i że chunker nadaje mu nietykalny=false, czyli klasyfikuje go jako chunk edytowalny — TO JEST CAŁE C. Poza C wypchnięte: twierdzenie, że blob przy pełnym przebiegu POLECIAŁBY DO MODELU i że Redaktor nie ma strażnika na ładunek binarny; oba są inferencją z kontraktu (chunk edytowalny idzie do W2, ODPOWIEDZ §C), NIE pomiarem — przebieg był --tylko-w1, zero wywołań modelu. Spec v0.4 §_media/ oznacza je jawnie jako inferencję | M=ODPOWIEDZ ERRATA E4 (bajty i procent) + ZWIAD-EWA-R8.md §0 (przebieg W1, run-idy, flaga nietykalny) | E=R1: 118 843 B pliku, 83 127 B bloba, 69,9% — zmierzone na pliku z Google Docs, bez uruchomienia Redaktora · R2: uruchomiony przebieg --tylko-w1 na tym samym materiale, dwa run-idy 2026-08-07-38300c i 2026-08-07-630047, proponowane_procent 0,0120% vs 0,0412% (iloraz 3,44), chunk p-215 z nietykalny=false, W1 obojętny na blob (7 edycji vs 7, NOM 58 vs 59, RYT 13 vs 13) · R3: bez nowego przebiegu; zmieniło się tylko to, że druga wzmianka o tym pomiarze w §Co odrzucone podawała `~3×` i została zrównana z `3,44×` | poza=poza dowodem zostaje zachowanie W2 na blobie (przebieg był --tylko-w1, zero wywołań modelu) oraz to, czy nasze processed_html w ogóle niosą data: URI — proporcjonalne, bo eksport wycina blob bezwarunkowo, więc odpowiedź nie zmienia ani jednej linii kodu; pytanie o processed_html pokryte zapytaniem SQL zapisanym w §_media/ na krok 1 implementacji | werdykt=PASS
- CME: typ=MEASURED | dowod=przebieg-w1-na-rozdziale-8-ewy | C=(ZAWĘŻONE po R2) spec §Krok 4 twierdzi, że rozdział 8 Ewy dał 215 chunków przy chunking: akapit — TO JEST CAŁE C. Poza C wypchnięte: przełożenie 215 chunków na SETKI CYKLI stop-wypełnij-wznów; to inferencja z kontraktu transportu plikowego (przy provider: plik przebieg staje na każdym wywołaniu W2, ODPOWIEDZ P1), NIE pomiar | M=ZWIAD-EWA-R8.md §1 (tabela wyników W1 na kopii roboczej, 215 chunków) | E=R2: policzone na kopii roboczej ewa-r8-bez-obrazu.md (448 linii, 35 728 B) z data-URI podmienionym na referencję, run-id 2026-08-07-38300c — zmierzona jest LICZBA CHUNKÓW, nie liczba wywołań W2 ani czas operatora · R3: bez zmian, liczba nietknięta i nieużyta w żadnej nowej bramce | poza=poza dowodem zostaje przełożenie 215 chunków na realne wywołania W2 oraz liczba dla rozdziału wyprodukowanego przez NASZ eksport, który będzie miał inną gęstość akapitów po wycięciu bloba — proporcjonalne, bo liczba nie steruje żadną bramką tego speca, służy wyłącznie ostrzeżeniu operatora; pokryte krokiem 4 planu, który liczy chunki na naszym własnym wyjściu | werdykt=PASS
- CME: typ=MEASURED | dowod=przebieg-redaktora-na-rozdziale-bozeny | C=(ZAWĘŻONE po R2) spec §Krok 4 twierdzi, że rozdział Bożeny dał 27 chunków — TO JEST CAŁE C. Poza C wypchnięte: "blisko trzydzieści wywołań W2"; to wyprowadzenie z liczby chunków edytowalnych, nie odczyt z przebiegu (skrzynka niesie 59 kluczy z TRZECH przebiegów), więc inferencja z kontraktu, nie pomiar | M=ODPOWIEDZ ERRATA E1 (sprostowanie wcześniejszego "14 wywołań") | E=R0: 27 chunków policzone z przebiegu · E1: skrzynka tego rozdziału zawiera 59 kluczy z TRZECH przebiegów, więc liczba wywołań na przebieg jest wyprowadzona z liczby chunków edytowalnych, nie odczytana wprost z jednego przebiegu · R2: liczba niezmieniona, zestawiona w specu z 215 chunkami Ewy jako kontrast, nie jako prognoza · R3: bez zmian | poza=poza dowodem zostaje czas operatora na jeden cykl stop-wypełnij-wznów — proporcjonalne, bo nie steruje żadną bramką; pokryte pierwszym realnym przebiegiem właściciela | werdykt=PASS
- CME: typ=MEASURED | dowod=preflight-R2-dryrun-escaping | C=spec §Kontrakt escapingu twierdzi, że jedno wstawienie backslasha neutralizuje każdy z pięciu wzorców strukturalnych, że escaping jest węższy niż w v0.2 i że przypadki negatywne zostają czyste | M=sekcja Parser self-test w `_review/R2-opus-preflight.md`, 78 przypadków | E=R2: 68 pozytywnych (17 wzorców × wcięcia 0-3) i 10 negatywnych, PASS=78 FAIL=0, EXIT=0, na regexach przepisanych z segmentuj.ts:12-17 — testowana jest FUNKCJA escape_line, nie przebieg prawdziwego segmentuj() na naszym pliku · R3: nie powtarzane, bo §Kontrakt escapingu nie zmienił się między v0.3.1 a v0.4.1; potwierdzone natomiast, że plik źródłowy regexów jest bajtowo ten sam także w 134f8e4 | poza=poza dowodem zostaje zachowanie prawdziwego chunkera na wyjściu konwertera oraz interakcja escapingu z resztą kolejności operacji (kroki 1-9) — proporcjonalne, bo pierwsze jest wprost treścią bramki G1-G4 z kroku 4, a drugie testami jednostkowymi z kroku 1 | werdykt=PASS
- CME: typ=MEASURED | dowod=preflight-R2-python-i-postgrest | C=spec twierdzi, że sygnatury Optional[...] są uruchamialne w venv, że PEP 604 tam nie jest, że produkcja stoi na 3.11 i że dwa .order() dają order=sort_order,id | M=cztery uruchomienia w tiolibri-api/venv plus odczyt Dockerfile:2 | E=R2: PEP 604 w Pydantic i w dataclass rzuca TypeError na 3.9.6 (dwa osobne uruchomienia), warianty Optional[list[UUID]] i Optional[bytes] budują się bez błędu EXIT=0, builder PostgREST zwrócił order=sort_order%2Cid bez ruchu sieciowego, Dockerfile:2 to python:3.11-bookworm · R3: Optional[list[UUID]] potwierdzone po raz drugi, tym razem w żywej aplikacji FastAPI z walidacją UUID (nie-UUID → 422), EXIT=0 | poza=poza dowodem zostaje zachowanie samego PostgREST na tak zbudowanym zapytaniu (builder testowany bez sieci i bez bazy) — proporcjonalne, bo wieloczłonowy order jest udokumentowanym zachowaniem PostgREST, a skutkiem błędu byłaby wyłącznie niedeterministyczna kolejność numerów NN, wykrywalna w kroku 4 | werdykt=PASS
- CME: typ=CONTRACTED | dowod=kontrakt-redaktora-KONTRAKT-md-v1 | C=spec §Problem i §Kontrakt escapingu twierdzą, że chunker jest parserem Markdowna, K-NAG porównuje nagłówki ATX i przerywa apply przy rozjeździe, kotwice są exact-match, wymagane jest NFC i wyłącznie ATX | M=ODPOWIEDZ A2/A4/A5 wyprowadzone przez Redaktora z ICH kodu; KONTRAKT.md v1 w dwóch miejscach odstaje od kodu, więc źródłem jest ODPOWIEDZ. Ta część C, która ZOSTAŁA uruchomiona, jest niesiona przez OSOBNE rekordy MEASURED, bo to osobne artefakty wykonania (reguła 2): `preflight-R2-dryrun-escaping` dowodzi, czym chunker rozpoznaje bloki (78 przypadków), a `preflight-R3-blocks-vs-prawdziwy-chunker` dowodzi uruchomieniem prawdziwego `segmentuj()`, że dzieli tekst tak, jak opisuje tabela konsekwencji. Ten rekord nie ma pola `E` i mieć go nie może (reguła 5) — w R2 dopisano tu `E`, żeby domknąć bramkę strukturalną, i to była zła forma: rekord stawał się MEASURED i CONTRACTED naraz, co bramka `cme_typ_both` odrzuca. Poprawione w R3 bez utraty faktu, bo fakt mieszka w tamtych dwóch rekordach | mierzalne-od=nieuruchomiona reszta C (K-NAG przerywa apply przy rozjeździe, kotwice exact-match, wymóg NFC) mierzalna od kroku 4 planu wdrożenia (przepuszczenie wyeksportowanego rozdziału Ewy przez CLI Redaktora do chunks.json, asercje G1-G4), a pełny K-NAG dopiero przy ręcznym apply właściciela poza tą fazą | poza=poza kontraktem zostaje zachowanie strażników przy suwakach innych niż testowe oraz pełny K-NAG, który uruchamia się dopiero przy apply — proporcjonalne, bo eksport jest read-only i najgorszy skutek to zły plik .md kasowany ponownym eksportem; pokryte ręcznym przebiegiem apply właściciela, jawnie wyłączonym z tej fazy | werdykt=PASS

**Czego ten preflight NIE dowodzi.** Nie dowodzi, że wyeksportowany `.md` przejdzie przez
`segmentuj()` **jako całość rozdziału** — uruchomiliśmy prawdziwy chunker po raz pierwszy, ale
na jedenastu krótkich fixture'ach pisanych ręcznie, nie na wyjściu konwertera, którego jeszcze
nie ma. Zostaje i jest proporcjonalne: krok 4 planu ma na to cztery asercje z zerową tolerancją.
Nie dowodzi też, że nasze `processed_html` niosą `data:` URI (zapytanie SQL na krok 1), ani
niczego o zachowaniu endpointu poza semantyką parametru body — pozostałe kody HTTP są
przedmiotem ręcznego sprawdzenia odbiorczego z kroku 2, jawnie tam opisanego.
