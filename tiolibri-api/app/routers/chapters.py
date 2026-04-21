from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.supabase_client import supabase
from app.services.activity import log_activity
from app.dependencies import verify_supabase_jwt
from app.routers.snapshots import maybe_auto_snapshot
from pydantic import BaseModel
from typing import Literal, Optional

router = APIRouter(prefix="/chapters", tags=["chapters"])


class ChapterUpdateRequest(BaseModel):
    processed_html: Optional[str] = None
    title: Optional[str] = None


class ChapterStatusRequest(BaseModel):
    status: Literal['draft', 'review', 'done']


# ---------------------------------------------------------------------------
# PATCH /chapters/{chapter_id}
# Save chapter content. Writes a version snapshot when processed_html changes.
# ---------------------------------------------------------------------------

@router.patch("/{chapter_id}")
async def update_chapter(
    chapter_id: str,
    body: ChapterUpdateRequest,
    user: dict = Depends(verify_supabase_jwt),
):
    chapter = _assert_chapter_access(chapter_id, user["id"])

    # Block edits when chapter is locked by someone else
    locked_by = chapter.get("locked_by")
    if locked_by and locked_by != user["id"]:
        raise HTTPException(status_code=403, detail="Chapter is locked by another user")

    updates = {}
    if body.processed_html is not None:
        updates["processed_html"] = body.processed_html
    if body.title is not None:
        updates["title"] = body.title

    if not updates:
        return {"chapter_id": chapter_id}

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    updated_resp = supabase.table("chapters").update(updates) \
        .eq("id", chapter_id).select().execute()

    if not updated_resp.data:
        raise HTTPException(status_code=500, detail="Failed to update chapter")

    # Snapshot version whenever content changes; use updated title if one was also sent.
    if body.processed_html is not None:
        title_snapshot = body.title if body.title is not None else chapter.get("title")
        _write_version(chapter_id, body.processed_html, title_snapshot, user["id"])

    updated_chapter = updated_resp.data[0]

    if body.title is not None and body.title != chapter.get("title"):
        log_activity(
            project_id=chapter["project_id"],
            user_id=user["id"],
            action_type="chapter.rename",
            target_id=chapter_id,
            details={"old_title": chapter.get("title"), "new_title": body.title},
        )
    elif body.processed_html is not None:
        _log_chapter_edit(chapter["project_id"], user["id"], chapter_id, chapter.get("title"))

    maybe_auto_snapshot(chapter["project_id"])

    return updated_chapter


# ---------------------------------------------------------------------------
# DELETE /chapters/{chapter_id}
# Soft-delete: sets deleted_at instead of removing the row.
# ---------------------------------------------------------------------------

