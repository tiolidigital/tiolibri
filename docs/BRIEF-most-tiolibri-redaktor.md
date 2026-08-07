# BRIEF — most TIOLIBRI ↔ Redaktor

**Od:** projekt TIOLIBRI (edytor i generator ebooków — EPUB/PDF)
**Do:** projekt FABRYKA-redaktor, moduł Redaktor (odsztuczniacz)
**Data:** 2026-08-07
**Status:** propozycja do weryfikacji — **prosimy o odpowiedź**, nie o wykonanie

---

## 0. Po co ten dokument

Chcemy przepuścić przez Redaktora dwie prawdziwe książki, które żyją dziś w TIOLIBRI.
Zanim zaczniemy budować cokolwiek po naszej stronie, chcemy:

1. **potwierdzenia albo sprostowania** naszego odczytania waszego kontraktu (§2),
2. odpowiedzi na **cztery pytania** (§5),
3. decyzji w sprawie **jednej małej rzeczy do dopisania** u was (§4.1).

Nie prosimy o żadną przebudowę. Jeśli odpowiedź na §4.1 brzmi „nie", też jest dobrze —
zrobimy to skryptem pętli u siebie.

---

## 1. Kontekst: co to jest TIOLIBRI i co chcemy zrobić

TIOLIBRI to edytor ebooków (React + TipTap, backend FastAPI + Supabase). Treść rozdziału
jest przechowywana jako **HTML** w kolumnie `chapters.processed_html` — HTML, bo źródłem
są eksporty z Google Docs, a TipTap i generatory EPUB/PDF mówią HTML-em natywnie.

W TIOLIBRI żyją dziś dwie książki **dwóch różnych autorek**:
- **grzyby** — Bożena Muszyńska. Na jednym jej rozdziale powstał
  `docs/redaktor/slowniki/SLOWNIK-bozena.md`; terminologia to głównie łacińskie nazwy
  gatunków i związków.
- **osteoporoza** — Ewa Stachowska. Jeszcze nietknięta przez Redaktora, brak słownika.
  Tekst gęsty od liczb, dawek, jednostek i terminów medycznych (T-score, densytometria, DXA…).

Docelowo autorek będzie więcej, ale na starcie to te dwie — **z kilkoma książkami każda**.

Obie powstawały z asystą modelu i mają w sobie sporo AI-izmów. Stąd pomysł: **przepuścić
je przez Redaktora rozdział po rozdziale i wgrać wyniki z powrotem**, zamiast klepać
poprawki ręcznie w edytorze.

Dziś umowa jest taka, że właściciel wkleja Redaktorowi jeden rozdział ręcznie. Chcemy to
zamienić na przepływ, w którym cała książka wyjeżdża i wjeżdża automatycznie.

---

## 2. Nasze odczytanie waszego kontraktu — prosimy o potwierdzenie lub sprostowanie

Przeczytaliśmy `docs/redaktor/KONTRAKT.md` v1 oraz kod (`src/redaktor/chunker/segmentuj.ts`,
`src/redaktor/apply/k-nag.ts`, `src/redaktor/cli/run.ts`, `src/redaktor/model/typy.ts`).
Poniżej to, na czym opieramy projekt. **Każdy punkt może być błędny — prosimy o korektę.**

