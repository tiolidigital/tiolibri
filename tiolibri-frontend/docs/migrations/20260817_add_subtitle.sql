-- ============================================================
-- Podtytuł książki na stronie tytułowej
-- Run in Supabase SQL Editor (single transaction)
-- ============================================================
-- Kolumna jest nullable i bez defaultu: istniejące projekty
-- zachowują dotychczasową stronę tytułową (tytuł + autor),
-- bo render podtytułu jest warunkowy.

BEGIN;

ALTER TABLE projects ADD COLUMN IF NOT EXISTS subtitle text;

COMMENT ON COLUMN projects.subtitle IS
    'Podtytuł książki renderowany na stronie tytułowej (PDF + EPUB). Nullable.';

COMMIT;
