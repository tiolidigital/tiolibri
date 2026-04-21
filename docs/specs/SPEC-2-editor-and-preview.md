# SPEC 2 — Editor & Preview

**Priority:** 🟡 High
**Status:** 📝 Ready
**Estimated effort:** 3–5 days (4 independent features, can ship one at a time)
**Written:** 2026-04-21

---

## Context

SPEC-1 focuses on data safety. This spec focuses on **writer ergonomics** — features that make the day-to-day editing experience substantially better:

1. Find & Replace — critical for typography cleanup (mdash/dash, quotes, ellipsis) across a 300-page book.
2. WYSIWYG preview — the current live preview doesn't match the generated PDF, causing surprises. A preview that matches the PDF ~95% removes iteration cost.
3. Comments — lightweight review workflow without full live-collab.
4. Word count / reading time — planning aid for books with target length.

Each feature is **independent** — can be shipped in any order, each in its own PR. Unlike SPEC-1, no shared data model; this lets the implementer pick and choose.

---

## Scope

- [ ] **Find & Replace** with typography presets.
- [ ] **WYSIWYG preview** (PDF-matching, on-demand).
- [ ] **Comments on the margin** (Google-Docs style, lightweight).
- [ ] **Word count & reading time** per chapter and per project.

---

## Out of scope

