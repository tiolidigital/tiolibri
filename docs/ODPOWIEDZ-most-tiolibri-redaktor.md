# ODPOWIEDŹ na BRIEF — most TIOLIBRI ↔ Redaktor

**Od:** FABRYKA-redaktor (branch `redaktor`, HEAD `4ebec8c`)
**Do:** TIOLIBRI
**Data:** 2026-08-07
**Dotyczy:** `BRIEF-most-tiolibri-redaktor.md` z 2026-08-07

Brief przeczytany w całości, wszystkie dziewięć założeń §2 sprawdzone na kodzie (nie na
KONTRAKCIE — kontrakt w dwóch miejscach odstaje od kodu, o tym niżej). Cztery pytania §5
mają odpowiedzi. **Jedna rzecz w §4.2 jest błędna i zawaliłaby wam weryfikację** — to
najważniejszy akapit tego dokumentu, jest w §C.

---

## ERRATA — dopiski nadawcy po wysłaniu

> Poniższe przysłał FABRYKA-redaktor **2026-08-07**, po wysłaniu dokumentu.
> Wpisane przez TIOLIBRI, treść nadawcy. Reszta dokumentu bez zmian — tabela §2,
> korekta §C i P2/P3/P4 czytać jak stoją.

**[E1] Sprostowanie liczby w P1.** „27 chunków / 14 wywołań W2" było **błędne**: 14 to liczba
EDYCJI, które z przebiegu wyszły, nie wywołań modelu. Wywołań W2 jest tyle, ile chunków
edytowalnych — czyli **blisko TRZYDZIEŚCI na jeden rozdział** (skrzynka tego rozdziału ma
59 kluczy z trzech przebiegów). Wniosek P1 się nie zmienia, tylko **robi się mocniejszy**:
pętla po katalogu nie da automatyzacji przed ich `PHASE-18`. Poprawione w miejscu, w §D/P1.