@router.delete("/{chapter_id}")
async def soft_delete_chapter(
    chapter_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    chapter = _assert_chapter_access(chapter_id, user["id"])

    locked_by = chapter.get("locked_by")
    if locked_by and locked_by != user["id"]:
        raise HTTPException(status_code=403, detail="Chapter is locked by another user")

    now = datetime.now(timezone.utc).isoformat()
    resp = supabase.table("chapters").update({
        "deleted_at": now,
        "deleted_by": user["id"],
        "updated_at": now,
    }).eq("id", chapter_id).select().execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to delete chapter")

    log_activity(
        project_id=chapter["project_id"],
        user_id=user["id"],
        action_type="chapter.delete",
        target_id=chapter_id,
        details={"title": chapter.get("title")},
    )

    return {"deleted": True, "chapter_id": chapter_id}


# ---------------------------------------------------------------------------
# POST /chapters/{chapter_id}/restore
# Restore a soft-deleted chapter (clears deleted_at).
# ---------------------------------------------------------------------------

@router.post("/{chapter_id}/restore")
async def restore_chapter(
    chapter_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    # Fetch the chapter including deleted ones
    chapter_resp = supabase.table("chapters") \
        .select("id, project_id, deleted_at") \
        .eq("id", chapter_id).execute()

    if not chapter_resp.data:
        raise HTTPException(status_code=404, detail="Chapter not found")

    chapter = chapter_resp.data[0]

    if not chapter.get("deleted_at"):
        raise HTTPException(status_code=400, detail="Chapter is not in Trash")

    _assert_project_access(chapter["project_id"], user["id"])

    resp = supabase.table("chapters").update({
        "deleted_at": None,
        "deleted_by": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", chapter_id).select().execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to restore chapter")

    restored = resp.data[0]
    log_activity(
        project_id=chapter["project_id"],
        user_id=user["id"],
        action_type="chapter.restore",
        target_id=chapter_id,
        details={"title": restored.get("title")},
    )

    return {"restored": True, "chapter": restored}


# ---------------------------------------------------------------------------
# DELETE /chapters/{chapter_id}/permanent
# Hard-delete a soft-deleted chapter (from Trash only).
# ---------------------------------------------------------------------------

@router.delete("/{chapter_id}/permanent")
async def permanent_delete_chapter(
    chapter_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    chapter_resp = supabase.table("chapters") \
        .select("id, project_id, deleted_at, source_file_path") \
        .eq("id", chapter_id).execute()

    if not chapter_resp.data:
        raise HTTPException(status_code=404, detail="Chapter not found")

    chapter = chapter_resp.data[0]

    if not chapter.get("deleted_at"):
        raise HTTPException(status_code=400, detail="Chapter must be in Trash before permanent delete")

    _assert_project_access(chapter["project_id"], user["id"])

    # Remove source file from storage (best-effort)
    if chapter.get("source_file_path"):
        try:
            supabase.storage.from_("uploads").remove([chapter["source_file_path"]])
        except Exception:
            pass

    supabase.table("chapters").delete().eq("id", chapter_id).execute()

    return {"deleted_permanently": True, "chapter_id": chapter_id}


# ---------------------------------------------------------------------------
# GET /chapters/trash?project_id=...
# List soft-deleted chapters for a project.
# ---------------------------------------------------------------------------

@router.get("/trash")
async def list_trash(
    project_id: str = Query(...),
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_project_access(project_id, user["id"])

    resp = supabase.table("chapters") \
        .select("id, project_id, title, sort_order, deleted_at, deleted_by, status") \
        .eq("project_id", project_id) \
        .not_.is_("deleted_at", "null") \
        .order("deleted_at", desc=True) \
        .execute()

    return {"chapters": resp.data or []}


# ---------------------------------------------------------------------------
# PATCH /chapters/{chapter_id}/status
# Change chapter status: draft | review | done.
# ---------------------------------------------------------------------------

@router.patch("/{chapter_id}/status")
async def update_chapter_status(
    chapter_id: str,
    body: ChapterStatusRequest,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_chapter_access(chapter_id, user["id"])

    resp = supabase.table("chapters").update({
        "status": body.status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", chapter_id).select().execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to update status")

    chapter_row = resp.data[0]
    log_activity(
        project_id=chapter_row["project_id"],
        user_id=user["id"],
        action_type="chapter.status_change",
        target_id=chapter_id,
        details={"status": body.status, "title": chapter_row.get("title")},
    )

    return chapter_row


# ---------------------------------------------------------------------------
# POST /chapters/{chapter_id}/lock
# Toggle lock. Owner or current locker can lock/unlock.
# ---------------------------------------------------------------------------

@router.post("/{chapter_id}/lock")
async def toggle_lock(
    chapter_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    chapter = _assert_chapter_access(chapter_id, user["id"])
    locked_by = chapter.get("locked_by")

    # Determine whether the caller is the project owner
    project_id = chapter["project_id"]
    owner_resp = supabase.table("projects") \
        .select("id") \
        .eq("id", project_id) \
        .eq("user_id", user["id"]) \
        .execute()
    is_owner = bool(owner_resp.data)

    if locked_by:
        # Only the locker or owner can unlock
        if locked_by != user["id"] and not is_owner:
            raise HTTPException(status_code=403, detail="Only the locker or project owner can unlock")
        updates = {"locked_by": None, "locked_at": None}
    else:
        updates = {
            "locked_by": user["id"],
            "locked_at": datetime.now(timezone.utc).isoformat(),
        }

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    resp = supabase.table("chapters").update(updates).eq("id", chapter_id).select().execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to update lock")

    action = "chapter.unlock" if locked_by else "chapter.lock"
    log_activity(
        project_id=chapter["project_id"],
        user_id=user["id"],
        action_type=action,
        target_id=chapter_id,
        details={"title": chapter.get("title")},
    )

    return resp.data[0]


# ---------------------------------------------------------------------------
# GET /chapters/{chapter_id}/versions
# List versions newest-first, paginated.
# ---------------------------------------------------------------------------

@router.get("/{chapter_id}/versions")
async def list_versions(
    chapter_id: str,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_chapter_access(chapter_id, user["id"])

    versions_resp = supabase.table("chapter_versions") \
        .select("id, chapter_id, title_snapshot, created_by, created_at") \
        .eq("chapter_id", chapter_id) \
        .order("created_at", desc=True) \
        .range(offset, offset + limit - 1) \
        .execute()

    # Attach author emails for display
    versions = versions_resp.data or []
    user_ids = list({v["created_by"] for v in versions if v.get("created_by")})
    email_map = _fetch_user_emails(user_ids)

    for v in versions:
        v["author_email"] = email_map.get(v.get("created_by"))

    return {"versions": versions, "count": len(versions)}


# ---------------------------------------------------------------------------
# GET /chapters/{chapter_id}/versions/{version_id}
# Get one version's full content.
# ---------------------------------------------------------------------------

@router.get("/{chapter_id}/versions/{version_id}")
async def get_version(
    chapter_id: str,
    version_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_chapter_access(chapter_id, user["id"])
    version_resp = supabase.table("chapter_versions") \
        .select("*") \
        .eq("id", version_id) \
        .eq("chapter_id", chapter_id) \
        .execute()

    if not version_resp.data:
        raise HTTPException(status_code=404, detail="Version not found")

    version = version_resp.data[0]
    email_map = _fetch_user_emails([version["created_by"]] if version.get("created_by") else [])
    version["author_email"] = email_map.get(version.get("created_by"))

    return version


# ---------------------------------------------------------------------------
# POST /chapters/{chapter_id}/versions/{version_id}/restore
# Restore a past version. Saves current content as a new version first.
# ---------------------------------------------------------------------------

@router.post("/{chapter_id}/versions/{version_id}/restore")
async def restore_version(
    chapter_id: str,
    version_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    chapter = _assert_chapter_access(chapter_id, user["id"])

    locked_by = chapter.get("locked_by")
    if locked_by and locked_by != user["id"]:
        raise HTTPException(status_code=403, detail="Chapter is locked by another user")

    version_resp = supabase.table("chapter_versions") \
        .select("*") \
        .eq("id", version_id) \
        .eq("chapter_id", chapter_id) \
        .execute()

    if not version_resp.data:
        raise HTTPException(status_code=404, detail="Version not found")

    target_version = version_resp.data[0]

    # Snapshot current state before overwriting (so the user can undo the restore)
    if chapter.get("processed_html"):
        _write_version(chapter_id, chapter["processed_html"], chapter.get("title"), user["id"])

    # Apply the historical version
    restored_resp = supabase.table("chapters").update({
        "processed_html": target_version["content"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", chapter_id).select().execute()

    if not restored_resp.data:
        raise HTTPException(status_code=500, detail="Failed to restore version")

    log_activity(
        project_id=chapter["project_id"],
        user_id=user["id"],
        action_type="chapter.restore_version",
        target_id=chapter_id,
        details={"version_id": version_id, "title": chapter.get("title")},
    )

    return {"restored": True, "chapter": restored_resp.data[0]}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_chapter_access(chapter_id: str, user_id: str) -> dict:
    """
    Fetch the chapter (non-deleted) and verify the caller has project access.
    Raises 404 if not found, 403 if the caller has no project access.
    Returns the chapter row.
    """
    chapter_resp = supabase.table("chapters") \
        .select("id, project_id, title, processed_html, locked_by") \
        .eq("id", chapter_id).is_("deleted_at", "null").execute()

    if not chapter_resp.data:
        raise HTTPException(status_code=404, detail="Chapter not found")

    chapter = chapter_resp.data[0]
    _assert_project_access(chapter["project_id"], user_id)
    return chapter


def _assert_project_access(project_id: str, user_id: str) -> None:
    """Raise 403 if user_id has neither ownership nor a share for project_id."""
    owner_resp = supabase.table("projects") \
        .select("id") \
        .eq("id", project_id) \
        .eq("user_id", user_id) \
        .execute()

    if not owner_resp.data:
        share_resp = supabase.table("project_shares") \
            .select("id") \
            .eq("project_id", project_id) \
            .eq("shared_with_user_id", user_id) \
            .execute()
        if not share_resp.data:
            raise HTTPException(status_code=403, detail="Access denied")


def _write_version(chapter_id: str, content: str, title_snapshot: Optional[str], created_by: str):
    supabase.table("chapter_versions").insert({
        "chapter_id": chapter_id,
        "content": content,
        "title_snapshot": title_snapshot,
        "created_by": created_by,
    }).execute()
    # Pruning of oldest versions beyond VERSIONS_KEEP is handled by the
    # trg_prune_chapter_versions DB trigger defined in 20260421_spec1.sql.


def _fetch_user_emails(user_ids: list[str]) -> dict[str, str]:
    """Return {user_id: email} for the given IDs using service-role admin API."""
    if not user_ids:
        return {}
    try:
        response = supabase.auth.admin.list_users()
        # GoTrue SDK returns a list of UserResponse objects (not a plain list attribute)
        users = response if isinstance(response, list) else getattr(response, "users", []) or []
        return {str(u.id): u.email for u in users if str(u.id) in user_ids}
    except Exception:
        return {}


def _log_chapter_edit(project_id: str, user_id: str, chapter_id: str, title: Optional[str]) -> None:
    """Log chapter.edit, deduplicating: skip if the same user already logged an edit
    for this chapter within the last 5 minutes (autosave noise reduction)."""
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        recent = supabase.table("activity_log") \
            .select("id") \
            .eq("project_id", project_id) \
            .eq("user_id", user_id) \
            .eq("action_type", "chapter.edit") \
            .eq("target_id", chapter_id) \
            .gte("created_at", cutoff) \
            .limit(1) \
            .execute()
        if recent.data:
            return
    except Exception:
        pass
    log_activity(
        project_id=project_id,
        user_id=user_id,
        action_type="chapter.edit",
        target_id=chapter_id,
        details={"title": title},
    )
