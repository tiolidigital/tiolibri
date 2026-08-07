**Temat:** eksport rozdziałów z TIOLIBRI do Markdown dla odsztuczniacza z FABRYKA-redaktor — bo Piotrek chce przepuścić gotowe książki przez Redaktora zamiast poprawiać AI-izmy ręcznie w edytorze

Wątek był ROBOTĄ: `/spec-apply-review md-export`. **Spec jest GREEN.** Strona SPEC zamknięta —
cztery rundy skończone, nic już do niej nie wraca. Zaczyna się strona IMPL.

> ⚠️ **Kanon ustaleń: `docs/ODPOWIEDZ-most-tiolibri-redaktor.md`** — nadrzędny wobec speca
> i wobec `docs/BRIEF-most-tiolibri-redaktor.md`. Nie projektuj z głowy, sprawdź tam.
> **Kanon konsumenta: `FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts`** (gałąź `redaktor`).
> HEAD gałęzi przy R3 to **`134f8e4`**. **Ten wskaźnik zestarzał się już dwa razy z rzędu**
> (R2 i R3) — sprawdź HEAD, zanim zaufasz kotwicom po numerach linii.

---

## NASTĘPNY KROK

**`/spec-impl md-export`** — implementacja, tryb light, R1.

W tym wątku NIE zaczęta: kontekst przekroczył próg dokładnie na granicy GREEN, a impl to
5 plików / ~582 LOC, czyli nowa duża jednostka pracy. Preflight `/spec-impl` startuje od zera.

**Czego się spodziewać w preflightcie (sprawdzone, nie zgadywane):**
- `spec: GREEN` / `impl: not-started` — stan zgodny, `_impl/` jest pusty, więc `N=1`.
- **`test_cmd` z `.claude/spec-config.json` to `cd tiolibri-api && source venv/bin/activate && pytest`,
  a `pytest` w tym venv NIE jest zainstalowany.** Spec każe `pip install pytest` lokalnie
  i **jawnie zabrania dopisywania go do `requirements.txt`** (§Plan wdrożenia pkt 1). To nie jest
  usterka configu — to świadoma decyzja speca. Nie „napraw" jej instalacją do requirements.
- `build_cmd` = `cd tiolibri-frontend && npm run build` (krok Build obowiązuje).
- Sizing ma **jawną dyspensę właściciela na LOC** z R1 (~82 LOC ponad limit); oś plików 5/5
  i oś czasu przechodzą bez dyspensy. Dyspensa obejmuje LOC, **nie liczbę plików** — szósty
  plik testowy zamieniłby oś plików w FAIL (dlatego sprawdzian endpointu jest ręczny, patrz niżej).

## Plan wdrożenia — cztery kroki, w tej kolejności

1. **`tiolibri-api/app/services/md_exporter.py`** + `tiolibri-api/test_md_exporter.py` —
   `chapter_to_markdown()`, `slugify()`, `sha256_nfc()`, `escape_line()`, dekodowanie `data:` URI.
   Fixture escapingu **wyprowadzony z `segmentuj.ts`**, nie z własnego regexu (to był bloker R1).
   Fixture `blocks` — jeden per konsekwencja, każdy asertuje **cały słownik**, nie pojedynczy klucz.
2. **`POST /projects/{project_id}/export-md`** w `export_import.py` — sygnatura **musi** być
   `request: Optional[ExportMdRequest] = None`. Po niej **ręczny sprawdzian czterech wejść body**
   na żywym backendzie `:8000` (tabela a–d w §Plan wdrożenia). Wariant (a) — POST **bez `-d`** —
   jest jedynym, który wykrywa brak `Optional` (200 vs 422); b–d przechodzą w obu wariantach.
   Wynik czterech wywołań (kod HTTP per wiersz) idzie do `_impl/`.
3. **Przycisk w `EditorPage.jsx`** ze stanami z §Frontend (double-submit lock, `aria-busy`,
   komunikat błędu). Modal i jego focus contract są **jawnie poza zakresem**.
4. **Bramka kontraktowa G1–G4 na żywym materiale** — jeden rozdział Ewy o osteoporozie,
   **najgęstszy od liczb i dawek, nie najłatwiejszy**. G1 rozkład typów chunków = `blocks`
   (zero tolerancji), G2 `kod` i `tabela` twarde zera, G3 ciąg nagłówków = `<h1..h6>` źródła,
   G4 zero chunków frontmatteru. `lista` jest w G1, **nie** w G2 — to była sprzeczność z R2.

## Co zrobione w tym wątku

Odebrane review R3 Codexa i przetworzone przez `/spec-apply-review`.

**Werdykt NITS.** Jedyny NIT był stale footerem speca (opisywał stan „po R1" i kierował do
`/spec-handoff`, mimo `R3-codex-pending`) — Codex poprawił go sam, **9 LOC**, jeden hunk,
zero zmian w kontrakcie produktu. Klasa uwagi wg L-C: **D**. Uwag klasy PRODUKT: **0**.

