# SPEC 1 — Safety & Collaboration

**Priority:** 🔴 Critical
**Status:** 📝 Ready
**Estimated effort:** 1–2 weeks
**Written:** 2026-04-21

---

## Context

Piotr and Kasia are actively working on two books in TIOLIBRI. The app currently has no safety nets against:

- Accidental deletion of chapters (permanent delete, no undo).
- Bad edits overwriting good work (no version history).
- Collaborators editing each other into oblivion (no activity log, no locks).
- Data loss on DB corruption / Supabase outage (no export backup).

There are also plans to onboard 2–3 internal collaborators (small team, no public launch). Live collaboration (Google-Docs-style CRDT) is overkill for ~5 users — this spec deliberately chooses **asynchronous sharing** instead: one user edits at a time, with clear attribution and recovery paths.

A frontend audit in session 20 also surfaced two security-relevant issues that must be addressed before enabling sharing:
- Most backend requests don't send the Supabase auth token (anyone can hit `/generate`, `/chapters/reorder`).
- There's a race condition in `loadContent` (EditorPage.jsx) that can load stale content into a newly-selected chapter.

This spec bundles all of the above into a single coherent change because they share a data model and a UX surface (the "Inspector" panel).

---

## Scope

### Safety features
- [ ] **Version history** — snapshot on every save, compare + restore.
- [ ] **Project-level snapshots** — full backup of project state every 6h if changes occurred.
- [ ] **Export/import `.tiolibri`** — portable offline backup format.
- [ ] **Soft delete** — deleted chapters land in a Trash, restorable for 30 days.

### Collaboration features
- [ ] **Project shares** — owner invites user by email; user sees shared project in their dashboard.
- [ ] **Activity log** — per-project timeline of who did what.
- [ ] **Chapter lock** — owner can mark a chapter read-only ("done, don't touch").
- [ ] **Chapter status** — draft / review / done, color-coded in ChapterList.

### P0 audit fixes (required for share safety)
- [ ] Add auth Bearer token to all backend fetch calls.
- [ ] Fix race condition in `loadContent` with AbortController.
- [ ] Extend RLS policies on `chapters`/`assets`/`generated_files` to honor `project_shares`.

### Already done (don't re-implement)
- [x] Cursor-jump fix (commit `638095f`).
- [x] Autosave debounce fix (commit `638095f`).

---

## Out of scope

- Live collaborative editing (CRDT, OT, cursors-visible). Deferred indefinitely — wrong tool for ~5 users.
- Fine-grained permissions (read-only collaborators, commenter role). Everyone with share = full edit access. May revisit later.
- Email notifications for share invites / activity. For now the other user just sees the project appear in their dashboard on next load.
- Public sharing (view by link for non-users). Out of scope for this internal tool.
- WYSIWYG preview (Spec 2).
- Find & replace (Spec 2).

---

## Data model

### New tables

