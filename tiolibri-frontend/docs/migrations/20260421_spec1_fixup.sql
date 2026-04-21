-- ============================================================
-- SPEC-1 Phase 1 — Fixup: lock down search_path on SECURITY
-- DEFINER helper to close a potential privilege-escalation path.
--
-- Why: without an explicit search_path, a role that can create
-- tables in a schema earlier in the resolution order could shadow
-- `projects` / `project_shares` and trick the helper into returning
-- TRUE for projects they don't own. Supabase's security advisor
-- flags this on every SECURITY DEFINER function.
--
-- Run in Supabase SQL Editor after 20260421_spec1.sql.
-- ============================================================

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