**Codex nie przyjął pomiarów preflightu na słowo — odtworzył je u siebie:** prawdziwy
`segmentuj()` na F1–F11 (`REAL_SEGMENTUJ_EXIT=0`), algorytm `blocks` ze speca `PASS=11 FAIL=0`,
sygnatura endpointu na `TestClient` `PASS=6 FAIL=0` z kontrpróbą bez `Optional`, bramki
`FACT 18/18` i `CME 8/8` obie `EXIT=0`. Potwierdził też wprost, że **cofnięta forma poprawki #2
domyka blokera R2**, a nie przenosi go gdzie indziej (rekord CONTRACTED bez pola `E`, typy
rozłączne) — o to był w promptcie zapytany imiennie.

**Blokery malały monotonicznie:** R2 = 3 blokery + 2 major + 1 ze sweepu → R3 = 0 blokerów,
1 NIT klasy D. Przedłużenie konwergencji przyznane w R2 zamknęło serię w rundzie, na którą
je przyznano — bez ESCALATED i bez briefu dla Fable.

**Zastrzeżenie nieblokujące Codexa zostawione bez zmiany w specu:** rekord
`preflight-R3-blocks-vs-prawdziwy-chunker` opisuje dwa przebiegi (Node + Python) w jednym
rekordzie, choć rygor „rekord per artefakt" sugerowałby rozdzielenie. Sam Codex warunkuje to
istnieniem kanonicznego `CME-MANIFEST.md`, którego w żadnym repo nie ma. Gdy kanon powstanie —
rozdzielenie jest jednolinijkowe.

**RETRO:** +1 wpis w FABRYCE (lektura pliku konsumenta ≠ uruchomienie go; kolejność gałęzi jako
część kontraktu, F10/F11 jako kontrpróba). Proactive drain: **0 obserwacji** — Codex napisał
`Brak proactive suggestions.`

## Stan: pliki, commity

- **`0cdff7e`** — R3 NITS → GREEN (ten wątek): self-fix Codexa w specu + `R3-opus-response.md`
  + STATE bump + logi przebiegu Codexa
- `94e6d93` — HANDOFF po handoffie R3
- `6ef6164` — spec v0.4.1 + preflight R3
- `docs/specs/md-export/STATE.md` → **`spec: GREEN`** / `impl: not-started` /
  `rundy-rdzenia: 0` / `convergence-ext: R2`
- `docs/specs/md-export/_impl/` — **pusty**, `N=1` przy starcie
- `_review/R3-codex.md` + `R3-opus-response.md` — komplet rundy R3
- `_review/.base-R3.md` — baseline R3, **nie kasować** (mierzył LOC self-fixu Codexa)

**Niezacommitowane w worktree:** tylko `.DS_Store` (dwa) — świadomie pominięte.

RETRO w FABRYCE (drain z R1 + nowy wpis z R3) wciąż **niezacommitowane**, leży w
`/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/RETRO.md`.

## Wskaźniki do kanonów

- Spec: `docs/specs/md-export/SPEC-MD-EXPORT.md` **v0.4.1**, `spec: GREEN`
- Rundy: `_review/R{1,2,3}-codex.md` + `R{1,2,3}-opus-*.md` (preflight R3 ma §Parser self-test
  z tabelą 11 fixture'ów i §Audyt C/M/E z 8 rekordami — najgęstszy dokument tej serii)
- Kanon spec-workflow: **w FABRYCE**,
  `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`
- Kontrakt Redaktora: `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/docs/redaktor/KONTRAKT.md`
  (v1 — w dwóch miejscach odstaje od kodu, patrz ODPOWIEDZ B3)

## Uwagi operacyjne

- **Prawdziwy `segmentuj()` da się odpalić w sandboxie** — Node v24.12.0,
  `node --experimental-strip-types`, import po ścieżce bezwzględnej z FABRYKA-redaktor.
  Ostrzega o `MODULE_TYPELESS_PACKAGE_JSON`, ale działa. To najtańszy sposób rozstrzygnięcia
  każdego sporu o to, jak konsument dzieli tekst — i przy G1 z zerową tolerancją będzie
  potrzebny w kroku 4.
- **`tiolibri-api/venv` ma `httpx` 0.27.2**, więc `fastapi.testclient` działa bez instalacji.
  `pytest` trzeba doinstalować lokalnie — **bez dopisywania do `requirements.txt`**.
- **Codex ma dwa konta.** Pierwsze wyczerpało tygodniowy limit (reset **2026-08-08 08:47** —
  czyli już minął, jeśli czytasz to później). Gdy `codex exec` milczy dłużej niż kilka minut:
  sprawdź `used_percent` w najnowszym `~/.codex/sessions/**/rollout-*.jsonl`, zanim uznasz,
  że pracuje.
- `codex` nie jest w PATH sandboxa — wołać `/opt/homebrew/bin/codex`.
- Nie przepuszczać wyjścia `codex exec` przez `| tail` — buforuje do końca, nie widać postępu.

**Model docelowy: Opus.**
