**Temat:** eksport rozdziałów z TIOLIBRI do Markdown dla odsztuczniacza z FABRYKA-redaktor — bo Piotrek chce przepuścić gotowe książki przez Redaktora zamiast poprawiać AI-izmy ręcznie w edytorze

Wątek był ROBOTĄ: `/spec-apply-review md-export`. Review R2 przetworzone, spec w **v0.4**,
STATE zbumpowany, **przedłużenie konwergencji przyznane — R3 jest twardym końcem budżetu.**

> ⚠️ **Kanon ustaleń: `docs/ODPOWIEDZ-most-tiolibri-redaktor.md`** — nadrzędny wobec speca
> i wobec `docs/BRIEF-most-tiolibri-redaktor.md`. Nie projektuj z głowy, sprawdź tam.
> **Kanon konsumenta: `FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts`** (gałąź `redaktor`,
> HEAD `d7087bd`). Escaping I NOWY ALGORYTM LICZENIA `blocks` są przepisane z tego pliku.
> **Trzeci dokument, młodszy od ODPOWIEDZI:** `FABRYKA-redaktor/docs/redaktor/kalibracja/ZWIAD-EWA-R8.md`
> (commit `5a4fd8e`) — źródło liczb `3,44×` i `215 chunków`.

---

## NASTĘPNY KROK

**Odpal `/spec-handoff md-export`** — wygeneruje prompt R3 dla Codexa (TARGET=3) i doręczy go
przez Codex CLI. STATE stoi na `spec: R2-opus-pending`, czyli dokładnie w stanie, z którego
handoff liczy N+1. **Nie bumpuj STATE ręcznie.**

**To jest OSTATNIA runda.** `convergence-ext: R2` jest już zapisane w STATE — kolejnego
przedłużenia nie ma. R3 musi wyjść GREEN (APPROVE / NITS / NITS-EXT), inaczej spec idzie
do ESCALATED i wchodzi brief dla Fable.

## Co zrobione w tym wątku

Codex w R2 dał **REQUEST_CHANGES: 3 BLOCKER + 2 MAJOR**, 11/11 kategorii sprawdzonych.
Wszystkie przyjęte, żadna nie odrzucona. Plus jedna znaleziona sweepem, której Codex nie widział.

**Klasy PRODUKT (te uzasadniają rundę R3, reguła L-C):**
1. **G2 przeczyło samo sobie** — jednocześnie dopuszczało listy i nazywało je zerem, więc dwaj
   implementatorzy bramki dostawali przeciwne werdykty na tym samym `chunks.json`. Rozdzielone:
   G2 = `kod=0 ∧ tabela=0`, `lista` zostaje wyłącznie w G1.
