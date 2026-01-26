-- ============================================
-- TIOLIBRI - Supabase Schema Setup
-- Run this in Supabase SQL Editor
-- ============================================

BEGIN;

-- ============================================
-- 1. PROJECTS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Nowy projekt',
    author TEXT DEFAULT '',
    language TEXT DEFAULT 'pl',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed')),
    style_preset TEXT DEFAULT 'classic' CHECK (style_preset IN ('classic', 'modern', 'minimal', 'custom')),
    custom_styles JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for user queries
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ============================================
-- 2. CHAPTERS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Rozdział',
    sort_order INTEGER DEFAULT 0,
    source_file_path TEXT,
    processed_html TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_chapters_project_id ON chapters(project_id);
CREATE INDEX IF NOT EXISTS idx_chapters_sort_order ON chapters(project_id, sort_order);

-- ============================================
-- 3. ASSETS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('image', 'divider')),
    file_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_assets_project_id ON assets(project_id);

-- ============================================
-- 4. GENERATED_FILES TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS generated_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    format TEXT NOT NULL CHECK (format IN ('epub', 'pdf')),
    file_path TEXT NOT NULL,
    file_size INTEGER,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_generated_files_project_id ON generated_files(project_id);

-- ============================================
-- 5. UPDATED_AT TRIGGER
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_chapters_updated_at ON chapters;
CREATE TRIGGER update_chapters_updated_at
    BEFORE UPDATE ON chapters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. ENABLE ROW LEVEL SECURITY
-- ============================================

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_files ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 7. RLS POLICIES - PROJECTS
-- ============================================

-- Users can view their own projects
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own projects
DROP POLICY IF EXISTS "Users can create own projects" ON projects;
CREATE POLICY "Users can create own projects" ON projects
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own projects
DROP POLICY IF EXISTS "Users can update own projects" ON projects;
CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own projects
DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- 8. RLS POLICIES - CHAPTERS
-- ============================================

-- Users can view chapters of their own projects
DROP POLICY IF EXISTS "Users can view own chapters" ON chapters;
CREATE POLICY "Users can view own chapters" ON chapters
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = chapters.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- Users can create chapters in their own projects
DROP POLICY IF EXISTS "Users can create own chapters" ON chapters;
CREATE POLICY "Users can create own chapters" ON chapters
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = chapters.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- Users can update chapters in their own projects
DROP POLICY IF EXISTS "Users can update own chapters" ON chapters;
CREATE POLICY "Users can update own chapters" ON chapters
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = chapters.project_id
            AND projects.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = chapters.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- Users can delete chapters from their own projects
DROP POLICY IF EXISTS "Users can delete own chapters" ON chapters;
CREATE POLICY "Users can delete own chapters" ON chapters
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = chapters.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- ============================================
-- 9. RLS POLICIES - ASSETS
-- ============================================

DROP POLICY IF EXISTS "Users can view own assets" ON assets;
CREATE POLICY "Users can view own assets" ON assets
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = assets.project_id
            AND projects.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can create own assets" ON assets;
CREATE POLICY "Users can create own assets" ON assets
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = assets.project_id
            AND projects.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can update own assets" ON assets;
CREATE POLICY "Users can update own assets" ON assets
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = assets.project_id
            AND projects.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = assets.project_id
            AND projects.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can delete own assets" ON assets;
CREATE POLICY "Users can delete own assets" ON assets
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = assets.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- ============================================
-- 10. RLS POLICIES - GENERATED_FILES
-- ============================================

DROP POLICY IF EXISTS "Users can view own generated files" ON generated_files;
CREATE POLICY "Users can view own generated files" ON generated_files
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = generated_files.project_id
            AND projects.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can create own generated files" ON generated_files;
CREATE POLICY "Users can create own generated files" ON generated_files
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = generated_files.project_id
            AND projects.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can delete own generated files" ON generated_files;
CREATE POLICY "Users can delete own generated files" ON generated_files
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = generated_files.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- ============================================
-- 11. STORAGE BUCKETS (run separately in Dashboard)
-- ============================================

-- Note: Storage buckets should be created via Supabase Dashboard:
-- 1. uploads   - for HTML files from Google Docs
-- 2. assets    - for images and dividers
-- 3. outputs   - for generated EPUB/PDF files
--
-- All buckets should be PRIVATE with RLS policies

COMMIT;

-- ============================================
-- VERIFICATION QUERIES (run after setup)
-- ============================================

-- Check tables exist:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Check RLS is enabled:
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- Check policies:
-- SELECT schemaname, tablename, policyname FROM pg_policies WHERE schemaname = 'public';
