**Temat:** eksport rozdziałów z TIOLIBRI do Markdown dla odsztuczniacza z FABRYKA-redaktor — bo Piotrek chce przepuścić gotowe książki przez Redaktora zamiast poprawiać AI-izmy ręcznie w edytorze

Wątek był ROBOTĄ: handoff speca `md-export` do review Codexa. Review wrócił, jest REQUEST_CHANGES.

> ⚠️ **Kanon ustaleń: `docs/ODPOWIEDZ-most-tiolibri-redaktor.md`** — nadrzędny wobec speca
> i wobec `docs/BRIEF-most-tiolibri-redaktor.md` wszędzie tam, gdzie się różnią. Nie projektuj
> z głowy, sprawdź tam.

---

## Co zrobione w tym wątku

1. **Porządki.** Trzy dokumenty mostu + spec `md-export` zacommitowane i wypchnięte
   (`3e8a909`). Wcześniej wisiały niezacommitowane.
2. **Założony `.claude/spec-config.json`** — nie powstał przy `/spec-draft`, a bez niego
   `/spec-handoff` STOPuje na onboardingu. Ważny szczegół zapisany w `codex_inbox_hint`:
   **kanon spec-workflow nie leży w tym repo**, tylko w
   `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`.
   Prompty dla Codexa muszą podawać go ścieżką bezwzględną. `CME-MANIFEST.md` nie istnieje
   w żadnym z repo → audyt C/M/E nie jest blokerem (reguła 1), ale bramka strukturalna działa.
3. **Preflight L5** (`_review/R1-opus-preflight.md`) — 23 fakty nośne, bramka L5 PASS,
   C/M/E PASS, health-check PASS. Trzy fakty wyszły błędne i zostały **zmigrowane do speca**
   (v0.1 → v0.2, commit `739409b`):
   - styl separatora czytany z atrybutu **`data-divider-style`**, nie z gołego
     `div[data-divider]`; atrybut `style` niesie CSS, nie styl separatora;
   - `<svg>`/`<script>`/`<style>` przez **`decompose()`**, nie unwrap — zmierzone:
     `get_text()` na węźle separatora zwraca tekst z wnętrza SVG, który poleciałby do prozy
     jako chunk do redakcji;
   - sizing 490 → ~495 LOC (koszt powyższych).
4. **R1 review Codexa** (`_review/R1-codex.md`, commit `da332c0`) — **REQUEST_CHANGES**,
   11/11 kategorii, 8 blokerów + 5 major.

## Stan: pliki, commity

- `3e8a909` — kanon mostu (BRIEF, ODPOWIEDZ, HANDOFF) + spec md-export
- `739409b` — preflight R1 + dwie korekty konwertera + spec-config.json
- `da332c0` — R1 review Codexa
- `docs/specs/md-export/STATE.md` → `spec: R1-codex-pending` / `impl: not-started`.
  **Bump należy do `/spec-apply-review`, nie ruszać ręcznie.**
- `_review/.base-R1.md` — baseline pomiaru LOC dla self-fixu. Nie kasować.
- Codex **nie ruszył speca** (RC nie uprawnia do self-fixu) — spec jest w wersji 0.2, mojej.

## Co Codex znalazł — trzy rzeczy, które musisz znać przed apply

