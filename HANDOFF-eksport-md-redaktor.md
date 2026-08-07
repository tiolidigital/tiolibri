**Temat:** eksport rozdziałów z TIOLIBRI do Markdown i powrót po redakcji — bo Piotrek chce przepuścić gotowe książki przez odsztuczniacz z FABRYKI-redaktor, zamiast poprawiać AI-izmy ręcznie w edytorze

Wątek był ROZMOWĄ projektową, nie implementacją. Nic nie zakodowane, nic nie zacommitowane.

> ⚠️ **Zanim cokolwiek zaprojektujesz — przeczytaj `docs/ODPOWIEDZ-most-tiolibri-redaktor.md`.**
> Redaktor odpowiedział na brief, weryfikując nasze założenia **na kodzie** (ich KONTRAKT
> w dwóch miejscach odstaje od kodu). Odpowiedź prostuje nasz błąd projektowy i jest
> ważniejsza od briefu tam, gdzie się różnią. Poniżej streszczenie, nie zamiennik.

---

## Co ustalone

**Cel.** Wyeksportować rozdziały książek z TIOLIBRI do plików .md, przepuścić przez Redaktora
(`/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor`), wgrać wyniki z powrotem
do TEGO SAMEGO projektu, z historią wersji. Właściciel ma NIE porównywać niczego ręcznie.

**Dlaczego Markdown, nie HTML.** Twardy wymóg Redaktora, nie preferencja: chunker
(`segmentuj.ts`) to parser Markdowna, K-NAG porównuje strukturę nagłówków ATX i przerywa
apply przy rozjeździe, kotwice edycji są exact-match. HTML rozbroiłby te zabezpieczenia.
TIOLIBRI dalej trzyma treść jako HTML w `chapters.processed_html` — to się nie zmienia.

**Kształt eksportu** (potwierdzony przez Redaktora, z dwiema korektami):
- ZIP → rozpakowanie do `redaktor/wsad/<ksiazka>/`. **NIE do `redaktor/praca/`** — to katalog
  wyjściowy, tworzony przez ich CLI.
- Plik .md na rozdział, **czysta proza**. Metadane (chapter id, hash, style separatorów)
  w `_tiolibri/manifest.json` obok — potwierdzone empirycznie: frontmatter YAML staje się
  chunkiem typu `akapit` i leci do W1/W2 jako proza do redakcji.
- ⚠️ **KOREKTA: nazwy plików muszą być unikalne GLOBALNIE, nie w obrębie ZIP-a.** Katalog
  przebiegu i skrzynka W2 to `redaktor/praca/<basename bez .md>/`. Dwa `01-wstep.md` z różnych
  książek wpadną do tego samego katalogu — ciche zatrucie, Redaktor się nie poskarży.
  **Prefiksować nazwą książki:** `osteoporoza-02-densytometria.md`. Diakrytyki OK.
- ⚠️ **KOREKTA: separatory jako `---`, nie `***`.** Oba są chunkiem `akapit` (koszt: jedno
  wywołanie W2 na separator = jedna ręczna iteracja operatora), ale `***` mnoży się w tekście.
- Wymagane: NFC, `&nbsp;` → zwykła spacja, nagłówki wyłącznie ATX (setext poza kontraktem).
- ⚠️ **`[E4]` OBRAZY NIGDY INLINE — warunek, nie optymalizacja.** `data:image` w base64 →
  plik w `_media/` + `![alt](_media/…)` w prozie. Powód: 83 kB w jednej linii to chunk
  EDYTOWALNY (leci do modelu jako proza), a mianownikiem strażnika budżetu jest długość
  całego pliku, więc przy ~70% balastu bramka budżetu świeci zielono nic nie mierząc.
  **Uwaga:** próbka, na której to zmierzono, wyszła prosto z Google Docs, **nie z TIOLIBRI** —
  czy nasze `processed_html` niosą `data:` URI, jest NIESPRAWDZONE (`htmlConverter.js` ich
  nie rusza, ale TipTap ma `allowBase64: false` i wyrzuca je przy wczytaniu). Zabezpieczamy
  w obie strony.

