# SPEC 3 — Tech Debt Cleanup

**Priority:** 🟢 Nice-to-have
**Status:** 📝 Ready
**Estimated effort:** 15–45 min per item, ship one at a time
**Written:** 2026-04-21

---

## Context

Audit findings from session 20 (2026-04-21), P1 and P2 severity. None of these block shipping features; none cause active bugs today. But each one is a small cleanup that reduces future surprise.

This spec is a **menu**, not a sequence. Pick items as time allows, in any order. Each item is a self-contained fix that can be done in one commit.

**P0 items from the same audit went into SPEC-1** (auth tokens, loadContent race, RLS for shares) because they're blocking for sharing.

---

## Items

---

### 3.1 — Typography debounce leak on project switch

**Severity:** P1
**File:** [tiolibri-frontend/src/features/editor/useTypography.js:52-69](../../tiolibri-frontend/src/features/editor/useTypography.js#L52-L69)
**Effort:** 15 min

#### Problem

```js
const saveToDb = useCallback(
  debounce(async (newSettings) => { ... }, 1000),
  [projectId]
)
```

`useCallback(debounce(...), [projectId])` creates a new debounced function each time `projectId` changes, but the **previous** debounced function may still have a pending timer. If a user changes typography on Project A, then quickly switches to Project B before 1s elapses, the debounced save from A fires **after** the project switch — with A's settings but possibly racing against B's first save.

Extremely unlikely in practice (1-second window), but incorrect.

#### Fix

Clear the old timer on unmount or when `projectId` changes:

```js
useEffect(() => {
  return () => {
    // cancel any pending debounced save on unmount / projectId change
    if (saveToDb.cancel) saveToDb.cancel()
  }
}, [saveToDb])
```

This requires the debounce utility to support `.cancel()`. Current `debounce()` in `lib/utils.js:42-52` doesn't. Either:
- (A) Add `.cancel()` to `debounce()` (attach function).
- (B) Replace with `lodash.debounce` (already supports `.cancel()`).

Recommend **A** (keep dep-free):

```js
export function debounce(func, wait) {
  let timeout
  const debounced = function (...args) {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
  debounced.cancel = () => clearTimeout(timeout)
  return debounced
}
```

#### Verification
- Change typography on Project A, quickly switch to Project B within 1s. Project A should not get a save after the switch.

---

### 3.2 — Optimistic update without rollback in `handleUpdateProject`

**Severity:** P1
**File:** [tiolibri-frontend/src/features/editor/EditorPage.jsx:178-190](../../tiolibri-frontend/src/features/editor/EditorPage.jsx#L178-L190)
**Effort:** 15 min

#### Problem

```js
const handleUpdateProject = async (field, value) => {
  try {
    const { error } = await supabase.from('projects').update({ [field]: value, ... })
    if (error) throw error
    setProject(prev => ({ ...prev, [field]: value }))  // only on success
  } catch (err) {
    console.error('Failed to update project:', err)
  }
}
```

Actually this one is **correct** (state only updates on success). The issue I flagged in the audit was wrong — re-reading confirms the state update is AFTER the await. False alarm.

**Action: no change needed.** Remove from SPEC-3.

(Keeping this entry as a record that the audit was wrong here.)

---

### 3.3 — Orphan files on `uploadChapter` failure

**Severity:** P1
**File:** [tiolibri-frontend/src/features/editor/useChapters.js:32-70](../../tiolibri-frontend/src/features/editor/useChapters.js#L32-L70)
**Effort:** 30 min

#### Problem

Current order:
1. Upload file to Supabase Storage.
2. Insert chapter row in DB.

If step 2 fails, the file stays in storage forever with no DB reference. Over time this accumulates garbage.

#### Fix

Wrap in try/catch; on DB insert failure, delete the uploaded file:

```js
const uploadChapter = async (file) => {
  // ... upload to storage ...
  const { error: uploadError } = await supabase.storage.from('uploads').upload(filePath, file)
  if (uploadError) throw uploadError

  try {
    const { data, error: insertError } = await supabase.from('chapters').insert({...}).select().single()
    if (insertError) throw insertError
    setChapters(prev => [...prev, data])
    return data
  } catch (err) {
    // Rollback: remove orphan file
    await supabase.storage.from('uploads').remove([filePath]).catch(() => {})
    throw err
  }
}
```

Same pattern should apply to `deleteChapter` (currently deletes DB before storage — if storage fails, row is gone but file remains). After SPEC-1 `soft-delete` lands, `deleteChapter` becomes a simple UPDATE and the problem disappears — do this only if SPEC-1 is not yet merged.

#### Verification
- Force insert failure (bad input), check storage bucket — file should be removed.

---

### 3.4 — `document.title` not reset on EditorPage unmount

**Severity:** P2
**File:** [tiolibri-frontend/src/features/editor/EditorPage.jsx:138-144](../../tiolibri-frontend/src/features/editor/EditorPage.jsx#L138-L144)
**Effort:** 5 min

#### Problem

After leaving editor, browser tab still shows book title ("Bajka o kozie – TIOLIBRI") even on Dashboard.

#### Fix

Add cleanup to the `useEffect` that sets the title:

```js
useEffect(() => {
  if (project?.title) {
    document.title = `${project.title} - TIOLIBRI`
  } else {
    document.title = 'Editor - TIOLIBRI'
  }
  return () => {
    document.title = 'TIOLIBRI'
  }
}, [project])
```

---

### 3.5 — Cover upload validation

**Severity:** P2
**File:** `tiolibri-frontend/src/features/editor/CoverUpload.jsx` (not yet read in detail, verify first)
**Effort:** 20 min

#### Problem (suspected)

Likely no validation of file type / size. User could upload 50MB raw TIFF, or non-image file.

#### Fix

Before upload:
- Validate `file.type` is one of `image/jpeg`, `image/png`, `image/webp`.
- Validate `file.size` ≤ 5MB.
- Show user-visible error if either fails.

#### Verification
- Try to upload a PDF — rejected with clear message.
- Try to upload a 10MB JPEG — rejected with clear message.
- Upload a valid 1MB JPEG — works.

---

### 3.6 — Missing `useCallback` / `useMemo` in EditorPage

**Severity:** P2 (performance only, not a bug)
**File:** [tiolibri-frontend/src/features/editor/EditorPage.jsx](../../tiolibri-frontend/src/features/editor/EditorPage.jsx)
**Effort:** 20 min

#### Problem

Inline handlers like `onPreviewToggle={() => setShowPreview(!showPreview)}` create new function references on every render, causing `ChapterEditor` (a memo-able component) to re-render unnecessarily. Similarly `toggleSection` is defined inline.

Minor perf cost. Noticeable on low-end laptops with long chapters.

#### Fix

Wrap frequently-passed handlers in `useCallback`, and consider `React.memo(ChapterEditor)` if profiler shows re-render cost.

#### Verification
- Profile re-renders with React DevTools before and after. Confirm reduction.
- No functional change expected.

---

### 3.7 — Double Google Docs HTML conversion

**Severity:** P2
**File:** [tiolibri-frontend/src/features/editor/useChapters.js:148-168](../../tiolibri-frontend/src/features/editor/useChapters.js#L148-L168)
**Effort:** 20 min

#### Problem

`getChapterContent` reads source file from storage, checks `isGoogleDocsHtml(html)`, and converts if yes. But the converted HTML is **not persisted back** — every time the chapter loads, it re-converts.

`EditorPage` already prefers `chapter.processed_html` if present, falling back to storage — so after the first edit + save, it's fine. But before the first save, every chapter open re-converts.

#### Fix

After conversion, save back to DB immediately:

```js
if (isGoogleDocsHtml(html)) {
  html = convertGoogleDocsHtml(html, projectLanguage)
  // Persist converted HTML so we don't re-convert on next load
  await supabase.from('chapters').update({ processed_html: html }).eq('id', chapterId)
}
```

Small perf improvement; eliminates repeated work.

#### Verification
- Upload Google Docs HTML chapter → open → close → open again → second open should be instant (no conversion log message).

---

### 3.8 — CSRF / rate limiting (backend)

**Severity:** P2 (production concern, not urgent for internal tool)
**File:** backend FastAPI config
**Effort:** 30 min

#### Problem

Backend has no rate limiting or CSRF protection. For an internal tool with ~5 users and Bearer-token auth, this is acceptable. Flagging for when the tool eventually goes public.

#### Fix (deferred until public)

- Add `slowapi` or similar for per-IP rate limit on `/generate` (it's expensive).
- CSRF doesn't apply to Bearer-token APIs, so no action needed.

**Action: defer. Revisit before any public launch.**

---

### 3.9 — EditorPage.jsx has grown to 500+ lines

**Severity:** P2 (maintainability)
**File:** [tiolibri-frontend/src/features/editor/EditorPage.jsx](../../tiolibri-frontend/src/features/editor/EditorPage.jsx)
**Effort:** 45 min

#### Problem

`EditorPage` is becoming a god-component (project fetch, chapter management, typography, cover, keybindings, preview state, focus mode, inspector sections). Adding SPEC-1 features (share, activity log, history) and SPEC-2 (find/replace, comments) will push it past 1000 lines.

#### Fix

Extract:
- `Inspector.jsx` — right panel with all CollapsibleSections.
- `EditorHeader.jsx` — top bar.
- `useEditorKeybindings.js` — hook for all Ctrl+Shift+P / Cmd+F etc.
- `useWindowSize.js` — the `isUltrawide` / resize listener.

Do this **before** SPEC-1 Phase 3 (when you add Trash, Status, Lock UI — lots of new Inspector content).

#### Verification
- Editor still works exactly as before.
- Type check + build pass.
- Same visual result (screenshot diff if possible).

---

### 3.10 — Find & Replace: book-scope doesn't flush current editor autosave

**Severity:** P2
**File:** [tiolibri-frontend/src/features/editor/FindReplacePanel.jsx](../../tiolibri-frontend/src/features/editor/FindReplacePanel.jsx) + [EditorPage.jsx](../../tiolibri-frontend/src/features/editor/EditorPage.jsx)
**Effort:** 15 min
**Source:** SPEC-2 Phase 1 review (2026-04-21), item #4

#### Problem

When user runs "Replace all / Entire book", the panel replaces other chapters via `onSaveChapter` (direct backend PATCH) while the current chapter is handled by `editor.commands.replaceAll()` — which triggers the 2s autosave debounce. If the user closes the tab or switches chapters within 2s, the current chapter's replace may be lost while other chapters are already persisted. Final state is inconsistent.

#### Fix

Before iterating chapters in `runBookReplaceAll`, explicitly save the current chapter's HTML: `await onSaveChapter(selectedChapterId, editor.getHTML())`. This forces the current chapter to be flushed through the backend before any other chapter is touched.

#### Verification

- Edit a word in chapter 1, immediately click "Replace all / Entire book" for "foo" → "bar". After completion, close the tab. Reopen project — chapter 1 should have both the edit AND the replace, not just one.

---

### 3.11 — Find & Replace: scrollToMatch doesn't account for F&R panel overlay

**Severity:** P2
**File:** [tiolibri-frontend/src/features/editor/extensions/SearchAndReplace.js:64-81](../../tiolibri-frontend/src/features/editor/extensions/SearchAndReplace.js#L64-L81)
**Effort:** 20 min
**Source:** SPEC-2 Phase 1 review (2026-04-21), item #6

#### Problem

The panel is `sticky top-0` with ~160px height. `scrollToMatch` walks up parents looking for a scrollable container, then uses a hard-coded 80/40/120 offset — which doesn't reliably keep the match visible below the panel. A match near the top of the scroll viewport can end up hidden behind the F&R panel.

#### Fix

Replace the parent-walking heuristic with ProseMirror's built-in scroll: `editor.view.dispatch(editor.state.tr.setSelection(TextSelection.create(doc, match.from, match.to)).scrollIntoView())`. Alternatively, measure the F&R panel height at runtime and pass it as explicit offset.

#### Verification

- Open F&R panel, search for a term that matches near the top of the chapter. Use next/prev — the current match should always be visible, never obscured by the panel.

---

### 3.12 — Find & Replace: Cmd+F fires globally even when focus is in sidebar inputs

**Severity:** P2
**File:** [tiolibri-frontend/src/features/editor/EditorPage.jsx:105-144](../../tiolibri-frontend/src/features/editor/EditorPage.jsx#L105-L144)
**Effort:** 10 min
**Source:** SPEC-2 Phase 1 review (2026-04-21), item #9

#### Problem

The `keydown` listener is attached to `window`, so Cmd+F/Cmd+H intercept browser behavior in *any* input on the page — including "Project Details" title/author fields in the Inspector. User typing in the title field can't use browser Find, instead gets the F&R panel.

#### Fix

In the handler, check `document.activeElement`:

```js
const active = document.activeElement
const inTextField = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable)
// Only intercept Cmd+F when focus is in the editor (contentEditable) or nowhere.
// Specifically: let Cmd+F pass through when focus is in a plain INPUT/TEXTAREA.
if (mod && !e.shiftKey && e.key === 'f') {
  if (inTextField && !active.classList.contains('tiptap-editor')) return
  // ...
}
```

Simpler alternative: only attach the listener when a chapter is selected AND focus is in the editor region (check `contentEditable`).

#### Verification

- Click into "Project Details / Title" in the right panel, press Cmd+F — browser Find should open, not F&R panel.
- Click into the chapter editor, press Cmd+F — F&R panel opens.

---

### 3.13 — Find & Replace: empty `processed_html` silently skipped in book-scope

**Severity:** P2
**File:** [tiolibri-frontend/src/features/editor/FindReplacePanel.jsx:190-224](../../tiolibri-frontend/src/features/editor/FindReplacePanel.jsx#L190-L224)
**Effort:** 20 min
**Source:** SPEC-2 Phase 1 review (2026-04-21), item #11

#### Problem

Chapters that were uploaded from Google Docs but never opened in the editor have `processed_html === null` (content lives only in Storage). The `runBookReplaceAll` loop does `if (!ch.processed_html) continue` — so those chapters are silently skipped. User thinks "replace in entire book" covered everything, but some chapters kept their original text.

#### Fix

Two options, recommend (A):

**(A) Warn the user:** before running, count chapters with null `processed_html`. Show in confirm dialog: `"Zamienić X wystąpień w Y rozdziałach? Uwaga: N rozdziałów nie ma jeszcze przetworzonej zawartości — otwórz je najpierw w edytorze, żeby uwzględnić w zamianie."` User decides whether to proceed or cancel.

**(B) Fetch-on-demand:** for each chapter with null `processed_html`, call `getChapterContent(ch.id)` inline (downloads source HTML, runs `convertGoogleDocsHtml` if needed, then applies the replace). Slower but complete. Requires wiring `getChapterContent` through to the panel.

#### Verification

- Upload 3 chapters from Google Docs, open only chapter 1. Run "Replace all / Entire book" for a word present in all 3.
- With fix (A): confirm dialog mentions 2 chapters not yet processed.
- With fix (B): all 3 chapters updated.

---

### 3.14 — Find & Replace: add `position: relative` to panel root

**Severity:** P2 (cosmetic robustness)
**File:** [tiolibri-frontend/src/features/editor/FindReplacePanel.jsx:355-359](../../tiolibri-frontend/src/features/editor/FindReplacePanel.jsx#L355-L359)
**Effort:** 2 min
**Source:** SPEC-2 Phase 1 review (2026-04-21), item #8

#### Problem

Confirm overlay uses `absolute inset-0` — it's positioned against the nearest positioned ancestor. Currently `EditorPage` provides `relative` on the wrapper, which works, but makes the panel component fragile to reuse elsewhere.

#### Fix

Add `relative` to the outer div of `FindReplacePanel.jsx` root so the overlay is self-contained.

#### Verification

- Remove `relative` from `EditorPage` wrapper — confirm overlay still renders correctly within the panel (visual test).

---

### 3.15 — Auto-snapshot triggered only from chapter content edits

**Severity:** P1
**File:** [tiolibri-api/app/routers/chapters.py:75](../../tiolibri-api/app/routers/chapters.py#L75), [tiolibri-api/app/routers/projects.py](../../tiolibri-api/app/routers/projects.py)
**Effort:** 20 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

`maybe_auto_snapshot()` is only called from `update_chapter`. So edits to project metadata (title, typography, cover), chapter create/delete/reorder, and snapshot restore don't trigger auto-snapshot. If a user refactors structure heavily without touching existing chapter content, 6h can pass with no safety net.

Also: docstring in [snapshots.py:9-12](../../tiolibri-api/app/routers/snapshots.py#L9-L12) lies — it claims "and there has been a mutating write since then", but the code only checks timestamp. Either fix the docstring, or actually track last-write-time separately.

#### Fix

Add `maybe_auto_snapshot(project_id)` calls to:
- `projects.update_project` (after successful update)
- `chapters.create_chapter`, `chapters.delete_chapter`, `chapters.soft_delete_chapter`, reorder endpoint
- After `restore_snapshot` the pre-restore snapshot already covers this

Fix docstring to match reality: "If the last snapshot is older than N hours, insert a new one. Caller decides when to invoke."

#### Verification

- Edit project title → wait 6h+ (or temporarily lower interval to 1min) → edit again → confirm new auto snapshot appears.

---

### 3.16 — Silent swallowing of auto-snapshot errors

**Severity:** P2
**File:** [tiolibri-api/app/routers/snapshots.py:152-153](../../tiolibri-api/app/routers/snapshots.py#L152-L153)
**Effort:** 5 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

`except Exception: pass` in `maybe_auto_snapshot`. Intent is correct (never break write path) but zero logging means broken auto-snapshots can go undetected for months.

#### Fix

```python
import logging
logger = logging.getLogger(__name__)

except Exception:
    logger.exception("auto-snapshot failed for project %s", project_id)
```

Behavior unchanged (still swallowed), but Railway logs will show the trail.

---

### 3.17 — Snapshot restore not atomic across chapters

**Severity:** P2 (data-integrity)
**File:** [tiolibri-api/app/routers/snapshots.py:212-258](../../tiolibri-api/app/routers/snapshots.py#L212-L258)
**Effort:** 60 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

`_restore_chapters` runs N+M individual UPDATE/INSERT calls through Supabase REST. If the network drops on chapter 7 of 20, the project is left half-restored. Pre-restore snapshot protects the user (they can undo), but the DB itself is in an inconsistent mid-state and the user doesn't know which chapters applied vs. which didn't.

Also N+1 perf: 100-chapter book = 100 round trips.

#### Fix

Two paths:

**(A) Quick:** wrap the restore in a try/except; if anything fails, auto-trigger restore of the `pre-restore` snapshot (watch out for infinite recursion). Return an explicit `{"restored": false, "rolled_back": true}` when that path fires.

**(B) Proper:** move the restore logic into a Postgres function (`supabase.rpc(...)`) that runs in a single transaction. Gets both atomicity and batch perf.

Recommend (B) once Phase 5 stabilizes.

#### Verification

- Inject a failure mid-restore (e.g. temporarily reject one chapter id in RLS) → confirm either full rollback (A) or full atomic transaction failure (B).

---

### 3.18 — Restored chapters inserted with snapshot's UUIDs

**Severity:** P2 (minor data-hygiene)
**File:** [tiolibri-api/app/routers/snapshots.py:243-251](../../tiolibri-api/app/routers/snapshots.py#L243-L251)
**Effort:** 10 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

When a chapter existed in the snapshot but not in current DB, it's re-inserted with the snapshot's original `id`. Since `project_snapshots.snapshot` is editable JSONB, an attacker with write-access to the project could craft a snapshot with arbitrary chapter UUIDs. RLS blocks cross-project writes, but it's still smells bad.

#### Fix

In the else-branch of `_restore_chapters` loop, generate a fresh UUID instead of reusing `ch["id"]`. Nothing outside the DB references chapter ids by value.

---

### 3.19 — 50 MB import size check happens after RAM buffering

**Severity:** P2 (resource)
**File:** [tiolibri-api/app/routers/export_import.py:132-137](../../tiolibri-api/app/routers/export_import.py#L132-L137)
**Effort:** 30 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

Current check uses `file.read(_MAX+1)` — defensive (won't read past 50MB+1) but the whole blob sits in Railway process RAM. Ten concurrent 50MB imports on a 512MB Railway plan → OOM.

#### Fix

Stream to a tempfile with running byte count, or honor `Content-Length` when present and reject early. Not urgent — imports are rare — but worth addressing before broader launch.

---

### 3.20 — `_assert_project_access` duplicated + ignores share role

**Severity:** P2 (DRY + future RBAC)
**File:** [tiolibri-api/app/routers/snapshots.py:160-173](../../tiolibri-api/app/routers/snapshots.py#L160-L173), [tiolibri-api/app/routers/export_import.py:217-230](../../tiolibri-api/app/routers/export_import.py#L217-L230)
**Effort:** 20 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

Two identical copies of `_assert_project_access` across routers. Both treat any shared user as fully privileged — so a viewer-level share (once that distinction exists) could restore snapshots, export, or import. Phase 4 shares currently have no role field, so this is a latent issue rather than active bug.

#### Fix

Extract to `app/services/permissions.py` with signature `assert_project_access(project_id, user_id, *, require_role="owner"|"editor"|"viewer")`. Snapshots restore + export = editor+; snapshot list = viewer+. Wire up once `project_shares.role` exists.

---

### 3.21 — Exception detail leak in import error messages

**Severity:** P2 (info disclosure)
**File:** [tiolibri-api/app/routers/export_import.py:183-184](../../tiolibri-api/app/routers/export_import.py#L183-L184)
**Effort:** 5 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

```python
raise HTTPException(status_code=422, detail=f"Could not parse .tiolibri file: {exc}")
```

`{exc}` can include internal paths, library internals, stack fragments. Low severity, but the user doesn't need that detail.

#### Fix

Show generic user-facing message, log full exception server-side:

```python
logger.exception("Import parse failure")
raise HTTPException(status_code=422, detail="Invalid .tiolibri file")
```

---

### 3.22 — ProjectSnapshots restore button hidden until hover

**Severity:** P2 (a11y / touch)
**File:** [tiolibri-frontend/src/features/editor/ProjectSnapshots.jsx:135-140](../../tiolibri-frontend/src/features/editor/ProjectSnapshots.jsx#L135-L140)
**Effort:** 5 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

"Przywróć" button uses `opacity-0 group-hover:opacity-100` — invisible on touch devices (no hover), and keyboard users only see it if their TAB lands on it (`focus:opacity-100` helps but is flaky). Snapshot restore is a rare action; hiding it this aggressively is over-engineered.

#### Fix

Make button always visible (drop opacity classes), or at minimum use `sm:opacity-0 sm:group-hover:opacity-100` so mobile gets the unconditional version.

---

### 3.23 — Verify ProjectSnapshots onRestored integration in EditorPage

**Severity:** P1 (UX — restored state may be invisible until refresh)
**File:** [tiolibri-frontend/src/features/editor/EditorPage.jsx](../../tiolibri-frontend/src/features/editor/EditorPage.jsx), [ProjectSnapshots.jsx:88](../../tiolibri-frontend/src/features/editor/ProjectSnapshots.jsx#L88)
**Effort:** 15 min
**Source:** SPEC-1 Phase 5 review (2026-04-21)

#### Problem

`ProjectSnapshots` calls `onRestored?.()` after a successful restore, expecting the parent (EditorPage) to reload chapters + content. Review didn't verify that wiring exists. If `onRestored` is not passed or is a no-op, user clicks "Przywróć", sees "success", but editor still shows pre-restore state until manual refresh.

#### Fix

Ensure EditorPage passes `onRestored={async () => { await refreshChapters(); await loadContent(selectedChapterId); setProject(await fetchProject()); }}` (or similar). Verify by manual test.

#### Verification

- Edit chapter, create snapshot.
- Edit further, restore the old snapshot.
- Without page refresh, editor should immediately show the snapshot state.

---

## Order of operations

If shipping tech debt items alongside feature work:

- **Before SPEC-1 Phase 1:** 3.1 (debounce leak) — takes 15 min, prevents confusing race.
- **Before SPEC-1 Phase 3:** 3.9 (EditorPage split) — prepares for all the new Inspector content.
- **Between sessions:** 3.4, 3.5, 3.6, 3.7 — each is a 15-minute diff.
- **Phase 5 follow-ups (next session, bundle together):** 3.15, 3.23 (P1 — do first), then 3.16, 3.17, 3.20 (P2 data-integrity), then 3.18, 3.19, 3.21, 3.22 (P2 polish).
- **Defer indefinitely:** 3.8 (CSRF/rate limit) until public launch.
- **Skip:** 3.2 (false alarm from audit).

## Phase 5 review summary (2026-04-21)

Must-fix found during review and **already fixed in this session**:
- B1: `.insert().select().execute()` → `.insert().execute()` in `_insert_snapshot` + `import_project`
- S5: zip bomb guards in import (entry count, per-file uncompressed size)
- S8: max chapters per import cap (2000)

Everything else from that review lives as items 3.15–3.23 above.

---

## Open questions for Piotr

None for this spec — these are all straightforward fixes. Pick items as time allows.