**Obalił mój własny preflight.** Uruchomił kontrpróbę na produkcyjnym `segmentuj.ts`
(Node 24 `--experimental-strip-types`, `EXIT=0`) i pokazał, że mój test T3 badał **własny
regex, nie język konsumenta**. Chunker rozpoznaje ponadto: fenced code (```` ``` ```` i `~~~`),
listę `cyfra)`, tabelę po `|` + linia separatora. Reguła escapingu ze speca nie neutralizuje
żadnego z tych trzech. Fixture trzeba wyprowadzić **z `segmentuj.ts`**, nie z głowy.

**Sizing liczy zły zbiór.** Master §4.5 liczy WSZYSTKIE pliki i linie, także testy. Z testami
to ~605 LOC i ≥6 plików przy limicie 500. Linia cięcia „gdy urośnie, odetnę UI" nie ratuje
bramki, bo wzrost jest widoczny już teraz, a odcięcie widoku do osobnej fazy jest decyzją
cross-fazową z denylisty — nie awaryjną decyzją implementatora.

**Dwa blokery, których nie widziałem, a są w kodzie:**
- rozdział bez `processed_html` jest legalnym stanem — `useChapters.js:177-212` ma fallback
  na `source_file_path` + `convertGoogleDocsHtml`. Endpoint czytający tylko `processed_html`
  taki rozdział zgubi.
- filtr „tylko zmienione" **nie ma przepływu danych**: frontend dostaje sam `Blob`,
  `authedFetch` nie wystawia nagłówków, nikt nie rozpakowuje ZIP-a w JS. Nie ma skąd wziąć
  hashy do localStorage. D2 wybrało miejsce przechowania, nie zaprojektowało przepływu.

## Czego właściciel jeszcze nie rozstrzygnął

Codex słusznie odmówił wyboru za Ciebie (guardrail 4.4b). Do decyzji przy `/spec-apply-review`:
- **D1** — nazwy plików ASCII czy z diakrytykami. Powiązane z blokerem 2: slug **tytułu**
  nie daje globalnej unikalności, bo dwa projekty mogą nazywać się tak samo. Potrzebny
  stabilny klucz książki.
- **D2** — czy filtr „tylko zmienione" zostaje w tej fazie (wtedy trzeba mu zaprojektować
  przepływ, np. osobna odpowiedź metadanych), czy wypada z zakresu. To także odpowiedź na
  część problemu sizingu.
- **O1** — `<br>` → `\n` czy spacja. **Przestało być otwarte:** `segmentuj.ts` jest dostępny,
  Codex go czytał, rozstrzygnąć na kodzie przed GREEN.

## NASTĘPNY KROK

`/spec-apply-review md-export` — przerobić 8 blokerów + 5 major, przy D1/D2 zapytać Piotrka.
MAX_ROUNDS = 2 przy Risk STANDARD, więc **została jedna runda** — R2 musi wyjść GREEN albo
spec idzie do ESCALATED.

## Wskaźniki do kanonów

- **Kanon ustaleń:** `docs/ODPOWIEDZ-most-tiolibri-redaktor.md` (sekcja ERRATA na górze)
- Brief (historyczny): `docs/BRIEF-most-tiolibri-redaktor.md`
- Spec: `docs/specs/md-export/SPEC-MD-EXPORT.md` v0.2
- Review: `docs/specs/md-export/_review/R1-codex.md`, preflight: `R1-opus-preflight.md`
- Kanon spec-workflow: **w FABRYCE**, `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`
- Kontrakt Redaktora: `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/docs/redaktor/KONTRAKT.md`
  (v1 — w dwóch miejscach odstaje od kodu, patrz ODPOWIEDZ B3)
- Chunker, na którym trzeba oprzeć fixture: `FABRYKA-redaktor` → `segmentuj.ts:12-16,58-129`

## Uwagi operacyjne

- **Codex ma dwa konta.** Pierwsze wyczerpało tygodniowy limit (reset 2026-08-08 08:47) —
  wisiało 50 minut z zerem wywołań narzędzi. Piotrek przelogował na drugie i przeszło.
  Gdy `codex exec` milczy dłużej niż kilka minut: sprawdź `used_percent` w najnowszym
  `~/.codex/sessions/**/rollout-*.jsonl`, zanim uznasz, że pracuje.
- `codex` nie jest w PATH sandboxa — wołać `/opt/homebrew/bin/codex`.
- Nie przepuszczać wyjścia `codex exec` przez `| tail` — buforuje wszystko do końca i nie
  widać postępu.

**Model docelowy: Opus.**
