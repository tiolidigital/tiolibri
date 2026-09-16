-- Blokada usuwania rozdzialow w projekcie „Grzyby lecznicze" (fe9cba47, kanon Bozeny).
-- 2026-09-16: przypadkowe usuniecie przekladki „CZESC I" podczas dodawania zdjec.
-- Edycja, dodawanie i zmiana kolejnosci dzialaja normalnie; blokowane jest tylko
-- przeniesienie do kosza (deleted_at) i twarde DELETE (takze kaskada z projektu).
-- STATUS 2026-09-16: NIE WYKONANA na bazie (PAT 401). Piotrek wybral blokade rozdzialow
-- w edytorze (locked_by) – blokuje usuwanie, ale tez edycje. Ta migracja zostaje jako
-- opcja na pozniej, gdyby trzeba bylo edytowac bez ryzyka usuniecia.
-- Zdjecie blokady: usunac projekt z listy w chapters_delete_protected_ids().

CREATE OR REPLACE FUNCTION public.chapters_delete_protected_ids()
RETURNS uuid[] LANGUAGE sql IMMUTABLE AS $$
  SELECT ARRAY['fe9cba47-9760-4a40-8030-d5bc5e70b512'::uuid]
$$;

CREATE OR REPLACE FUNCTION public.block_chapter_delete()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.project_id = ANY (public.chapters_delete_protected_ids()) THEN
      RAISE EXCEPTION 'Usuwanie rozdzialow w tym projekcie jest zablokowane';
    END IF;
    RETURN OLD;
  END IF;
  IF OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL
     AND NEW.project_id = ANY (public.chapters_delete_protected_ids()) THEN
    RAISE EXCEPTION 'Usuwanie rozdzialow w tym projekcie jest zablokowane';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_block_chapter_delete ON public.chapters;
CREATE TRIGGER trg_block_chapter_delete
  BEFORE UPDATE OF deleted_at OR DELETE ON public.chapters
  FOR EACH ROW EXECUTE FUNCTION public.block_chapter_delete();
