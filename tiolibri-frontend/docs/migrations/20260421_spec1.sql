-- ============================================================
-- SPEC-1: Safety & Collaboration — Phase 1 Foundations
-- Run in Supabase SQL Editor (single transaction)
-- ============================================================

BEGIN;

-- ============================================================
-- 1. chapter_versions
-- ============================================================
CREATE TABLE IF NOT EXISTS chapter_versions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id  UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    title_snapshot TEXT,
    created_by  UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chapter_versions_chapter_created
    ON chapter_versions(chapter_id, created_at DESC);

-- Trigger: keep newest 20 versions per chapter
CREATE OR REPLACE FUNCTION prune_chapter_versions()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM chapter_versions
    WHERE chapter_id = NEW.chapter_id
      AND id NOT IN (
          SELECT id FROM chapter_versions
          WHERE chapter_id = NEW.chapter_id
          ORDER BY created_at DESC
          LIMIT 20
      );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prune_chapter_versions ON chapter_versions;
CREATE TRIGGER trg_prune_chapter_versions
    AFTER INSERT ON chapter_versions
    FOR EACH ROW EXECUTE FUNCTION prune_chapter_versions();


-- ============================================================
-- 2. project_snapshots
-- ============================================================
CREATE TABLE IF NOT EXISTS project_snapshots (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    snapshot     JSONB NOT NULL,
    triggered_by TEXT NOT NULL
        CHECK (triggered_by IN ('auto', 'manual', 'pre-restore')),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_snapshots_project_created
    ON project_snapshots(project_id, created_at DESC);

-- Trigger: keep newest 15 snapshots per project
CREATE OR REPLACE FUNCTION prune_project_snapshots()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM project_snapshots
    WHERE project_id = NEW.project_id
      AND id NOT IN (
          SELECT id FROM project_snapshots
          WHERE project_id = NEW.project_id
          ORDER BY created_at DESC
          LIMIT 15
      );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prune_project_snapshots ON project_snapshots;
CREATE TRIGGER trg_prune_project_snapshots
    AFTER INSERT ON project_snapshots
    FOR EACH ROW EXECUTE FUNCTION prune_project_snapshots();


-- ============================================================
-- 3. chapters — soft delete + lock + status
-- ============================================================
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS deleted_at  TIMESTAMPTZ;
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS deleted_by  UUID REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS locked_by   UUID REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS locked_at   TIMESTAMPTZ;
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS status      TEXT DEFAULT 'draft'
    CHECK (status IN ('draft', 'review', 'done'));

CREATE INDEX IF NOT EXISTS idx_chapters_active
    ON chapters(project_id) WHERE deleted_at IS NULL;


-- ============================================================
-- 4. assets — append-only (soft archive)
-- ============================================================
ALTER TABLE assets ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS archived_by UUID REFERENCES auth.users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_assets_active
    ON assets(project_id) WHERE archived_at IS NULL;


-- ============================================================
-- 5. project_shares
-- ============================================================
CREATE TABLE IF NOT EXISTS project_shares (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shared_by_user_id   UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (project_id, shared_with_user_id)
);

CREATE INDEX IF NOT EXISTS idx_project_shares_user
    ON project_shares(shared_with_user_id);


-- ============================================================
-- 6. activity_log
-- ============================================================
CREATE TABLE IF NOT EXISTS activity_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id     UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action_type TEXT NOT NULL,
    target_id   UUID,
    details     JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_log_project_created
    ON activity_log(project_id, created_at DESC);


-- ============================================================
-- 7. RLS helper + updated policies
-- ============================================================

-- Helper function (SECURITY DEFINER to avoid row-level recursion).
-- search_path is pinned to block schema-shadowing attacks — a SECURITY
-- DEFINER function without this is an escalation path.
CREATE OR REPLACE FUNCTION user_has_project_access(p_project_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM projects
        WHERE id = p_project_id AND user_id = auth.uid()
    ) OR EXISTS (
        SELECT 1 FROM project_shares
        WHERE project_id = p_project_id AND shared_with_user_id = auth.uid()
    );
END;
$$;


-- projects: shared users can SELECT
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
CREATE POLICY "Users can view accessible projects" ON projects
    FOR SELECT USING (user_has_project_access(id));

-- chapters: replace owner-only SELECT with share-aware
DROP POLICY IF EXISTS "Users can view own chapters" ON chapters;
CREATE POLICY "Users can view accessible chapters" ON chapters
    FOR SELECT USING (user_has_project_access(project_id));

DROP POLICY IF EXISTS "Users can create own chapters" ON chapters;
CREATE POLICY "Users can insert accessible chapters" ON chapters
    FOR INSERT WITH CHECK (user_has_project_access(project_id));

DROP POLICY IF EXISTS "Users can update own chapters" ON chapters;
CREATE POLICY "Users can update accessible chapters" ON chapters
    FOR UPDATE USING (user_has_project_access(project_id));

DROP POLICY IF EXISTS "Users can delete own chapters" ON chapters;
CREATE POLICY "Users can delete accessible chapters" ON chapters
    FOR DELETE USING (user_has_project_access(project_id));

-- assets
DROP POLICY IF EXISTS "Users can view own assets" ON assets;
CREATE POLICY "Users can view accessible assets" ON assets
    FOR SELECT USING (user_has_project_access(project_id));

DROP POLICY IF EXISTS "Users can create own assets" ON assets;
CREATE POLICY "Users can insert accessible assets" ON assets
    FOR INSERT WITH CHECK (user_has_project_access(project_id));

DROP POLICY IF EXISTS "Users can update own assets" ON assets;
CREATE POLICY "Users can update accessible assets" ON assets
    FOR UPDATE USING (user_has_project_access(project_id));

DROP POLICY IF EXISTS "Users can delete own assets" ON assets;
CREATE POLICY "Users can delete accessible assets" ON assets
    FOR DELETE USING (user_has_project_access(project_id));

-- generated_files (original policy names use spaces, not underscores)
DROP POLICY IF EXISTS "Users can view own generated files" ON generated_files;
CREATE POLICY "Users can view accessible generated_files" ON generated_files
    FOR SELECT USING (user_has_project_access(project_id));

DROP POLICY IF EXISTS "Users can create own generated files" ON generated_files;
CREATE POLICY "Users can insert accessible generated_files" ON generated_files
    FOR INSERT WITH CHECK (user_has_project_access(project_id));

DROP POLICY IF EXISTS "Users can delete own generated files" ON generated_files;
CREATE POLICY "Users can delete accessible generated_files" ON generated_files
    FOR DELETE USING (user_has_project_access(project_id));

-- chapter_versions: follow chapter project access
ALTER TABLE chapter_versions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view accessible chapter_versions" ON chapter_versions;
CREATE POLICY "Users can view accessible chapter_versions" ON chapter_versions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM chapters c
            WHERE c.id = chapter_id AND user_has_project_access(c.project_id)
        )
    );