```sql
-- ============================================
-- Per-save snapshots of a chapter
-- ============================================
CREATE TABLE chapter_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    content TEXT NOT NULL,                  -- full processed_html at save time
    title_snapshot TEXT,                    -- chapter title at save time
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chapter_versions_chapter_created
    ON chapter_versions(chapter_id, created_at DESC);

-- Retention: keep newest 20 versions per chapter.
-- Enforced by a trigger (see below) or by a periodic cleanup job.
-- Tunable — bump to 30-50 if disk usage stays small and users want more headroom.

-- ============================================
-- Full project snapshots (every 6h if changed)
-- ============================================
CREATE TABLE project_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    snapshot JSONB NOT NULL,                -- full project + chapters + typography
    triggered_by TEXT NOT NULL              -- 'auto' | 'manual' | 'pre-restore'
        CHECK (triggered_by IN ('auto', 'manual', 'pre-restore')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_project_snapshots_project_created
    ON project_snapshots(project_id, created_at DESC);

-- Retention: keep newest 15 per project.
-- Snapshot contains text + asset REFERENCES (URLs), not asset files themselves.
-- Assets are append-only (see ALTER TABLE assets below) so old snapshot URLs stay valid.

-- ============================================
-- Soft-delete support on chapters
-- ============================================
ALTER TABLE chapters ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE chapters ADD COLUMN deleted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE INDEX idx_chapters_active ON chapters(project_id) WHERE deleted_at IS NULL;

-- ============================================
-- Chapter lock + status
-- ============================================
ALTER TABLE chapters ADD COLUMN locked_by UUID REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE chapters ADD COLUMN locked_at TIMESTAMPTZ;
ALTER TABLE chapters ADD COLUMN status TEXT DEFAULT 'draft'
    CHECK (status IN ('draft', 'review', 'done'));

-- ============================================
-- Assets append-only (protects snapshots)
-- ============================================
-- When user "deletes" an image from a chapter, we set archived_at instead of
-- removing the file from storage. Snapshot URLs stay valid forever.
-- Storage grows, but slowly (images are write-once in practice).
-- A future cleanup job can hard-delete assets where archived_at > 90 days AND
-- no snapshot references them — but not needed for v1.
ALTER TABLE assets ADD COLUMN archived_at TIMESTAMPTZ;
ALTER TABLE assets ADD COLUMN archived_by UUID REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE INDEX idx_assets_active ON assets(project_id) WHERE archived_at IS NULL;

-- ============================================
-- Project shares
-- ============================================
CREATE TABLE project_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (project_id, shared_with_user_id)
);

CREATE INDEX idx_project_shares_user ON project_shares(shared_with_user_id);

-- ============================================
-- Activity log
-- ============================================
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action_type TEXT NOT NULL,              -- 'chapter.create' | 'chapter.edit' | 'chapter.delete' | 'chapter.restore' | 'chapter.rename' | 'chapter.lock' | 'chapter.unlock' | 'chapter.status_change' | 'typography.update' | 'project.share' | 'project.unshare' | 'project.restore_snapshot' | 'project.rename'
    target_id UUID,                         -- chapter_id, share_id, etc.
    details JSONB DEFAULT '{}',             -- action-specific payload (old/new title, diff stats, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_log_project_created
    ON activity_log(project_id, created_at DESC);
```

### Updated RLS policies (share-aware)

Replace existing `chapters` / `assets` / `generated_files` policies with helper function:

```sql
CREATE OR REPLACE FUNCTION user_has_project_access(p_project_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM projects
        WHERE id = p_project_id AND user_id = auth.uid()
    ) OR EXISTS (
        SELECT 1 FROM project_shares
        WHERE project_id = p_project_id AND shared_with_user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Then rewrite chapters policies:
DROP POLICY IF EXISTS "Users can view own chapters" ON chapters;
CREATE POLICY "Users can view accessible chapters" ON chapters
    FOR SELECT USING (user_has_project_access(project_id));

-- (Same pattern for INSERT / UPDATE / DELETE on chapters, assets, generated_files.)

-- For project_snapshots + chapter_versions + activity_log, same pattern.
-- Share and unshare restricted to project owner only:
CREATE POLICY "Owners can manage shares" ON project_shares
    FOR ALL USING (
        EXISTS (SELECT 1 FROM projects WHERE id = project_id AND user_id = auth.uid())
    );

-- Shared users can see project_shares row that belongs to them (so dashboard shows shared projects):
CREATE POLICY "Users can view shares to themselves" ON project_shares
    FOR SELECT USING (shared_with_user_id = auth.uid());

-- Projects table: allow shared users to SELECT:
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
CREATE POLICY "Users can view accessible projects" ON projects
    FOR SELECT USING (user_has_project_access(id));
-- INSERT/DELETE stays owner-only. UPDATE stays owner-only for now — shared users can edit chapters but not rename/delete project itself.
```

### `.tiolibri` file format

ZIP archive with the following structure:

```
project.tiolibri (ZIP)
├── manifest.json         # { version: 1, exported_at, project_id, exporter_email }
├── project.json          # full project row (title, author, language, style_preset, typography_settings, status)
├── chapters.json         # array of chapters (id, title, sort_order, processed_html, status, created_at)
├── assets/               # all asset files referenced by chapters
│   ├── cover.jpg
│   └── images/
│       └── ...
└── README.txt            # human-readable description of what this file is
```

On import: create a new project owned by the importing user (NOT restore into existing). Generate new UUIDs for project + chapters. Copy referenced assets into storage. Log a single `project.import_from_tiolibri` activity entry.

---

## API contracts

