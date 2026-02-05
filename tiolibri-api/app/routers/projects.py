from fastapi import APIRouter, HTTPException
from app.services.supabase_client import supabase
from app.models.schemas import Project
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["projects"])


class ReorderItem(BaseModel):
    """Item w liście do reordering"""
    chapter_id: str
    sort_order: int


class ReorderRequest(BaseModel):
    """Request do zmiany kolejności rozdziałów"""
    order: List[ReorderItem]

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Test endpoint - pobiera projekt z Supabase"""
    try:
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return response.data[0]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/chapters")
async def get_project_chapters(project_id: str):
    """Pobiera rozdziały projektu (posortowane)"""
    try:
        response = supabase.table("chapters") \
            .select("*") \
            .eq("project_id", project_id) \
            .order("sort_order") \
            .execute()

        return {"chapters": response.data, "count": len(response.data)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/chapters/reorder")
async def reorder_chapters(project_id: str, request: ReorderRequest):
    """
    Zmienia kolejność rozdziałów w projekcie.

    Flow:
    1. Weryfikuje że wszystkie chapter_id należą do project_id
    2. Aktualizuje sort_order dla każdego rozdziału

    Args:
        project_id: ID projektu
        request: ReorderRequest z listą {chapter_id, sort_order}

    Returns:
        Success message i zaktualizowana lista rozdziałów

    Raises:
        HTTPException 400: Invalid chapter IDs
        HTTPException 500: Database error
    """
    try:
        # 1. Pobierz wszystkie rozdziały projektu (weryfikacja)
        verify_response = supabase.table("chapters") \
            .select("id") \
            .eq("project_id", project_id) \
            .execute()

        valid_chapter_ids = {ch["id"] for ch in verify_response.data}
        request_chapter_ids = {item.chapter_id for item in request.order}

        # Sprawdź czy wszystkie chapter_id są valid
        invalid_ids = request_chapter_ids - valid_chapter_ids
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid chapter IDs: {invalid_ids}"
            )

        # 2. Update sort_order dla każdego rozdziału
        for item in request.order:
            supabase.table("chapters") \
                .update({"sort_order": item.sort_order}) \
                .eq("id", item.chapter_id) \
                .execute()

        # 3. Pobierz zaktualizowane rozdziały
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
