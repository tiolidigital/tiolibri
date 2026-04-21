from fastapi import APIRouter, HTTPException, Depends
from app.services.supabase_client import supabase
from app.services.activity import log_activity
from app.dependencies import verify_supabase_jwt
from app.models.schemas import Project
from typing import List, Optional
from pydantic import BaseModel, field_validator
import uuid

router = APIRouter(prefix="/projects", tags=["projects"])


class ReorderItem(BaseModel):
    chapter_id: str
    sort_order: int


class ReorderRequest(BaseModel):
    order: List[ReorderItem]


class ShareRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v


@router.get("/shared")
async def list_shared_projects(user: dict = Depends(verify_supabase_jwt)):
    """Return projects shared with the current user, enriched with owner email."""
    shares_resp = supabase.table("project_shares") \
        .select("id, project_id, shared_by_user_id, created_at") \
        .eq("shared_with_user_id", user["id"]) \
        .order("created_at", desc=True) \
        .execute()

    shares = shares_resp.data or []
    if not shares:
        return {"projects": []}

    project_ids = [s["project_id"] for s in shares]
    projects_resp = supabase.table("projects") \
        .select("*") \
        .in_("id", project_ids) \
        .execute()

    projects_by_id = {p["id"]: p for p in (projects_resp.data or [])}

    owner_ids = list({s["shared_by_user_id"] for s in shares if s.get("shared_by_user_id")})
    email_map = _fetch_user_emails(owner_ids)

    result = []
    for share in shares:
        project = projects_by_id.get(share["project_id"])
        if not project:
            continue
        result.append({
            **project,
            "_share_id": share["id"],
            "_shared_by_email": email_map.get(share.get("shared_by_user_id"), ""),
        })

    return {"projects": result}


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str, _user: dict = Depends(verify_supabase_jwt)):
    try:
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/chapters")
async def get_project_chapters(project_id: str, _user: dict = Depends(verify_supabase_jwt)):
    try:
        response = supabase.table("chapters") \
            .select("*") \
            .eq("project_id", project_id) \
            .order("sort_order") \
            .execute()
        return {"chapters": response.data, "count": len(response.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/duplicate")
async def duplicate_project(project_id: str, user: dict = Depends(verify_supabase_jwt)):
    """
    Duplicates a project and all its chapters.
    Only the project owner may duplicate.
    """
    try:
        project_response = supabase.table("projects") \
            .select("*") \
            .eq("id", project_id) \
            .execute()

        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        original = project_response.data[0]

        if original["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Not the project owner")

        new_id = str(uuid.uuid4())
        new_project_data = {
            "id": new_id,
            "user_id": original["user_id"],
            "title": f"{original['title']} (kopia)",
            "author": original.get("author"),
            "language": original.get("language", "pl"),
            "status": "draft",
            "style_preset": original.get("style_preset", "classic"),
            "typography_settings": original.get("typography_settings"),
            "cover_image_url": original.get("cover_image_url"),
        }

        supabase.table("projects").insert(new_project_data).execute()

        new_project_response = supabase.table("projects") \
            .select("*") \
            .eq("id", new_id) \
            .execute()

        if not new_project_response.data:
            raise HTTPException(status_code=500, detail="Failed to create duplicate project")

        new_project = new_project_response.data[0]

        chapters_response = supabase.table("chapters") \
            .select("*") \
            .eq("project_id", project_id) \
            .order("sort_order") \
            .execute()

        if chapters_response.data:
            new_chapters = []
            for ch in chapters_response.data:
                new_chapters.append({
                    "project_id": new_id,
                    "title": ch["title"],
                    "sort_order": ch["sort_order"],
                    "processed_html": ch.get("processed_html"),
                    "source_file_path": ch.get("source_file_path"),
                })
            supabase.table("chapters").insert(new_chapters).execute()

        return new_project

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/chapters/reorder")
async def reorder_chapters(
    project_id: str,
    request: ReorderRequest,
    _user: dict = Depends(verify_supabase_jwt),
):
    try:
        verify_response = supabase.table("chapters") \
            .select("id") \
            .eq("project_id", project_id) \
            .execute()

        valid_chapter_ids = {ch["id"] for ch in verify_response.data}
        request_chapter_ids = {item.chapter_id for item in request.order}

        invalid_ids = request_chapter_ids - valid_chapter_ids
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid chapter IDs: {invalid_ids}"
            )

        for item in request.order:
            supabase.table("chapters") \
                .update({"sort_order": item.sort_order}) \
                .eq("id", item.chapter_id) \
                .execute()

        updated_response = supabase.table("chapters") \
            .select("*") \
            .eq("project_id", project_id) \
            .order("sort_order") \
            .execute()

        return {
            "success": True,
            "message": f"Reordered {len(request.order)} chapters",
            "chapters": updated_response.data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/shares
# List current shares for the project (owner only).
# ---------------------------------------------------------------------------

@router.get("/{project_id}/shares")
async def list_shares(
    project_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_owner(project_id, user["id"])

    resp = supabase.table("project_shares") \
        .select("id, shared_with_user_id, shared_by_user_id, created_at") \
        .eq("project_id", project_id) \
        .order("created_at", desc=False) \
        .execute()

    shares = resp.data or []

    # Enrich with emails
    user_ids = list({
        uid
        for s in shares
        for uid in [s.get("shared_with_user_id"), s.get("shared_by_user_id")]
        if uid
    })
    email_map = _fetch_user_emails(user_ids)

    for s in shares:
        s["shared_with_email"] = email_map.get(s.get("shared_with_user_id"))
        s["shared_by_email"] = email_map.get(s.get("shared_by_user_id"))

    return {"shares": shares}


# ---------------------------------------------------------------------------
# POST /projects/{project_id}/share
# Body: { email }. Look up user by email, create project_shares row.
# ---------------------------------------------------------------------------

@router.post("/{project_id}/share")
async def share_project(
    project_id: str,
    body: ShareRequest,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_owner(project_id, user["id"])

    # Look up target user by email
    target_user = _find_user_by_email(body.email)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono użytkownika z tym adresem e-mail. Poproś go, żeby najpierw założył konto."
        )

    if target_user["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Nie możesz udostępnić projektu samemu sobie.")

    # UNIQUE constraint on (project_id, shared_with_user_id) — detect duplicate
    # via Postgres SQLSTATE 23505, fall back to string match for older clients.
    try:
        resp = supabase.table("project_shares").insert({
            "project_id": project_id,
            "shared_with_user_id": target_user["id"],
            "shared_by_user_id": user["id"],
        }).execute()
    except Exception as exc:
        code = getattr(exc, "code", None)
        msg = str(exc).lower()
        if code == "23505" or "unique" in msg or "duplicate" in msg:
            raise HTTPException(status_code=409, detail="Projekt jest już udostępniony temu użytkownikowi.")
        raise HTTPException(status_code=500, detail=str(exc))

    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create share")

    share = resp.data[0]
    share["shared_with_email"] = target_user["email"]
    share["shared_by_email"] = user["email"]

    log_activity(
        project_id=project_id,
        user_id=user["id"],
        action_type="project.share",
        target_id=share["id"],
        details={"shared_with_email": target_user["email"]},
    )

    return share


# ---------------------------------------------------------------------------
# DELETE /projects/{project_id}/share/{share_id}
# Revoke a share (owner only).
# ---------------------------------------------------------------------------

@router.delete("/{project_id}/share/{share_id}")
async def unshare_project(
    project_id: str,
    share_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_owner(project_id, user["id"])

    share_resp = supabase.table("project_shares") \
        .select("id, shared_with_user_id") \
        .eq("id", share_id) \
        .eq("project_id", project_id) \
        .execute()

    if not share_resp.data:
        raise HTTPException(status_code=404, detail="Share not found")

    shared_with_id = share_resp.data[0].get("shared_with_user_id")
    email_map = _fetch_user_emails([shared_with_id] if shared_with_id else [])

    supabase.table("project_shares").delete().eq("id", share_id).execute()

    log_activity(
        project_id=project_id,
        user_id=user["id"],
        action_type="project.unshare",
        target_id=share_id,
        details={"shared_with_email": email_map.get(shared_with_id, "")},
    )

    return {"revoked": True, "share_id": share_id}


# ---------------------------------------------------------------------------
# GET /projects/{project_id}/activity
# List activity log, newest first, paginated.
# ---------------------------------------------------------------------------

@router.get("/{project_id}/activity")
async def list_activity(
    project_id: str,
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_project_access(project_id, user["id"])

    resp = supabase.table("activity_log") \
        .select("id, user_id, action_type, target_id, details, created_at") \
        .eq("project_id", project_id) \
        .order("created_at", desc=True) \
        .range(offset, offset + limit - 1) \
        .execute()

    events = resp.data or []

    user_ids = list({e["user_id"] for e in events if e.get("user_id")})
    email_map = _fetch_user_emails(user_ids)

    for e in events:
        e["user_email"] = email_map.get(e.get("user_id"))

    return {"events": events, "count": len(events)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_owner(project_id: str, user_id: str) -> dict:
    resp = supabase.table("projects") \
        .select("id, user_id") \
        .eq("id", project_id) \
        .execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    if resp.data[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Only the project owner can perform this action")
    return resp.data[0]


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


def _fetch_user_emails(user_ids: list[str]) -> dict[str, str]:
    if not user_ids:
        return {}
    try:
        response = supabase.auth.admin.list_users()
        users = response if isinstance(response, list) else getattr(response, "users", []) or []
        return {str(u.id): u.email for u in users if str(u.id) in user_ids}
    except Exception:
        return {}


def _find_user_by_email(email: str) -> Optional[dict]:
    """Look up a user by email using the admin API. Returns {id, email} or None."""
    try:
        response = supabase.auth.admin.list_users()
        users = response if isinstance(response, list) else getattr(response, "users", []) or []
        for u in users:
            if u.email and u.email.lower() == email.lower():
                return {"id": str(u.id), "email": u.email}
    except Exception:
        pass
    return None
