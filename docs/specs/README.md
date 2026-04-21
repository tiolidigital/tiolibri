# TIOLIBRI — Specs Index

Specifications for upcoming features, organized by priority.
Each spec is implementation-ready: Sonnet (or any implementer) should be able to open the file and execute without re-deriving context.

## Overview

| # | Spec | Priority | Status | Effort |
|---|------|----------|--------|--------|
| 1 | [Safety & Collaboration](./SPEC-1-safety-and-collaboration.md) | 🔴 Critical | 📝 Ready | Large (1–2 weeks) |
| 2 | [Editor & Preview](./SPEC-2-editor-and-preview.md) | 🟡 High | 📝 Ready | Medium (3–5 days) |
| 3 | [Tech Debt Cleanup](./SPEC-3-tech-debt-cleanup.md) | 🟢 Nice-to-have | 📝 Ready | Small (per-item 15–45 min) |

## Context

Written: 2026-04-21
Author: Piotr (with Opus 4.7)
Trigger: Two books actively in production, need safety nets before adding collaborators.

## Implementation order

1. **Spec 1 first** — protects work from loss and prepares ground for multi-user. Has 5 phases.
2. **Spec 2 next** — quality-of-life for the editor. Has 4 phases.
3. **Spec 3 parallel** — can be done between sessions, one item at a time.

### Session strategy

Each **phase** = one new Claude Code session (new thread with Sonet).
- Keeps token usage focused.
- Each phase reviewed and merged to `main` before the next starts.
- Code review pass between phases — catch regressions before they compound.

Order across specs:

| Step | What | Effort |
|------|------|--------|
| 1 | SPEC-1 Phase 1 (auth spike + foundations) | 1 day |
| 2 | SPEC-1 Phase 2 (version history) | 2 days |
| 3 | SPEC-1 Phase 3 (soft delete + lock + status) | 2 days |
| 4 | SPEC-1 Phase 4 (sharing + activity log) | 2-3 days |
| 5 | SPEC-1 Phase 5 (snapshots + export/import) | 2 days |
| 6 | SPEC-2 Phase 1 (Find & Replace) | 1-2 days |
| 7 | SPEC-2 Phase 2 (word count) | 0.5 day |
| 8 | SPEC-2 Phase 3 (WYSIWYG preview) | 2-3 days |
| 9 | SPEC-2 Phase 4 (Comments) | 2-3 days |
| — | SPEC-3 items | menu, pick as time allows |

## Already merged (don't re-do)

- Cursor-jump fix in `ChapterEditor.jsx` — commit `638095f` (2026-04-21).
  `setContent()` no longer runs on every content update, only on chapter change.
- Autosave debounce fix in `ChapterEditor.jsx` — same commit.
  Single shared timer (useRef), reset per keystroke. Previously spawned a new timer per keystroke, causing N saves per sentence.
- Save indicator ("Zapisywanie…" / "Zapisano HH:MM") added to toolbar in `ChapterEditor.jsx` — completes the previously unused `saving`/`lastSaved` state. Also clears all ESLint errors in the file. (Session 20.)

## Conventions for specs

Each spec has:

- **Context** — why this spec exists, what problem it solves.
- **Scope** — checklist of features/fixes.
- **Out of scope** — explicit non-goals, so the implementer doesn't scope-creep.
- **Data model** — DB migrations (SQL), API contracts.
- **UX notes** — where each feature lives in the UI.
- **Implementation plan** — ordered steps; each step is small enough for one commit.
- **Testing checklist** — what to verify before marking done.
- **Open questions** — things that need Piotr's call before implementation.

## Status legend

- 📝 Ready — spec is written, implementation can start.
- 🚧 In progress — implementation started (add commit refs here).
- ✅ Done — all scope items merged to main.
- ⏸️ Paused — intentionally on hold.
