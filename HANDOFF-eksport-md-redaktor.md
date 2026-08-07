**Temat:** eksport rozdziałów z TIOLIBRI do Markdown dla odsztuczniacza z FABRYKA-redaktor — bo Piotrek chce przepuścić gotowe książki przez Redaktora zamiast poprawiać AI-izmy ręcznie w edytorze

Wątek był ROBOTĄ: `/spec-handoff md-export`. Prompt R3 doręczony Codexowi przez CLI,
**review R3 odebrane — werdykt NITS, czyli GREEN.** Spec w **v0.4.1** (+ self-fix footera
przez Codexa), STATE na `R3-codex-pending`.

> ⚠️ **Kanon ustaleń: `docs/ODPOWIEDZ-most-tiolibri-redaktor.md`** — nadrzędny wobec speca
> i wobec `docs/BRIEF-most-tiolibri-redaktor.md`. Nie projektuj z głowy, sprawdź tam.
> **Kanon konsumenta: `FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts`** (gałąź `redaktor`).
> HEAD gałęzi to teraz **`134f8e4`** — plik jest bajtowo identyczny w `4ebec8c`, `d7087bd`
> i `134f8e4`, więc kotwice po numerach linii trzymają. **Ten wskaźnik zestarzał się już dwa
> razy z rzędu** (R2 i R3) — sprawdzaj HEAD przed każdą rundą.

---

## NASTĘPNY KROK

**Odpal `/spec-apply-review md-export`.**

Review odebrane i zwalidowane: `_review/R3-codex.md` istnieje, linia werdyktu parsuje się
(1 dopasowanie), **`**Werdykt:** NITS`**. To jest GREEN — spec **nie idzie** do ESCALATED,
runda R3 zamyka stronę SPEC. Po apply-review następny ruch to strona IMPL (szew 1b→1).

**Co Codex zrobił sam (do zwalidowania przez apply-review, nie na słowo):** self-fix footera
speca — **11 zmienionych linii** wobec `_review/.base-R3.md`, wyłącznie sekcja „Dla Piotrka"
i komenda w bloku „Kopiuj dalej" (`/spec-handoff` → `/spec-apply-review`). Zero zmian
kontraktu, mieści się w kopercie NITS (≤20 LOC). **Spec jest niezacommitowany** — apply-review
domknie go commitem.

**Codex odtworzył oba moje pomiary niezależnie**, na własnych fixture'ach, i doszedł do tych
samych liczb: `segmentuj()` + algorytm `blocks` `PASS=11 FAIL=0 EXIT=0`, TestClient sygnatury
`PASS=6 FAIL=0 EXIT=0`, bramki strukturalne FACT i C/M/E `EXIT=0`. Czyli **nie zakwestionował
ani cofnięcia formy poprawki #2 z R2, ani korekty kolejności gałęzi** — to były dwie rzeczy,
o które prompt pytał wprost.

## Co zrobione w tym wątku

Preflight R3 **uruchomił oba parsery speca**, zamiast je czytać — i to złapało jedną rzecz
merytoryczną, której trzy poprzednie rundy nie widziały.

**Dowody uruchomieniowe (nowe w tej rundzie):**
1. **Sygnatura endpointu na `TestClient`** — dwie aplikacje FastAPI: ta ze speca
   (`Optional[ExportMdRequest] = None`) i kontrpróba bez `Optional`. **PASS=6 FAIL=0, EXIT=0.**
   Brak body → 200 przy sygnaturze ze speca, **422** przy kontrpróbie, a warianty b–d
   przechodzą identycznie w obu. Czyli twierdzenie speca „wariant (a) jest jedynym, który
   wykrywa brak `Optional`" jest **zmierzone**, nie założone. To domyka blokera #4 z R2.
2. **Algorytm `blocks` wobec PRAWDZIWEGO `segmentuj()`** — 11 fixture'ów przez prawdziwy
   chunker (Node 24 `--experimental-strip-types`, import wprost z FABRYKA-redaktor, EXIT=0)
   i przez implementację algorytmu ze speca w Pythonie. **Wszystkie 9 wierszy tabeli
   konsekwencji potwierdzone** — pierwszy raz zmierzone, a nie wyprowadzone z lektury kodu.