### New backend endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET    | `/projects/{id}/chapters/{chapter_id}/versions` | List versions (newest first, paginated). |
| GET    | `/projects/{id}/chapters/{chapter_id}/versions/{version_id}` | Get one version's full content. |
| POST   | `/projects/{id}/chapters/{chapter_id}/versions/{version_id}/restore` | Restore this version (creates a new version from current state first). |
| GET    | `/projects/{id}/snapshots` | List project snapshots. |
| POST   | `/projects/{id}/snapshots` | Create manual snapshot (on-demand). |
| POST   | `/projects/{id}/snapshots/{snapshot_id}/restore` | Restore full project state. Takes a `pre-restore` snapshot first. |
| POST   | `/projects/{id}/export` | Generate `.tiolibri` ZIP and return download URL. |
| POST   | `/projects/import` | Accept `.tiolibri` multipart upload, return new project id. |
| POST   | `/projects/{id}/share` | Body: `{ email }`. Looks up user by email, creates `project_shares` row. |
| DELETE | `/projects/{id}/share/{share_id}` | Revoke share. |
| GET    | `/projects/{id}/activity` | List activity log (paginated). |
| POST   | `/chapters/{id}/restore` | Restore soft-deleted chapter (clears `deleted_at`). |
| POST   | `/chapters/{id}/lock` | Lock/unlock (toggle based on `locked_by`). |
| PATCH  | `/chapters/{id}/status` | Body: `{ status: 'draft' \| 'review' \| 'done' }`. |

**All new endpoints MUST verify auth via Supabase JWT** (FastAPI dependency that reads `Authorization: Bearer <token>`, validates with Supabase). This is already how `/projects/{id}/duplicate` works — extend that pattern.

### Frontend API helper

Create `tiolibri-frontend/src/lib/authedFetch.js`:

```js
import { supabase } from './supabase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function authedFetch(path, options = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }
  const res = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.message || `HTTP ${res.status}`)
  }
  return res.json()
}
```

