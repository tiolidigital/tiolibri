# R1 — preflight Opusa (L5) · md-export

**Spec:** `docs/specs/md-export/SPEC-MD-EXPORT.md` (wersja 0.2, light, Risk STANDARD)
**Runda generowana:** R1 (STATE `spec: draft` → N=1)
**Data:** 2026-08-07
**Środowisko dowodów:** repo TIOLIBRI @ `03e2f76`+ (docs-only commit `3e8a909`), venv `tiolibri-api/venv`, Python 3.9.6

Wszystkie fakty nośne poniżej sprawdzone w kodzie albo uruchomione. Dwie rzeczy okazały się
błędne i **zostały wpisane do speca**, nie zostawione Codexowi do rozstrzygnięcia.

---

## Fakty

- FACT: VERIFIED | kind=path-new | source=test -d tiolibri-api/app/services && test -f tiolibri-api/app/services/md_exporter.py | note=rodzic istnieje (PARENT_OK), plik docelowy jeszcze nie istnieje (NOT_EXISTS_OK)
- FACT: VERIFIED | kind=path-new | source=test -f tiolibri-frontend/src/features/editor/ExportMarkdownModal.jsx | note=rodzic istnieje, plik docelowy jeszcze nie istnieje (NOT_EXISTS_OK)
- FACT: VERIFIED | kind=path-existing | source=tiolibri-frontend/src/features/editor/EditorPage.jsx | note=plik istnieje, 10 trafień na Inspector/ProjectSnapshots — jest gdzie wpiąć przycisk
- FACT: VERIFIED | kind=path-existing | source=tiolibri-frontend/src/features/editor/activityLabels.js | note=plik istnieje, spec dokłada do niego etykietę project.export_md
- FACT: VERIFIED | kind=signature | source=tiolibri-api/app/routers/export_import.py:238 | note=def _assert_project_access(project_id: str, user_id: str) -> None — sygnatura zgodna z wywołaniem w specu, wzorzec użycia na :39
- FACT: VERIFIED | kind=anchor | source=tiolibri-api/app/routers/export_import.py:113-122 | note=StreamingResponse + Content-Disposition z filename*=UTF-8'' na :119 — spec cytuje 114-122, kotwica mieści się w zakresie
- FACT: VERIFIED | kind=export | source=tiolibri-api/app/services/activity.py:5 | note=log_activity(project_id, user_id, action_type, target_id=None, details=None) -> None, wyjątki połykane — zgodne z użyciem w specu
- FACT: VERIFIED | kind=export | source=tiolibri-frontend/src/lib/authedFetch.js:13,33 | note=opcja responseType z obsługą 'blob' istnieje realnie (wcześniejszy odczyt przez rg był zniekształcony przez podstawianie argumentów slasha — potwierdzone lekturą pliku)
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/projects/ProjectCard.jsx:194-215 | note=handleExport z responseType 'blob' + createObjectURL + a.download + revokeObjectURL — wzorzec do skopiowania zgadza się co do linii
- FACT: VERIFIED | kind=anchor | source=tiolibri-frontend/src/features/editor/ChapterEditor.jsx:62 | note=allowBase64: false — spec cytuje 60-62, kotwica w zakresie; potwierdza ryzyko utraty obrazów base64 przy zapisie w edytorze
- FACT: VERIFIED | kind=anchor | source=grep -c img tiolibri-frontend/src/lib/htmlConverter.js | note=0 trafień — konwerter z Google Docs faktycznie nie dotyka <img>, więc data: URI mogą przetrwać do processed_html
- FACT: VERIFIED | kind=arg | source=tiolibri-api/requirements.txt:4,31 | note=beautifulsoup4==4.14.3 i lxml==6.0.2 są w zależnościach — spec nie dokłada nowej biblioteki
- FACT: VERIFIED | kind=arg | source=tiolibri-api/app/routers/export_import.py:52-55 | note=kolumny chapters (id, title, sort_order, processed_html, status) + .is_("deleted_at","null") + .order("sort_order") — dokładnie zapytanie, które spec zakłada dla export-md
- FACT: VERIFIED | kind=execution | source=python3 -c "from bs4 import BeautifulSoup; import lxml" w tiolibri-api/venv | note=import przeszedł, bs4 4.14.3 + lxml 6.0.2 zgodne z requirements, EXIT=0
- FACT: VERIFIED | kind=execution | source=unicodedata.normalize('NFKD', ch) dla "łąćęńóśźż" | note=ł (0x142) NIE rozkłada się pod NFKD, pozostałe 8 diakrytyków rozkłada się na 2 punkty — osobna mapa dla ł w slugify jest konieczna, nie ozdobna, EXIT=0
- FACT: VERIFIED | kind=execution | source=BeautifulSoup('<p>a&nbsp;b</p>','lxml').find('p').get_text() | note=zwraca 'a\xa0b' — U+00A0 przeżywa parsowanie, więc jawna podmiana na spację jest wymagana, EXIT=0
- FACT: VERIFIED | kind=execution | source=hashlib.sha256(unicodedata.normalize('NFC',s).encode()).hexdigest() z prefiksem | note=format "sha256:<64 hex>" ma długość 71 znaków, zgodny z chunks.json.hash_input Redaktora, EXIT=0
- FACT: VERIFIED | kind=parser | source=re.compile(r'^(\s*)([#\-+*>]|\d+\.)') na 7 przypadkach | note=dry-run escapingu początku linii PASS=7 FAIL=0, w tym odrzucenie myślnika w środku linii — pełny wynik w sekcji Parser self-test
- FACT: VERIFIED | kind=state-machine | source=docs/specs/md-export/STATE.md:1 | note=spec: draft → N=1, TARGET=1, nazwa preflightu R1-opus-preflight.md zgodna z TARGET
- FACT: CORRECTED | kind=export | source=tiolibri-frontend/src/features/editor/extensions/Divider.js:12-19,80-92 | note=stare=styl separatora czytany z węzła div[data-divider] bez wskazania atrybutu nowe=data-divider-style
- FACT: CORRECTED | kind=parser | source=BeautifulSoup(...).find('div', attrs={'data-divider': True}).get_text() zwrócił 'x' z wnętrza SVG | note=stare=tagi nieznane unwrap bez wyjątku nowe=decompose()
- FACT: CORRECTED | kind=sizing | source=docs/specs/md-export/SPEC-MD-EXPORT.md:8-14 | note=stare=~490 LOC produkcyjnych nowe=~495
- FACT: VERIFIED | kind=sizing | source=docs/specs/md-export/SPEC-MD-EXPORT.md:8-14 | note=marker "Sizing: PASS" obecny, wartości ~495 LOC / ~90 min / 5 plików mieszczą się w zadeklarowanym limicie 500 LOC / 90 min / 5 plików — margines jednocyfrowy, linia cięcia (krok 3 UI do osobnej fazy) zapisana w specu

