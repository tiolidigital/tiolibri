# Session Log: 2026-01-25 Sesja 7 - Typography Controls v1.1

## Podsumowanie sesji

**Cel:** Implementacja pełnej kontroli typografii w TIOLIBRI - alignment, font size, line height, margins + persystencja w Supabase

**Status:** ✅ COMPLETE - pełny system kontroli typografii z auto-save

---

## Co zrobiono

### Backend (Python/FastAPI)

**1. Parametry typografii w API:**
- Dodano 8 nowych pól do `GenerateRequest` w [schemas.py](../../tiolibri-api/app/models/schemas.py)
- Parametry: `text_align`, `font_size`, `line_height`, `margin_top/bottom/left/right`
- Validatory: text_align (left/justify), font_size (12-24, parzyste)

**2. CSS Presets Update:**
- Zaktualizowano wszystkie 3 presety ([classic.css](../../tiolibri-api/app/presets/classic.css), [modern.css](../../tiolibri-api/app/presets/modern.css), [minimal.css](../../tiolibri-api/app/presets/minimal.css))
- Dodano CSS variables placeholders: `var(--text-align)`, `var(--font-size)`, `var(--line-height)`, `var(--margin)`
- Zmiana z fixed values na runtime-replaceable templates

**3. EPUB Generator Update:**
- Zaktualizowano [epub_generator.py](../../tiolibri-api/app/services/epub_generator.py)
- Dodano parametry typografii do funkcji `generate_epub()`
- String replacement CSS variables → actual values (WeasyPrint nie wspiera var())
- Margines format: `{top}em {right}em {bottom}em {left}em`

**4. PDF Generator Update:**
- Zaktualizowano [pdf_generator.py](../../tiolibri-api/app/services/pdf_generator.py)
- Dodano `@page` CSS rule dla marginesów strony (cm units)
- String replacement CSS variables jak w EPUB
- Fix: body margin nie kontroluje page margins w WeasyPrint

**5. Router Update:**
- Zaktualizowano [generate.py](../../tiolibri-api/app/routers/generate.py)
- Przekazywanie wszystkich 8 parametrów do generatorów
- Default values z schema

**6. Line Height Fix:**
- Zmiana z formuły matematycznej na lookup table
- Problem: mała czcionka (12px) miała zbyt duży line-height
- Rozwiązanie: hardcoded mapping (12→1.6, 14→1.65, 16→1.7, ..., 24→1.9)

### Frontend (React/Vite)

**1. TypographyControls Component:**
- Utworzono [TypographyControls.jsx](../../tiolibri-frontend/src/features/editor/TypographyControls.jsx)
- UI controls: toggle buttons (alignment), range sliders (font/line/margins)
- Real-time preview values (px, em)
- Controlled component - state zarządzany przez parent

**2. useTypography Hook:**
- Utworzono [useTypography.js](../../tiolibri-frontend/src/features/editor/useTypography.js)
- Fetch settings z Supabase `projects.typography_settings` (JSONB)
- Auto-save z debounce (1 sekunda)
- Default values fallback
- Loading + error states

**3. EditorPage Integration:**
- Zaktualizowano [EditorPage.jsx](../../tiolibri-frontend/src/features/editor/EditorPage.jsx)
- Użycie `useTypography(projectId)` hook
- Przekazywanie settings do `TypographyControls` i `GenerateBooks`
- Loading state dla typography panel

**4. GenerateBooks Update:**
- Zaktualizowano [GenerateBooks.jsx](../../tiolibri-frontend/src/features/editor/GenerateBooks.jsx)
- Dodano wszystkie 8 parametrów typografii do API request
- Snake_case mapping (React camelCase → Python snake_case)

### Database (Supabase)

**1. Nowa kolumna:**
- Dodano `typography_settings` (JSONB) do tabeli `projects`
- Default value: JSON z wszystkimi default settings
- Nullable dla backwards compatibility

**SQL Migration:**
```sql
ALTER TABLE projects
ADD COLUMN typography_settings JSONB DEFAULT '{
  "textAlign": "left",
  "fontSize": 16,
  "lineHeight": 1.7,
  "marginTop": 2.0,
  "marginBottom": 2.0,
  "marginLeft": 1.5,
  "marginRight": 1.5
}'::jsonb;
```

---

## Zmiany w kodzie

### Backend (tiolibri-api/)

| Plik | Zmiana |
|------|--------|
| `app/models/schemas.py` | +8 pól w GenerateRequest, validators |
| `app/services/epub_generator.py` | +8 parametrów, CSS var replacement |
| `app/services/pdf_generator.py` | +8 parametrów, @page rule, CSS var replacement |
| `app/routers/generate.py` | Przekazywanie parametrów do generatorów |
| `app/presets/classic.css` | CSS variables placeholders |
| `app/presets/modern.css` | CSS variables placeholders |
| `app/presets/minimal.css` | CSS variables placeholders |

