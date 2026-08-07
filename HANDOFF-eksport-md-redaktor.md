**Temat:** eksport rozdziałów z TIOLIBRI do Markdown dla odsztuczniacza z FABRYKA-redaktor — bo Piotrek chce przepuścić gotowe książki przez Redaktora zamiast poprawiać AI-izmy ręcznie w edytorze

Wątek był ROBOTĄ: `/spec-handoff md-export`. Preflight R2 domknięty, spec w v0.3.1,
STATE zbumpowany, **prompt R2 doręczony Codexowi — review pisze się w tle**.

> ⚠️ **Kanon ustaleń: `docs/ODPOWIEDZ-most-tiolibri-redaktor.md`** — nadrzędny wobec speca
> i wobec `docs/BRIEF-most-tiolibri-redaktor.md`. Nie projektuj z głowy, sprawdź tam.
> **Kanon konsumenta: `FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts`** (gałąź `redaktor`,
> HEAD `d7087bd`; plik bajtowo identyczny z cytowanym `4ebec8c`). Reguła escapingu jest
> przepisana z jego sześciu regexów `:12-17`. Nie zmieniaj jej bez zajrzenia tam.
> **Trzeci dokument, młodszy od ODPOWIEDZI:** `FABRYKA-redaktor/docs/redaktor/kalibracja/ZWIAD-EWA-R8.md`
> (commit `5a4fd8e`) — źródło liczb `3,44×` i `215 chunków`. Wciągnięte do speca w tej rundzie.

---

## NASTĘPNY KROK

**Sprawdź, czy `docs/specs/md-export/_review/R2-codex.md` już istnieje, i odpal `/spec-apply-review md-export`.**

Codex został odpalony w tle (`nohup`, PID zapisany w logu) o 16:2x, model `gpt-5.6-sol`:

```bash
tail -5 docs/specs/md-export/_review/.R2-codex-run.log     # postęp
test -s docs/specs/md-export/_review/R2-codex.md && echo GOTOWE
rg -c '^\**Werdykt:\**\s*(APPROVE|NITS-EXT|NITS|REQUEST_CHANGES)\**\s*$' docs/specs/md-export/_review/R2-codex.md   # oczekiwane: 1
```

- Plik jest, werdykt parsowalny → `/spec-apply-review md-export`.
- Pliku brak, ale `.R2-codex-last-msg.md` niesie pełne review → zapisz jego treść jako
  `R2-codex.md` i odnotuj „odzyskane z last-message".
- Codex padł / limit konta → prompt leży gotowy w `_review/.R2-prompt.md`, odpal ponownie:
  `/opt/homebrew/bin/codex exec -s workspace-write -C "$PWD" -o _review/.R2-codex-last-msg.md - < docs/specs/md-export/_review/.R2-prompt.md`
- Linii werdyktu 0 albo >1 → **nie naprawiaj sam**, pokaż Piotrkowi (footer wariant C).

**Budżet: to ostatnia runda.** MAX_ROUNDS=2 przy Risk STANDARD, N_EFF=1 zużyte. R2 musi wyjść
GREEN (albo NITS/NITS-EXT), inaczej spec idzie do ESCALATED i wchodzi ścieżka z briefem dla Fable.
Konwergencja: jeśli R2 wróci REQUEST_CHANGES, ale **blokery wyraźnie maleją**, przysługuje
jednorazowe przedłużenie o rundę (`convergence-ext`) — warunki w `/spec-apply-review` Krok 6.
`rundy-rdzenia` = 0, więc przedłużenie jest dostępne.

## Co zrobione w tym wątku

1. **Preflight R2 (L5)** — `_review/R2-opus-preflight.md`, 29 faktów, obie bramki komendy
   uruchomione i PASS (`invalid=0 blocked=0 corrected=5 malformed=0 migrated_missing=0`;
   C/M/E `valid=6 dup=0 fail=0`).
2. **Parser self-test escapingu** — `PASS=78 FAIL=0` na regexach **przepisanych z produkcyjnego
   `segmentuj.ts` w tej rundzie**, nie z głowy: 68 przypadków pozytywnych (17 wzorców ×
   wcięcia 0-3) + **10 negatywnych**, które muszą zostać nietknięte. Wyszło m.in., że `1)`
   jest markerem listy (reguła v0.2 by go przepuściła).
3. **Pięć korekt wpisanych do speca** (v0.3 → **v0.3.1**), każda zmierzona:
   - **`Optional[...]` zamiast `X | None`** — venv to **Python 3.9.6**, produkcja **3.11**
     (`Dockerfile:2`). PEP 604 wywala `TypeError` **przy imporcie modułu**, więc testy z kroku 1
     planu były nieuruchamialne lokalnie, mimo że produkcja by ruszyła. Cichy bloker.
   - **SHA kanonu konsumenta** `4ebec8c` → `d7087bd` (plik bajtowo identyczny, sprawdzone
     `git diff`) — stale-ref klasy LESSONS#20.
   - **`3,44×` zamiast `~3×`** — zaniżenie mianownika strażnika budżetu, zmierzone na
     rozdziale Ewy: `0,0120%` z blobem vs `0,0412%` bez (`ZWIAD-EWA-R8.md`, dwa run-idy).
   - **215 chunków dla rozdziału Ewy** — spec pisał „nie mamy przedziału". Mamy, i jest
     o rząd wielkości większy od 27 Bożeny. Wniosek dla operatora: setki cykli
     stop-wypełnij-wznów, nie trzydzieści.
   - **Drugi tryb awarii bloba** — chunker nadaje data-URI `nietykalny=false`, więc bez
     naszego wycięcia ~21k tokenów base64 poleciałoby do modelu; Redaktor nie ma na to
     strażnika. Nasz eksport jest jedynym miejscem, w którym to się zatrzymuje.
4. **Zweryfikowane kotwice v0.3, wszystkie trafiają** — `segmentuj.ts:20/91/100-105/118-125/142`,
   `Divider.js:14,17,84`, `authedFetch.js:28-33`, `export_import.py:238`, `chapters.py:211`,
   `useChapters.js:184-209`, `ChapterEditor.jsx:60-62`, `Modal.jsx:64,87-90`,
   `ProjectCard.jsx:197-209`.
5. **Tie-breaker sortowania potwierdzony wykonaniem** — dwa `.order()` w supabase-py sklejają
   się w `order=sort_order%2Cid` (builder odpalony bez sieci), drugie nie nadpisuje pierwszego.

## Stan: pliki, commity

- `b502702` — **spec v0.3.1 + preflight R2 + baseline + STATE bump + prompt** (ten wątek)
- `7a7dec1` — HANDOFF po R1
- `cfda3ce` — spec v0.3 po R1
- `docs/specs/md-export/STATE.md` → **`spec: R2-codex-pending`** / `impl: not-started`.
  **Nie bumpować ręcznie** — zrobi to `/spec-apply-review`.
- `_review/.base-R2.md` — baseline pomiaru LOC dla ewentualnego NITS-EXT Codexa. **Nie kasować.**
- `_review/.R2-prompt.md` — prompt doręczony, do ponownego odpalenia gdyby Codex padł.
- `_review/.R2-codex-run.log`, `.R2-codex-last-msg.md` — artefakty diagnostyczne, niezacommitowane.

## Wskaźniki do kanonów

- Spec: `docs/specs/md-export/SPEC-MD-EXPORT.md` **v0.3.1**
- Preflight tej rundy: `_review/R2-opus-preflight.md`; R1: `_review/R1-codex.md` + `R1-opus-response.md`
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