### Co poszło do speca z korekt

1. **`data-divider-style`** — spec mówił „styl (`stars`/`line`/`dots`) ląduje w manifeście", nie
   nazywając atrybutu. `Divider.js` renderuje `<div data-divider="" data-divider-style="stars"
   style="text-align: center; …">`, więc naiwne sięgnięcie po `style` dałoby CSS zamiast stylu
   separatora. Tabela konwersji nazywa teraz atrybut wprost i ostrzega przed `style`.
2. **`<svg>` przez `decompose()`, nie unwrap** — reguła „tagi nieznane → unwrap, bez wyjątku"
   w zderzeniu z separatorem wpuszczała tekst z wnętrza SVG do prozy (zmierzone: `get_text()`
   na węźle separatora zwraca zawartość SVG). To byłby chunk `akapit` lecący do W2 jako proza.
   Tabela ma teraz osobny wiersz `<svg>`/`<script>`/`<style>` → usunięcie z treścią, a wiersz
   unwrapu ma jawny wyjątek na węzły skonsumowane atomowo.
3. **Sizing** — dwie powyższe kosztują ~5 LOC, więc estymata poszła 490 → ~495 przy limicie 500.

---

## Parser self-test

Dry-run każdego parsera/reguły, którą spec deklaruje jako egzekwowalną. Wykonane w
`tiolibri-api/venv`, jednym skryptem, `EXIT=0`.

**T1 — dekompozycja NFKD (§Slug).** Teza speca: `ł` nie rozkłada się pod NFKD, więc potrzebuje
osobnej mapy. Wynik:

