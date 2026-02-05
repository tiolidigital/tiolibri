-- Migration: Add sort_order column to chapters table
-- Date: 2026-02-05
-- Purpose: Enable manual chapter reordering via drag & drop

-- 1. Add sort_order column (allows NULL initially for existing rows)
ALTER TABLE chapters
ADD COLUMN IF NOT EXISTS sort_order integer;

-- 2. Populate sort_order for existing chapters (sorted by created_at)
WITH ranked_chapters AS (
  SELECT
    id,
    ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY created_at) AS rn
  FROM chapters
)
UPDATE chapters
SET sort_order = ranked_chapters.rn
FROM ranked_chapters
WHERE chapters.id = ranked_chapters.id
  AND chapters.sort_order IS NULL;

-- 3. Make sort_order NOT NULL after backfilling data
ALTER TABLE chapters
ALTER COLUMN sort_order SET NOT NULL;

-- 4. Add default value for new inserts (will be overridden by application)
ALTER TABLE chapters
ALTER COLUMN sort_order SET DEFAULT 1;

-- 5. Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_chapters_project_sort
ON chapters(project_id, sort_order);

-- Rollback script (if needed):
-- ALTER TABLE chapters DROP COLUMN sort_order;
-- DROP INDEX IF EXISTS idx_chapters_project_sort;
