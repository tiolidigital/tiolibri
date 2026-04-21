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

## Order of operations

If shipping tech debt items alongside feature work:

- **Before SPEC-1 Phase 1:** 3.1 (debounce leak) — takes 15 min, prevents confusing race.
- **Before SPEC-1 Phase 3:** 3.9 (EditorPage split) — prepares for all the new Inspector content.
- **Between sessions:** 3.4, 3.5, 3.6, 3.7 — each is a 15-minute diff.
- **Defer indefinitely:** 3.8 (CSRF/rate limit) until public launch.
- **Skip:** 3.2 (false alarm from audit).

---

## Open questions for Piotr

None for this spec — these are all straightforward fixes. Pick items as time allows.
