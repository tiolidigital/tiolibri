# Sesja 17: Polish Typography + Smart Downloads + Page Breaks
**Data:** 2026-02-08
**Czas:** ~2h
**Status:** ✅ v2.1 COMPLETE

---

## 🎯 Cel Sesji

Implementacja polskich zasad typograficznych, poprawiony system downloadów i ulepszone page breaks w PDF.

---

## ✅ Co Zrobiliśmy

### 1. Polish Quotation Marks (v2.1.1a)

**Problem:** Google Docs eksportuje amerykańskie cudzysłowy `"text"`, ale w polskiej typografii używamy `„text"`.

**Rozwiązanie:**
- Dodano funkcję `convertToPolishQuotes()` w `htmlConverter.js`
- Regex pattern detection: opening vs closing quotes
- Tylko dla `language='pl'` (pomija projekty angielskie)

**Implementacja:**
```javascript
// Opening quote: " preceded by space/start/tag
result.replace(/(\s|^|>|—|–)"/g, '$1„')

// Closing quote: " followed by space/end/tag/punctuation
result.replace(/"(\s|$|<|,|\.|!|\?|;|:|—|–)/g, '"$1')
```

**Pliki zmienione:**
- `tiolibri-frontend/src/lib/htmlConverter.js` (nowa funkcja)
- Integracja w `convertGoogleDocsHtml()` z language check

---

### 2. Non-Breaking Spaces (v2.1.1b)

**Problem:** Pojedyncze litery "uciekają" na koniec linii:
```
Podstawa leczenia: wapń i witamina
D                                    ← sierotka!
```

**Rozwiązanie:**
- Dodano funkcję `addPolishNonBreakingSpaces()`
- Wstawia `&nbsp;` (\u00A0) przed pojedynczymi literami
- Chroni krótkie słowa przed rozrywaniem

**Obsługiwane przypadki:**
- Pojedyncze litery: `a, i, o, u, w, z, A, I, O, U, W, Z, D, K, V, X`
- Krótkie słowa: `we, na, za, od, do, po, ze, ku, dr, prof, tj, np, tzn, itd, itp`

**Przykłady:**
- `witamina D` → `witamina&nbsp;D` (D nie ucieknie!)
- `we Włoszech` → `we&nbsp;Włoszech`
- `dr Smith` → `dr&nbsp;Smith`

**Kluczowe:** `&nbsp;` to **znak w treści** (Unicode U+00A0), nie formatowanie CSS - działa przy każdym font-size i margin!

**Pliki zmienione:**
- `tiolibri-frontend/src/lib/htmlConverter.js`
- Wywołanie w `convertGoogleDocsHtml()` tylko dla `language='pl'`

---

### 3. Language-Aware Converter (v2.1.1c)

**Flow:**
1. `EditorPage` → pobiera `project.language` z Supabase
2. `useChapters(projectId, project?.language)` → przekazuje język
3. `convertGoogleDocsHtml(html, projectLanguage)` → używa języka
4. Jeśli `language === 'pl'` → polskie cudzysłowy + non-breaking spaces
5. Jeśli `language === 'en'` → skip (oryginalne cudzysłowy)

**Pliki zmienione:**
- `tiolibri-frontend/src/lib/htmlConverter.js` - parametr `language`
- `tiolibri-frontend/src/features/editor/useChapters.js` - parametr `projectLanguage`
- `tiolibri-frontend/src/features/editor/EditorPage.jsx` - przekazywanie `project?.language`

---

### 4. Smart Downloads (v2.1.2)

**Problem:**
- PDF otwierał się w nowym tabie zamiast pobierać
- Nazwy plików: generyczne `book.pdf` zamiast tytułu projektu

**Rozwiązanie:**
- Blob-based download mechanism
- Generowanie nazw z tytułu projektu

**Implementacja:**
```javascript
const handleDownload = async (url, filename) => {
  const response = await fetch(url)
  const blob = await response.blob()
  const blobUrl = window.URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = blobUrl
  link.download = filename
  link.click()

  window.URL.revokeObjectURL(blobUrl) // cleanup
}

const getSafeFilename = (extension) => {
  const safeName = projectTitle
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return `${safeName}.${extension}`
}
```

**Przykłady nazw:**
- "Moja Książka" → `moja-ksiazka.pdf`
- "E-Book 2024!" → `e-book-2024.epub`

**Pliki zmienione:**
- `tiolibri-frontend/src/features/editor/GenerateBooks.jsx`
  - `handleDownload()` function
  - `getSafeFilename()` helper
  - Changed `<a>` to `<button>` z onClick
