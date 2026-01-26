from fastapi import APIRouter, HTTPException
from app.services.supabase_client import supabase
from app.models.schemas import Project
from typing import List

router = APIRouter(prefix="/projects", tags=["projects"])

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