| # | Nasze założenie | Skąd |
|---|---|---|
| A1 | Wejście to **Markdown**, jeden dokument = jeden rozdział; wyjście to `output.md`. | §1 słownik, §6 pipeline |
| A2 | Chunker segmentuje wyłącznie Markdown; typy chunków to `akapit \| naglowek \| lista \| blockquote \| kod \| tabela`. Nie ma typu dla frontmattera ani dla linii poziomej. | `typy.ts:48`, `segmentuj.ts` |
| A3 | **Wniosek z A2:** frontmatter YAML na górze pliku zostałby potraktowany jako zwykły `akapit` i trafił do W1/W2 jako proza do redakcji. Dlatego **nie umieszczamy metadanych w plikach .md**. | nasza inferencja — **prosimy o potwierdzenie** |
| A4 | K-NAG porównuje strukturę nagłówków wejścia i wyjścia i **przerywa apply** przy rozjeździe; rozpoznaje wyłącznie ATX (`#`). | `k-nag.ts` |
| A5 | Kotwica exact-match: cytat musi wystąpić w chunku znak w znak i dokładnie raz. Wejście jest normalizowane do NFC. | §0 pkt 2, §6.2, `segmentuj.ts` |
| A6 | Strażnik słownika (K-GLO) daje **odrzut auto**; strażnik faktów (K-LIC) daje **koszyk 3 + flagę**. | §6.2 |
| A7 | Apply jest idempotentny: te same `input.md` + `edits.json` + `decyzje.json` dają bajt w bajt ten sam `output.md`. | §7.3 / okolice wiersza 549 |
| A8 | W3 (weryfikator adwersaryjny) to **etap 2** — dziś grupa C = `null`. | §9 |
| A9 | Transport plikowy jest domyślny i bezterminowy; etap 3b (API) wyłącznie on-demand. | §0 pkt 6 |

---

## 3. Planowany przepływ

```
TIOLIBRI (aplikacja)          VS Code / dysk                    TIOLIBRI (aplikacja)
─────────────────────         ────────────────────────          ─────────────────────
wybór rozdziałów
  → ZIP z .md          →      katalog roboczy Redaktora
                              → przebieg per rozdział
                              → raport.html → decyzje.json
                              → apply → output.md
                                                          →     import katalogu
                                                                → weryfikacja (§4.2)
                                                                → zapis z historią wersji
```

Granica jest po odpowiedzialności: **TIOLIBRI trzyma książkę, tożsamość i historię;
Redaktor przetwarza pliki.** Nic w tym przepływie nie wymaga od was API ani znajomości
naszej bazy.

**Zależność jest jednokierunkowa i chcemy, żeby taka została:** TIOLIBRI będzie znał
format waszych artefaktów. Redaktor nie powinien wiedzieć o istnieniu TIOLIBRI.

---

## 4. Co budujemy u siebie (żebyście tego nie dublowali)

### 4.1 Eksport do Markdown

ZIP z jednym katalogiem głównym, w środku plik .md na rozdział, w kolejności książki.
Pliki są **czystą prozą** — metadane (id rozdziału, hash treści, style separatorów)
jadą w osobnym `_tiolibri/manifest.json` obok, nie we frontmatterze (A3).

Konwersja pilnuje waszych wymagań: normalizacja NFC, `&nbsp;` → zwykła spacja,
nagłówki wyłącznie jako ATX, separatory graficzne jako `***`.

**Prosimy o wskazanie układu katalogu**, w który mamy się rozpakowywać, żeby po pobraniu
ZIP-a nie trzeba było przekładać plików ręcznie.

### 4.2 Import z weryfikacją — i tu prosimy o szczególną uwagę

Zależy nam, żeby **właściciel nie musiał niczego porównywać ręcznie**. Zamiast tego,
przy imporcie TIOLIBRI zrobi rzecz następującą, opierając się na A7:

1. sprawdzi, że hash `input.md` zgadza się z tym, co sam wyeksportował,
2. **niezależnie** zaaplikuje na `input.md` wyłącznie edycje o stanie `przyjeta`
   z `decyzje.json`, biorąc cytaty i propozycje z `edits.json`,
3. porówna wynik bajt w bajt z waszym `output.md`.

Zgodność = dowód, że wracający tekst różni się od wyjściowego **wyłącznie o zatwierdzone
edycje**. To druga, niezależna implementacja tego samego kroku — więc łapie także
ewentualny błąd po waszej stronie.

**To jedyne miejsce, w którym wiążemy się z waszym formatem wewnętrznym.** Dlatego
pytanie 3 w §5 jest dla nas najważniejsze.

Niezależnie od tego zawsze uruchamiamy lekkiego strażnika (struktura nagłówków, zgodność
liczb i nazw własnych, procent zmienionych znaków), żeby import luźnego `output.md`
bez katalogu przebiegu też był bezpieczny.

### 4.3 Bezpieczeństwo zapisu

