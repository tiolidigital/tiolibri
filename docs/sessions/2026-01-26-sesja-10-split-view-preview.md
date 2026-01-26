# TIOLIBRI - Session 2026-01-26 - Split View & Preview Alignment

**Date:** 2026-01-26, 11:00 AM - 1:20 PM CET  
**Duration:** ~2h 20min  
**Context:** Kontynuacja implementacji preview funkcjonalności

---

## 🎯 Goals Accomplished

### 1. ✅ Split View Implementation (60/40 layout)

**What:** Live book preview alongside editor on ultrawide monitor (3440x1440)

**Implementation:**
- **Frontend:** `src/features/editor/BookPreview.jsx` (new component)
- **Frontend:** `src/features/editor/EditorPage.jsx` (split layout)
- **Frontend:** `src/features/editor/EditorToolbar.jsx` (toggle button)

**Features:**
- Split view: 60% Editor / 40% Preview
- Toggle button "Show/Hide Preview" 
- Keyboard shortcut: `Cmd+Shift+P`
- Live content updates (liveContent state)
- Preview shows book-like page (700px width, white page, shadow)
- Page numbers (top-right, bottom-center)
- State persistence (localStorage)

**Status:** ✅ Working

---

### 2. ✅ Margins Alignment (Preview ↔ PDF)

**Problem:** Preview używał `em` units, PDF używał `cm` - różne wartości wizualne.

**Solution:**
- **Frontend:** `BookPreview.jsx` - zamieniono `padding: Xem` na `padding: Xcm`
- **Backend:** `app/services/pdf_generator.py` - usunięto body margins, zostawiono tylko @page margins

**Key changes in pdf_generator.py (lines 181-201):**
```python
# Remove body margin (replace var(--margin) with 0)
css_final = css_final.replace('margin: var(--margin, 2em 1.5em);', 'margin: 0;')

# @page controls ALL margins
@page {
  size: A5 portrait;
  margin-top: {margin_top}cm;
  margin-bottom: {margin_bottom}cm;
  margin-left: {margin_left}cm;
  margin-right: {margin_right}cm;
}
Key changes in BookPreview.jsx:

jsx
// Use cm units (like PDF), not em
paddingTop: `${settings.marginTop}cm`,
paddingBottom: `${settings.marginBottom}cm`,
paddingLeft: `${settings.marginLeft}cm`,
paddingRight: `${settings.marginRight}cm`,
Status: ✅ Much better (ale dalej różnice - see below)

🐛 Remaining Issues
Issue 1: Preview vs PDF Width Mismatch
Problem:

Preview tekst jest szerszy niż PDF tekst (przy tych samych margin settings)

Example: 3em margins → Preview ~450px text width, PDF ~350px text width

Possible causes:

Page container padding conflicts?

Font rendering differences (browser vs WeasyPrint)?

Box model calculation differences?

Screenshots: file:45, file:46, file:47, file:48

Priority: 🔴 High

Issue 2: Bottom Margin Not Working in Preview
Problem:

User zmienia "Bottom" slider w Inspector → preview nie reaguje

Top, Left, Right margins działają ✅

PDF bottom margin działa ✅

Tylko preview bottom margin nie działa ❌

Possible cause:

paddingBottom w BookPreview nie jest aplikowany?

Conflict z minHeight style?

CSS specificity issue?

Priority: 🔴 High

Issue 3: 0em Margins Jump Bug
Problem:

User ustawia Left/Right na 0em → margins są większe niż przy 0.25em

Weird behavior, but user nie potrzebuje 0em, więc low priority

Priority: 🟡 Low (not blocking)

📋 Next Steps (Planned Features)
Feature: Paginated Preview (Prev/Next Navigation)
Goal: Zamiast continuous scroll, pokazywać jedną stronę na raz z buttons do nawigacji.

Design:

text
┌─────────────────────────────┐
│ [← Prev]  Page 2 of 8  [Next →] │
├─────────────────────────────┤
│                             │
│   ┌─────────────────┐      │
│   │                 │      │
│   │ Page 2 content  │      │
│   │ only            │      │
│   │                 │      │
│   │            2    │      │
│   └─────────────────┘      │
│                             │
└─────────────────────────────┘
Implementation plan:

Pagination algorithm: word count (~400 words/page)

Add Prev/Next buttons above preview

Add page counter (Page X of Y)

Fixed page height (no scroll within page)

Keyboard arrows (← →) to navigate pages

Reset to page 1 when content changes

Priority: 🔵 Medium (nice-to-have after fixing issues)

Estimated time: 3-4h

📂 Modified Files Summary
Frontend:
NEW: src/features/editor/BookPreview.jsx - Preview component

MODIFIED: src/features/editor/EditorPage.jsx - Split layout + keyboard shortcut

MODIFIED: src/features/editor/EditorToolbar.jsx - Toggle button

MODIFIED: src/features/editor/ChapterEditor.jsx - Live content updates

MODIFIED: src/features/editor/editor.css - Book preview styles

Backend:
MODIFIED: app/services/pdf_generator.py - Margins logic (lines 181-201)

🎨 Current Preview Implementation
BookPreview.jsx key styles:

jsx
// Page container
style={{
  width: '700px',
  minHeight: '990px',
  padding: '0.5cm', // Minimal (tylko dla page numbers)
  boxSizing: 'border-box',
}}

// Content
style={{
  fontSize: `${settings.fontSize}px`,
  lineHeight: settings.lineHeight,
  textAlign: settings.textAlign,
  fontFamily: preset?.fontFamily || 'Georgia, serif',
  
  paddingTop: `${settings.marginTop}cm`,
  paddingBottom: `${settings.marginBottom}cm`,
  paddingLeft: `${settings.marginLeft}cm`,
  paddingRight: `${settings.marginRight}cm`,
  
  maxWidth: 'none',
  overflowWrap: 'break-word',
  minHeight: '100%',
  overflow: 'hidden',
}}
🔧 Technical Notes
Typography Settings Flow:
text
Inspector sliders (em values)
    ↓
Supabase DB (margin_top, margin_bottom, margin_left, margin_right)
    ↓
useTypography hook → typographySettings object
    ↓
BookPreview component → applies as `padding: Xcm`
    ↓
PDF generator → @page margin: Xcm
Key Discovery:
Backend converts em → cm with 1:1 ratio:

User sets 3em in slider

Backend receives margin_left: 3.0

PDF CSS: margin-left: 3cm

Preview should match: paddingLeft: 3cm ✅

💡 Questions for Next Session
Width mismatch: Why is preview text wider than PDF? Measure exact pixel widths?

Bottom margin: Why doesn't paddingBottom work? CSS inspector check?

Pagination: Should we implement now or fix alignment first?

Page size: Is 700px (scaled A5) correct? Should we match exact PDF dimensions?

🚀 Ready for Next Session
Priority order:

🔴 Fix bottom margin (preview)

🔴 Fix width mismatch (preview vs PDF)

🟡 Debug 0em jump (optional)

🔵 Implement pagination (feature enhancement)

Recommended starting point:
Debug bottom margin - add console.log to see if paddingBottom value is calculated correctly, then check CSS inspector in browser to see computed styles.