Then replace every raw `fetch(${API_URL}...)` call in the frontend with `authedFetch(...)`. Sites to update:
- [GenerateBooks.jsx:47](../../tiolibri-frontend/src/features/editor/GenerateBooks.jsx#L47)
- [useChapters.js:122](../../tiolibri-frontend/src/features/editor/useChapters.js#L122)
- [useProjects.js:89](../../tiolibri-frontend/src/features/projects/useProjects.js#L89) (already has auth, refactor to use helper)
- [api.js:15](../../tiolibri-frontend/src/lib/api.js#L15) — the generic `request()` function.

---

## UX notes

### Inspector panel — new sections

Add two new `CollapsibleSection` in EditorPage right panel:

- **History** — lists recent versions of the currently selected chapter. Click to preview in a modal with split-pane diff view. "Restore this version" button.
- **Collaboration** — share controls (list current shares, "Add collaborator" form with email input). Only visible if current user is project owner. Also shows activity log (last 20 events) with "See all" link to full modal.

### Chapter list — status + lock

In `ChapterList`, each chapter row shows:
- Small colored dot left of title: gray=draft, yellow=review, green=done.
- Lock icon if `locked_by` is set, with tooltip "Locked by {user_email}".
- Right-click menu (already exists for rename) extended with:
  - Set status → Draft / Review / Done
  - Lock / Unlock (only shown for owner)
  - Move to Trash (replaces current hard delete)

If chapter is locked AND current user is not the locker, `ChapterEditor` renders read-only (TipTap `editable: false`).

### Trash

New "Trash" accordion section in the left sidebar (below Chapters). Shows soft-deleted chapters from current project. Actions:
- Restore → clear `deleted_at`, return to chapter list.
- Delete forever → hard delete + remove source file from storage.

Auto-purge after 30 days (backend cron, simple daily job).

### Dashboard — shared projects

`Dashboard` shows two sections when user has shares: "My projects" and "Shared with me". Shared projects show owner's email + "Shared by" badge.

### Export / Import

New menu in ProjectCard kebab:
- "Export backup (.tiolibri)" — downloads ZIP.
- (Only on dashboard, not inside project): "Import backup" button → file picker → upload → new project appears.

### Activity log modal

Full-screen modal, Google-Docs-style list grouped by day:

```
─── Today ───
👤 Kasia  14:32  edited "Wstęp"
👤 Piotr  13:10  renamed chapter "Rozdział 2" → "Dzieciństwo"
👤 Kasia  12:45  changed typography (font: Merriweather → Lora)

─── Yesterday ───
👤 Piotr  18:22  shared project with kasia@...
👤 Piotr  18:01  created project
```

---

## Implementation plan

Ordered for atomic commits; each step should be independently reviewable and deployable.

**Session strategy:** Each Phase below should be implemented in a **separate Claude Code session** (new thread with Sonet). This keeps context focused, token usage sane, and makes each phase easier to review independently. Before starting a new phase, the previous phase should be merged to `main` and verified working.

**Between phases:** run a code review pass (can be this file + git diff of merged work). Fix anything flagged before starting the next phase.

### Phase 1 — Foundations (no visible UI change)

> ⚠️ **BEFORE anything else: Auth spike test.** Historically Piotr hit "JWT not working" issues on Supabase — root cause unclear. Before we commit to auth-everywhere, verify JWT works end-to-end on a single endpoint. If it fails, we diagnose and fix ONCE here, not 10 times across the codebase.
>
> **Spike procedure (before step 1):**
> - Add FastAPI dependency `verify_supabase_jwt(authorization: str = Header(...))` that validates the token using Supabase's JWT public key (or by calling `supabase.auth.get_user(token)`).
> - Apply it to `/generate` only (highest-risk unauthed endpoint today).
> - Frontend: update `GenerateBooks.jsx` to send Bearer token.
> - Test:
>   - (a) Click "Generate" while logged in → works.
>   - (b) Log out, click "Generate" → 401.
>   - (c) Log in, wait 1h, click "Generate" → works (token auto-refresh).
>   - (d) Curl `/generate` without header → 401.
> - If all pass → proceed with step 1 below.
> - If something fails → diagnose first. Likely suspects: wrong `SUPABASE_JWT_SECRET` in backend env, `supabase-js` not refreshing tokens, CORS preflight issues.
>
> **Note on keys:** Backend currently uses `SUPABASE_SERVICE_KEY` which bypasses RLS. Continue using it for DB ops (SECURITY DEFINER pattern), but add a **separate** Supabase client with anon key for token verification. Don't mix them.

1. **DB migrations** — all `CREATE TABLE` + `ALTER TABLE` + new RLS policies. Single SQL file `tiolibri-frontend/docs/migrations/20260421_spec1.sql`. Run in Supabase SQL Editor.
2. **`authedFetch` helper** — create + wire through `api.js`. No behavior change, just defense.
3. **Backend auth dependency** — now that the spike proved it works, apply the auth dependency to all other endpoints: `/chapters/reorder`, `/projects/{id}/duplicate` (replace ad-hoc check), and all new endpoints from this spec.
4. **Fix `loadContent` race** — AbortController in `EditorPage.jsx:147-176`.

### Phase 2 — Version history (contained, visible in-editor)
5. **Backend version write path** — add a hook in `PATCH /chapters/{id}` (or wherever `processed_html` is updated) to insert into `chapter_versions`. Enforce "keep newest 30" via a trigger or inline query.
6. **Backend version read/restore endpoints** — the three `.../versions` routes above.
7. **Frontend History section** — CollapsibleSection in Inspector, list of versions with relative time + author initial.
8. **Frontend diff viewer** — modal with split pane, `diff-match-patch` library for text diff. Restore button calls backend.

### Phase 3 — Soft delete + status + lock
9. **Backend soft-delete** — change `DELETE /chapters/{id}` to set `deleted_at` instead of hard delete. Add `POST /chapters/{id}/restore`, and keep a separate `DELETE .../permanent` for hard delete from Trash.
10. **Frontend Trash UI** — new section in sidebar, list + restore + delete-forever.
11. **Backend status + lock endpoints** — `PATCH .../status`, `POST .../lock`.
12. **Frontend chapter status UI** — dot indicator, right-click menu.
13. **Frontend lock UI** — lock icon, read-only editor when locked by someone else.

### Phase 4 — Sharing + activity log
14. **Backend share endpoints** — `POST /projects/{id}/share` (looks up user by email), `DELETE .../share/{share_id}`. Return 404 if email not found (explicit error).
15. **Frontend share UI** — Collaboration section in Inspector. Email input, list of current shares, remove button.
16. **Dashboard "Shared with me"** — query `project_shares` joined with `projects`, render as separate section.
17. **Activity log write path** — backend writes to `activity_log` on all mutating endpoints. Centralize via a helper function.
18. **Activity log UI** — last 20 events inline in Collaboration section + "See all" modal with full pagination.

### Phase 5 — Project snapshots + export/import
19. **Backend snapshot scheduler** — a simple cron-ish approach: on each write to project/chapters, check `last_snapshot_at` from `project_snapshots`. If >6h and changes exist, create snapshot. (Simpler than a real scheduler.)
20. **Backend restore-snapshot endpoint** — restores project + chapters from JSONB, takes a `pre-restore` snapshot first.
21. **Frontend snapshots UI** — list in Inspector (under History), "Restore this snapshot" with confirmation dialog.
22. **Backend export/import endpoints** — ZIP builder, ZIP parser. Use Python `zipfile` + `json`.
23. **Frontend export/import UI** — ProjectCard kebab option, Dashboard import button.

---

## Testing checklist

Before marking SPEC-1 done:

- [ ] Type 200 characters in an editor, verify ONE save happens, then check `chapter_versions` has exactly one new row (not 200).
- [ ] Edit a chapter, close browser, reopen — verify chapter loads with last saved content.
- [ ] Delete a chapter → appears in Trash → restore → back in chapter list, no data loss.
- [ ] Share project with second user, second user sees it on dashboard, can edit chapters, cannot delete project.
- [ ] Try to hit `POST /projects/{id}/duplicate` without Bearer token — get 401. Same for `/generate`, `/chapters/reorder`.
- [ ] Rapidly click between 5 chapters — verify no "wrong content in wrong chapter" (race condition).
- [ ] Lock chapter as User A, verify User B sees read-only editor with lock indicator.
- [ ] Restore a version — verify current state becomes a new version first (no data loss).
- [ ] Export `.tiolibri`, delete original project, import — verify all chapters, typography, cover image preserved.
- [ ] Activity log shows correct actor + timestamp for: edit, rename, status change, lock, share, restore.
- [ ] RLS: User B cannot SELECT chapters from User A's non-shared project (test with Supabase REST directly).
- [ ] Snapshot auto-created after 6h + changes; manual snapshot works; restore creates pre-restore snapshot.

---

## Decisions (from session 20 conversation)

1. **Version retention:** chapter_versions = **20** per chapter, project_snapshots = **15** per project. Tunable later if needed. ✅ decided.
2. **Project snapshot frequency: every 6h** if changes exist. ✅ decided.
3. **Snapshots contain text + asset URLs** (not embedded asset bytes). Protected by making assets append-only (soft-archive instead of hard-delete). ✅ decided.
4. **Share by email:** if email doesn't match a user → error "no such user, ask them to register first." No email invite flow in v1. ✅ decided.
5. **Shared users have full edit access** including project metadata (rename, typography, cover) but NOT project delete. Only owner can delete. ✅ decided.
6. **Trash auto-purge: 30 days.** ✅ decided.
7. **Activity log visible to everyone** with project access. ✅ decided.
8. **Chapter unlock:** both the locker AND the project owner can unlock. No force-unlock by other shared users. ✅ decided.

## Open questions for Piotr

*None remaining — all decisions made in session 20 (2026-04-21). Any questions that emerge during implementation should be raised in the implementation thread.*

---

## Dependencies & risks

- **Supabase RLS function `user_has_project_access`** uses `SECURITY DEFINER` — verify this doesn't create a privilege escalation path. Test thoroughly.
- **`.tiolibri` format versioned at v1** — future changes must bump version and handle both on import.
- **Snapshot size limit** — if a project grows beyond a few MB of text, JSONB snapshot may become unwieldy. Monitor row sizes; consider external storage for snapshots if books exceed 500KB text.
- **Frontend `authedFetch` refactor touches many files** — do it early (Phase 1) to avoid mixed patterns during other work.
- **Phase 4 shares require email lookup on backend** — Supabase admin API needed (`supabase.auth.admin.listUsers()` or similar). Verify service-role key is available in backend env.
