"""
Generate Router
Endpoint do generowania EPUB/PDF z projektu.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.services.supabase_client import supabase
from app.services.epub_generator import generate_epub
from app.services.pdf_generator import generate_pdf
from app.models.schemas import GenerateRequest, GenerateResponse
from app.storage import upload_to_supabase
from app.dependencies import verify_supabase_jwt
import time
import os
import tempfile


router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", response_model=GenerateResponse)
async def generate_ebook(request: GenerateRequest, _user: dict = Depends(verify_supabase_jwt)):
    """
    Główny endpoint - generuje EPUB/PDF z projektu.

    Flow:
    1. Pobierz projekt z Supabase
    2. Pobierz rozdziały (ORDER BY sort_order)
    3. Generuj EPUB (jeśli w request.formats)
    4. Generuj PDF (jeśli w request.formats)
    5. Upload do Supabase Storage i zwróć publiczne URLe

    Args:
        request: GenerateRequest z project_id, formats, style_preset

    Returns:
        GenerateResponse z success, files, stats, message

    Raises:
        HTTPException 404: Project not found
        HTTPException 400: No chapters found / Invalid format
        HTTPException 500: Generation error
    """
    start_time = time.time()

    # Walidacja formatu
    valid_formats = {"epub", "pdf"}
    invalid_formats = set(request.formats) - valid_formats
    if invalid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid formats: {invalid_formats}. Valid formats: {valid_formats}"
        )

    # Walidacja presetu
    valid_presets = {"classic", "modern", "minimal"}
    if request.style_preset not in valid_presets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid style_preset: {request.style_preset}. Valid presets: {valid_presets}"
        )

    try:
        # 1. Pobierz projekt
        project_response = supabase.table("projects") \
            .select("*") \
            .eq("id", request.project_id) \
            .execute()

        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        project = project_response.data[0]

        # 2. Pobierz rozdziały
        chapters_response = supabase.table("chapters") \
            .select("*") \
            .eq("project_id", request.project_id) \
            .order("sort_order") \
            .execute()

        chapters = chapters_response.data

        if not chapters:
            raise HTTPException(status_code=400, detail="No chapters found for this project")

        # Sprawdź czy są rozdziały z treścią
        chapters_with_content = [
            c for c in chapters
            if c.get("processed_html") or c.get("content")
        ]

        if not chapters_with_content:
            raise HTTPException(
                status_code=400,
                detail="No chapters with content found. Please add content to at least one chapter."
            )

        # 3. Generuj pliki i upload do Supabase
        files = {}
        temp_dir = tempfile.gettempdir()

        # EPUB
        if "epub" in request.formats:
            epub_path = os.path.join(temp_dir, f"{request.project_id}.epub")
            try:
                generate_epub(
                    project,
                    chapters,
                    epub_path,
                    request.style_preset,
                    request.text_align,
                    request.font_size,
                    request.line_height,
                    request.margin_top,
                    request.margin_bottom,
                    request.margin_left,
                    request.margin_right,
                    request.chapter_spacing,
                    request.cover_image_url,
                    request.toc_enabled,
                    request.toc_depth
                )
                epub_url = upload_to_supabase(epub_path, "epub", request.project_id)
                files["epub"] = epub_url
                os.remove(epub_path)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"EPUB generation failed: {str(e)}"
                )

        # PDF
        if "pdf" in request.formats:
            pdf_path = os.path.join(temp_dir, f"{request.project_id}.pdf")
            try:
                generate_pdf(
                    project,
                    chapters,
                    pdf_path,
                    request.style_preset,
                    request.text_align,
                    request.font_size,
                    request.line_height,
                    request.margin_top,
                    request.margin_bottom,
                    request.margin_left,
                    request.margin_right,
                    request.chapter_spacing,
                    request.cover_image_url,
                    request.toc_enabled,
                    request.toc_depth
                )
                pdf_url = upload_to_supabase(pdf_path, "pdf", request.project_id)
                files["pdf"] = pdf_url
                os.remove(pdf_path)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"PDF generation failed: {str(e)}"
                )

        # 4. Stats
        generation_time = round(time.time() - start_time, 2)

        return GenerateResponse(
            success=True,
            files=files,
            stats={
                "chapters": len(chapters_with_content),
                "total_chapters": len(chapters),
                "generation_time_seconds": generation_time
            },
            message=f"Generated {len(files)} file(s) successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during generation: {str(e)}"
        )