Snapshot projektu przed importem, wersja każdego nadpisanego rozdziału (mamy to),
wykrywanie kolizji przez hash (rozdział zmieniony w TIOLIBRI po eksporcie nie zostanie
po cichu nadpisany), poszanowanie blokady rozdziału.

---

## 5. Pytania — prosimy o odpowiedź

**P1. Tryb wsadowy.** `parsujArgi` w `src/redaktor/cli/run.ts` przyjmuje dokładnie jeden
`--input <dok.md>`. Przy kilkunastu rozdziałach to kilkanaście ręcznych odpaleń.
Czy widzicie sens w cienkiej nakładce `--input-dir <katalog>`, która przelatuje pliki
i woła istniejący pipeline per dokument — bez żadnej zmiany w silniku, z osobnym raportem
na rozdział? Czy raczej mamy to zrobić skryptem pętli po naszej stronie i nie dotykać
waszego CLI?

**P2. Ziarnistość słownika chronionego.** Dziś odwzorowanie jest 1:1 — Bożena ma grzyby,
Ewa ma osteoporozę — więc `SLOWNIK-<tworczyni>.md` działa bez zgrzytu. Ale **każda z autorek
będzie miała po kilka książek**, i wtedy jeden plik zacznie mieszać słownictwo różnych
dziedzin tej samej osoby.

Pod tym siedzi pytanie o to, **co słownik ma właściwie chronić**: idiolekt autorki (jej
zwroty, rytm, ulubione konstrukcje — to jest per osoba i przenosi się między książkami),
czy terminologię dziedziny (nazwy gatunków, jednostki, wartości progowe — to jest per
książka i nie przenosi się wcale)? Jeśli jedno i drugie, to czy warto je rozdzielić.

Pytamy teraz, bo za chwilę budujemy `SLOWNIK-ewa.md` od zera i wolimy założyć od razu
właściwą strukturę, niż migrować ją później.

**P3. Stabilność artefaktów przebiegu.** Opieramy weryfikację z §4.2 na `input.md`,
`output.md`, `edits.json`, `decyzje.json` i `run-meta.json`. Prosimy o potwierdzenie
dokładnego układu katalogu przebiegu i o odpowiedź: czy wersja kontraktu w `run-meta.json`
jest wystarczającym sygnałem, żeby nasz import odmówił działania przy nieznanej wersji
formatu? Czy jest coś jeszcze, na co powinniśmy patrzeć?

**P4. Osteoporoza a kalibracja.** Kalibracja (`docs/redaktor/kalibracja/`) powstała na
tekście Bożeny o grzybach. Ewa to **inna autorka i inny rejestr**, z dużo większą gęstością
liczb — czyli K-LIC będzie pracował znacznie ciężej, a wnioski z kalibracji grzybowej mogą
się nie przenieść. Czy zalecacie osobny przebieg kalibracyjny na jednym rozdziale Ewy przed
puszczeniem całości, i czy są ustawienia suwaka, od których warto zacząć?

---

## 6. Czego świadomie NIE prosimy

Żebyście nie planowali pracy, której nie potrzebujemy:

- **W3 / weryfikator adwersaryjny (etap 2)** — nie na tę książkę. Weryfikacja z §4.2 jest
  deterministyczna i darmowa; W3 kosztuje tokeny za każdą edycję.
- **Zbiorczy raport przez wszystkie rozdziały** — koszyki mają sens per dokument, wolimy
  osobne raporty.
- **Etap 3b / transport API** — kontrakt mówi jasno, że to on-demand za odpłatnością.
  Pracujemy plikami.

---

## 7. Propozycja w drugą stronę

Gdy eksport ruszy, możemy dostarczyć **prawdziwy eksport rozdziału z TIOLIBRI jako fixture
do waszego golden setu**. To zwykły plik .md, więc nie wprowadza żadnej wiedzy o TIOLIBRI
do waszego kodu — a sprawia, że zmiana po którejkolwiek stronie mostu wywala test u tego,
kto ją zrobił.

Dajcie znać, czy to dla was użyteczne, czy raczej zaśmieca golden set.
