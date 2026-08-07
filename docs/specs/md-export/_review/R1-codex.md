# R1 — review speca MD-EXPORT

**Spec:** `docs/specs/md-export/SPEC-MD-EXPORT.md` v0.2  
**Zakres:** review przed implementacją, light, Risk STANDARD  
**Data:** 2026-08-07

## Werdykt

**Werdykt:** REQUEST_CHANGES

Sprawdziłem **11/11 kategorii** checklisty. Jedyna kategoria N/A: **SQL/RLS/migracja** — zakres
nie zapisuje do bazy ani nie zmienia polityk; `log_activity` jest istniejącym zapisem audytowym,
nie migracją ani zmianą modelu danych. Znalazłem niżej wszystkie warstwy problemów w jednym
przejściu. To nie jest zakres NITS/NITS-EXT: poprawki wymagają decyzji właściciela, zmiany
kontraktów endpointu i serializatora oraz ponownego sizingu.

## Co wymaga zmiany

### 1. BLOCKER — `Sizing: PASS` liczy nie ten zbiór i przekracza limit

Spec deklaruje 5 plików i ~495 LOC **produkcyjnych**, po czym osobno dodaje ~110 LOC testów
(`SPEC:8-14`). Master §4.5 liczy wszystkie zmienione/utworzone pliki i wszystkie dodane/zmienione
linie kodu, nie tylko produkcję. Sam plan wymaga co najmniej jednego pliku testowego, więc to co
najmniej 6 plików, a estymata wynosi około **605 LOC**, nie 495. To przekracza limit 500 przed
implementacją. Brakuje też wymaganych osi: konkretnej listy plików z LOC, domen, migracji i decyzji
architektonicznych. Liczba testów nie jest tu argumentem — problemem są LOC i pliki testów.

Linia cięcia „gdy urośnie, odciąć UI” nie naprawia bramki: wzrost już jest widoczny w obecnej
arytmetyce, a odłożenie całego widoku do nowej fazy/speca jest decyzją cross-fazową z denylisty,
nie awaryjną decyzją implementatora. Dodatkowo §Bramki nadal mówi ~80 min (`:27`), nagłówek mówi
~90 min, a krok 4 wymaga zewnętrznego przebiegu Redaktora z około 30 ręcznymi iteracjami W2 — nie
jest wiarygodne, że cały zakres mieści się w 90 minutach.

### 2. BLOCKER — globalna unikalność basename'ów nie jest zapewniona

Prefiks ze sluga **tytułu** książki (`:84-90`, `:224-228`) rozwiązuje kolizję dwóch różnych
tytułów, ale nie dwóch projektów o tym samym tytule. Dwa projekty „Osteoporoza” nadal wygenerują
`osteoporoza-01-wstep.md` i zatrują ten sam katalog/skrzynkę Redaktora. Sufiksy `-2`, `-3` z
`:221-222` są wyliczane tylko w jednym ZIP-ie, więc również nie zapewniają wymaganej przez
ODPOWIEDZ B2 globalnej unikalności między eksportami. Spec musi dostać stabilny, globalnie
unikalny klucz książki albo jawny kontrakt rejestracji unikalnego sluga; wybór należy do właściciela.

### 3. BLOCKER — T3 przechodzi, ale nie testuje języka rzeczywistego chunkera

Escaping (`:121-123`) neutralizuje tylko `#`, `-`, `+`, `*`, `>` i `cyfra.`. Produkcyjny
`segmentuj.ts:12-16,58-129` rozpoznaje ponadto:

- fenced code zaczynający się od co najmniej trzech backticków lub tyld;
- listę numerowaną `cyfra)`;
- tabelę jako linię z `|` oraz następną linię separatora.

Uruchomiona kontrpróba na kodzie Redaktora (`node --experimental-strip-types ...`, `EXIT=0`)
potwierdziła: trzy backticki przed `tekst` i `~~~tekst` → `kod`, `1) tekst` → `lista`, a
`| a | b |\n|---|---|` → `tabela`. T3 preflightu (`PASS=7 FAIL=0`) testuje własny regex,
nie pełny kontrakt konsumenta, więc jego rekord C/M/E nie może mieć PASS jako dowód poprawności
escapingu. Trzeba wyprowadzić regułę i fixture bezpośrednio z `segmentuj.ts`, w tym warianty
0–3 spacji na początku linii.

### 4. BLOCKER — algorytm HTML→MD nadal nie jest implementowalny bez zgadywania

Tabela nie rozstrzyga co najmniej tych interakcji:

