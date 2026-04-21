from fastapi import APIRouter, HTTPException, Depends
from app.services.supabase_client import supabase
from app.dependencies import verify_supabase_jwt
from app.models.schemas import Project
from typing import List
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/projects", tags=["projects"])


class ReorderItem(BaseModel):
    chapter_id: str
    sort_order: int


class ReorderRequest(BaseModel):
    order: List[ReorderItem]


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
