# R2 — preflight Opusa (L5) · md-export

**Spec:** `docs/specs/md-export/SPEC-MD-EXPORT.md` (wersja 0.3.1, light, Risk STANDARD)
**Runda generowana:** R2 (STATE `spec: R1-opus-pending` → N=2, TARGET=2)
**Data:** 2026-08-07
**Środowisko dowodów:** repo TIOLIBRI @ `7a7dec1`, venv `tiolibri-api/venv` (Python **3.9.6**),
obraz Railway `python:3.11-bookworm` (`Dockerfile:2`); kanon konsumenta `FABRYKA-redaktor`
gałąź `redaktor` @ `d7087bd`.

R1 zweryfikował kotwice v0.2. Ta runda weryfikuje **to, co v0.3 dopisała** (escaping z sześciu
regexów konsumenta, sygnatury dataclass/Pydantic, tie-breaker sortowania, kotwice cytowane
po numerach linii) plus dwie rzeczy, które zmieniły się **poza tym repo** od R1.

Pięć faktów wyszło błędnie i **wszystkie są już wpisane do speca**, nie zostawione Codexowi.

---

## Fakty

- FACT: VERIFIED | kind=state-machine | source=docs/specs/md-export/STATE.md:1 | note=spec: R1-opus-pending → N=2, nazwa pliku R2-opus-preflight.md zgodna z TARGET=2, impl bez zmian
- FACT: VERIFIED | kind=path-existing | source=/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts:12-17 | note=sześć regexów odczytane 1:1 i przepisane do §Kontrakt escapingu bez zmiany treści — RE_FENCE_OPEN, RE_ATX, RE_TABLE_SEP, RE_BQ, RE_MARKER, RE_BLANK
- FACT: VERIFIED | kind=anchor | source=segmentuj.ts:20 | note=const INDENT_MIN = 2 — spec wyprowadza z tego wcięcie 2 spacji na poziom listy, kotwica trafia w linię
- FACT: VERIFIED | kind=anchor | source=segmentuj.ts:91 | note=L.includes("|") && i+1<n && RE_TABLE_SEP.test(lines[i+1].text) — warunek tabeli jest dwuliniowy, tak jak twierdzi spec
- FACT: VERIFIED | kind=anchor | source=segmentuj.ts:100-105 | note=blockquote bez lazy continuation, RE_BQ testowany na KAŻDEJ kolejnej linii — zgodne z tabelą reguł
- FACT: VERIFIED | kind=anchor | source=segmentuj.ts:118-125 | note=lookahead przez pustą linię w liście (isBlank → skok do k, powrót gdy isMarker albo isIndent2) — spec cytuje ten zakres poprawnie
- FACT: VERIFIED | kind=anchor | source=segmentuj.ts:142 | note=akapit ciągnie się while !isBlank && !startsBlock — pojedynczy \n nie rozbija akapitu, czyli <br> → \n jest bezpieczne
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/editor/extensions/Divider.js:14,17,84 | note=:14 parseHTML czyta data-divider-style, :17 renderHTML atrybutu, :84 emisja w renderze node'a — rozdzielenie cytatów w specu zgadza się co do linii
- FACT: VERIFIED | kind=export | source=tiolibri-frontend/src/lib/authedFetch.js:28-33 | note=if(!res.ok) na :28 i throw Error(err.detail) na :30 wypadają PRZED gałęzią responseType==='blob' na :33 — 409/413 dojdą do UI bez zmian w authedFetch
- FACT: VERIFIED | kind=signature | source=tiolibri-api/app/routers/export_import.py:238 | note=def _assert_project_access(project_id: str, user_id: str) -> None — sygnatura zgodna z wywołaniem w §Endpoint
- FACT: VERIFIED | kind=arg | source=tiolibri-api/app/routers/chapters.py:211 | note=select("id, project_id, title, sort_order, deleted_at, deleted_by, status") — kolumny created_at nadal brak, więc tie-breaker na id jest jedyną pewną drogą (LESSONS#20)
- FACT: VERIFIED | kind=path-existing | source=tiolibri-frontend/src/features/editor/useChapters.js:184,195,199,209 | note=fallback source_file_path → bucket uploads → convertGoogleDocsHtml żyje w JS przeglądarki, w zakresie 177-212 cytowanym przez spec — uzasadnienie fail-closed 409 stoi
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/editor/ChapterEditor.jsx:60-62 | note=Image.configure({ inline: true, allowBase64: false }) — kotwica w zakresie, ryzyko utraty base64 przy zapisie potwierdzone
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/components/ui/Modal.jsx:64,87-90 | note=Escape na :64 i klik w overlay na :87-90; brak focus trapu i role="dialog" — notatka dla przyszłego speca modala trafna
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/projects/ProjectCard.jsx:197-209 | note=responseType 'blob' + createObjectURL + a.download + revokeObjectURL w cytowanym zakresie 194-215 — wzorzec do skopiowania istnieje
- FACT: VERIFIED | kind=path-new | source=test -f tiolibri-api/app/services/md_exporter.py && test -f tiolibri-api/test_md_exporter.py | note=oba pliki docelowe jeszcze nie istnieją, rodzice istnieją (PARENT_OK, NOT_EXISTS_OK)
- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python -c "import pytest" | note=ModuleNotFoundError: No module named 'pytest' — brak runnera w venv potwierdzony, EXIT=1 dla importu przy EXIT=0 powłoki
- FACT: VERIFIED | kind=execution | source=grep -in pytest tiolibri-api/requirements.txt | note=zero trafień, EXIT=1 — pytest nie jest zależnością obrazu, zapis speca "pip install pytest lokalnie" jest jedyną drogą
- FACT: VERIFIED | kind=fixture | source=ls tiolibri-api/test_*.py | note=tiolibri-api/test_polish_pdf.py istnieje w korzeniu — konwencja umiejscowienia pliku testowego ze speca ma precedens w repo
- FACT: CORRECTED | kind=execution | source=tiolibri-api/venv/bin/python -c "class M(BaseModel): chapter_ids: list[UUID] | None = None" | note=stare=chapter_ids z unią PEP 604 nowe=Optional[list[UUID]]
- FACT: CORRECTED | kind=execution | source=tiolibri-api/venv/bin/python -c "@dataclass class X: a: bytes | None = None" | note=stare=pola ExportImage z unią PEP 604 nowe=data: Optional[bytes]
- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python -c "Optional[list[UUID]] w Pydantic + Optional[str]/Optional[bytes] w dataclass" | note=oba warianty zbudowały się na 3.9.6, generyki PEP 585 (list[str], dict[str,int]) też — EXIT=0, wersja przepisana w specu jest uruchamialna w tym venv
- FACT: VERIFIED | kind=arg | source=tiolibri-api/Dockerfile:2 | note=FROM python:3.11-bookworm — produkcja jest na 3.11, więc rozjazd dotyczy wyłącznie lokalnego uruchamiania testów i jest nazwany w specu
- FACT: VERIFIED | kind=execution | source=tiolibri-api/venv/bin/python -c "SyncPostgrestClient(...).from_('chapters').order('sort_order').order('id').params" | note=zwrócone order=sort_order%2Cid — dwa .order() sklejają się w jeden parametr PostgREST, drugie nie nadpisuje pierwszego, EXIT=0
- FACT: VERIFIED | kind=parser | source=venv/bin/python scratchpad/t3.py — 68 przypadków pozytywnych i 10 negatywnych na regexach przepisanych z segmentuj.ts:12-17 | note=PASS=78 FAIL=0, escape neutralizuje każdy z pięciu wzorców przy wcięciach 0-3 i NIE rusza #hasztag, -myslnik, 1.5 mg, 1.lista — pełny wynik w sekcji Parser self-test, EXIT=0
- FACT: CORRECTED | kind=path-existing | source=git -C FABRYKA-redaktor diff --stat 4ebec8c..HEAD -- src/redaktor/chunker/segmentuj.ts | note=stare=segmentuj.ts opisany jako HEAD 4ebec8c gdy HEAD to już d7087bd nowe=bajtowo identyczny w `d7087bd`
- FACT: CORRECTED | kind=fixture | source=FABRYKA-redaktor/docs/redaktor/kalibracja/ZWIAD-EWA-R8.md:26-28 (commit 5a4fd8e) | note=stare=zaniżenie mianownika opisane za ODPOWIEDZIĄ jako ~3x nowe=3,44×
- FACT: CORRECTED | kind=fixture | source=FABRYKA-redaktor/docs/redaktor/kalibracja/ZWIAD-EWA-R8.md:31,35 (commit 5a4fd8e) | note=stare=dla rozdziału Ewy nie mamy oczekiwanego przedziału nowe=215 chunków
- FACT: VERIFIED | kind=sizing | source=docs/specs/md-export/SPEC-MD-EXPORT.md:8-24 | note=marker "Sizing: DYSPENSA" z nazwanym źródłem autoryzacji (decyzja właściciela R1) obecny, tabela plik→LOC daje 5 plików / ~567 LOC wobec limitu 500/90min/5 plików — zmiany tej rundy są prozą w specu, zero LOC produkcyjnych dołożonych

### Co poszło do speca z korekt

1. **`Optional[...]` zamiast `X | None`** — najgroźniejsza z pięciu, bo cicha. Venv jest na
   **3.9.6**, PEP 604 działa od 3.10, a adnotacja pola dataclassy i Pydantica jest ewaluowana
   **przy imporcie modułu**. Plan wdrożenia każe uruchomić testy w tym venv → `import
   md_exporter` wywaliłby `TypeError` zanim odpali się pierwszy test, mimo że produkcja na 3.11
   ruszyłaby bez szemrania. Spec ma teraz akapit „Składnia typów" i obie sygnatury przepisane.
   `app/` nie używa dziś PEP 604 w żadnym pliku — ten spec nie miał być pierwszy.
2. **SHA kanonu konsumenta** — `4ebec8c` przestało być HEAD-em (jest `d7087bd`). `segmentuj.ts`
   jest między nimi **bajtowo identyczny**, więc reguła escapingu stoi, ale opis był stale
   (LESSONS#20).
3. **Zaniżenie mianownika: `3,44×` zamiast `~3×`** — i to nie jest kosmetyka. Liczba pochodzi
   z **przebiegu na rozdziale Ewy**, nie z szacunku: `0,0120%` z blobem vs `0,0412%` bez.
4. **215 chunków dla rozdziału Ewy** — v0.3 pisała „nie mamy oczekiwanego przedziału". Mamy,
   i jest o rząd wielkości większy od 27 Bożeny. Nie zmienia zakresu, ale przesądza wniosek
   o pętli po książce, który spec już nosił w §Co odrzucone.
5. **Drugi tryb awarii bloba, którego ODPOWIEDZ nie znała** — chunker nadaje data-URI
   `nietykalny=false`, więc bez naszego wycięcia ~21k tokenów base64 poleciałoby do modelu.
   Redaktor nie ma na to strażnika. To wzmacnia §`_media/` z „warunek Redaktora" do „jedyne
   miejsce, w którym to się zatrzymuje".

Trzy ostatnie korekty pochodzą z dokumentu **młodszego od kanonu ustaleń** (`ZWIAD-EWA-R8.md`,
commit `5a4fd8e`, ta sama data co ODPOWIEDZ). Wskaźnik do niego jest teraz w nagłówku speca,
żeby następna runda nie musiała go szukać.

---

## Parser self-test

Reguła escapingu jest jedynym parserem, który ten spec deklaruje jako egzekwowalny. Dry-run
wykonany w `tiolibri-api/venv`, **na regexach przepisanych z `segmentuj.ts:12-17` w tej rundzie**
(nie na regexie wymyślonym przez nas — to była dokładnie treść blokera 3 z R1), `EXIT=0`.

Implementacja pod testem to reguła ze speca dosłownie: jeśli linia pasuje do **któregokolwiek**
z pięciu wzorców strukturalnych, wstaw `\` przed pierwszym nie-białym znakiem.

```
POSITIVE (ma złapać ORAZ escape ma zneutralizować): PASS=68 FAIL=0
NEGATIVE (nie wolno ruszyć):                        PASS=10 FAIL=0
```

Zbiór pozytywny: 17 wzorców × wcięcia 0, 1, 2, 3 spacje — fence ` ``` ` i `~~~`, ATX od `#`
do `######` i samo `#`, `>` i `>cytat`, markery `-` `*` `+`, `1.` i **`1)`**, `999999999.`,
separatory tabeli `|---|---|`, `---`, `:--:|:--`, `- - -`.

Zbiór negatywny (musi wyjść nietknięty): `#hasztag`, `-myslnik`, `1.5 mg`, `zwykly tekst`,
`srodek - myslnik`, `2026 rok`, `a | b`, `tekst z ``` w srodku`, `1.lista bez spacji`,
`    - cztery spacje wciecia`.

Próbki wyniku:

```
'```py'                       -> match=FENCE       escaped='\```py'
'1) lista'                    -> match=MARKER      escaped='\1) lista'
'|---|---|'                   -> match=TABLE_SEP   escaped='\|---|---|'
'   > cytat'                  -> match=BQ          escaped='   \> cytat'
'#hasztag'                    -> match=-           escaped='#hasztag'     (bez zmian)
'1.lista bez spacji'          -> match=-           escaped='1.lista bez spacji'
```

Gate **odrzuca** zły wkład, nie tylko istnieje: dziesięć przypadków negatywnych przechodzi
przez `escape_line` bez zmiany bajtu. Dwa wyniki warte nazwania:

- **`1)` jest markerem listy** (`\d{1,9}[.)]`) — reguła z v0.2 („cyfra kropka") by go
  przepuściła. Fixture w specu ma go wymieniony.
- **`    - cztery spacje wciecia` nie jest escape'owane**, bo wszystkie regexy konsumenta
  wymagają `^ {0,3}`. Jest to bezpieczne dwukrotnie: krok 5 kolejności operacji robi `strip()`
  każdej linii **przed** escapingiem, więc taka linia w naszym wyjściu nie powstaje, a nawet
  gdyby powstała — wcięcie ≥2 znaczy „kontynuacja listy" tylko wewnątrz bloku listy.

**Czego self-test NIE pokrywa:** reguł konwersji bez parsera do odpalenia (mapowanie `<h1>`–`<h6>`
na ATX, listy, blockquote, `<br>`, inline). To mapowania 1:1 bez gałęzi, mierzalne od testów
jednostkowych z kroku 1 planu i od bramki G1–G4 z kroku 4. Nie pokrywa też zachowania
prawdziwego `segmentuj()` na naszym wyjściu — to jest krok 4, po implementacji.

---

## Audyt C/M/E

Kanon `docs/specs/spec-workflow/CME-MANIFEST.md` **nie istnieje** ani w TIOLIBRI, ani w FABRYCE
(sprawdzone ponownie w tej rundzie). Zgodnie z regułą 1 audyt nie jest tu blokerem; sekcja jest
wypełniona, bo bramka strukturalna obowiązuje, a spec cytuje cudze pomiary.

- CME: typ=MEASURED | dowod=pomiar-bloba-w-rozdziale-ewy | C=spec §_media/ twierdzi, że blob to ~70% pliku, że jest chunkiem edytowalnym i że zaniża mianownik strażnika budżetu o 3,44×, oraz że chunker nadaje mu nietykalny=false | M=ODPOWIEDZ ERRATA E4 (bajty i procent) + ZWIAD-EWA-R8.md §0 (przebieg W1, run-idy, flaga nietykalny) | E=R1: 118 843 B pliku, 83 127 B bloba, 69,9% — zmierzone na pliku z Google Docs, bez uruchomienia Redaktora · R2: uruchomiony przebieg --tylko-w1 na tym samym materiale, dwa run-idy 2026-08-07-38300c i 2026-08-07-630047, proponowane_procent 0,0120% vs 0,0412% (iloraz 3,44), chunk p-215 z nietykalny=false, W1 obojętny na blob (7 edycji vs 7, NOM 58 vs 59, RYT 13 vs 13) | poza=poza dowodem zostaje zachowanie W2 na blobie (przebieg był --tylko-w1, zero wywołań modelu) oraz to, czy nasze processed_html w ogóle niosą data: URI — proporcjonalne, bo eksport wycina blob bezwarunkowo, więc odpowiedź nie zmienia ani jednej linii kodu; pytanie o processed_html pokryte zapytaniem SQL zapisanym w §_media/ na krok 1 implementacji | werdykt=PASS
- CME: typ=MEASURED | dowod=przebieg-w1-na-rozdziale-8-ewy | C=spec §Krok 4 twierdzi, że rozdział Ewy dał 215 chunków przy chunking: akapit i że oznacza to setki cykli stop-wypełnij-wznów przy provider: plik | M=ZWIAD-EWA-R8.md §1 (tabela wyników W1 na kopii roboczej, 215 chunków) | E=R2: policzone na kopii roboczej ewa-r8-bez-obrazu.md (448 linii, 35 728 B) z data-URI podmienionym na referencję, run-id 2026-08-07-38300c — zmierzona jest LICZBA CHUNKÓW, nie liczba wywołań W2 ani czas operatora | poza=poza dowodem zostaje przełożenie 215 chunków na realne wywołania W2 (zwiad był --tylko-w1) oraz liczba dla rozdziału wyprodukowanego przez NASZ eksport, który będzie miał inną gęstość akapitów po wycięciu bloba — proporcjonalne, bo liczba nie steruje żadną bramką tego speca, służy wyłącznie ostrzeżeniu operatora; pokryte krokiem 4 planu, który liczy chunki na naszym własnym wyjściu | werdykt=PASS
- CME: typ=MEASURED | dowod=preflight-R2-dryrun-escaping | C=spec §Kontrakt escapingu twierdzi, że jedno wstawienie backslasha neutralizuje każdy z pięciu wzorców strukturalnych, że escaping jest węższy niż w v0.2 i że przypadki negatywne zostają czyste | M=sekcja Parser self-test tego pliku, 78 przypadków | E=R2: 68 pozytywnych (17 wzorców × wcięcia 0-3) i 10 negatywnych, PASS=78 FAIL=0, EXIT=0, na regexach przepisanych z segmentuj.ts:12-17 w tej rundzie — testowana jest FUNKCJA escape_line, nie przebieg prawdziwego segmentuj() na naszym pliku | poza=poza dowodem zostaje zachowanie prawdziwego chunkera na wyjściu konwertera oraz interakcja escapingu z resztą kolejności operacji (kroki 1-9) — proporcjonalne, bo pierwsze jest wprost treścią bramki G1-G4 z kroku 4, a drugie testami jednostkowymi z kroku 1 | werdykt=PASS
- CME: typ=MEASURED | dowod=preflight-R2-python-i-postgrest | C=spec twierdzi, że sygnatury Optional[...] są uruchamialne w venv, że PEP 604 tam nie jest, że produkcja stoi na 3.11 i że dwa .order() dają order=sort_order,id | M=cztery uruchomienia w tiolibri-api/venv plus odczyt Dockerfile:2 | E=R2: PEP 604 w Pydantic i w dataclass rzuca TypeError na 3.9.6 (dwa osobne uruchomienia), warianty Optional[list[UUID]] i Optional[bytes] budują się bez błędu EXIT=0, builder PostgREST zwrócił order=sort_order%2Cid bez ruchu sieciowego, Dockerfile:2 to python:3.11-bookworm | poza=poza dowodem zostaje zachowanie samego PostgREST na tak zbudowanym zapytaniu (builder testowany bez sieci i bez bazy) — proporcjonalne, bo wieloczłonowy order jest udokumentowanym zachowaniem PostgREST, a skutkiem błędu byłaby wyłącznie niedeterministyczna kolejność numerów NN, wykrywalna w kroku 4 | werdykt=PASS
- CME: typ=MEASURED | dowod=przebieg-redaktora-na-rozdziale-bozeny | C=spec §Krok 4 twierdzi, że rozdział Bożeny dał 27 chunków, czyli blisko trzydzieści wywołań W2 przy provider: plik | M=ODPOWIEDZ ERRATA E1 (sprostowanie wcześniejszego "14 wywołań") | E=R0: 27 chunków policzone z przebiegu · E1: skrzynka tego rozdziału zawiera 59 kluczy z TRZECH przebiegów, więc liczba wywołań na przebieg jest wyprowadzona z liczby chunków edytowalnych, nie odczytana wprost z jednego przebiegu · R2: liczba niezmieniona, zestawiona w specu z 215 chunkami Ewy jako kontrast, nie jako prognoza | poza=poza dowodem zostaje czas operatora na jeden cykl stop-wypełnij-wznów — proporcjonalne, bo nie steruje żadną bramką; pokryte pierwszym realnym przebiegiem właściciela | werdykt=PASS
- CME: typ=CONTRACTED | dowod=kontrakt-redaktora-KONTRAKT-md-v1 | C=spec §Problem i §Kontrakt escapingu twierdzą, że chunker jest parserem Markdowna, K-NAG porównuje nagłówki ATX i przerywa apply przy rozjeździe, kotwice są exact-match, wymagane jest NFC i wyłącznie ATX | M=ODPOWIEDZ A2/A4/A5 wyprowadzone przez Redaktora z ICH kodu; KONTRAKT.md v1 w dwóch miejscach odstaje od kodu, więc źródłem jest ODPOWIEDZ — dodatkowo w R2 potwierdzone, że KONTRAKT.md nie zmienił się między 4ebec8c a d7087bd | mierzalne-od=krok 4 planu wdrożenia — przepuszczenie wyeksportowanego rozdziału Ewy przez CLI Redaktora do etapu chunks.json i asercje G1-G4 | poza=poza kontraktem zostaje zachowanie strażników przy suwakach innych niż testowe oraz pełny K-NAG, który uruchamia się dopiero przy apply — proporcjonalne, bo eksport jest read-only i najgorszy skutek to zły plik .md kasowany ponownym eksportem; pokryte ręcznym przebiegiem apply właściciela, jawnie wyłączonym z tej fazy | werdykt=PASS

**Czego ten preflight NIE dowodzi.** Nie dowodzi, że wyeksportowany `.md` przejdzie przez
`segmentuj()` — druga strona nie była uruchamiana na NASZYM wyjściu ani razu (zwiad Ewy szedł
na pliku z Google Docs, nie z TIOLIBRI). Zostaje i jest proporcjonalne: krok 4 planu ma na to
cztery asercje z zerową tolerancją, a kontrakt jest fail-closed po ich stronie. Nie dowodzi też,
że nasze `processed_html` niosą `data:` URI — spec traktuje to jako możliwe, nie pewne, i ma na
to jednozdaniowe zapytanie SQL na krok 1.