**Import — weryfikacja dowodowa. MOJA PIERWOTNA PROCEDURA BYŁA BŁĘDNA.**
Zakładałem, że `decyzje.json` zawiera listę przyjętych edycji. **Nie zawiera** — trzyma
wyłącznie odstępstwa od stanów domyślnych + akcepty hurtowe, i przy czystym przeglądzie może
nie istnieć wcale. Moja procedura dałaby `output.md` ≈ `input.md` i rozjazd na każdym rozdziale.

Poprawna rekonstrukcja (pełna, z uzasadnieniem: ODPOWIEDZ §C):
1. Odrzuć edycje ze `status: "odrzucona-auto"` — nigdy nie wchodzą.
2. Precedencja stanu: wpis per-`id` w `decyzje.decyzje` → wpis hurtowy per `kod`
   w `decyzje.hurtowe` → **domyślny stan koszyka: 1 = przyjęta, 2 = przyjęta, 3 = odrzucona.**
3. `propozycja === null` = sygnał W1 = **no-op**, nie błąd.
4. Kotwiczenie przez `indexOf` w `chunk.tekst`, **nie w całym `input.md`** → `chunks.json`
   jest niezbędny; globalny search-and-replace da fałszywe alarmy.
5. Kolejność podmian w chunku: malejąco po offsecie; remis → dłuższy cytat → `id` rosnąco.
6. Przy składaniu wyjścia **odfiltruj chunki-kanarki** (`kanarek !== undefined`, `offset: -1`).
7. Wyjście składane z `input.md` po offsetach (`chunk.offset` + `chunk.tekst.length`),
   nie z konkatenacji chunków — luki między blokami muszą zostać.
8. Hash: `sha256` na NFC, porównanie z `chunks.json.hash_input`, format **z prefiksem**
   `"sha256:<hex>"`.

**Konsumujemy PIĘĆ artefaktów, nie trzy:** `input.md`, `chunks.json`, `edits.json`,
`run-meta.json`, `decyzje.json`. (`decyzje.json` bywa poza katalogiem przebiegu — ścieżka wolna.)

**Bezpiecznik wersji: `wersje.kontrakt` NIE wystarcza** — wartość przepisywana ręcznie
z configu, a pod niezmienionym `v1` dokładano pola i zmieniano kształt `kanarki`. Zamiast tego:
walidować KSZTAŁT konsumowanych pól **fail-closed**, patrzeć na `wersje.rulebook` (wyprowadzana
z pliku, dziś `v2`), `chunks.json.hash_input`, zgodność `run_id`, `status: "zastosowany"`.

**Bezpieczeństwo zapisu.** Snapshot `pre-import`, wersja każdego nadpisanego rozdziału
(`_write_version` w `chapters.py` — istnieje), strażnik kolizji po hashu, lustro K-NAG,
poszanowanie blokady (`chapters.py:35-38` już działa poprawnie).

**Ekran eksportu.** Modal z listą rozdziałów, DOMYŚLNIE WSZYSTKIE zaznaczone. Status i kłódka
NIE filtrują (u Piotrka wszystko w `draft`, zablokowane też chce eksportować — kłódka chroni
zapis, nie odczyt). Przy każdym liczba znaków. Filtr „zmienione od ostatniego eksportu" za
darmo z tego samego hasha.

**Podział na dwa specy** (bramki `/spec-draft` policzone):
- `md-export` → thin PASS, Risk STANDARD (tylko odczyt) → **light, 2 rundy**
- `md-import` → thin FAIL (2 fazy, >2h) + Risk HIGH (nadpisuje treść prawdziwej książki)
  → **full struktura, 3 rundy**

**Gdzie się to dzieje.** Eksport/import = przyciski w aplikacji TIOLIBRI (auth, snapshoty,
historia, DiffViewer). Redakcja = pliki w VS Code.

---

## Co zmieniła odpowiedź Redaktora — poza §C

