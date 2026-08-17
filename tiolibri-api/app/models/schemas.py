from pydantic import BaseModel, validator
from typing import List, Optional


class GenerateRequest(BaseModel):
    """Request do generowania EPUB/PDF"""
    project_id: str
    formats: List[str] = ["epub", "pdf"]
    style_preset: str = "classic"

    # Typography customization
    text_align: str = "left"        # "left" | "justify"
    font_size: int = 16             # 12-24 (step 2)
    line_height: float = 1.7        # 1.2-2.5

    # Margins (em units)
    margin_top: float = 2.0
    margin_bottom: float = 2.0
    margin_left: float = 1.5
    margin_right: float = 1.5

    # Chapter spacing
    chapter_spacing: float = 2.0

    # Cover image
    cover_image_url: Optional[str] = None

    # Table of Contents
    toc_enabled: bool = False
    toc_depth: int = 2  # 1=H1 only, 2=H1+H2, 3=H1+H2+H3

    @validator('toc_depth')
    def validate_toc_depth(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError('toc_depth must be 1, 2, or 3')
        return v

    @validator('text_align')
    def validate_text_align(cls, v):
        if v not in ['left', 'justify']:
            raise ValueError('text_align must be "left" or "justify"')
        return v

    @validator('font_size')
    def validate_font_size(cls, v):
        if v < 12 or v > 24 or v % 2 != 0:
            raise ValueError('font_size must be between 12-24 (even numbers only)')
        return v

    @validator('line_height')
    def validate_line_height(cls, v):
        if v < 1.0 or v > 3.0:
            raise ValueError('line_height must be between 1.0-3.0')
        return v

    @validator('margin_top', 'margin_bottom', 'margin_left', 'margin_right')
    def validate_margins(cls, v):
        if v < 0 or v > 5:
            raise ValueError('Margins must be between 0-5em')
        return v

    @validator('chapter_spacing')
    def validate_chapter_spacing(cls, v):
        if v < 0.5 or v > 4:
            raise ValueError('Chapter spacing must be between 0.5-4em')
        return v

class GenerateResponse(BaseModel):
    """Response po wygenerowaniu plików"""
    success: bool
    files: dict  # {"epub": "url", "pdf": "url"}
    stats: dict  # {"chapters": 5, "generation_time_seconds": 12}
    message: Optional[str] = None

class Project(BaseModel):
    """Model projektu z Supabase"""
    id: str
    user_id: str
    title: str
    subtitle: Optional[str] = None
    author: Optional[str]
    language: str
    status: str  # "draft" | "published"
    style_preset: str
    custom_styles: Optional[dict] = {}
    created_at: str
    updated_at: str


class Chapter(BaseModel):
    """Model rozdziału z Supabase"""
    id: str
    project_id: str
    title: str
    sort_order: int
    content: Optional[str]
    processed_html: Optional[str]
    original_filename: Optional[str]
    created_at: str
    updated_at: str
