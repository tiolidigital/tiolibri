-- ============================================
-- TIOLIBRI - Supabase Storage Setup
-- Run this AFTER supabase-schema.sql
-- ============================================

BEGIN;

-- ============================================
-- 1. CREATE STORAGE BUCKETS
-- ============================================

-- Uploads bucket - HTML files from Google Docs
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'uploads',
    'uploads',
    false,
    10485760, -- 10MB limit
    ARRAY['text/html', 'application/xhtml+xml']
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 10485760,
    allowed_mime_types = ARRAY['text/html', 'application/xhtml+xml'];

-- Assets bucket - images, SVG dividers
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'assets',
    'assets',
    false,
    5242880, -- 5MB limit
    ARRAY['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/svg+xml']
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 5242880,
    allowed_mime_types = ARRAY['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/svg+xml'];

-- Outputs bucket - generated EPUB/PDF
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'outputs',
    'outputs',
    false,
    52428800, -- 50MB limit
    ARRAY['application/epub+zip', 'application/pdf']
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 52428800,
    allowed_mime_types = ARRAY['application/epub+zip', 'application/pdf'];

-- ============================================
-- 2. HELPER FUNCTION - Check project ownership
-- ============================================

CREATE OR REPLACE FUNCTION storage.user_owns_project(project_uuid TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.projects
        WHERE id::text = project_uuid
        AND user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 3. RLS POLICIES - UPLOADS BUCKET
-- ============================================

-- SELECT: Users can view files in their own projects
DROP POLICY IF EXISTS "Users can view own files in uploads" ON storage.objects;
CREATE POLICY "Users can view own files in uploads" ON storage.objects
    FOR SELECT
    USING (
        bucket_id = 'uploads'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

-- INSERT: Users can upload to their own projects
DROP POLICY IF EXISTS "Users can upload to own projects in uploads" ON storage.objects;
CREATE POLICY "Users can upload to own projects in uploads" ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'uploads'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

-- UPDATE: Users can update files in their own projects
DROP POLICY IF EXISTS "Users can update own files in uploads" ON storage.objects;
CREATE POLICY "Users can update own files in uploads" ON storage.objects
    FOR UPDATE
    USING (
        bucket_id = 'uploads'
        AND storage.user_owns_project((storage.foldername(name))[1])
    )
    WITH CHECK (
        bucket_id = 'uploads'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

-- DELETE: Users can delete files from their own projects
DROP POLICY IF EXISTS "Users can delete own files in uploads" ON storage.objects;
CREATE POLICY "Users can delete own files in uploads" ON storage.objects
    FOR DELETE
    USING (
        bucket_id = 'uploads'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

-- ============================================
-- 4. RLS POLICIES - ASSETS BUCKET
-- ============================================

DROP POLICY IF EXISTS "Users can view own files in assets" ON storage.objects;
CREATE POLICY "Users can view own files in assets" ON storage.objects
    FOR SELECT
    USING (
        bucket_id = 'assets'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

DROP POLICY IF EXISTS "Users can upload to own projects in assets" ON storage.objects;
CREATE POLICY "Users can upload to own projects in assets" ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'assets'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

DROP POLICY IF EXISTS "Users can update own files in assets" ON storage.objects;
CREATE POLICY "Users can update own files in assets" ON storage.objects
    FOR UPDATE
    USING (
        bucket_id = 'assets'
        AND storage.user_owns_project((storage.foldername(name))[1])
    )
    WITH CHECK (
        bucket_id = 'assets'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

DROP POLICY IF EXISTS "Users can delete own files in assets" ON storage.objects;
CREATE POLICY "Users can delete own files in assets" ON storage.objects
    FOR DELETE
    USING (
        bucket_id = 'assets'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

-- ============================================
-- 5. RLS POLICIES - OUTPUTS BUCKET
-- ============================================

DROP POLICY IF EXISTS "Users can view own files in outputs" ON storage.objects;
CREATE POLICY "Users can view own files in outputs" ON storage.objects
    FOR SELECT
    USING (
        bucket_id = 'outputs'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

DROP POLICY IF EXISTS "Users can upload to own projects in outputs" ON storage.objects;
CREATE POLICY "Users can upload to own projects in outputs" ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'outputs'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

DROP POLICY IF EXISTS "Users can update own files in outputs" ON storage.objects;
CREATE POLICY "Users can update own files in outputs" ON storage.objects
    FOR UPDATE
    USING (
        bucket_id = 'outputs'
        AND storage.user_owns_project((storage.foldername(name))[1])
    )
    WITH CHECK (
        bucket_id = 'outputs'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

DROP POLICY IF EXISTS "Users can delete own files in outputs" ON storage.objects;
CREATE POLICY "Users can delete own files in outputs" ON storage.objects
    FOR DELETE
    USING (
        bucket_id = 'outputs'
        AND storage.user_owns_project((storage.foldername(name))[1])
    );

COMMIT;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check buckets exist:
-- SELECT id, name, public, file_size_limit, allowed_mime_types FROM storage.buckets;

-- Check storage policies:
-- SELECT policyname, tablename FROM pg_policies WHERE schemaname = 'storage';

-- ============================================
-- USAGE EXAMPLES (from frontend)
-- ============================================

-- Upload file:
-- const { data, error } = await supabase.storage
--   .from('uploads')
--   .upload(`${projectId}/${filename}.html`, file);

-- Download file:
-- const { data, error } = await supabase.storage
--   .from('outputs')
--   .download(`${projectId}/ebook.epub`);

-- Get signed URL (for download links):
-- const { data } = await supabase.storage
--   .from('outputs')
--   .createSignedUrl(`${projectId}/ebook.epub`, 3600); // 1 hour