**P1. Pętla wsadowa NIE odblokuje — i to zmienia planowanie.** Przy `provider: plik`
(domyślny, darmowy) `run` staje na KAŻDYM wywołaniu W2: zapisuje zapytanie do skrzynki,
nie znajduje odpowiedzi, rzuca wyjątek i przerywa przebieg. Operator wypełnia, odpala od nowa,
przebieg dochodzi o chunk dalej. Na rozdziale Bożeny: **27 chunków = blisko TRZYDZIEŚCI wywołań
W2**, czyli tyleż cykli stop-wypełnij-wznów **na jeden rozdział**. Pętla po katalogu da
kilkanaście razy więcej ręcznej roboty naraz, nie automatyzację.
> `[E1]` Pierwotnie było tu „27 chunków / **14** wywołań W2" — **liczba błędna, sprostowana
> przez Redaktora 2026-08-07**: 14 to liczba EDYCJI, które z przebiegu wyszły, nie wywołań
> modelu. Wywołań jest tyle, ile chunków edytowalnych (skrzynka tego rozdziału: 59 kluczy
> z trzech przebiegów). Wniosek P1 się nie zmienia — **robi się mocniejszy**.
> Pełna errata: `docs/ODPOWIEDZ-most-tiolibri-redaktor.md` §ERRATA.
→ **„Przebieg per rozdział" w diagramie §3 nie jest dziś jedną komendą.** Reszta mostu jest od
tego niezależna — budować od zaraz, ale nie planować „wypuszczam książkę na noc".
→ Ich `PHASE-18` (uogólnienie wypełniacza skrzynki) to zdejmie. Wtedy nasza pętla zacznie mieć
sens bez zmian u nas. Awaryjnie: `provider: anthropic` daje jedną komendę dziś, kosztem tokenów
(pełny golden = 4,35 USD).

**P2. `SLOWNIK-ewa.md` — na idiolekt i TYLKO na idiolekt.** K-GLO daje FAIL, gdy cytat
**przecina** frazę chronioną — przy zachodzeniu na jeden znak, bez granic słowa. Zmierzone:
7 fraz terminologicznych zablokowało 6/21 edycji, z czego **1 zamierzenie** (`ekosyste|m`
zachodziło na `m|ykoryza`). To maszynka do cichych odrzutów. Terminologii medycznej Ewy
(`T-score`, `DXA`, dawki) tam NIE wkładać — od tego jest K-LIC, który degraduje do koszyka 3
zamiast kasować. Plik prawie pusty jest stanem poprawnym; brak pliku też jest legalny.
Wymóg parsera: dokładnie jedna linia `Wersja: **vX**`, sekcja `## Frazy chronione`.

**P4. K-LIC ma dziury trafiające dokładnie w książkę Ewy** (zmierzone na żywym strażniku):
`1000 mg` → `1000 g` przechodzi jako **PASS** (lista jednostek to `zł, %, minut, min, godz, kg`
— brak `mg/g/µg/IU/ml/g/cm²`); `-2,5` → `2,5` przechodzi jako **PASS** (minus nie jest częścią
encji — a to różnica między normą a osteoporozą). Stąd: rozdział kalibracyjny Ewy **przed**
całością, **suwak 0 i 1** na tym samym rozdziale, rozdział **najgęstszy od liczb**, koszyk 2
czytany ręcznie pod kątem liczb. Gotowy config: ODPOWIEDZ §D/P4. Wnioski wracają do nich jako
lista jednostek do K-LIC.

