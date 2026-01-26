-- ============================================
-- TIOLIBRI - Storage RLS Policies ONLY
-- Buckets already created manually
-- ============================================

-- ============================================
-- UPLOADS BUCKET
-- ============================================

CREATE POLICY "Users can view own files in uploads"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'uploads'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can upload to own projects in uploads"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'uploads'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can update own files in uploads"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'uploads'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can delete own files in uploads"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'uploads'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

-- ============================================
-- ASSETS BUCKET
-- ============================================

CREATE POLICY "Users can view own files in assets"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'assets'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can upload to own projects in assets"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'assets'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can update own files in assets"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'assets'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can delete own files in assets"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'assets'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

-- ============================================
-- OUTPUTS BUCKET
-- ============================================

CREATE POLICY "Users can view own files in outputs"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'outputs'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can upload to own projects in outputs"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'outputs'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can update own files in outputs"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'outputs'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can delete own files in outputs"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'outputs'
    AND (storage.foldername(name))[1] IN (
        SELECT id::text FROM public.projects WHERE user_id = auth.uid()
    )
);