- Real-time collaborative cursors, presence indicators, live-typing visible to others. (Explicitly deferred — see SPEC-1.)
- Grammarly-style grammar/style checking. (Out of scope, maybe future.)
- Export to `.docx`. (Listed in Piotr's "maybe" pile; defer unless requested.)
- Reading analytics (time on page, scroll depth). Not a need.

---

## Feature 1: Find & Replace

### UX

Keyboard shortcuts (override the OS default when editor is focused):
- `Cmd/Ctrl + F` → opens Find panel (search only).
- `Cmd/Ctrl + H` or clicking "Replace" toggle → expands to Find + Replace.
- `Enter` → next match. `Shift + Enter` → previous.
- `Esc` → close panel.

Panel UI (floating over the top of the editor):

```
┌──────────────────────────────────────────────────────┐
│ [Find: ______________]  3 of 47  ↑ ↓  ✕             │
│ [Replace: ______________]  [Replace] [Replace all]   │
│ ☐ Match case  ☐ Whole word  ☐ Regex                 │
│ Scope: [Current chapter ▾]  (or: Entire book)        │
│                                                       │
│ Quick fixes:                                          │
│  [--→—]  ["…"→„…"]  [...→…]  [Remove double spaces] │
└──────────────────────────────────────────────────────┘
```

Matches highlighted inline in yellow, current match in orange. The editor auto-scrolls so the current match stays visible.

### Quick-fix presets (Polish typography)

Each is a one-click button that runs a scoped replace:

| Button | Finds | Replaces with | Notes |
|--------|-------|---------------|-------|
| `--→—` | `--` (two hyphens) | `—` (em-dash) | |
| `-→–` (in ranges) | ` - ` (spaced hyphen between digits) | ` – ` (en-dash) | Regex: `(\d+)\s*-\s*(\d+)` → `$1–$2` |
| `"…"→„…"` | `"text"` | `„text"` | Polish quotation marks. Pair-aware: open → `„`, close → `"`. |
| `...→…` | `...` (three dots) | `…` (ellipsis) | |
| `Remove double spaces` | `  +` (two or more spaces) | ` ` (one space) | |
| `Trim trailing spaces` | ` +$` per line | removed | |

Each quick-fix shows a confirmation: "Replace 23 instances in current chapter?" with Yes/No.

### Implementation

Use [`@tiptap/extension-search-and-replace`](https://github.com/ueberdosis/tiptap/tree/main/packages/extension-search-and-replace) as the base. It provides:
- `editor.commands.setSearchTerm(term)` — highlights all matches.
- `editor.commands.setReplaceTerm(term)`
- `editor.commands.replace()` / `editor.commands.replaceAll()`
- `editor.storage.searchAndReplace.results` — array of match positions.

Wrap in a React component `FindReplacePanel.jsx` that renders the UI above.

For **"entire book" scope**, iterate chapters one-by-one on the client: for each chapter, load content → run regex → save. Show progress: "Replacing in chapter 3 of 7…". This is slow but correct. Do NOT try to do it server-side — keeps the feature self-contained and preserves TipTap's HTML normalization.

**Critical:** `Ctrl+Z` must undo "replace all" as one operation, not 47. TipTap's `replaceAll` is already single-transaction; just verify.

### UX edge cases
- If match count is 0, show "No matches" in place of counter.
- Regex mode shows inline error if invalid regex.
- Close panel → clear highlights.
- Switching chapters while panel is open → re-run search in new chapter, keep scope dropdown at "current chapter".

### Testing
- [ ] Open panel, type term, see highlights and correct count.
- [ ] Replace one at a time, verify cursor/selection, verify count decrements.
- [ ] Replace all → single undo restores everything.
- [ ] Quick-fix `"→„"`: verify pair logic (odd count = error? or just do best-effort?).
- [ ] Scope "Entire book" across 5 chapters: verify all chapters updated and saved.
- [ ] Regex mode with invalid pattern shows error gracefully.

---

## Feature 2: WYSIWYG Preview (matches PDF)

### Context & constraint

The current `BookPreview` component renders HTML with editor CSS but the result doesn't match the generated PDF (different page width, margins, font metrics, pagination). A true 100%-accurate preview would require rendering the actual PDF via WeasyPrint, which is slow (~3s per render) and blocks the backend worker. So:

- **Fast live preview (Option A)** — current approach, improved. Should match PDF ~85–90%.
- **On-demand PDF preview (Option B)** — a button that actually generates a PDF and shows it in an iframe.

This feature implements **both** with a clear UX: live preview is always shown; a button promotes it to "real PDF" on demand.

### UX

Preview panel gets a toggle bar at the top:

```
┌─────────────────────────────────────────────┐
│ Preview mode:  [Live]  [PDF]  [EPUB]        │
│                                              │
│   <content>                                  │
└─────────────────────────────────────────────┘
```

- **Live** (default): current `BookPreview` component, improved (see below).
- **PDF**: button triggers backend to generate PDF, shows in iframe. "Refresh PDF" button to regenerate.
- **EPUB**: same pattern, uses an embedded EPUB reader (e.g., [epub.js](https://github.com/futurepress/epub.js)).

Live preview mode switch is instant (client-side). PDF/EPUB modes show a spinner while generating.

### Live preview — improvements to match PDF

Apply the **same CSS variables** that WeasyPrint uses to generate the PDF. The CSS presets in `tiolibri-api/app/presets/*.css` are the source of truth; the frontend preview should consume those same values.

Concrete changes to `BookPreview.jsx`:
- Page container width: `148mm` (A5) or `170mm` (B5) depending on `project.page_size` (if exists) — otherwise default A5.
- Page padding matches `typography_settings.marginTop/Bottom/Left/Right`.
- Font family, size, line-height from preset + typography_settings (already done).
- First-line indent on paragraphs matches PDF (`text-indent`).
- Chapter spacing between `<h1>` and previous content matches PDF.
- No page breaks visualized — show all chapters scrollable (the live preview doesn't need to simulate pagination).

Deliberate gap: **pagination is not simulated** in Live mode. Users who want to see page breaks click "PDF" tab.

### PDF preview — backend

Existing `/generate` endpoint already produces a PDF. Add a new endpoint:

```
POST /projects/{id}/preview/pdf
Body: { typography_settings, style_preset, cover_image_url }
Returns: { url, expires_at }
```

Behavior:
- Generates a PDF with current state (same logic as `/generate`, but single-format, skip file saving to `generated_files` table since it's ephemeral).
- Returns signed Supabase Storage URL valid for 30 minutes.
- Cache: if nothing changed since last preview (hash of settings + chapter contents), return cached URL.

Frontend renders URL in `<iframe src={url}>`.

### EPUB preview — backend

Same pattern: `POST /projects/{id}/preview/epub`. Frontend embeds via `epub.js`:

```jsx
import ePub from 'epubjs'

function EpubPreview({ url }) {
  const ref = useRef()
  useEffect(() => {
    const book = ePub(url)
    const rendition = book.renderTo(ref.current, { width: '100%', height: '100%' })
    rendition.display()
    return () => book.destroy()
  }, [url])
  return <div ref={ref} className="h-full" />
}
```

### Testing
- [ ] Live preview renders with same font, line-height, margins as PDF.
- [ ] Switch to PDF preview → spinner → PDF appears in iframe.
- [ ] Edit a chapter → switch to PDF preview → new content present in PDF.
- [ ] PDF preview caches: clicking "Preview PDF" twice without edits hits cache.
- [ ] EPUB preview loads in epub.js without errors.
- [ ] Mobile/narrow viewport: preview panel collapses gracefully (existing behavior).

---

## Feature 3: Comments on the margin

### UX

Select text in the editor → small "💬" button appears near the selection → click → sidebar comment composer opens → type comment → save.

Comment appears as a marker next to the line. Hovering shows the comment; clicking expands the comments panel with full thread.

### Data model

```sql
CREATE TABLE chapter_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    author_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    text_anchor TEXT NOT NULL,        -- a snippet of the text the comment attaches to
    position_from INTEGER NOT NULL,   -- ProseMirror document position
    position_to INTEGER NOT NULL,
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    parent_comment_id UUID REFERENCES chapter_comments(id) ON DELETE CASCADE,  -- for replies
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chapter_comments_chapter ON chapter_comments(chapter_id) WHERE resolved_at IS NULL;
```

RLS: same as chapters — accessible if user has access to the project.

### Position anchoring — the hard part

ProseMirror document positions (`position_from`/`position_to`) drift when the document changes. Options:
- (A) **Simple:** store position, accept that comments "detach" when the surrounding text is edited. Show them as "orphan comments" in a sidebar list.
- (B) **Robust:** use TipTap's [CollaborationCursor](https://tiptap.dev/api/extensions/collaboration) decoration system with marks that track position.
- (C) **Hybrid:** store both position AND a `text_anchor` (20 chars before+after the selection). On load, try the position first; if the text at that position doesn't match `text_anchor`, do a search for `text_anchor` and re-anchor. If not found → orphan.

**Recommendation: C.** Pragmatic, handles most real-world edits.

### UX decisions
- Comments visible to everyone with project access (shared users included).
- Any user with access can resolve (not just author). Resolved comments hidden by default, toggle "Show resolved" to see.
- No notifications for new comments (out of scope — small team, they'll see it).

### Endpoints

```
GET    /chapters/{id}/comments
POST   /chapters/{id}/comments
PATCH  /comments/{id}
DELETE /comments/{id}
POST   /comments/{id}/resolve
POST   /comments/{id}/unresolve
```

### Testing
- [ ] Select text, comment, see marker at that location.
- [ ] Edit surrounding text — comment re-anchors or becomes orphan.
- [ ] Reply to a comment, thread shows correctly.
- [ ] Resolve comment, hidden by default, visible with toggle.
- [ ] Second user sees comments from first user.

---

## Feature 4: Word count & reading time

### UX

Small indicator at the bottom of the editor (status bar):

```
3,247 words · 13 min read · Chapter 2 of 5
```

Per-chapter and per-book counts. Click the indicator to open a modal:

```
Total: 42,103 words · 2h 48min

Chapter              Words   Read time
─────────────────────────────────────
1. Wstęp              2,145    8 min
2. Rozdział 1         5,203   20 min
3. Rozdział 2         8,450   32 min
4. Rozdział 3         4,010   15 min
5. Zakończenie        1,289    5 min
─────────────────────────────────────
                     21,097   1h 20min
```

### Implementation

Client-side calculation from `processed_html`:

```js
function countWords(html) {
  const text = html.replace(/<[^>]+>/g, ' ').replace(/&\w+;/g, ' ')
  return text.trim().split(/\s+/).filter(Boolean).length
}

function readingTime(wordCount) {
  const wordsPerMinute = 200  // Polish avg reading speed
  return Math.max(1, Math.ceil(wordCount / wordsPerMinute))
}
```

Memoize per chapter (recompute only when chapter content changes).

No backend changes. Purely a UI helper.

### Testing
- [ ] Word count matches expectations on a known chapter (count manually).
- [ ] Updates live as user types (debounce 500ms to avoid flicker).
- [ ] Per-book total equals sum of per-chapter.
- [ ] Images/dividers don't affect count.

---

## Implementation plan — by phase

Each feature = one phase = **one Claude Code session (new thread with Sonet)**. Same strategy as SPEC-1: keep token usage focused, merge each phase to `main` and verify before starting the next.

**Between phases:** run a code review pass on what was just merged. Fix anything flagged before starting the next phase.

Phases are independent, so order below is "recommended by impact" but you can reorder if a specific need comes up:

### Phase 1 — Find & Replace (highest impact, 1-2 days)

**Why first:** solves concrete immediate pain (mdash cleanup), self-contained, no DB migration.

Steps:
1. Install `@tiptap/extension-search-and-replace`, add to editor extensions.
2. Build `FindReplacePanel.jsx` component (floating panel with fields + checkboxes).
3. Wire keyboard shortcuts (`Cmd+F`, `Cmd+H`, `Enter`, `Shift+Enter`, `Esc`).
4. Implement **"current chapter" scope** first — works entirely on active TipTap instance.
5. Implement **"entire book" scope** — iterate chapters, load content, regex replace, save. Show progress indicator.
6. Implement **quick-fix preset buttons** (mdash/dash, Polish quotes, ellipsis, double spaces, trailing spaces).
7. Verify `Ctrl+Z` undoes "replace all" as one operation.

**Phase 1 done when:** all testing checklist items for Find & Replace pass.

### Phase 2 — Word count & reading time (quick win, 0.5 day)

**Why second:** tiny effort, high user-visible value, no backend changes, good "palate cleanser" between bigger phases.

Steps:
1. Create `countWords()` + `readingTime()` utilities in `lib/utils.js`.
2. Add memoized hook `useWordCount(chapters)` that computes per-chapter + total.
3. Status bar component at bottom of editor: `{chapterWords} words · {chapterTime} min read · Chapter {n} of {total}`.
4. "Book stats" modal triggered by click on status bar: table of all chapters + total row.
5. Debounce live updates (500ms) to avoid flicker while typing.

**Phase 2 done when:** counts match manual verification on a test chapter, total equals sum.

### Phase 3 — WYSIWYG Preview (backend + frontend, 2-3 days)

**Why third:** bigger change (backend endpoint, epub.js integration), but no DB migration so less risky than Phase 4.

**Prerequisite:** SPEC-1 Phase 1 auth must be merged (this endpoint must be authenticated).

Steps:
1. Improve `BookPreview.jsx` "Live" mode: match page width (A5/B5), margins, font metrics to PDF preset.
2. Add Preview mode tabs in `BookPreview` top bar: Live / PDF / EPUB.
3. Backend: `POST /projects/{id}/preview/pdf` endpoint — same logic as `/generate` but single-format, ephemeral URL (30 min signed URL), cache by hash of settings+content.
4. Frontend: PDF tab renders `<iframe src={url}>` with "Refresh PDF" button.
5. Backend: `POST /projects/{id}/preview/epub` — analogous.
6. Frontend: EPUB tab uses `epub.js` to render.

**Phase 3 done when:** Live preview matches PDF ~85-90% visually, PDF tab generates and displays correct PDF, EPUB tab loads in reader.

**Open question for this phase:** do we need a `page_size` field on projects, or is A5 hardcoded OK? Piotr's call when starting this phase.

### Phase 4 — Comments (largest, 2-3 days)

**Why last:** requires DB migration, position anchoring is the hard part, least urgent (small team, they can talk IRL).

**Prerequisite:** SPEC-1 Phase 4 (sharing) must be merged — comments are most valuable when multiple people can see them.

Steps:
1. DB migration: `chapter_comments` table + RLS policies (honor `project_shares` like other tables).
2. Backend CRUD endpoints: `GET/POST/PATCH/DELETE /chapters/{id}/comments`, `POST /comments/{id}/resolve|unresolve`.
3. Frontend: selection-triggered "💬" button near editor selection.
4. Frontend: `CommentsPanel.jsx` sidebar with thread UI.
5. Position anchoring: hybrid strategy (position + text_anchor, re-anchor on load if position drifts).
6. "Show resolved" toggle; orphan comments section.
7. Activity log integration: comment events logged (prerequisite from SPEC-1 Phase 4).

**Phase 4 done when:** all testing checklist items for Comments pass, including re-anchoring after text edits.

---

## Skip order

If time is tight, ship **Phase 1 + Phase 2 only** and defer Phases 3-4. The editor gets massively better and the backend stays simple.

---

## Open questions for Piotr

1. **Find & Replace "entire book" scope** — OK to iterate client-side chapter-by-chapter (slow but self-contained), or worth doing backend-side (faster but requires new endpoint)?
2. **WYSIWYG preview** — is A5/B5 page size hardcoded per project OK, or do you want a setting? (Right now there's no `page_size` field on `projects`.)
3. **Comments resolution** — who can resolve? Only author, or anyone with project access? (Recommend: anyone.)
4. **Reading time formula** — 200 wpm is Polish average for leisure reading. Increase to 250 for "fast reader" or keep 200?
5. **Priority** — if you had to pick only ONE of these four to ship first, which? (I'd say Find & Replace, based on your mdash comment.)