- kolejności i reprezentacji zagnieżdżonych list oraz kontynuacji `<li>`;
- zachowania spacji między sąsiednimi inline nodes i tekstem przed/po `<strong>/<em>`;
- literalnych znaków Markdown w zwykłym tekście oraz w `alt` (`]`, `\`, newline) i URL-u (`)`,
  spacje); „alt bez zmian” (`:161`) może zamknąć składnię obrazu i stworzyć nową strukturę;
- kolejności „whitespace do jednej spacji” względem `<br> → \n`; literalne brzmienie `:124`
  kasuje newline, który `:109` każe zachować;
- pustych/wyłącznie-whitespace bloków oraz tekstu top-level poza `<p>`;
- atomowej konsumpcji obrazka względem jego ewentualnych tagów-rodziców.

To nie są kosmetyczne edge case'y. Wynik jest wejściem obcego parsera, a co najmniej część luk
zmienia typ chunka albo treść exact-match. Plan testów (`:248-253`) pomija `<br>`, nesting,
fences/tabele/`1)`, składnię obrazu, whitespace inline oraz puste/nullish wejścia.

### 5. BLOCKER — kontrakt obrazów/base64 i limitów jest niepełny

„`src` zaczynające się od `data:` → zdekoduj base64” nie mówi, co zrobić z malformed base64,
URI bez `;base64`, parametrami MIME, pustym payloadem ani z deklarowanym MIME niezgodnym z danymi.
Nie wiadomo też, czy limit 10 MB jest sprawdzany na bajtach zdekodowanych czy tekście base64,
a limit „80 MB na cały ZIP” nie określa rozmiaru skompresowanego czy sumy wpisów przed kompresją.
Przy buforowaniu ZIP-a w pamięci różnica ma znaczenie dla ochrony zasobów. `image/svg+xml` i inne
aktywne formaty również wymagają jawnej decyzji: wspierany bezpieczny typ czy `.bin`.

Sygnatura `chapter_to_markdown(html, title) -> (md, meta)` nie ma kanału na bajty obrazów, choć
`extract_images()` ma je przekazać builderowi ZIP-a. Spec musi podać typ wyniku i własność limitu,
żeby endpoint nie implementował tego ad hoc.

### 6. BLOCKER — endpoint gubi legalny stan rozdziału i ma niebezpieczną semantykę pustej listy

Kod aplikacji jawnie wspiera rozdział bez `processed_html`: `useChapters.js:177-212` pobiera wtedy
`source_file_path`, ściąga oryginalny HTML i ewentualnie uruchamia `convertGoogleDocsHtml`.
Endpoint opisany w `:212-215` czyta tylko `processed_html`, więc taki rozdział zostanie pusty,
pominięty albo wysadzi konwerter — spec nie rozstrzyga którego. Teza `:49`, że cała treść żyje w
`processed_html`, jest zbyt szeroka wobec wykonywanego kodu.

Ponadto `[] = wszystkie` powoduje klasyczny błąd UI: użytkownik odznaczy wszystkie checkboxy,
frontend wyśle pustą listę, a backend wyeksportuje **całą książkę**. Brakuje modelu body i rozróżnienia
„body/lista niepodana” od „jawnie wybrano zero”, walidacji UUID-ów, zachowania dla ID spoza projektu,
stabilnego tie-breakera przy równym `sort_order` oraz odpowiedzi dla projektu/wyboru bez rozdziałów.

### 7. BLOCKER — filtr „zmienione” nie ma przepływu danych

Frontend dostaje wyłącznie `Blob` (`:242-243`). Spec każe po sukcesie zapisać hashe z manifestu
do `localStorage`, ale nie mówi, skąd JS ma je wziąć: `authedFetch(... responseType: 'blob')` nie
udostępnia nagłówków, a frontend nie ma biblioteki/kontraktu rozpakowania ZIP-a. Nie wiadomo też,
z czym porównać zapisany hash przed kolejnym eksportem: frontend nie wykonuje kanonicznego
HTML→MD, a hash źródłowego HTML nie jest hashem NFC `.md`. D2 wybiera miejsce przechowania,
ale nie definiuje przepływu ani klucza namespacingu (projekt/użytkownik/wersja formatu).

To wymaga decyzji kontraktowej (np. osobny preview/metadata response, nagłówek, albo świadome
usunięcie filtra z tej fazy), a więc nie wolno pozostawić wyboru implementatorowi.

### 8. BLOCKER — krok weryfikacyjny odwołuje się do bramki, która nie działa na etapie `chunks.json`

Plan `:257-265` mówi „przepuścić do etapu `chunks.json`” i sprawdzić, że K-NAG nie protestuje.
Z ODPOWIEDZ A4 wynika jednak, że K-NAG działa podczas `apply`, po edycjach, nie przy utworzeniu
`chunks.json`. Żeby naprawdę sprawdzić K-NAG, trzeba wykonać dalszą część przepływu (przy
`provider: plik` około 30 cykli W2 + apply) albo zdefiniować osobną uruchamialną bramkę. Obecne
kryterium jest niewykonalne w opisanym punkcie. „Liczba chunków odpowiada z grubsza liczbie
akapitów” również nie ma tolerancji ani definicji mianownika (nagłówki, listy, obrazy i separatory
też tworzą bloki), więc nie jest kryterium akceptacji.

### 9. MAJOR — Risk STANDARD ma nieprawdziwe uzasadnienie

K-NAG jest fail-closed tylko dla struktury nagłówków. Nie ochroni przed utratą treści, błędnym
unwrap/decompose, stworzeniem `kod`/`lista`/`tabela`, uszkodzeniem obrazka ani przed rozjechaniem
chunków. Argument `:40-42` przedstawia go jak backstop całego serializatora. Dodatkowo plik nie
jest tylko „złym plikiem na dysku”: trafia do W1/W2 i może wygenerować płatną/ręczną pracę oraz
decyzje na błędnych chunkach. Ocena może ostatecznie pozostać STANDARD ze względu na read-only,
ale dopiero po uczciwym opisaniu ograniczonego zakresu K-NAG i po domknięciu testu kontraktowego;
obecne uzasadnienie nie broni klasyfikacji.

### 10. MAJOR — dwie decyzje produktowe pozostawiono właścicielowi dopiero w review

D1 (ASCII jako globalny klucz) i D2 (funkcja „tylko zmienione” oraz jej trwałość) są decyzjami
produktowo-kontraktowymi, a nie pytaniami do recenzenta. D3 nie jest decyzją: ODPOWIEDZ wymaga
normalizacji spacji, więc należy przenieść je do ograniczeń/import backlogu. O1 także nie powinno
pozostać otwarte: produkcyjny `segmentuj.ts` jest dostępny i trzeba rozstrzygnąć zachowanie przed
GREEN. Zgodnie z guardrailem 4.4b Codex nie może wybrać D1/D2 za właściciela.

### 11. MAJOR — C/M/E i proza rozciągają lub mylą zakres dowodów

- Pomiar E4 jest poprawnie zawężony do jednego pliku z Google Docs, ale zdanie „koszt
  zabezpieczenia zerowy” (`:141`) przeczy własnemu sizingowi: E4 podniosło estymatę z ~420 do
  ~490/~495 LOC i z ~80 do ~90 min. To nie jest wynik pomiaru i jest fałszywe.
- Rekord T1–T4 mówi o PASS escapingu, ale E obejmuje tylko 7 przypadków własnego regexu; nie
  obejmuje języka chunkera wykazanego w findingu 3. `M` opisujące cztery grupy testów nie czyni
  `E` kompletnym.
- „27 chunków → blisko 30 wywołań” jest wyłącznie skalą jednego rozdziału Bożeny, nie prognozą
  dla Ewy. Spec nazywa to „skalą oczekiwaną”; trzeba zostawić literalnie obserwację Bożeny i
  wskazać, że dla Ewy brak oczekiwanego przedziału.
- Preflight twierdzi, że „dry-run każdego parsera/reguły” wykonano, po czym sam wyłącza większość
  tabeli. Poprawne C brzmi: uruchomiono cztery wąskie sondy T1–T4, nie wszystkie reguły konwersji.

Brak `CME-MANIFEST.md` zgodnie z podaną regułą 1 nie jest osobnym blokerem. Blokerem są
nieprawdziwe relacje C⊆E w istniejących rekordach, nie brak pliku manifestu.

### 12. MAJOR — UI nie ma minimalnego kontraktu a11y i stanów błędu

Modal nie definiuje: focus trap i focus return do przycisku, zamknięcia Escape, nazwy dostępnej,
powiązania label–checkbox, obsługi klawiatury listy, stanu loading/error, blokady podwójnego submitu,
komunikatu 413 ani zachowania przy zerowym wyborze. Nie trzeba projektować nowego widoku, ale
istniejący modal musi mieć egzekwowalny minimalny kontrakt dostępności i stanów. Spec powinien też
wskazać istniejące komponenty/tokeny modala albo jawnie powiedzieć, że takiego wzorca nie ma;
inaczej implementator zgaduje stylistykę Tailwind 4.

### 13. MAJOR — stale/nieprecyzyjne odwołania i sprzeczności prozy

- `:215` cytuje „ODPOWIEDZ/HANDOFF, ekran eksportu” bez rozwiązywalnej sekcji/ścieżki; kanon
  ODPOWIEDZ nie ustanawia tego ekranu. Należy podać dokładne źródło albo nazwać decyzję lokalną.
- `Divider.js:10-22` jest wystarczające dla atrybutu, ale zapis „`renderHTML` :80-92” miesza
  metodę atrybutu z renderem całego node'a; warto cytować dokładnie `:12-19` i `:80-92` zgodnie
  z tym, czego każde miejsce dowodzi.
- `:32` mówi „Asercja `--light` potwierdzona”, ale nie wskazuje wykonanej komendy/dowodu.
- Manifest mówi, że `dividers`/`images` są dla przyszłego importu, choć import jest poza scope;
  to jest dopuszczalne tylko jako kontrakt eksportu, lecz format nie podaje schematu dla braku
  HTML, błędnego obrazu ani wersjonowania przyszłych zmian.

## Exhaustiveness checklist

- [✓ sprawdzone] **Budżet rozmiaru:** FAIL — co najmniej ~605 LOC i ≥6 plików; brak pełnych osi.
- [✓ sprawdzone] **Spójność z ODPOWIEDZ + stale refs:** FAIL — globalna unikalność nieosiągnięta,
  krok K-NAG sprzeczny z etapem, jedno martwe/nieprecyzyjne źródło.
- [✓ sprawdzone] **Egzekwowalność:** FAIL — przepływ hashy, fallback treści, request body i kilka
  decyzji konwertera wymagają zgadywania.
- [✓ sprawdzone] **Logika + edge/nullish:** FAIL — escaping, base64, listy/inline whitespace,
  pusty wybór, brak `processed_html`, deterministyczne sortowanie i limity ZIP-a.
- [✓ sprawdzone] **Typy/sygnatury/argi/ścieżki:** częściowy PASS dla istniejących kotwic;
  FAIL dla wyniku `chapter_to_markdown`/obrazów i modelu body. Sprawdzone wskazane pliki obu
  podprojektów.
- [✓ sprawdzone] **Bramki maszynowe uruchomione:** T1 `EXIT=0`, T2 `EXIT=0`, T3 `EXIT=0`,
  T4 `EXIT=0`; dodatkowa kontrpróba produkcyjnego chunkera `EXIT=0` obala kompletność T3.
  Pierwsza próba przez `tsx` była niewykonalna w sandboxie (`EXIT=1`, IPC `EPERM`), więc
  powtórzono bez IPC przez Node 24 `--experimental-strip-types` i uzyskano wykonany dowód.
- [✓ sprawdzone] **Manifest pokrycia dowodu C/M/E:** FAIL merytoryczny mimo nieblokującego braku
  `CME-MANIFEST.md`; szczegóły w findingu 11.
- [N/A — spec jest odczytowy] **SQL/RLS/migracja:** brak migracji i zmian RLS; istniejący
  `log_activity` nie zmienia klasyfikacji. Zapytanie diagnostyczne `SELECT count(*)` jest read-only.
- [✓ sprawdzone] **UI/a11y/tokeny:** FAIL — brak kontraktu a11y, stanów błędu i wskazania wzorca/tokenów.
- [✓ sprawdzone] **Ryzyko/dane:** FAIL uzasadnienia STANDARD; read-only ogranicza szkodę, ale K-NAG
  nie chroni większości kontraktu serializatora.
- [✓ sprawdzone] **Docs/proza:** FAIL — niespójne 80/90 min, „koszt zerowy”, otwarte D1–D3/O1,
  niewykonalny krok weryfikacji i nieprecyzyjne źródła.

## Proactive suggestions (rzeczy o które nie pytano)

- **Workflow:** Preflight parsera powinien generować przypadki z regexów rzeczywistego konsumenta, bo self-test własnego regexu może być zielony przy niepełnym kontrakcie.
- **Risk flag:** Globalna unikalność oparta na tytule książki jest pozorna; identyfikator przestrzeni roboczej musi przeżyć dwa projekty o identycznym tytule.

---

## Dla Piotrka — jedno zdanie

R1 zatrzymał implementację: spec przekracza budżet i ma luki w nazwach, konwersji, endpointzie, hashach oraz weryfikacji z Redaktorem.

**Kopiuj dalej:**
```
/spec-apply-review md-export
```
