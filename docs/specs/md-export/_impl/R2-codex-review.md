## Werdykt

**Werdykt:** APPROVE

## Co działa / Co wymaga zmiany

Oba blokery R1 są domknięte. Rozszerzenie **(B) → (B′)** akceptuję: nie jest arbitralnym
odejściem od review, lecz naprawą kontraktu po literalnym pomiarze G3 na całej książce.
Wariant (B) zostawiał realny nagłówek z częściową emfazą i wynik 11/12; (B′) usuwa markery
wyłącznie w `<h1>`…`<h6>`, zachowuje emfazę w akapitach, listach i blockquote oraz daje
literalne G3 = 12/12 (280 nagłówków, zero różnic). Spec 0.4.2 zapisuje wyjątek, odrzucenie
wariantu (A), dowód produkcyjny i decyzję właściciela, więc implementacja i kontrakt są spójne.

Testy pełnej i częściowej emfazy obejmują kształt z produkcji, lokalną równość z `get_text()`,
brak markerów w nagłówku i regresje emfazy poza nagłówkiem. Harness szeroki nie zawiera już
diagnostycznego `strip_em`, zatem nie maskuje `_` ani `*`; wkład, który wcześniej dawał FAIL,
jest udokumentowany. To odpowiada LESSONS#13: bramka ma rzeczywistą kontrpróbę, a ścieżka
fallbacku parsera ma osobny test potwierdzający faktyczne przełączenie narzędzia.

Sizing ma teraz jawną decyzję właściciela obejmującą zmierzone ~1307 LOC churn, pięć plików
implementacji i dokładnie 162 przypadki testowe. Tym samym drugi bloker R1 nie pozostaje
domyślną zgodą recenzenta, tylko udokumentowaną dyspensą właściciela zgodnie z LESSONS#17.

### Kryteria, edge cases i regresja

- [x] **Build:** `cd tiolibri-frontend && npm run build` — PASS, exit 0.
- [x] **Testy (baseline-relatywnie):** fail@teraz = {`test_polish_pdf.py` — collection error:
  brak `libgobject-2.0-0`}; fail@HEAD = ten sam zbiór. Zatem fail@teraz ⊆ fail@HEAD.
  `pytest -q test_md_exporter.py` = **162 passed** (+162 przypadki fazy).
- [x] **Scope discipline:** pięć plików implementacji odpowiada specowi; untracked
  `md_exporter.py` i `test_md_exporter.py` przeczytane w całości. Artefakty `_impl/harness/`
  są wymaganym dowodem bramki. Niezwiązane `.DS_Store` i pliki robocze nie należą do commita.
- [x] **Kolejność rejestracji routerów:** `export_import`, `snapshots`, potem `projects`.
- [x] **supabase-py:** nie dodano `.select()` po `.update().eq()`.
- [x] **TipTap:** brak nowego `this.editor` i brak zmian w `addProseMirrorPlugins()`.
- [x] **Bez over-engineeringu:** parametr `emphasis=False` jest lokalnym wyjątkiem nagłówka;
  testy parytetu wyznaczają granicę fallbacku bez nowej abstrakcji ani zależności.
- [x] **G1–G4:** wymagany rozdział Ewy PASS 4/4; przebieg szeroki PASS na 12/12 rozdziałów
  i 1141 chunkach, z literalnym G3.

Brak wymaganych zmian.

## Proactive suggestions (rzeczy o które nie pytano)

- **Workflow:** przy commicie trzeba selektywnie pominąć trackowane `.DS_Store`; `.gitignore`
  nie usunie już śledzonych plików.
- **Risk flag:** harness zależy od bezwzględnej ścieżki do checkoutu Redaktora i żywych danych;
  dowód jest odtwarzalny w obecnym środowisku, ale nie jest przenośnym testem CI.

---

## Dla Piotrka — jedno zdanie

(B′) jest uzasadnione pomiarem: G1–G4 przechodzi na 12/12 rozdziałów, 162 testy i build są zielone, a oba blokery R1 są zamknięte.

**Kopiuj dalej — w tym samym wątku:**
```
/spec-apply-impl-review md-export
```