**Korekta merytoryczna, którą to złapało:** v0.4 wypisywała gałęzie algorytmu w kolejności
ATX → marker → BQ → fence → tabela. Konsument sprawdza je w kolejności fence → ATX →
**tabela** → BQ → marker (`segmentuj.ts:55-146`), a wzorce **nie są rozłączne**: linia
`> a | b` bezpośrednio nad `---` daje u konsumenta **jeden chunk `tabela`**, a w kolejności
ze speca `blockquote` + `akapit` (to samo dla `- a | b`). W naszym wyjściu ta klasa jest
nieosiągalna, ale przy **zerowej tolerancji G1** algorytm ma odtwarzać konsumenta, nie
przybliżać. Kolejność jest teraz jawną częścią kontraktu z nazwanym przypadkiem rozjazdu.

**Trzy korekty stale-refów** (wszystkie ze sweepu `rg`, nie z lektury — LESSONS#3 pkt 1):
- SHA kanonu konsumenta `d7087bd` → `134f8e4` (drugi raz z rzędu ten sam wskaźnik).
- `~3×` → **`3,44×`** w §Co odrzucone — przeżyło korektę R2, która podniosła tę liczbę
  w §`_media/`. Jeden dokument podawał dwie różne liczby dla tego samego pomiaru.
- `~67 LOC` → **`~82 LOC`** w §Decyzje właściciela — §Sizing mówił `~82` po wzroście w R2.

**Cofnięta forma poprawki #2 z R2.** Dopisane wtedy pole `E` do rekordu CONTRACTED łamie
regułę 5 audytu C/M/E (rekord był MEASURED i CONTRACTED naraz) — bramka `cme_typ_both`
zatrzymała handoff. Uruchomiona część `C` jest teraz niesiona przez **dwa osobne rekordy
MEASURED**, więc fakt nie zginął, a rekord CONTRACTED ma samo `mierzalne-od`. **Codex jest
o tym uprzedzony w promptcie i poproszony o sprawdzenie, czy to faktycznie domyka jego
blokera #2, czy tylko przenosi go gdzie indziej.**

Bramki L5 i C/M/E: **PASS** (18 faktów, 0 malformed, 0 BLOCKED, 4 CORRECTED wszystkie
zmigrowane do speca; 8 rekordów CME, 0 invalid, 0 FAIL, 0 typ_both, 0 dup).

## Stan: pliki, commity

- **`6ef6164`** — spec v0.4.1 + preflight R3 + STATE bump (ten wątek)
- `f0940c4` — HANDOFF po R2
- `d7e20c7` — spec v0.4 + response R2
- `docs/specs/md-export/STATE.md` → **`spec: R3-codex-pending`** / `impl: not-started` /
  `rundy-rdzenia: 0` / **`convergence-ext: R2`**
- `_review/R3-opus-preflight.md` — 18 faktów, §Parser self-test z tabelą 11 fixture'ów,
  §Audyt C/M/E z 8 rekordami
- `_review/.base-R3.md` — baseline R3. **Nie kasować** (mierzy LOC self-fixu Codexa).
- `_review/.R3-prompt.md` — prompt doręczony Codexowi (gdyby trzeba było powtórzyć ręcznie)
- `_review/.R3-codex-run.log` + `.R3-codex-last-msg.md` — przebieg Codexa

Skrypty dowodowe leżą w scratchpadzie sesji (`scratchpad/t_signature.py`,
`scratchpad/blocks/`) — **nie w repo**. Jeśli Codex zakwestionuje liczby, odtworzenie to
kilka minut; opis metody jest w §Parser self-test preflightu.

## Wskaźniki do kanonów

- Spec: `docs/specs/md-export/SPEC-MD-EXPORT.md` **v0.4.1**
- Ta runda: `_review/R3-opus-preflight.md` (+ `R3-codex.md`, gdy dojdzie)
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
- **Prawdziwy `segmentuj()` da się odpalić w sandboxie** — Node v24.12.0,
  `node --experimental-strip-types`, import po ścieżce bezwzględnej z FABRYKA-redaktor.
  Ostrzega o `MODULE_TYPELESS_PACKAGE_JSON`, ale działa. To najtańszy sposób rozstrzygnięcia
  każdego sporu o to, jak konsument dzieli tekst.
- **`tiolibri-api/venv` ma `httpx` 0.27.2**, więc `fastapi.testclient` działa bez instalacji —
  ale `pytest` w nim nadal NIE ma (i zgodnie ze specem nie wchodzi do `requirements.txt`).
- RETRO w FABRYCE (drain z R1) wciąż **niezacommitowane**, leży w
  `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/RETRO.md`.

**Model docelowy: Opus.**