**§7 fixture — chcą, ale z oczekiwanym wynikiem.** Sam plik .md niczego nie mierzy (byłby
zielony zawsze). Przysłać fragment realnego eksportu + listę kodów, które POWINNY się zapalić
(albo „nie powinno nic" — też mocna pozycja). **Raz, w paczce** — każda zmiana golden setu
wymusza obowiązkowy przebieg.

**Otwarte po ich stronie** (decyzja właściciela Redaktora): pole `wersja_artefaktow`
w `run-meta.json` emitowane przez kod (rekomendują), oraz `PHASE-18`.

---

## Stan plików

- `docs/BRIEF-most-tiolibri-redaktor.md` — wysłany, odpowiedziany. Wartość historyczna.
- `docs/ODPOWIEDZ-most-tiolibri-redaktor.md` — **kanon ustaleń.** Od FABRYKA-redaktor,
  branch `redaktor`, HEAD `4ebec8c`.
- `HANDOFF-eksport-md-redaktor.md` — ten plik.
- Nic nie zacommitowane; w repo wiszą tylko niezwiązane zmiany `.DS_Store`.

---

## Czego właściciel NIE kupił

**Nic nie zostało odrzucone** — Piotrek powiedział „wszystko, co proponujesz, to bierzemy".
Ale: **nie padła zgoda na start implementacji.** Pytanie „odpalam `/spec-draft md-export
--light`?" zadane trzy razy, za każdym razem rozmowa szła dalej w projektowanie.
NIE zakładaj zgody — zapytaj raz jeszcze, krótko.

---

## NASTĘPNY KROK

~~Zapytać Piotrka o zielone światło i odpalić `/spec-draft md-export --light`.~~
**ZROBIONE 2026-08-07** — zielone światło dane, spec założony: `docs/specs/md-export/`
(light, thin PASS, Risk STANDARD → 2 rundy), wypełniony z kanonu. Następny krok:
`/spec-handoff md-export`. Do przejrzenia przez właściciela decyzje **D1–D3** na końcu speca.

**Kolejność prac potwierdzona przez Redaktora `[E2]`:** eksport PRZED importem. Import tylko
domyka pętlę — dopóki go nie ma, wartość i tak jest dostarczona, bo `raport.html` mówi, co
Redaktor znalazł, a wgranie z powrotem da się zrobić później. Drugi powód: import wymaga
poprawek z §C, więc niech ten kawałek dojrzeje, zamiast być budowany dwa razy.

**Pierwszy rozdział próbny `[E3]`: EWA (osteoporoza), nie Bożena** — najgęstszy od liczb
i dawek, nie najłatwiejszy. Ta sama sztuka służy za rozdział kalibracyjny z P4.

### Stan na 2026-08-07, koniec wątku

Zrobione w tym wątku: `/spec-draft md-export --light` → `docs/specs/md-export/`
(SPEC-MD-EXPORT.md wypełniony z kanonu, STATE.md `spec: draft`, `_review/`, `_impl/`).
Wpisane erraty E1–E4 do `docs/ODPOWIEDZ-most-tiolibri-redaktor.md` (sekcja `## ERRATA`
na górze + znacznik w miejscu w §D/P1). Spec przerobiony pod E3 (rozdział próbny Ewy)
i E4 (`_media/`, limity, licznik znaków z tekstu, sizing na granicy). **Nic nie zacommitowane.**

**NASTĘPNY KROK:** `/spec-handoff md-export` (review Codexa, 2 rundy, Risk STANDARD).
Przedtem właściciel przegląda **D1–D3 + sizing na granicy** na końcu / górze speca.

**Do sprawdzenia przy implementacji, nie tu:**
`select count(*) from chapters where processed_html like '%data:image%'` — baza TIOLIBRI była
poza zasięgiem wątku (na koncie Supabase w MCP widać tylko QuoteFLOW i fabryka).

**Znalezisko poboczne, POZA zakresem md-export:** `Image.configure({ allowBase64: false })`
w `ChapterEditor.jsx:60-62` oznacza, że otwarcie i zapisanie w edytorze rozdziału z obrazem
osadzonym w base64 **kasuje ten obraz bez ostrzeżenia**. To cicha utrata danych w produkcie,
niezależna od mostu. Zasługuje na własny zgrzyt/spec.

Eksport jest niezależny od wszystkiego, co zostało otwarte po stronie Redaktora (`PHASE-18`,
`wersja_artefaktow`), i odblokowuje dwie rzeczy, które dziś oznaczają ręczne wyklejanie
rozdziałów: budowę `SLOWNIK-ewa.md` i rozdział kalibracyjny Ewy.

Do speca eksportu wnieść z ODPOWIEDZI: globalnie unikalne nazwy plików z prefiksem książki (B2),
separatory jako `---` (B1), rozpakowanie do `redaktor/wsad/<ksiazka>/` (§B), manifest obok
plików zamiast frontmattera (A3).

## Wskaźniki do kanonów

- **Kanon ustaleń:** `docs/ODPOWIEDZ-most-tiolibri-redaktor.md` (nadrzędny wobec briefu)
- Brief: `docs/BRIEF-most-tiolibri-redaktor.md`
- Kontrakt Redaktora: `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/docs/redaktor/KONTRAKT.md`
  (v1 — **w dwóch miejscach odstaje od kodu**, patrz ODPOWIEDZ B3)
- Stare specy TIOLIBRI (płaski format sprzed spec-workflow): `docs/specs/SPEC-1..3`
- Model docelowy: **Opus**