```
ł → [0x142]              len=1  decomposed=False   ← teza potwierdzona
ą → [0x61, 0x328]        len=2  decomposed=True
ć ę ń ó ś ź ż            len=2  decomposed=True (8/9 znaków)
```

**T2 — bs4 + lxml na realnym fragmencie.** PASS: atrybut separatora odczytany poprawnie.
FAIL wykryty: `get_text()` przepuszcza treść SVG.

```
bs4 4.14.3 · lxml 6.0.2                                          OK
div[data-divider].get('data-divider-style')  → 'dots'            PASS (atrybut istnieje i jest czytelny)
div[data-divider].get_text()                 → 'x'               FAIL (tekst z <svg> wycieka → korekta 2)
p.get_text() na 'a&nbsp;b'                   → 'a\xa0b'          PASS (U+00A0 przeżywa → jawna podmiana wymagana)
```

**T3 — escaping początku linii (§Kontrakt konwersji).** Regex `^(\s*)([#\-+*>]|\d+\.)`,
komplet przypadków PASS i FAIL, z licznikiem:

```
PASS-oczekiwane (ma złapać):   '# nie naglowek' ✓   '- myslnik' ✓   '1. lista' ✓   '> cytat' ✓   '2026. rok byl' ✓
FAIL-oczekiwane (ma odrzucić): 'zwykly tekst' ✓     'srodek - myslnik' ✓
counter: PASS=7 FAIL=0
```