2. **Sygnatura endpointu nie egzekwowała własnej tabeli** — przy `request: ExportMdRequest`
   FastAPI zwraca **422 na brak body**, czyli odwrotnie niż wiersz 1. Wpisane
   `request: Optional[ExportMdRequest] = None`. Sygnatura **zwalidowana wobec produkcji**
   (`export_import.py:34-38`): `verify_supabase_jwt`, `project_id: str`, prefiks `/projects` —
   pierwsza wersja poprawki miała trzy zmyślone nazwy, `rg` je złapał (LESSONS#20).
3. **`blocks` nie miało reguły liczenia**, a G1 porównuje je z zerową tolerancją. Nowy
   podrozdział: liczymy **z finalnego Markdowna**, odtwarzając granice bloków konsumenta —
   bo `chunks.json` powstaje z `segmentuj()` na naszym `.md`, więc licząc po HTML-u
   porównywalibyśmy dwa różne języki. Tabela 9 konsekwencji (lista wieloelementowa = 1 blok,
   obraz i `---` = `akapit`) + 8 fixture'ów.

**Klasy APARATURA (audyt dowodu):**
4. **Trzy rekordy C/M/E miały fałszywe `PASS`** — `C` obejmowało wnioski o W2, których przebieg
   `--tylko-w1` nie wykonał. Zawężone; wnioski oznaczone jako inferencja z kontraktu, nie pomiar.
   **Trzeci rekord (Bożena, „blisko trzydzieści wywołań W2") znalazł sweep, nie Codex** —
   ta sama konstrukcja, ten sam defekt. Bez tego R3 miałby czwarty bloker tej samej klasy.
5. **Rekord CONTRACTED nie miał pola `E`** (miał `mierzalne-od` zamiast, nie obok) — bramka
   strukturalna niespełniona. Dopisane realne `E`: byte-diff `segmentuj.ts` + 78 przypadków
   escapingu. `mierzalne-od` zostaje na nieuruchomioną resztę.

**Sizing urósł i jest to zapisane, nie przemilczane:** dyspensa ~67 → **~82 LOC** (fixture'y
`blocks`), z jawną liczbą nowych przypadków (8). Osie plików (5/5) i czasu bez zmian. Dlatego
sprawdzenie czterech wejść body jest **ręczne (curl), nie `TestClient`** — automatyzacja
wymagałaby mocka Supabase, szóstego pliku i zamieniłaby oś plików w FAIL.

## Dlaczego R3 w ogóle przysługuje

Budżet: `N=2`, `rundy-rdzenia=0`, `reset-po-spike=0` → **`N_EFF=2` = MAX_ROUNDS** (Risk STANDARD).
Czyli próg. Przedłużenie przyznane, bo wszystkie cztery warunki spełnione: `N_EFF = MAX_ROUNDS`
dokładnie, brak wcześniejszego `convergence-ext`, `rundy-rdzenia=0`, `DELTA=177 > 0` — i **blokery
wyraźnie maleją: R1 `8 BLOCKER + 5 MAJOR` → R2 `3 BLOCKER + 2 MAJOR`**, przy czym R1 obalał
wykonalność rdzenia („algorytm HTML→MD nie jest implementowalny bez zgadywania"), a R2 tego rdzenia
w ogóle nie tknął.

**STOP-and-SPIKE sprawdzone i nie kwalifikuje się** — R2 nie wraca do rdzenia z R1. Rekurencja
klasy C/M/E (R1 #11 → R2 #1/#2) jest realna, ale to aparatura dowodu, nie rdzeń projektowy;
spike na realnych danych niczego by tam nie rozstrzygnął.

## Stan: pliki, commity

- **`d7e20c7`** — spec v0.4 + response R2 + korekta preflightu + STATE bump (ten wątek)
- `c9b2e0d` — HANDOFF po handoffie R2
- `b502702` — spec v0.3.1 + preflight R2
- `docs/specs/md-export/STATE.md` → **`spec: R2-opus-pending`** / `impl: not-started` /
  `rundy-rdzenia: 0` / **`convergence-ext: R2`**
- `_review/R2-opus-response.md` — decyzje per uwaga + klasyfikacja L-C + uzasadnienie przedłużenia
- `_review/R2-opus-preflight.md` — §Audyt C/M/E pod znacznikiem **KOREKTA PO R2**
- `_review/.base-R2.md` — baseline R2. **Nie kasować** (handoff R3 zrobi `.base-R3.md`).

## Wskaźniki do kanonów

- Spec: `docs/specs/md-export/SPEC-MD-EXPORT.md` **v0.4**
- Ta runda: `_review/R2-codex.md` + `R2-opus-response.md` + `R2-opus-preflight.md`
- Kanon spec-workflow: **w FABRYCE**,
  `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`
- Kontrakt Redaktora: `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/docs/redaktor/KONTRAKT.md`
  (v1 — w dwóch miejscach odstaje od kodu, patrz ODPOWIEDZ B3)

## Uwagi operacyjne

- **Codex ma dwa konta.** Pierwsze wyczerpało tygodniowy limit (reset 2026-08-08 08:47). Gdy
  `codex exec` milczy dłużej niż kilka minut: sprawdź `used_percent` w najnowszym
  `~/.codex/sessions/**/rollout-*.jsonl`, zanim uznasz, że pracuje.
- `codex` nie jest w PATH sandboxa — wołać `/opt/homebrew/bin/codex`.
- Nie przepuszczać wyjścia `codex exec` przez `| tail` — buforuje do końca, nie widać postępu.
- RETRO w FABRYCE (drain z R1) wciąż **niezacommitowane**, leży w
  `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/RETRO.md`.

**Model docelowy: Opus.**