**[E2] Kolejność prac: EKSPORT (§4.1) PRZED IMPORTEM (§4.2)** — potwierdzenie i wzmocnienie
§F. Eksport odblokowuje realną pracę; bez niego rozdziały trzeba wyciągać ręcznie przez
Google Docs. Import tylko domyka pętlę i może poczekać: dopóki go nie ma, wartość i tak jest
dostarczona, bo `raport.html` mówi, co Redaktor znalazł, a wgranie z powrotem da się zrobić
później. Drugi powód: §4.2 wymaga poprawek z §C (`chunks.json` w liście artefaktów +
precedencja decyzji zamiast „listy przyjętych z `decyzje.json`"), więc niech ten kawałek
dojrzeje, zamiast być budowany dwa razy.

**[E3] Pierwszy rozdział na próbę: Ewa, nie Bożena.** Jeśli eksport ma wypuścić jeden rozdział
próbnie — ma to być rozdział ebooka Ewy o osteoporozie, **najgęstszy od liczb i dawek, nie
najłatwiejszy**. Spójne z P4 i z dziurami K-LIC opisanymi tamże.

**[E4] Eksport MUSI wycinać obrazy inline — warunek, żeby przebiegi cokolwiek mierzyły.**
Pomiar na pierwszym rozdziale Ewy, który do nich trafił: **118 843 B, z czego 83 127 B
(69,9%) to jeden obraz jako `data:image` w base64, w jednej linii o 83 138 znakach.**
Dwa skutki po ich stronie:
1. taka linia staje się chunkiem typu `akapit`, czyli **EDYTOWALNYM** — leci do modelu
   jako proza;
2. **mianownikiem strażnika budżetu zmian jest długość całego pliku**, więc przy 70%
   balastu procent zmian wychodzi zaniżony **~3×** i bramka budżetu świeci zielono,
   nie mierząc niczego.

Proszą o **obrazy jako referencje do plików, nie inline**. Dotyczy §4.1 (eksport).

> **Uściślenie pochodzenia próbki (TIOLIBRI, 2026-08-07).** Zmierzony plik został
> wyeksportowany **prosto z Google Docs, nie z TIOLIBRI** — więc pomiar 69,9% dowodzi, jak
> wygląda materiał źródłowy, a **nie** jak wygląda nasz eksport. Wymóg E4 przyjmujemy mimo to
> w całości: tryb awarii jest cichy (bramka budżetu świeci zielono nic nie mierząc), a koszt
> zabezpieczenia zerowy.
>
> Co wiadomo z kodu, bez dostępu do bazy w tym wątku (dwa mechanizmy ciągną w przeciwne strony):
> `htmlConverter.js` **nie dotyka `<img>`** — konwersja HTML-a z Google Docs zachowuje
> `data:` w całości; ale edytor ma `Image.configure({ allowBase64: false })`
> (`ChapterEditor.jsx:60-62`), więc TipTap **wyrzuca obrazy base64 przy wczytaniu** i pierwszy
> zapis rozdziału w edytorze utrwala treść już bez nich. Czy w `chapters.processed_html` siedzą
> dziś `data:` URI — **niesprawdzone**. Eksport ma być odporny w obie strony.
> Realizacja: SPEC-MD-EXPORT §`_media/`.

---

## A. Tabela założeń §2 — werdykt

| # | Werdykt | Komentarz |
|---|---------|-----------|
| **A1** | ✅ **potwierdzone** | Wejście = Markdown, `--input <dok.md>`, jeden dokument = jeden przebieg. Wyjście `output.md` w katalogu przebiegu. |
| **A2** | ✅ **potwierdzone** | `ChunkTyp` to enum ZAMKNIĘTY (`typy.ts:48`), chunker nie produkuje innych wartości. Brak typu dla frontmattera i dla linii poziomej — zgadza się. |
| **A3** | ✅ **potwierdzone empirycznie** | Przepuściłem plik z frontmatterem przez `segmentuj()`. Wynik: `---\ntitle: …\nid: …\n---` to **jeden chunk typu `akapit`** (nie `nietykalny`), czyli leci do W1 i do W2 jako proza. **Wasza decyzja o `_tiolibri/manifest.json` obok plików jest słuszna.** |
| **A4** | ✅ **potwierdzone** | `k-nag.ts` reużywa produkcyjnego `segmentuj()`, więc rozpoznaje wyłącznie ATX; setext jest poza kontraktem. Porównanie pozycyjne: liczba nagłówków → poziom → tekst. FAIL rzuca wyjątek **przed** fazą publikacji (`cli/apply.ts` krok 7), więc `output.md` w ogóle nie powstaje. Doprecyzowanie: klucz porównania jest **case-insensitive** i normalizuje białe znaki (wyjątek TIT), więc zmiana wielkości liter w nagłówku K-NAG przepuści. |
| **A5** | ✅ **potwierdzone**, z jednym doprecyzowaniem | NFC tak (`chunkuj.ts`, `apply.ts`). „Dokładnie raz" jest egzekwowane na **kwalifikacji** (K1); przy apply działa `indexOf` (pierwsze wystąpienie w chunku) — bo unikalność jest już rozstrzygnięta wcześniej. Dla was to ma znaczenie: patrz §C. |
| **A6** | ✅ **potwierdzone** | K-GLO → `odrzucona-auto` (edycja nie trafia do koszyków). K-LIC → `koszyk 3` + flaga `FAKT-STRAZNIK`, stan domyślny „nie wchodzi". |
| **A7** | ⚠️ **prawdziwe jako teza, niekompletne jako lista wejść** | Determinizm — tak, zero losowości w apply. Ale apply potrzebuje **pięciu** plików, nie trzech: `input.md`, `chunks.json`, `edits.json`, `run-meta.json`, `decyzje.json`. Bez `chunks.json` wyniku nie da się odtworzyć — patrz §C. |
| **A8** | ✅ **potwierdzone** | Grupa C = `null`. Wymuszone dwustronnie: parser configu rzuca błąd, jeśli `role.weryfikator` nie jest `null` (`config.ts`), a `Weryfikator` w etapie 1 nie ma producenta. |
| **A9** | ✅ **potwierdzone**, ale **czytacie „transport plikowy" o jeden poziom za wysoko** | KONTRAKT §0 pkt 6 mówi o transporcie **do modelu W2**, nie o wymianie plików między TIOLIBRI a Redaktorem. To rozróżnienie ma poważną konsekwencję operacyjną dla waszego §3 — patrz P1. |

### Czego w tabeli nie ma, a powinno

**B1. `***` też jest chunkiem typu `akapit`.** Sprawdzone empirycznie. Wasz §4.1 deklaruje
separatory graficzne jako `***` — one przejdą przez W1 i przez W2 jako proza. To nie jest
błąd (na `***` nie ma czego poprawiać), ale kosztuje jedno wywołanie W2 na separator, a przy
transporcie plikowym każde wywołanie W2 to jedna ręczna iteracja operatora. Przy książce
z separatorem co kilka stron to realny narzut. **Jeśli macie wybór, wolimy `---`** — ono
też ląduje w `akapit`, ale przynajmniej nie mnoży się w tekście tak jak `***`. Docelowo
to nasz dług: chunker powinien mieć `nietykalny` dla thematic break.

**B2. Nazwa pliku wyznacza katalog roboczy i musi być unikalna w całym Redaktorze.**
`katalogPrzebiegu` = `redaktor/praca/<basename bez .md>/<run-id>/`, a skrzynka W2 to
`redaktor/praca/<basename bez .md>/_skrzynka/`. Dwa rozdziały o nazwie `01-wstep.md`
z dwóch różnych książek **wpadną do tego samego katalogu i do tej samej skrzynki**. Wpływ
na wasz eksport: patrz §B.

**B3. KONTRAKT §5 (przykład `run-meta.json`) jest nieaktualny wobec kodu.** Pokazuje
`"kanarki": { "D": "PASS", "N": "PASS" }`, a kod emituje
`{ "D": { "id", "wynik", "mierzone_kody" }, "N": { "id", "wynik" } }`. Kod jest źródłem
prawdy. To samo dotyczy pól `pominiete_w2` i `liczniki.pominiete_sygnaly` — istnieją
w kodzie, nie ma ich w §5. Ma to bezpośredni wpływ na P3.

---

## B. §4.1 — układ katalogu, w który macie się rozpakowywać

Krótka odpowiedź: **`redaktor/praca/` to WYJŚCIE, nie wejście — nie rozpakowujcie się tam.**
Ten katalog tworzy CLI i tylko CLI.

Wejście jest wolne: `--input` to zwykła ścieżka względem korzenia repo Redaktora, kopiowana
potem jako `input.md`. Proponowana konwencja (zero zmian w kodzie po naszej stronie):

```
redaktor/wsad/<ksiazka>/
  01-wstep.md
  02-densytometria.md
  …
  _tiolibri/manifest.json
```

**Warunek wiążący (z B2): nazwy plików muszą być unikalne globalnie, nie w obrębie ZIP-a.**
Prefiksujcie nazwą książki, np. `osteoporoza-02-densytometria.md`. Inaczej dwie książki
podzielą katalog przebiegu i skrzynkę W2, a to jest ciche zatrucie, nie błąd — Redaktor się
nie poskarży. Polskie znaki i diakrytyki w nazwach są OK (mamy już taki katalog w produkcji).

`_tiolibri/` obok plików nam nie przeszkadza — CLI nie skanuje katalogu, bierze dokładnie
tę ścieżkę, którą dostanie.

---

## C. §4.2 — TU JEST BŁĄD. Weryfikacja w tej postaci nie zadziała

Wasz krok 2 brzmi: *„niezależnie zaaplikuje na `input.md` wyłącznie edycje o stanie
`przyjeta` z `decyzje.json`, biorąc cytaty i propozycje z `edits.json`"*.

**`decyzje.json` nie zawiera listy przyjętych edycji.** Zawiera wyłącznie ODSTĘPSTWA od
stanów domyślnych plus akcepty hurtowe (KONTRAKT §7.2, potwierdzone w `apply/apply.ts`).
Przy czystym przeglądzie plik decyzji może w ogóle nie istnieć, a apply i tak zastosuje
kilkanaście edycji. Idąc waszą procedurą dostalibyście `output.md` ≈ `input.md`
i **rozjazd na każdym rozdziale**.

Poprawna procedura rekonstrukcji — pięć reguł, wszystkie z kodu:

1. **Filtr statusu przed decyzjami.** Odrzućcie każdą edycję ze `status: "odrzucona-auto"`.
   Te nigdy nie wchodzą, niezależnie od decyzji.
2. **Precedencja stanu** (od najsilniejszej): wpis per-`id` w `decyzje.decyzje` → wpis
   hurtowy per `kod` w `decyzje.hurtowe` → **stan domyślny koszyka: 1 = przyjęta,
   2 = przyjęta, 3 = odrzucona**. Punkt trzeci jest tym, którego brakowało.
3. **Pomijalne edycje.** Edycja z `propozycja === null` to sygnał W1 (W2 miał dopisać tekst,
   nie dopisał) — jest **no-op**, nie błąd. Liczy się do `liczniki.pominiete_sygnaly`.
4. **Kotwiczenie WEWNĄTRZ chunka, nie w dokumencie.** `cytat` jest szukany przez `indexOf`
   w `chunk.tekst`, a nie w całym `input.md`. Fraza powtórzona w innym akapicie nie ma
   znaczenia. **Dlatego `chunks.json` jest wam niezbędny** — bez niego globalny
   search-and-replace trafi w złe wystąpienie i dostaniecie fałszywy alarm.
5. **Kolejność podmian w chunku:** malejąco po offsecie startu; remis rozstrzyga dłuższy
   cytat, potem `id` rosnąco (`apply/zastosuj.ts`). Przy rozłącznych cytatach kolejność nie
   zmienia wyniku, ale rozłączność jest sprawdzana, nie zakładana — kolizja to twardy błąd.

Do tego dwie rzeczy o montażu wyjścia:

- **Chunki-kanarki znikają.** `chunks.json` zawiera chunki syntetyczne (pole `kanarek`,
  `offset: -1`), których `input.md` nigdy nie zawierał. `edits.json` jest już od nich czysty,
  ale przy składaniu wyjścia **odfiltrujcie chunki z `kanarek !== undefined`**.
- **Wyjście jest składane z `input.md` po offsetach**, z zachowaniem luk między blokami
  (puste linie, białe znaki) — nie z konkatenacji chunków. Trzymajcie się `chunk.offset`
  i `chunk.tekst.length`.

Poza tym: wasz krok 1 (hash) — liczcie `sha256` na **NFC** tekstu i porównujcie
z `chunks.json.hash_input`, który ma format `"sha256:<hex>"` **z prefiksem**.

Jedno zdanie na koniec tej sekcji, bo warto: **ta weryfikacja jest dobrym pomysłem i chcemy
ją mieć.** U nas ten sam dowód zrobiliśmy rekonstrukcją (`_narzedzia-kalibracji/rekonstrukcja.mjs`)
i przeszedł bajt w bajt na obu przebiegach kalibracji. Wcześniejsza próba tego samego
skryptem-kontrolerem dała **siedem fałszywych alarmów** — więc idziecie właściwą drogą,
tylko lista wejść musi być pełna.

---

## D. Odpowiedzi na cztery pytania

### P1. Tryb wsadowy — `--input-dir` nie jest tym, co was odblokuje

**Rekomendacja: zróbcie pętlę u siebie, nie dotykajcie naszego CLI. Ale nie dlatego, że
nakładka jest zła — dlatego, że nie rusza wąskiego gardła.**

Wąskim gardłem nie jest liczba odpaleń per książka. Jest nim to, jak dziś działa transport
do W2. Przy `role.redaktor.provider: plik` (a to jest domyślny i darmowy tryb pracy):

- `run` idzie chunk po chunku, dla każdego zapisuje `_skrzynka/zapytania/<klucz>.md`
  i **od razu próbuje odczytać** `_skrzynka/odpowiedzi/<klucz>.json`;
- brak odpowiedzi = wyjątek `BrakOdpowiedzi`, który **przerywa cały przebieg**;
- operator (dziś: Claude Code w sesji) wypełnia odpowiedź, odpala `run` **od nowa** —
  zapytania już odpowiedziane są cache'owane po haszu promptu, więc przebieg dochodzi
  o jeden chunk dalej i znów staje.

Na rozdziale Bożeny to było **27 chunków**, czyli tyleż wywołań W2 (plus kanarki) —
**blisko trzydzieści** cykli stop-wypełnij-wznów **na jeden rozdział** `[E1 — liczba poprawiona
po wysłaniu, patrz ERRATA na górze; pierwotne „14 wywołań W2" to była liczba EDYCJI]`,
każdy zostawiający osobny katalog przebiegu
(`run_id` zawiera timestamp, więc nowy przy każdym odpaleniu). Pętla po katalogu nad takim
przebiegiem nie da wam automatyzacji — da wam kilkanaście razy więcej ręcznej roboty naraz.

Co to zmienia w waszym planie: **kwadrat „→ przebieg per rozdział" w diagramie §3 nie jest
dziś jedną komendą.** Reszta mostu (eksport, import, weryfikacja) jest niezależna od tego
i możecie ją budować od zaraz — po prostu nie planujcie „wypuszczam książkę na noc".

Mamy to zaadresowane po swojej stronie: automat wypełniający skrzynkę **istnieje** (zbudowany
dla przebiegów golden), ale jest zaszyty na golden set. Uogólnienie go na dowolny dokument
to zakres naszej `PHASE-18`. Damy znać, kiedy wejdzie — wtedy „jedna komenda na rozdział"
staje się prawdą i wasza pętla nagle zaczyna mieć sens bez zmian po waszej stronie.

Trzecia droga, gdybyście chcieli ruszyć wcześniej: `provider: anthropic` (klucz API) daje
jedną komendę na rozdział **dziś**, kosztem tokenów. Rzędy wielkości z naszych pomiarów:
pełny przebieg golden po API to 4,35 USD; rozdział jest tańszy, ale niezerowy. Decyzja
właściciela stoi na transporcie plikowym, więc traktujcie to jako opcję awaryjną, nie plan.

### P2. Ziarnistość słownika chronionego — rozdzielić, i **nie wkładać tam terminologii**

Pytacie, co słownik ma chronić: idiolekt czy terminologię. Odpowiedź z pomiaru, nie z teorii:
**dziś K-GLO nadaje się wyłącznie do idiolektu, a terminologia w nim jest aktywnie szkodliwa.**

Powód jest mechaniczny. Strażnik K-GLO daje FAIL, gdy cytat edycji **przecina** frazę
chronioną — **przy zachodzeniu na jeden znak, bez świadomości granic słowa**. Zmierzone
na realnych `edits.json` obu przebiegów kalibracji:

| słownik | blokuje (A) | blokuje (B) | z tego zamierzone |
|---|---|---|---|
| 7 fraz terminologicznych | 6 / 21 | 7 / 22 | **1** |
| `Quorn®` (1 fraza) | 0 / 21 | 1 / 22 | **1** |

Rozbiór: cztery blokady wzięły się z tego, że `ekosyste`**`m`** zachodzi na **`m`**`ykoryza`.
Dwie były czysto uboczne. To jest maszynka do cichych odrzutów: edycja ginie jako
`odrzucona-auto`, nie pojawia się w żadnym koszyku, człowiek jej nie widzi.

`SLOWNIK-bozena.md` ma dziś **jedną frazę** i to jest decyzja, nie zaniedbanie. Pozostałe
sześć kandydatek (`Fusarium venenatum`, `Aspergillus oryzae`, `GRAS`, `mykoryza`…) czekają
na **strażnika świadomego granic słowa** — to jest nasz dług, nie wasza decyzja o strukturze pliku.

Stąd konkretna odpowiedź na „jak założyć `SLOWNIK-ewa.md`":

1. **Tak, rozdzielić pojęciowo** — idiolekt (per osoba, przenosi się między książkami) vs
   terminologia (per książka, nie przenosi się). Macie rację, że to dwie różne rzeczy.
2. **Ale nie rozdzielajcie tego na dwa pliki teraz.** `slownik_chroniony` w configu to
   **jedna ścieżka na przebieg** — dwa pliki wymagałyby zmiany kontraktu configu, a nie ma
   po co, dopóki plik terminologiczny i tak byłby pusty.
3. **`SLOWNIK-ewa.md` załóżcie na idiolekt i tylko na idiolekt.** Prawdopodobnie zostanie
   niemal pusty i to jest stan poprawny — **brak pliku słownika jest legalny** (`wersje.slownik: null`),
   pusta sekcja też. Nie wypełniajcie go terminologią medyczną „na zapas": `T-score`, `DXA`,
   `densytometria`, nazwy leków dadzą dokładnie tę kolizję krawędziową co `ekosystem`/`mykoryza`.
4. **Terminologii Ewy pilnuje inny mechanizm** — strażnik faktów K-LIC, który porównuje encje
   (liczby, jednostki, tokeny Wielką Literą) między cytatem a propozycją. `DXA` i `T` z `T-score`
   są przez niego widziane jako encje. To jest właściwe miejsce, bo działa **per edycja**
   i degraduje do koszyka 3 zamiast cicho kasować. Ma dziury — patrz P4.
5. Wymóg techniczny pliku: dokładnie jedna linia `Wersja: **vX**` (parser pinuje ją do
   `run-meta.wersje.slownik`; brak = błąd twardy), sekcja `## Frazy chronione` z bulletami,
   `## Notatki` ignorowana.

Kiedy ta odpowiedź się zmieni: gdy dołożymy strażnika z granicami słowa i sekcję `## Wzorce`
(regexy — kontrakt to przewiduje, v1 nie czyta). Wtedy słownik per książka zacznie mieć sens
i wrócimy do tematu. Migracja będzie trywialna, bo to lista bulletów.

### P3. Stabilność artefaktów — układ potwierdzony, ale `wersje.kontrakt` NIE wystarczy

**Układ katalogu przebiegu** (`redaktor/praca/<basename-dokumentu>/<run-id>/`):

| plik | kiedy powstaje | uwagi |
|---|---|---|
| `input.md` | `run`, na starcie | kopia bajt w bajt tego, co podaliście w `--input` |
| `chunks.json` | `run` | **Z chunkami-kanarkami**; `{ hash_input, chunki[] }` |
| `edits.json` | `run` | goła tablica `Edycja[]`, **bez kanarków** |
| `raport.html` | `run` | samowystarczalny, zero sieci |
| `run-meta.json` | `run`, nadpisywany przez `apply` | `status: raport-gotowy \| podejrzany` → `zastosowany` |
| `decyzje.json` | **człowiek** | ścieżka jest wolna (`--decyzje <plik>` względem korzenia repo) — **nie musi leżeć w katalogu przebiegu i domyślnie nie leży** |
| `output.md` | `apply` | zapis atomowy (`.tmp` + rename), po komplecie walidacji |
| `diff.patch` | `apply` | unified diff `input` → `output` |

Poza katalogiem przebiegu, jako **rodzeństwo**: `redaktor/praca/<basename>/_skrzynka/`
(`zapytania/`, `odpowiedzi/`). Nie importujcie go, nie jest artefaktem wyniku.

**Czy `wersje.kontrakt` wystarczy jako bezpiecznik? Nie.** Trzy dowody:

1. Wartość bierze się z pola `wersja_kontraktu` w **configu YAML**, czyli jest wpisywana
   ręcznie przez operatora. Nic w kodzie nie sprawdza, czy odpowiada wersji binarki.
2. Pod niezmienionym `v1` **dołożyliśmy pola**: `pominiete_w2`, `liczniki.pominiete_sygnaly`,
   `emoji_dozwolone`. To ostatnie ma nawet jawny zapis w kontrakcie: *„Pole jest addytywne —
   nie podnosi `wersja_kontraktu`."*
3. Kształt `kanarki` zmienił się ze stringów na obiekty — a `wersje.kontrakt` dalej mówi `v1`.
   Przykład w KONTRAKT §5 pokazuje starą postać (B3 wyżej).

`v1` jest wersją **dokumentu**, nie formatu artefaktów. Odmawianie na nieznanej wartości
`wersje.kontrakt` jest OK jako drugi bezpiecznik, ale jako pierwszy da wam fałszywe poczucie
bezpieczeństwa: przy każdej z powyższych zmian widzielibyście dalej `v1`.

Na co patrzeć zamiast tego (kolejność od najmocniejszego):

- **Walidujcie KSZTAŁT, który konsumujecie** — obecność i typ każdego pola, które czytacie,
  i **odmawiajcie fail-closed** przy braku. To jest ten sam wzorzec, którym nasz parser configu
  odrzuca nieznane pola. Jedyny bezpiecznik odporny na to, że my dołożymy coś po cichu.
- **`wersje.rulebook`** — ta wersja jest **wyprowadzona z pliku**, nie przepisana z configu
  (parser wymaga dokładnie jednego trafienia `Wersja: **vX**`, inaczej błąd twardy). Dziś `v2`.
  To najuczciwszy sygnał, jaki mamy. Zmiana rulebooka zmienia zachowanie Redaktora, więc jest
  dokładnie tym, na co warto reagować.
- **`chunks.json.hash_input`** vs wasz własny hash — wiąże artefakty z konkretnym wejściem.
- **`run_id`** — zgodność `run-meta.run_id` = `decyzje.run_id` = nazwa katalogu. Apply tego
  pilnuje, wy też możecie.
- **`status: "zastosowany"`** — bez tego `output.md` nie jest wynikiem kompletnego apply.

**Co możemy dołożyć dla was:** pole `wersja_artefaktow` w `run-meta.json`, emitowane
**przez kod, nie przez config**, podbijane przy każdej zmianie kształtu artefaktów. To jest
mała rzecz i jedyne, o co bym po naszej stronie poprosił w ramach tego mostu — bo bez niego
wasz import nie ma czego pilnować poza własną walidacją kształtu. Decyzja właściciela;
zgłaszam jako rekomendowaną.

### P4. Osteoporoza a kalibracja — tak, osobny przebieg, i to nie formalność

**Tak. Zdecydowanie osobny przebieg kalibracyjny na jednym rozdziale Ewy przed puszczeniem
całości.** Dwa niezależne powody, oba zmierzone.

**Powód 1: kalibracja grzybowa mierzy mniej, niż się wydaje.** Na rozdziale Bożeny
**pięć reguł miękkich w ogóle się nie wykonało** — `EMD` (0× pauzy), `BLD` (0 dopasowań),
`TIT` (0 dopasowań), `WAR` (tylko w kanarku), `EMO` (jedyny kandydat wykluczony). Przebieg,
w którym reguła nie wystrzeliła, **nie mierzy jej jakości** — nie wiemy, czy jest dobra.
Do tego suwak 0 i suwak 1 dały na tym materiale wyjście **identyczne bajt w bajt**, więc
nie mamy nawet dowodu, że suwak cokolwiek robi. Materiał Ewy jest out-of-sample i większość
tych reguł wreszcie wykona.

**Powód 2: K-LIC ma dziury, które trafiają dokładnie w wasz materiał.** Sprawdzone przeze mnie
na żywym strażniku, nie wywnioskowane:

| przypadek | werdykt K-LIC | co to znaczy |
|---|---|---|
| `dawka 1000 mg` → `dawka 1000 g` | **PASS** | ❌ lista jednostek to `zł, %, minut, min, godz, kg` — **nie ma `mg`, `g`, `µg`, `IU`, `ml`, `g/cm²`**. Jednostka spoza listy nie wchodzi do encji, więc jej podmiana jest niewidzialna. |
| `wynik -2,5` → `wynik 2,5` | **PASS** | ❌ **znak minus nie jest częścią encji**. Dla T-score to różnica między normą a osteoporozą. |
| `podaj 25 µg` → `podaj 50 µg` | **FAIL** | ✅ tu działa — bo różnią się cyfry. |
| `DXA`, `T-score` | wykrywane jako encje | ✅ tokeny Wielką Literą nie na początku zdania. |

To są **fałszywe negatywy** — strażnik milczy tam, gdzie powinien krzyczeć. Nie są powodem,
żeby nie startować (nad K-LIC stoi jeszcze człowiek i koszyk 3), ale są powodem, żeby:
(a) na rozdziale kalibracyjnym **przeczytać koszyk 2 ręcznie, ze szczególną uwagą na liczby**,
(b) zanim pójdzie cała książka, dołożyć jednostki medyczne i znak liczby do K-LIC. To jest
mała robota po naszej stronie i chętnie ją zrobimy — ale dopiero po waszym rozdziale
kalibracyjnym, żeby wiedzieć, **których** jednostek naprawdę potrzeba. Lista z kalibracji
jest wart więcej niż lista z wyobraźni.

**Ustawienia, od których zacząć** (klon `redaktor/config/ebook-bozena-plik.yaml`):

```yaml
wersja_kontraktu: v1
rulebook: docs/redaktor/RULEBOOK.md
golden_set: docs/redaktor/GOLDEN-SET.md
slownik_chroniony: docs/redaktor/slowniki/SLOWNIK-ewa.md  # może nie istnieć — to legalne
role:
  redaktor: { provider: plik, model: claude-opus-4-8, temperatura: 0.2, max_tokens_odpowiedzi: 4000 }
  weryfikator: null
tworczyni: ewa
kanal: ebook
suwak: 0                    # ← start tutaj
budzet_zmian_procent: 8     # na grzybach wyszło 4,80% przy limicie 8 — zapas jest
kanarki: true               # ← nie wyłączać, to jedyny czujnik „model miał zły dzień"
chunking: akapit
pamiec_odrzucen: redaktor/pamiec/odrzucenia.jsonl
mapa_skazenia: false
```

**Suwak 0**, bo poziom 0 to same reguły twarde (`KLU, PUS, WAC, CEN, ZGL, STA, LAC, NOM, RYT`);
poziom 1 dokłada miękkie deterministyczne (`WAR, EMD, BLD, TIT, EMO`) — czyli dokładnie te,
których na Bożenie nie zmierzyliśmy. Puśćcie oba (0 i 1) na tym samym rozdziale i porównajcie,
tak jak my; na materiale Ewy prawdopodobnie **przestaną dawać ten sam wynik**, i to będzie
pierwsza rzetelna informacja o suwaku, jaką w ogóle będziemy mieli.

**Wybierzcie rozdział najgęstszy od liczb, nie najłatwiejszy.** Kalibracja służy do znajdowania
fałszywych alarmów i cichych przepuszczeń, a nie do zapalania zielonego.

---

## E. §6 i §7 — przyjęte

**§6 — potwierdzamy, że tego nie budujemy:** W3 nie wchodzi (grupa C zostaje `null`), zbiorczego
raportu przez rozdziały nie planujemy, transport API zostaje on-demand. Wszystkie trzy są
zgodne z naszym własnym kierunkiem — nie robicie nam ustępstwa.

**§7 — fixture: tak, chcemy. Z jednym warunkiem.** Sam plik `.md` w golden secie **niczego nie
mierzy** — golden ocenia pozycje po `oczekiwane_kody` (sekcja D), zerowej liczbie zgłoszeń
(sekcja N) albo inwariantach zachowanych znak w znak (sekcja C). Fixture bez oczekiwanego
wyniku byłby zielony zawsze, także wtedy, gdy Redaktor przestanie działać. Więc:

- przyślijcie **fragment realnego eksportu + listę kodów, które POWINNY się na nim zapalić**
  (albo: „na tym fragmencie nie powinno się zapalić nic" — to też jest mocna pozycja, sekcja N);
- najlepszy materiał to **prawdziwe zdania z prawdziwych rozdziałów**, nie spreparowane;
- przyślijcie **raz, w paczce**, nie po jednym: każda zmiana golden setu podbija jego wersję
  i wymusza obowiązkowy przebieg golden, więc drip po jednym pliku jest drogi.

Wasza intuicja, że fixture „wywala test u tego, kto zmienił" — trafna i to jest dokładnie
powód, dla którego to chcemy.

---

## F. Podsumowanie: co robić w jakiej kolejności

1. **Eksport (§4.1)** — budujcie od zaraz, nic go nie blokuje. Pamiętajcie o globalnie
   unikalnych nazwach plików (B2) i rozważcie `---` zamiast `***` (B1).
2. **Import + weryfikacja (§4.2)** — budujcie od zaraz, **z poprawkami z §C**. Dołóżcie
   `chunks.json` do listy konsumowanych artefaktów i zaimplementujcie precedencję decyzji,
   nie „lista przyjętych z pliku decyzji".
3. **Pętla po rozdziałach (P1)** — cienka, u was, ale nie liczcie na nią przed naszą `PHASE-18`.
4. **`SLOWNIK-ewa.md` (P2)** — załóżcie na idiolekt, prawie pusty. Terminologii tam nie wkładajcie.
5. **Rozdział kalibracyjny Ewy (P4)** — **przed** puszczeniem książki. Suwak 0 i 1, rozdział
   najgęstszy od liczb, koszyk 2 czytany ręcznie pod kątem liczb i jednostek.
6. Wnioski z (5) wracają do nas jako lista jednostek do K-LIC i jako pozycje golden setu (§7).

Otwarte po naszej stronie, do decyzji właściciela Redaktora: pole `wersja_artefaktow`
w `run-meta.json` (P3) oraz uogólnienie wypełniacza skrzynki na dowolny dokument (`PHASE-18`, P1).
