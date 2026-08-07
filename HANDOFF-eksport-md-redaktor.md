**Temat:** eksport rozdziałów z TIOLIBRI do Markdown dla odsztuczniacza z FABRYKA-redaktor — bo Piotrek chce przepuścić gotowe książki przez Redaktora zamiast poprawiać AI-izmy ręcznie w edytorze

Wątek był ROBOTĄ: `/spec-apply-review md-export`. R1 przerobione, spec w v0.3, STATE zbumpowany.
**Runda R2 NIE została odpalona** — wątek uciął się na progu kontekstu, nie na problemie.

> ⚠️ **Kanon ustaleń: `docs/ODPOWIEDZ-most-tiolibri-redaktor.md`** — nadrzędny wobec speca
> i wobec `docs/BRIEF-most-tiolibri-redaktor.md`. Nie projektuj z głowy, sprawdź tam.
> **Kanon konsumenta: `FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts`** — reguła escapingu
> w specu jest przepisana z jego sześciu regexów (`:12-17`). Nie zmieniaj jej bez zajrzenia tam.

---

## Co zrobione w tym wątku

1. **Przerobione wszystkie 13 uwag Codexa** (8 blokerów + 5 major) → spec v0.2 → **v0.3**,
   673 zmienione linie. Ślad decyzja-po-decyzji: `_review/R1-opus-response.md`.
2. **Trzy decyzje właściciela zamknięte** (AskUserQuestion, wszystkie wg rekomendacji):
   - **Zakres** → modal z wyborem rozdziałów i filtr „tylko zmienione" **odcięte**; zostaje
     przycisk „Eksportuj do Redaktora (.md)" pobierający całą książkę. Sizing: **DYSPENSA**
     ~567/500 LOC ze źródłem autoryzacji wpisanym w nagłówek speca.
   - **Klucz książki** → `book_key = slug(tytuł)-<8 hex z project_id>`. Sam slug tytułu nie dawał
     globalnej unikalności wymaganej przez ODPOWIEDZ B2.
   - **Filtr zmian** → wypada z tej fazy (nie miał przepływu danych).
3. **Escaping przepisany z produkcyjnego chunkera.** To była najcenniejsza uwaga rundy: mój
   preflight T3 badał własny regex, nie język konsumenta. `segmentuj.ts` rozpoznaje ponadto
   fenced code, listę `cyfra)` i tabelę. Efekt uboczny: reguła wyszła **węższa** od zgadywanej —
   `#hasztag` i `-myślnik` nie są strukturą (regexy wymagają białego znaku) i nie dostają
   backslasha.
4. **O1 zamknięte na kodzie.** `<br>` → `\n` zostaje (`segmentuj.ts:142` — pojedynczy newline nie
   rozbija akapitu), ale **escaping musi objąć KAŻDĄ linię bloku**, nie tylko pierwszą. v0.2
   escape'owała tylko początek bloku i to był ukryty bloker, którego nikt nie zgłosił.
5. **Drain proactive:** Workflow → `RETRO.md` w FABRYCE (EOF-append, bez anchora — LESSONS#10);
   Risk flag → `docs/specs/md-export/PROACTIVE-INBOX.md`.

## Czego Codex nie miał, a znalazłem przy okazji

- **`pytest` nie jest w `requirements.txt` ani w `tiolibri-api/venv`** (`bs4` i `lxml` **są** —
  ta część speca była prawdziwa). Spec ustala: `pip install pytest` lokalnie, plik testowy
  w korzeniu `tiolibri-api/` obok istniejącego `test_polish_pdf.py`, **bez dopisywania do
  `requirements.txt`** (chudy obraz Railway, zero rippla zależności, zero szóstego pliku).
- **`authedFetch` obsługuje błędy przy `responseType: 'blob'`** — sprawdza `res.ok` i rzuca
  `Error(err.detail)` **przed** gałęzią blobową (`lib/authedFetch.js:30` vs `:33`). Czyli 409/413
  z endpointu będą widoczne w UI bez zmian w `authedFetch`.
- **Tie-breaker sortowania to `order("id")`, nie `created_at`** — kolumny `created_at`
  w `chapters` **nie potwierdziłem** (`chapters.py:211` jej nie selektuje). LESSONS#20.
- **`Modal.jsx` istnieje**, ma Escape (`:64-80`) i klik w overlay (`:87-90`), ale **nie ma focus
  trapu, nie przywraca focusu i nie ma `role="dialog"`/`aria-modal`**. Zapisane w specu jako
  notatka dla przyszłego speca modala, żeby descope tego nie zgubił.

## Stan: pliki, commity

- `cfda3ce` — **spec v0.3 + R1-opus-response + PROACTIVE-INBOX + STATE bump** (ten wątek)
- `da332c0` — R1 review Codexa (REQUEST_CHANGES)
- `739409b` — preflight R1 + dwie korekty konwertera
- `3e8a909` — kanon mostu (BRIEF, ODPOWIEDZ) + spec md-export
- `docs/specs/md-export/STATE.md` → **`spec: R1-opus-pending`** / `impl: not-started`.
  To jest stan, z którego `/spec-handoff` wylicza TARGET=R2. **Nie bumpować ręcznie.**
- `_review/.base-R1.md` — baseline pomiaru. Nie kasować.
- RETRO w FABRYCE zmienione poza tym repo — **niezacommitowane**, leży w
  `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/RETRO.md`.

## NASTĘPNY KROK

`/spec-handoff md-export` — wygeneruje prompt R2 i doręczy go Codexowi.

**Budżet: to ostatnia runda.** MAX_ROUNDS=2 przy Risk STANDARD, N_EFF=1 zużyte. R2 musi wyjść
GREEN (albo NITS/NITS-EXT), inaczej spec idzie do ESCALATED i wchodzi ścieżka z briefem dla Fable.

Konwergencja: jeśli R2 wróci REQUEST_CHANGES, ale **blokery wyraźnie maleją**, przysługuje
jednorazowe przedłużenie o jedną rundę (`convergence-ext`) — warunki w `/spec-apply-review`
Krok 6. `rundy-rdzenia` = 0, więc przedłużenie jest dostępne.

## Wskaźniki do kanonów

- **Kanon ustaleń:** `docs/ODPOWIEDZ-most-tiolibri-redaktor.md` (sekcja ERRATA na górze)
- **Kanon konsumenta:** `FABRYKA-redaktor` → `src/redaktor/chunker/segmentuj.ts:12-17` (regexy),
  `:142` (kontynuacja akapitu), `:20` (`INDENT_MIN=2`), `:91` (warunek tabeli)
- Spec: `docs/specs/md-export/SPEC-MD-EXPORT.md` **v0.3**
- Odpowiedź na review: `_review/R1-opus-response.md`; review Codexa: `_review/R1-codex.md`
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

**Model docelowy: Opus.**
