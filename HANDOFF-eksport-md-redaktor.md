**Temat:** eksport rozdziałów z TIOLIBRI do Markdown dla odsztuczniacza z FABRYKA-redaktor — bo Piotrek chce przepuścić gotowe książki przez Redaktora zamiast poprawiać AI-izmy ręcznie w edytorze

Wątek był ROBOTĄ: **spec md-export DOMKNIĘTY**. Codex dał APPROVE na R2, faza zacommitowana
i **wypchnięta na produkcję**. `STATE: spec GREEN / impl merged`. Cykl workflow skończony.
**Klik-test na produkcji WYKONANY 2026-08-07 — most działa, zero zgrzytów w md-export.**

> ⚠️ **Kanon ustaleń: `docs/ODPOWIEDZ-most-tiolibri-redaktor.md`** — nadrzędny wobec speca.
> **Kanon konsumenta: `FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts`** (gałąź `redaktor`,
> HEAD `134f8e4`).

---

## NASTĘPNY KROK

**Po stronie TIOLIBRI nic nie czeka — most odebrany.** Otwarte są dwie rzeczy, obie
decyzją właściciela, żadna nie blokuje:

1. **Tytuły rozdziałów w bazie są zmielone** (`'ROZDZIA1OsteoporozacotooznaczadlaTwojego…'`,
   `'ZAKOCZENIECoteraz2.0'` — bez polskich znaków i spacji, z doklejonym „REGEX"). Przez to
   nazwy plików w ZIP-ie są nieczytelne. **To NIE defekt md-export** — eksporter przepuszcza
   `chapters.title` wiernie (`export_import.py:251`), a H1 w treści jest poprawny. Wada
   kosmetyczna: `chapter_id` w manifeście jest prawdziwym kluczem powrotu, nazwy są unikalne
   i stabilne. **Rekomendacja: NIE zakładać speca** — poprawić 12 + 24 tytuły ręcznie
   w edytorze (rename rozdziału istnieje w context menu ChapterList) i nazwy zrobią się
   ładne same.
2. **`.DS_Store`** — patrz „Stan" niżej, decyzja nietknięta.

Dalszy ciąg mostu leży już **po stronie Redaktora**, nie TIOLIBRI: żeby dostać listę
poprawek zamiast listy podejrzeń, trzeba puścić W2 na transporcie plikowym
(`src/redaktor/cli/wypelnij-skrzynke.ts` — istnieje, ma flagi czystości z werdyktu).
To repo ma własny następny krok (`/spec-commit`).

## Klik-test na produkcji — wynik (2026-08-07 20:06)

**Deploy potwierdzony:** `api.tiolibri.com` wystawia `/projects/{id}/export-md` (OpenAPI),
bundel `app.tiolibri.com/assets/index-oyUg5WAw.js` zawiera wywołanie. Railway + Vercel
przebudowały z `165e713`.

**Eksport z żywej apki — obie książki, HTTP 200, `application/zip`:**

| książka | ZIP | zawartość |
|---|---|---|
| Ewa / osteoporoza | 94 808 B | 12 × .md + manifest |
| Bożena / grzyby | 270 325 B | 24 × .md + manifest |

Manifest kompletny (`format/version/project_id/book_key`, per rozdział `chapter_id`,
`hash sha256`, `chars`, liczniki bloków, obrazki). Treść .md czysta — H1, obrazek, akapity,
polskie znaki nietknięte.

**Przepuszczone przez odsztuczniacz** (`redaktor run --tylko-w1`, zero kosztu API):

```
Ewa      1141 chunków,  36 edycji   ← 1141 zgadza się CO DO JEDNEGO z bramką R2
Bożena   2634 chunków, 161 edycji
status raport-gotowy 36/36 · kanarki (D,N) PASS 36/36 · budżet OK 36/36
najwyższy budżet 0,257 % przy limicie 8 %
```

Zgodność 1141 chunków z lokalną bramką R2 to **dowód parytetu produkcja ↔ odbiór**.
Znalezione sztuczności: `KLU` 127×, `PUS` 47×, `WAC` 18×, `STA` 5×.

⚠️ **Te 47 usunięć PUS nie jest gotowe do hurtu.** Mają `propozycja: ""`, ale klauzula
RULEBOOK-a „Nie ruszać gdy przymiotnik ma pokrycie treściowe" należy do W2, którego nie
puszczano. Sprawdzone na rozdziale 1 Ewy: **3 z 3 wycięć słowa „kompleksowe" to fałszywe
trafienia** (tekst zaraz wylicza, na czym kompleksowość polega; nagłówek „Kompleksowość
leczenia." został, bo regex łapie przymiotnik, nie rzeczownik). Bez W2 Redaktor produkuje
**listę podejrzeń, nie listę poprawek**.

Wyjście przebiegów: `FABRYKA-redaktor/redaktor/praca/{ewa,boz}-NN/<run-id>/` — katalog jest
gitignorowany (`/redaktor/*`), repo Redaktora niezabrudzone.

## Co zrobione w tym wątku

1. **Doręczono Codexowi impl review R2** (`codex exec -s workspace-write`, łącznik działa).
   W promptcie jawnie nazwane odstępstwo **(B) → (B′)** od jego własnego werdyktu R1.
2. **Werdykt: APPROVE**, `_impl/R2-codex-review.md`. Codex zaakceptował (B′) wprost —
   „nie arbitralne odejście, lecz naprawa kontraktu po literalnym pomiarze G3". Sizing
   przeszedł jako udokumentowana dyspensa właściciela, nie milcząca zgoda recenzenta.
   Zero wymaganych zmian, zero self-fixu.
3. **`/spec-apply-impl-review`** — walidator i parser czyste (1 linia werdyktu), drain
   proactive: Workflow → RETRO, Risk flag (harness nieprzenośny do CI) → PROACTIVE-INBOX.
   ZADANIE KOŃCOWE → RETRO: helper `filter_and_append_retro` ma `retro_file` jako ścieżkę
   **względną**, więc w repo z kanonem poza repo (jak TIOLIBRI) obserwacja ginie po cichu.
   Fix należy do factory-kit. STATE → `ready-to-commit`.
4. **`/spec-commit`** — bramka sekretów czysta (43 pliki), brud poza scope wyłącznie klasy 1.
   Dwa commity + push.

## Stan: pliki, commity

- **HEAD: `165e713`** (`chore(md-export): STATE -> merged`), przed nim **`c9e19f7`**
  (`feat(md-export): …`, 23 pliki, +2387 −26). **Wypchnięte na `origin/main`** razem
  z 9 zaległymi commitami ze starszych wątków — repo jest w sync.
- Hook repo doszył do obu commitów `tiolibri-frontend/package.json` (auto-bump wersji
  1.0.24 → 1.0.26). Legalne, nie ruszać.
- **Niezacommitowane, świadomie (klasa 1):** `.DS_Store` (dwa, *tracked*),
  `HANDOFF-eksport-md-redaktor.md` (ten plik).
- **`.DS_Store` — otwarta decyzja właściciela:** `git rm --cached .DS_Store docs/.DS_Store`
  zdjęłoby je z repo na stałe. Do tej pory były pomijane ręcznie przy każdym commicie fazy.
- **RETRO w FABRYCE — niezacommitowane** (inne repo): 3 nowe wpisy z tego wątku + METR
  `md-export/root/c9e19f7` (spec=3, impl=2, total=5, LOC 2387+26, KOSZT-WYSOKI=TAK)
  + wpisy z wcześniejszych wątków:
  `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/RETRO.md`

## Wskaźniki do kanonów

- Spec: `docs/specs/md-export/SPEC-MD-EXPORT.md` **v0.4.2** (zamknięty)
- STATE: `docs/specs/md-export/STATE.md` — `spec: GREEN` / `impl: merged (c9e19f7)`
- Księga fazy: `_impl/COMMIT-LOG.md`; review zamykające: `_impl/R2-codex-review.md`
- Dowód bramki: `_impl/R2-bramka-G1-G4.md` (12/12 rozdziałów, 1141 chunków, 280 nagłówków,
  0 różnic); harness: `_impl/harness/{chunkuj.mjs,bramka.py,bramka_all.py}`
- Kanon spec-workflow: **w FABRYCE**,
  `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`
- Projekty w bazie: Ewa/osteoporoza — `d73dcc3b-74ed-4d23-8cbb-d600c8f5306f`
  („Kości Na Całe Życie 4.0", 12 rozdziałów, użyty do bramki); Bożena/grzyby —
  `507b3ee4-a07d-4a69-b6a8-f88b53dc2ba6`

## Uwagi operacyjne

- **Odtworzenie bramki:** uvicorn `:8000` (venv, `PYTHONPATH="$PWD"`) → JWT przez
  `admin/generate_link` → `auth/v1/verify` → dwa `curl` POST na `/projects/{id}/export-md`
  → `unzip` → `chunkuj.mjs` → `bramka.py`, `bramka_all.py`.
- **Odtworzenie klik-testu na produkcji:** to samo, ale bez uvicorna — `curl` leci wprost
  na `https://api.tiolibri.com`. ⚠️ `hashed_token` z `admin/generate_link` leży w tej
  instancji GoTrue **na top-level odpowiedzi, nie w `properties`** (`r["properties"]` =
  `KeyError`). Potem: `npx tsx src/redaktor/cli/run.ts run --config
  redaktor/config/ebook-{ewa,bozena}.yaml --input <plik.md> --tylko-w1` z roota
  FABRYKA-redaktor.
- **NIE proponować płatnego przebiegu W2 / doładowania kredytu API** — decyzja D10
  „maszyna-first" zabetonowana (`FABRYKA-redaktor/docs/redaktor/00-USTALENIA.md:144-146`),
  potwierdzona werdyktem `docs/fable5-consult/21-VERDICT-transport-goldena-subskrypcja.md:80`.
  Budżetu w tym temacie NIE liczyć z `HANDOFF-api-koszt.md` — to archiwum sprzed
  rozstrzygnięcia, jego liczby są martwe.
- **Łącznik Codex CLI działa** (`/opt/homebrew/bin/codex`, 0.144.6). Nie przepuszczać
  wyjścia `codex exec` przez `| tail`.
- **`filter_and_append_retro` wymaga nadpisania `retro_file`** ścieżką bezwzględną do
  FABRYKI — inaczej drain po cichu nic nie zapisze (zgłoszone do RETRO, fix w factory-kit).
- **TIOLIBRI nie jest w koncie Supabase podpiętym przez MCP** — do bazy przez klienta
  z `tiolibri-api/.env`.

**Model docelowy: Opus.**