Gate faktycznie **odrzuca** zły wkład (`srodek - myslnik` nie jest escape'owany), nie tylko
istnieje. Efekt uboczny do świadomej akceptacji: `2026. rok byl` zostanie zaescape'owany —
poprawnie, bo bez tego CommonMark zrobiłby z tego listę numerowaną.

**T4 — hash (§manifest.json).** `sha256:` + 64 hex = 71 znaków, liczone po NFC. Format zgadza
się z `chunks.json.hash_input` Redaktora, więc `md-import` porówna je wprost.

**Czego self-test NIE pokrywa:** reguł konwersji, które nie mają dziś parsera do odpalenia
(mapowanie `<h1>`–`<h6>` na ATX, listy, blockquote, `<br>`) — te są kontraktem opisowym,
mierzalnym dopiero od testów jednostkowych z kroku 1 planu wdrożenia. Proporcjonalne: to
proste mapowania 1:1 bez gałęzi, a krok 4 planu (przepuszczenie żywego rozdziału przez
Redaktora do `chunks.json`) jest dla nich testem kontraktu.

---

## Audyt C/M/E

Kanon `docs/specs/spec-workflow/CME-MANIFEST.md` **nie istnieje** ani w TIOLIBRI, ani
w FABRYCE (sprawdzone: `find … -name CME-MANIFEST.md` → 0 trafień). Zgodnie z regułą 1
audyt nie jest w tym repo blokerem — sekcja jest wypełniona mimo to, bo bramka strukturalna
obowiązuje, a spec cytuje cudze pomiary.

- CME: typ=MEASURED | dowod=pomiar-E4-rozdzial-ewy-z-google-docs | C=spec §_media/ twierdzi, że plik miał 118 843 B, z czego 83 127 B (69,9%) to jeden data:image w jednej linii o 83 138 znakach, i że przez to mianownik strażnika budżetu rozjeżdża pomiar ~3x | M=ODPOWIEDZ-most-tiolibri-redaktor.md ERRATA E4 (jeden pomiar, jeden plik, strona Redaktora) | E=R0/kanon: pomiar wykonany na JEDNYM pliku pochodzącym prosto z Google Docs, nie z eksportu TIOLIBRI; zmierzone bajty i procent, NIE zmierzono zachowania strażnika na pliku z TIOLIBRI | poza=poza dowodem zostaje pytanie, czy processed_html w naszej bazie w ogóle niosą data: URI — proporcjonalne, bo wymóg przyjmujemy w całości niezależnie od odpowiedzi (koszt zabezpieczenia zerowy, tryb awarii cichy), a samo pytanie jest pokryte zapytaniem SQL zapisanym w specu §_media/ do wykonania w kroku 1 implementacji | werdykt=PASS
- CME: typ=MEASURED | dowod=przebieg-redaktora-na-rozdziale-bozeny | C=spec §Plan wdrożenia krok 4 twierdzi, że rozdział dał 27 chunków, czyli blisko trzydzieści wywołań W2 przy provider: plik | M=ODPOWIEDZ-most-tiolibri-redaktor.md ERRATA E1 (sprostowanie wcześniejszego "14 wywołań") | E=R0: 27 chunków policzone z przebiegu · E1: skrzynka tego rozdziału zawiera 59 kluczy z TRZECH przebiegów, więc liczba wywołań na przebieg jest wyprowadzona z liczby chunków edytowalnych, nie odczytana wprost z jednego przebiegu | poza=poza dowodem zostaje skala dla rozdziału Ewy, który jest gęstszy od liczb i może dać inną liczbę chunków — proporcjonalne, bo liczba służy tylko do ostrzeżenia operatora przed pętlą po katalogu, a nie do żadnej bramki; pokryte krokiem 4 planu, który mierzy to na rozdziale Ewy | werdykt=PASS
- CME: typ=MEASURED | dowod=preflight-R1-dryrun-python-T1-T4 | C=preflight twierdzi, że ł nie rozkłada się pod NFKD, że nbsp przeżywa get_text(), że regex escapingu odrzuca myślnik w środku linii i że get_text() na separatorze wypuszcza tekst z SVG | M=sekcja Parser self-test tego pliku, cztery testy T1-T4 | E=R1: wykonane w venv na Pythonie 3.9.6, EXIT=0 — T1 na 9 znakach, T2 na jednym fragmencie HTML z separatorem i nbsp, T3 na 7 przypadkach (PASS=7 FAIL=0), T4 na jednym stringu | poza=poza dowodem zostaje cała reszta tabeli konwersji (nagłówki, listy, blockquote, br) — proporcjonalne, bo to mapowania 1:1 bez gałęzi, a nie logika warunkowa; pokryte testami jednostkowymi z kroku 1 planu wdrożenia i testem kontraktu z kroku 4 | werdykt=PASS
- CME: typ=CONTRACTED | dowod=kontrakt-redaktora-KONTRAKT-md-v1 | C=spec §Problem i §Kontrakt konwersji twierdzą, że chunker jest parserem Markdowna, K-NAG porównuje nagłówki ATX i przerywa apply przy rozjeździe, kotwice są exact-match, wymagane jest NFC i wyłącznie ATX | M=ODPOWIEDZ-most-tiolibri-redaktor.md A2/A4/A5, wyprowadzone przez Redaktora z ICH kodu (segmentuj.ts, strażniki) — KONTRAKT.md v1 w dwóch miejscach odstaje od kodu, więc źródłem jest ODPOWIEDZ, nie KONTRAKT | mierzalne-od=krok 4 planu wdrożenia — przepuszczenie wyeksportowanego rozdziału Ewy przez CLI Redaktora do etapu chunks.json i sprawdzenie trzech rzeczy: K-NAG milczy, żaden chunk nie jest metadanymi, liczba chunków odpowiada liczbie akapitów | poza=poza kontraktem zostaje zachowanie strażników na naszym materiale przy suwakach innych niż testowe — proporcjonalne, bo eksport jest read-only i najgorszy skutek błędu to zły plik .md kasowany ponownym eksportem; pokryte rozdziałem kalibracyjnym z ODPOWIEDZ P4, który jest osobnym zadaniem treściowym, nie tym specem | werdykt=PASS

**Czego ten preflight NIE dowodzi.** Nie dowodzi, że wyeksportowany `.md` przejdzie przez
chunker Redaktora — druga strona nie była uruchamiana z tego repo ani razu. To zostaje
i jest proporcjonalne: kontrakt jest fail-closed po ICH stronie (K-NAG przerywa apply przed
powstaniem `output.md`), a spec ma na to jawny krok 4 planu wdrożenia z trzema mierzalnymi
kryteriami. Nie dowodzi też, że nasze `processed_html` niosą `data:` URI — spec świadomie
traktuje to jako możliwe, nie pewne, i zostawia jednozdaniowe zapytanie SQL na krok 1.
