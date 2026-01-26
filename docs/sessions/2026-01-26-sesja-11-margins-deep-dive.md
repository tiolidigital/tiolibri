# TIOLIBRI - Session 2026-01-26 - Margins Deep Dive & Alignment

**Date:** 2026-01-26, 2:00 PM - 4:07 PM CET  
**Duration:** ~2h 10min  
**Context:** Kontynuacja sesji 10 - debugging margins alignment (preview vs PDF)

---

## 🎯 Goals Accomplished

### 1. ✅ Opus Consultation - Margins Diagnosis

**Problem:** Preview text ~100px szerszy niż PDF przy tych samych margin settings

**Diagnosis przez Opus:**
- **Root cause:** Mieszanie jednostek - container w `px` (700px), marginesy w `cm`
- **Solution:** PX_PER_CM conversion factor: `700px / 14.8cm (A5 width) = ~47.3px/cm`
- **Implementation:** Opus przepisał `BookPreview.jsx` używając unified conversion

**Key insight:** Preview musi używać tej samej skali co PDF (A5 proportions), nie arbitrary 700px

---

### 2. ✅ Nuclear Reset CSS - Usuwa Domyślne Marginesy

**Problem:** TipTap/Tailwind prose dodają własne marginesy do `<p>`, `<h1>` które pszą alignment

**Solution:** Dodano do `editor.css`:

```css
/* Nuclear reset - nadpisuje inline styles */
.book-content * {
  margin-left: 0 !important;
  margin-right: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  box-sizing: border-box !important;
}
Status: ✅ Działa - DevTools pokazuje margin-left: 0px, padding-left: 0px

3. ⚠️ Width Mismatch - 10-15% Pozostaje (ZAAKCEPTOWANE)
Tested:

✅ Nuclear reset CSS

✅ Font change (Crimson Text → Georgia)

✅ margin: 0 w classic.css (forced)

✅ text-indent disable test

Result: Różnica ~10-15% pozostaje

Root cause (final): WeasyPrint rendering differences - font metrics, box model

Decision: Zaakceptowano jako "representative preview" (nie pixel-perfect)

4. ⚠️ Bottom Margin - Continuous Scroll Limitation (ZAAKCEPTOWANE)
Problem: Bottom margin slider nie pokazuje efektu w preview

Opus explanation:

Bottom margin ma sens tylko przy paginacji (stałej wysokości strony). W continuous scroll, spacer div dodaje przestrzeń za tekstem, ale niewidoczny wizualnie.

Status: Architectural limitation - wymaga v1.6 Paginated Preview

5. ✅ Preset Selector Bug Fix (Claude VSC)
Problem: Zmiana presetu (classic/modern/minimal) nie zmieniała fontu

Root cause: preset był stringiem ("classic"), ale komponenty oczekiwały obiektu z preset.fontFamily

Solution: Nowy plik src/lib/presets.js z centralnymi definicjami

Status: ✅ Działa - preset selector zmienia font instant

📋 Key Learnings
Preview vs PDF Alignment: Pixel-perfect nie jest możliwy - reprezentatywny preview jest OK

CSS Reset Strategies: !important jest OK w nuclear reset

Continuous Scroll Limitation: Bottom margin wymaga paginacji

State Management: Centralized definitions > rozproszone stringi

📂 Modified Files
Frontend:
MODIFIED: BookPreview.jsx - Opus version (PX_PER_CM)

MODIFIED: editor.css - book-content + nuclear reset

NEW: lib/presets.js - Centralized definitions

MODIFIED: ChapterEditor.jsx - stylePreset prop

MODIFIED: EditorPage.jsx - Preset flow fix

Backend:
MODIFIED: app/presets/classic.css - margin: 0

Status: v1.5 COMPLETE - Ready for v1.6 Paginated Preview 🎉
