# R2 — bramka kontraktowa G1–G4 po wdrożeniu (B′)

**Data:** 2026-08-07
**Zmiana wobec R1:** G3 stoi na **porównaniu literalnym**. Diagnostyczne `strip_em`, które
w R1 zdejmowało markery emfazy przed porównaniem, **usunięte z `harness/bramka_all.py`** —
to domyka Risk flag z `PROACTIVE-INBOX.md` (2026-08-07, Codex impl R1). `bramka.py` była
literalna od początku.

**Narzędzie:** prawdziwy `segmentuj()` z `FABRYKA-redaktor` (gałąź `redaktor`, HEAD `134f8e4`),
`node v24.12.0 --experimental-strip-types`. Wejście: **nasz własny `.md` wyjęty z ZIP-a
żywego endpointu** `POST /projects/{id}/export-md` na `127.0.0.1:8000`, oba warianty
(bez body → 12 rozdziałów; `chapter_ids` → rozdz. 8).

## Materiał wymagany przez spec — rozdz. 8 Ewy (210 chunków)

| # | Asercja | Tolerancja | R1 | R2 |
|---|---|---|---|---|
| G1 | rozkład typów chunków == `manifest.chapters[i].blocks` | zero | PASS | **PASS** |
| G2 | `blocks.kod == 0` ∧ `blocks.tabela == 0` ∧ zero chunków tych typów | zero | PASS | **PASS** |
| G3 | ciąg nagłówków `chunks.json` == ciąg `<h1..h6>` w HTML | zero | **FAIL** | **PASS** |
| G4 | żaden chunk nie jest frontmatterem ani metadanymi | zero | PASS | **PASS** |

**WERDYKT: PASS (4/4).**

- G1: `manifest = chunks = {naglowek: 30, akapit: 170, lista: 10, blockquote: 0, kod: 0, tabela: 0}`,
  typów spoza manifestu brak.
- G2: manifest `kod=0 tabela=0`, chunków `kod=0 tabela=0`.
- G3: `chunks=30`, `html=30`, pustych `<hN>` w HTML: 0, **pierwsza różnica: brak**.
- G4: podejrzanych chunków brak.

## Przebieg szeroki — 12/12 rozdziałów, 1141 chunków

```
poz | chunks | G1 | G2 | G3 | G4 | naglowki roznie/wszystkie
  1 |     57 | PASS | PASS | PASS | PASS | 0/9
  2 |    127 | PASS | PASS | PASS | PASS | 0/7
  3 |     73 | PASS | PASS | PASS | PASS | 0/23
  4 |     86 | PASS | PASS | PASS | PASS | 0/25
  5 |     63 | PASS | PASS | PASS | PASS | 0/22
  6 |     82 | PASS | PASS | PASS | PASS | 0/28
  7 |     80 | PASS | PASS | PASS | PASS | 0/27
  8 |     88 | PASS | PASS | PASS | PASS | 0/29
  9 |    210 | PASS | PASS | PASS | PASS | 0/30
 10 |     79 | PASS | PASS | PASS | PASS | 0/22
 11 |    141 | PASS | PASS | PASS | PASS | 0/28
 12 |     55 | PASS | PASS | PASS | PASS | 0/10

ZBIORCZO 12/12: G1=True G2=True G3=True G4=True
chunkow lacznie: 1141
```

**280 nagłówków, zero różnic wobec `get_text()` źródła.**

## Co odsłoniło zdjęcie maski — i dlaczego (B) urosło do (B′)

Pierwszy przebieg R2 **z samym (B)** (markery znikają tylko przy emfazie obejmującej całość)
dał **11/12**: rozdział 1 miał **1/9 nagłówków różny**. Sprawca, wyjęty z produkcji:

```html
<h1><img class="editor-image" src="https://…/1773427422941-wstep-0.png"/>WSTĘP:
<strong>Jak zaczęła się moja historia z osteoporozą.</strong></h1>
```

→ `# WSTĘP: **Jak zaczęła się moja historia z osteoporozą.**`

Emfaza nie obejmuje prefiksu „WSTĘP: ", więc wg (B) markery zostają — a to jest **ten sam
artefakt Google Docs** i **ta sama mina pod K-NAG** (nagłówek jest chunkiem edytowalnym,
`chunkuj.ts:13`), przed którą (B) miało chronić. W R1 ten nagłówek był niewidoczny, bo
diagnostyczne `strip_em` w harnessie zdejmowało markery po obu stronach porównania.

Decyzja właściciela z 2026-08-07: **(B′)** — w nagłówku żadnych markerów, także przy emfazie
częściowej. Po niej: 12/12, G3 literalne.

## Odtwarzalność

`harness/{chunkuj.mjs,bramka.py,bramka_all.py}`. Katalogi `gate/`, `gate_all/` i `chunks*.json`
**skasowane po przebiegu** — to rozpakowane ZIP-y, regenerowalne w minutę i nie mają wchodzić
do commita. Sekwencja: uvicorn `:8000` → JWT przez `admin/generate_link` → `auth/v1/verify` →
dwa `curl` na `/export-md` → `unzip` do `gate/` i `gate_all/` → `chunkuj.mjs` → `bramka.py`,
`bramka_all.py`.
