"""
Project-level snapshot endpoints.

GET  /projects/{id}/snapshots          — list snapshots (newest first)
POST /projects/{id}/snapshots          — create manual snapshot
POST /projects/{id}/snapshots/{sid}/restore — restore snapshot (takes pre-restore first)

Auto-snapshot logic: called from projects/chapters write paths.
If the last snapshot for the project is older than 6 h AND there has been a
mutating write since then, a new 'auto' snapshot is created synchronously.
The caller (update_chapter, update_project) is responsible for calling
maybe_auto_snapshot() after a successful write.
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends
from app.services.supabase_client import supabase
from app.services.activity import log_activity
from app.dependencies import verify_supabase_jwt

router = APIRouter(prefix="/projects", tags=["snapshots"])

_AUTO_SNAPSHOT_INTERVAL_H = 6


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/snapshots
# ---------------------------------------------------------------------------

@router.get("/{project_id}/snapshots")
async def list_snapshots(
    project_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_project_access(project_id, user["id"])

    resp = supabase.table("project_snapshots") \
        .select("id, project_id, triggered_by, created_at") \
        .eq("project_id", project_id) \
        .order("created_at", desc=True) \
        .execute()

    return {"snapshots": resp.data or []}


# ---------------------------------------------------------------------------
# POST /projects/{project_id}/snapshots  (manual)
# ---------------------------------------------------------------------------

@router.post("/{project_id}/snapshots")
async def create_snapshot(
    project_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_project_access(project_id, user["id"])

    snapshot = _build_snapshot(project_id)
    row = _insert_snapshot(project_id, snapshot, "manual")

    log_activity(
        project_id=project_id,
        user_id=user["id"],
        action_type="project.snapshot_manual",
        details={"snapshot_id": row["id"]},
    )

    return row


# ---------------------------------------------------------------------------
# POST /projects/{project_id}/snapshots/{snapshot_id}/restore
# ---------------------------------------------------------------------------

@router.post("/{project_id}/snapshots/{snapshot_id}/restore")
async def restore_snapshot(
    project_id: str,
    snapshot_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_project_access(project_id, user["id"])

    snap_resp = supabase.table("project_snapshots") \
        .select("*") \
        .eq("id", snapshot_id) \
        .eq("project_id", project_id) \
        .execute()

    if not snap_resp.data:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    target = snap_resp.data[0]["snapshot"]

    # Take pre-restore snapshot so the user can undo
    current_snapshot = _build_snapshot(project_id)
    _insert_snapshot(project_id, current_snapshot, "pre-restore")

    # Restore project fields
    project_fields = target.get("project", {})
    restorable = {
        k: v for k, v in project_fields.items()
        if k in ("title", "subtitle", "author", "language", "style_preset", "typography_settings")
    }
    if restorable:
        supabase.table("projects").update({
            **restorable,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", project_id).execute()

    # Restore chapters
    chapters_snapshot = target.get("chapters", [])
    _restore_chapters(project_id, chapters_snapshot)

    log_activity(
        project_id=project_id,
        user_id=user["id"],
        action_type="project.restore_snapshot",
        target_id=snapshot_id,
        details={"snapshot_created_at": snap_resp.data[0]["created_at"]},
    )

    return {"restored": True, "snapshot_id": snapshot_id}


# ---------------------------------------------------------------------------
# Auto-snapshot helper (called from other routers after writes)
# ---------------------------------------------------------------------------

def maybe_auto_snapshot(project_id: str) -> None:
    """
    Insert an 'auto' snapshot if the last one is older than AUTO_SNAPSHOT_INTERVAL_H.
    Errors are swallowed — this must never break the primary write path.
    """
    try:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(hours=_AUTO_SNAPSHOT_INTERVAL_H)
        ).isoformat()

        latest_resp = supabase.table("project_snapshots") \
            .select("created_at") \
            .eq("project_id", project_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        latest = latest_resp.data[0] if latest_resp.data else None

        if latest and latest["created_at"] >= cutoff:
            return  # Recent snapshot exists — skip

        snapshot = _build_snapshot(project_id)
        _insert_snapshot(project_id, snapshot, "auto")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assert_project_access(project_id: str, user_id: str) -> None:
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


def _build_snapshot(project_id: str) -> dict:
    """Fetch the current project + non-deleted chapters and return as a dict."""
    project_resp = supabase.table("projects") \
        .select("id, title, subtitle, author, language, style_preset, typography_settings, cover_image_url, status") \
        .eq("id", project_id) \
        .execute()

    if not project_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")

    chapters_resp = supabase.table("chapters") \
        .select("id, title, sort_order, processed_html, status, created_at") \
        .eq("project_id", project_id) \
        .is_("deleted_at", "null") \
        .order("sort_order") \
        .execute()

    return {
        "project": project_resp.data[0],
        "chapters": chapters_resp.data or [],
    }


def _insert_snapshot(project_id: str, snapshot: dict, triggered_by: str) -> dict:
    resp = supabase.table("project_snapshots").insert({
        "project_id": project_id,
        "snapshot": snapshot,
        "triggered_by": triggered_by,
    }).execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create snapshot")

    return resp.data[0]


def _restore_chapters(project_id: str, chapters_snapshot: list) -> None:
    """
    Restore chapter content from a snapshot.

    Strategy: update existing chapters by id (content + title), soft-un-delete
    any that were deleted after the snapshot was taken (set deleted_at = NULL),
    and soft-delete chapters that were created after the snapshot (they didn't
    exist at snapshot time). We do NOT hard-delete anything to preserve assets.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Current chapter state (including deleted)
    current_resp = supabase.table("chapters") \
        .select("id, deleted_at") \
        .eq("project_id", project_id) \
        .execute()
    current_ids = {ch["id"] for ch in (current_resp.data or [])}
    snapshot_ids = {ch["id"] for ch in chapters_snapshot}

    for ch in chapters_snapshot:
        if ch["id"] in current_ids:
            supabase.table("chapters").update({
                "title": ch.get("title"),
                "sort_order": ch.get("sort_order"),
                "processed_html": ch.get("processed_html"),
                "status": ch.get("status", "draft"),
                "deleted_at": None,
                "deleted_by": None,
                "updated_at": now,
            }).eq("id", ch["id"]).execute()
        else:
            # Chapter existed in snapshot but not in DB — insert it back
            supabase.table("chapters").insert({
                "id": ch["id"],
                "project_id": project_id,
                "title": ch.get("title"),
                "sort_order": ch.get("sort_order"),
                "processed_html": ch.get("processed_html"),
                "status": ch.get("status", "draft"),
            }).execute()

    # Chapters created after the snapshot → soft-delete them
    for ch_id in current_ids - snapshot_ids:
        supabase.table("chapters").update({
            "deleted_at": now,
            "updated_at": now,
        }).eq("id", ch_id).execute()