DROP POLICY IF EXISTS "Users can insert accessible chapter_versions" ON chapter_versions;
CREATE POLICY "Users can insert accessible chapter_versions" ON chapter_versions
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM chapters c
            WHERE c.id = chapter_id AND user_has_project_access(c.project_id)
        )
    );

-- project_snapshots
ALTER TABLE project_snapshots ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view accessible project_snapshots" ON project_snapshots;
CREATE POLICY "Users can view accessible project_snapshots" ON project_snapshots
    FOR SELECT USING (user_has_project_access(project_id));
DROP POLICY IF EXISTS "Users can insert accessible project_snapshots" ON project_snapshots;
CREATE POLICY "Users can insert accessible project_snapshots" ON project_snapshots
    FOR INSERT WITH CHECK (user_has_project_access(project_id));

-- project_shares: owner manages, shared user can see their own row
ALTER TABLE project_shares ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Owners can manage shares" ON project_shares;
CREATE POLICY "Owners can manage shares" ON project_shares
    FOR ALL USING (
        EXISTS (SELECT 1 FROM projects WHERE id = project_id AND user_id = auth.uid())
    );
DROP POLICY IF EXISTS "Users can view shares to themselves" ON project_shares;
CREATE POLICY "Users can view shares to themselves" ON project_shares
    FOR SELECT USING (shared_with_user_id = auth.uid());

-- activity_log: visible to anyone with project access
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view accessible activity_log" ON activity_log;
CREATE POLICY "Users can view accessible activity_log" ON activity_log
    FOR SELECT USING (user_has_project_access(project_id));
DROP POLICY IF EXISTS "Users can insert accessible activity_log" ON activity_log;
CREATE POLICY "Users can insert accessible activity_log" ON activity_log
    FOR INSERT WITH CHECK (user_has_project_access(project_id));

COMMIT;