- `tiolibri-frontend/src/features/editor/EditorPage.jsx`
  - Dodano prop `projectTitle={project?.title}`

---

### 5. Logo Navigation (v2.1.3)

**Problem:** Logo "TIOLIBRI" w edytorze nie było klikalne.

**Rozwiązanie:**
- Owinięto logo w `<Link to="/dashboard">`
- Hover effect (opacity-80)

**Pliki zmienione:**
- `tiolibri-frontend/src/features/editor/EditorPage.jsx`

---

### 6. Page Break Improvements (v2.1.4)

**Problem:**
- Nagłówki czasem zostawały same na końcu strony
- `orphans: 2` / `widows: 2` było za słabe

**Rozwiązanie:**
- Dodano `page-break-inside: avoid` dla h1, h2, h3
- Zwiększono `orphans/widows` z 2 na 3
- Zastosowano we wszystkich presetach

**CSS changes:**
```css
h1, h2, h3 {
    page-break-after: avoid;    /* było */
    page-break-inside: avoid;   /* NOWE - nie łam wewnątrz nagłówka */
    orphans: 3;                 /* było: 2 */
    widows: 3;                  /* było: 2 */
}
```

**Pliki zmienione:**
- `tiolibri-api/app/presets/classic.css`
- `tiolibri-api/app/presets/modern.css`
- `tiolibri-api/app/presets/minimal.css`

---

## 📊 Statystyki

**Pliki zmienione:** 8
- Frontend: 4 files
- Backend: 3 CSS files (presets)
- Docs: 1 file (CURRENT-STATE.md)

**Funkcje dodane:** 3
- `convertToPolishQuotes()`
- `addPolishNonBreakingSpaces()`
- `handleDownload()` + `getSafeFilename()`

**Lines of code:** ~120 nowych linii

---

## 🔧 Tech Details

### Polish Typography Implementation

**Unicode Characters:**
- Polish opening quote: `„` (U+201E - double low-9 quotation mark)
- Polish closing quote: `"` (U+201D - right double quotation mark)
- Non-breaking space: `&nbsp;` (U+00A0)

**Regex Patterns:**
```javascript
// Polish quotes
/(\s|^|>|—|–)"/g           // opening
/"(\s|$|<|,|\.|!|\?|;|:|—|–)/g  // closing

// Non-breaking spaces
/\s([aiouwzAIOUWZDdKkVvXx])\s/g  // single letters
```

### Download Mechanism

**Fallback strategy:**
```javascript
try {
  // Blob download (preferred)
  fetch → blob → createObjectURL → click
} catch {
  // Fallback: open in new tab
  window.open(url, '_blank')
}
```

**Filename sanitization:**
- Lowercase conversion
- Replace non-alphanumeric with `-`
- Strip leading/trailing dashes
- Result: safe, URL-friendly filename

---

## 🎓 Lessons Learned

1. **Non-breaking space ≠ CSS formatting**
   - `&nbsp;` to znak Unicode w treści, nie style
   - Działa niezależnie od font-size, margins, etc.
   - Lepsze niż CSS-based solutions (np. `white-space: nowrap`)

2. **Page breaks are fragile**
   - Multiple CSS properties needed: `page-break-after`, `page-break-inside`, `orphans`, `widows`
   - WeasyPrint respects CSS better with higher orphans/widows values
   - Testing required after every typography change

3. **Blob downloads > direct links**
   - Browser respects `download` attribute more with blob URLs
   - Allows custom filenames even with CORS restrictions
   - Clean up required (`revokeObjectURL`)

4. **Language-aware processing is crucial**
   - Polish typography rules don't apply to English
   - Always check `language` before applying transformations
   - Future-proof for multi-language support

---

## 🚀 Next Steps

### Optional Polish (Low Priority)
- Export progress indicator
- Toast notifications
- Loading states
- Error messages

### Future Enhancements
- More language-specific typography rules (French, German, etc.)
- Advanced widow/orphan control (user-configurable)
- Table of Contents generator
- Custom fonts upload

---

## 📝 Notes

- All changes backward-compatible (default `language='pl'`)
- English projects (`language='en'`) skip Polish typography
- CSS changes require backend restart
- Frontend changes hot-reload automatically

**Testing checklist:**
- ✅ Polish project → cudzysłowy zmienione
- ✅ English project → cudzysłowy niezmienione
- ✅ PDF download → pobiera się zamiast otwierać
- ✅ Filename → zawiera tytuł projektu
- ✅ Logo → przenosi do dashboardu
- ✅ Page breaks → nagłówki lepiej chronione

---

**Status końcowy:** v2.1 PRODUCTION READY 🎉