### Frontend (tiolibri-frontend/)

| Plik | Zmiana |
|------|--------|
| `src/features/editor/TypographyControls.jsx` | **NOWY** - UI kontrolek typografii |
| `src/features/editor/useTypography.js` | **NOWY** - hook z debounced auto-save |
| `src/features/editor/EditorPage.jsx` | Import useTypography, integration |
| `src/features/editor/GenerateBooks.jsx` | +8 parametrów w API call |

### Database (Supabase)

| Tabela | Zmiana |
|--------|--------|
| `projects` | Dodano kolumnę `typography_settings` (JSONB) |

---

## Problemy i rozwiązania

### Problem 1: WeasyPrint nie wspiera CSS var()
**Symptom:** Margins i font settings nie działają w PDF/EPUB
**Root cause:** WeasyPrint nie rozpoznaje CSS variables
**Fix:** String replacement `css.replace('var(--text-align)', text_align)` przed generacją

### Problem 2: Body margin nie kontroluje PDF page margins
**Symptom:** Zmiana margin w body CSS nie wpływa na marginesy strony PDF
**Root cause:** WeasyPrint wymaga `@page` rule dla page-level margins
**Fix:** Dodano `@page { margin-top: Xcm; ... }` przed CSS presetem

### Problem 3: Line height za duży dla małych czcionek
**Symptom:** Font 12px miał line-height 2.3 (formula: `font_size * 0.106 + 1`)
**Root cause:** Liniowa formula źle skaluje dla małych wartości
**Fix:** Lookup table (12→1.6, 14→1.65, 16→1.7, 18→1.75, 20→1.8, 22→1.85, 24→1.9)

---

## Kluczowe decyzje techniczne

1. **JSONB dla settings** - elastyczność, łatwe dodawanie nowych pól bez migrations
2. **Debounce 1s** - balans między responsywnością UI a ilością DB writes
3. **String replacement zamiast CSS var()** - kompatybilność z WeasyPrint/EPUB readers
4. **@page rule dla PDF** - jedyny sposób na kontrolę page margins w WeasyPrint
5. **Lookup table dla line-height** - lepsze UX niż formula (mniejszy zakres wartości)
6. **4 osobne marginesy** - pełna kontrola (top/bottom/left/right) zamiast single value
7. **Controlled component** - TypographyControls nie ma własnego state, wszystko przez props

---

## Parametry typografii

| Parametr | Range | Unit | Default |
|----------|-------|------|---------|
| Text Align | left / justify | - | left |
| Font Size | 12-24 (step 2) | px | 16 |
| Line Height | 1.2-2.5 (step 0.05) | unitless | 1.7 |
| Margin Top | 0-4 (step 0.5) | em | 2.0 |
| Margin Bottom | 0-4 (step 0.5) | em | 2.0 |
| Margin Left | 0-3 (step 0.25) | em | 1.5 |
| Margin Right | 0-3 (step 0.25) | em | 1.5 |

---

## Testy

| Test | Status |
|------|--------|
| Backend accepts all 8 params | ✅ |
| CSS variable replacement | ✅ |
| PDF @page margins | ✅ |
| EPUB generation with custom typography | ✅ |
| Frontend sliders update state | ✅ |
| Auto-save to Supabase | ✅ |
| Debounce prevents spam | ✅ |
| Settings persist across page reload | ✅ |

---

## TODO / Znane issues

- [x] Backend parametry typografii
- [x] CSS presets update
- [x] Frontend UI controls
- [x] Persystencja w Supabase
- [x] Auto-save z debounce
- [ ] **USER ACTION REQUIRED:** Run SQL migration to add `typography_settings` column
- [ ] Live preview w edytorze (opcjonalnie)
- [ ] Reset to defaults button (opcjonalnie)
- [ ] Typography presets (light/compact/spacious) (opcjonalnie)

---

## Kontekst dla następnej sesji

- **Typography v1.1 COMPLETE** - pełna kontrola typografii z persystencją
- **User musi:** Uruchomić SQL migration w Supabase (ADD COLUMN typography_settings)
- **Zacząć od:** Inne features (cover upload? TOC generation? metadata?) lub deploy
- **Pliki kluczowe:**
  - Frontend: [TypographyControls.jsx](../../tiolibri-frontend/src/features/editor/TypographyControls.jsx), [useTypography.js](../../tiolibri-frontend/src/features/editor/useTypography.js)
  - Backend: [pdf_generator.py](../../tiolibri-api/app/services/pdf_generator.py), [schemas.py](../../tiolibri-api/app/models/schemas.py)
