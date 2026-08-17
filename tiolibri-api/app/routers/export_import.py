"""
Export / import endpoints for .tiolibri ZIP backup files.

POST /projects/{id}/export     — build ZIP, return as streaming download
POST /projects/{id}/export-md  — build Markdown ZIP for the Redaktor bridge
POST /projects/import          — accept multipart ZIP, create new project, return new project row
"""

import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.supabase_client import supabase
from app.services.activity import log_activity
from app.services.md_exporter import (
    ImageTooLargeError,
    build_book_key,
    chapter_to_markdown,
    sha256_nfc,
    slugify,
    to_ascii,
)
from app.dependencies import verify_supabase_jwt

router = APIRouter(prefix="/projects", tags=["export-import"])

_FORMAT_VERSION = 1
_MAX_IMPORT_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
_MAX_UNCOMPRESSED_ENTRY_BYTES = 200 * 1024 * 1024  # zip-bomb guard per file
_MAX_ZIP_ENTRIES = 100  # sanity cap on namelist size
_MAX_CHAPTERS_PER_IMPORT = 2000

_MD_FORMAT = "tiolibri-md-export"
_MD_FORMAT_VERSION = 1
_MAX_MD_ZIP_BYTES = 80 * 1024 * 1024  # suma wpisow PRZED kompresja


# ---------------------------------------------------------------------------
# POST /projects/{project_id}/export
# ---------------------------------------------------------------------------

@router.post("/{project_id}/export")
async def export_project(
    project_id: str,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_project_access(project_id, user["id"])

    project_resp = supabase.table("projects") \
        .select("*") \
        .eq("id", project_id) \
        .execute()

    if not project_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")

    project = project_resp.data[0]

    chapters_resp = supabase.table("chapters") \
        .select("id, title, sort_order, processed_html, status, created_at") \
        .eq("project_id", project_id) \
        .is_("deleted_at", "null") \
        .order("sort_order") \
        .execute()

    chapters = chapters_resp.data or []

    # Build in-memory ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # manifest.json
        manifest = {
            "version": _FORMAT_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id,
            "exporter_email": user.get("email", ""),
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        # project.json — curated subset (no internal IDs leaked unnecessarily)
        project_export = {
            "title": project.get("title"),
            "subtitle": project.get("subtitle"),
            "author": project.get("author"),
            "language": project.get("language"),
            "style_preset": project.get("style_preset"),
            "typography_settings": project.get("typography_settings"),
            "cover_image_url": project.get("cover_image_url"),
            "status": project.get("status"),
        }
        zf.writestr("project.json", json.dumps(project_export, ensure_ascii=False, indent=2))

        # chapters.json
        zf.writestr("chapters.json", json.dumps(chapters, ensure_ascii=False, indent=2))

        # README.txt
        readme = (
            f"TIOLIBRI Project Backup\n"
            f"=======================\n"
            f"Project: {project.get('title', 'Untitled')}\n"
            f"Exported: {manifest['exported_at']}\n"
            f"Format version: {_FORMAT_VERSION}\n\n"
            f"This file is a portable backup of your TIOLIBRI project.\n"
            f"Import it at app.tiolibri.com to restore as a new project.\n"
        )
        zf.writestr("README.txt", readme)

    buf.seek(0)
    # Build a safe ASCII filename for the legacy `filename=` param; separately
    # expose the full UTF-8 title via `filename*=` (RFC 5987) for modern clients.
    raw_title = project.get("title") or "project"
    # to_ascii najpierw, inaczej polskie litery wypadaja jako "_" ("Kości" → "Ko_ci").
    ascii_title = "".join(
        c if c.isascii() and (c.isalnum() or c in " -_") else "_" for c in to_ascii(raw_title)
    ).strip("_") or "project"
    ascii_filename = f"{ascii_title}.tiolibri"
    utf8_filename = quote(f"{raw_title}.tiolibri", safe="")

    log_activity(
        project_id=project_id,
        user_id=user["id"],
        action_type="project.export",
        details={"filename": ascii_filename},
    )

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{utf8_filename}'
            ),
        },
    )


# ---------------------------------------------------------------------------
# POST /projects/{project_id}/export-md   (most TIOLIBRI -> Redaktor)
# ---------------------------------------------------------------------------

class ExportMdRequest(BaseModel):
    chapter_ids: Optional[list[UUID]] = None


@router.post("/{project_id}/export-md")
async def export_md(
    project_id: str,
    # `Optional[...] = None` jest czescia kontraktu, nie stylem: `request: ExportMdRequest`
    # czyni BRAK body bledem 422, a tabela §Endpoint wymaga tam 200.
    request: Optional[ExportMdRequest] = None,
    user: dict = Depends(verify_supabase_jwt),
):
    _assert_project_access(project_id, user["id"])

    chapter_ids = request.chapter_ids if request is not None else None
    if chapter_ids is not None and len(chapter_ids) == 0:
        raise HTTPException(status_code=400, detail="Wybrano zero rozdziałów")

    project_resp = supabase.table("projects").select("*").eq("id", project_id).execute()
    if not project_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project_resp.data[0]

    # tie-breaker po `id`: sort_order bywa dziurawy i bywa rowny, a od kolejnosci
    # zaleza numery NN i nazwy plikow (klucze katalogow przebiegu Redaktora)
    chapters_resp = supabase.table("chapters") \
        .select("id, title, sort_order, processed_html") \
        .eq("project_id", project_id) \
        .is_("deleted_at", "null") \
        .order("sort_order") \
        .order("id") \
        .execute()
    chapters = chapters_resp.data or []
    if not chapters:
        raise HTTPException(status_code=400, detail="Projekt nie ma rozdziałów")

    if chapter_ids is not None:
        wanted = [str(cid) for cid in chapter_ids]
        by_id = {ch["id"]: ch for ch in chapters}
        unknown = [cid for cid in wanted if cid not in by_id]
        if unknown:
            raise HTTPException(
                status_code=404,
                detail="Nierozpoznane rozdziały: {}".format(", ".join(unknown)),
            )
        selected = [ch for ch in chapters if ch["id"] in set(wanted)]
    else:
        selected = chapters

    missing_html = [ch.get("title") or "(bez tytułu)" for ch in selected if not (ch.get("processed_html") or "").strip()]
    if missing_html:
        raise HTTPException(
            status_code=409,
            detail=(
                "Rozdziały bez zapisanej treści: {}. Otwórz i zapisz je w edytorze, "
                "potem spróbuj ponownie.".format(", ".join(missing_html))
            ),
        )

    book_key = build_book_key(project.get("title") or "", project_id)
    pad = 3 if len(selected) > 99 else 2

    entries = []          # (sciezka w ZIP, bajty)
    manifest_chapters = []
    used_names = set()
    total_bytes = 0

    for index, chapter in enumerate(selected, start=1):
        try:
            result = chapter_to_markdown(chapter["processed_html"], book_key, index, pad)
        except ImageTooLargeError as exc:
            raise HTTPException(
                status_code=413,
                detail='Obraz w rozdziale "{}" przekracza limit 10 MB ({} B).'.format(
                    chapter.get("title") or "(bez tytułu)", exc.size_bytes
                ),
            )

        filename = _unique_md_name(book_key, index, pad, chapter.get("title") or "", used_names)
        md_bytes = result.md.encode("utf-8")
        entries.append(("{}/{}".format(book_key, filename), md_bytes))
        total_bytes += len(md_bytes)

        images_manifest = []
        for image in result.images:
            entry = {"order": image.order, "kind": image.kind, "alt": image.alt}
            if image.skipped:
                entry.update({"skipped": True, "reason": image.reason})
                if image.src:
                    entry["src"] = image.src
            elif image.kind == "remote":
                entry["src"] = image.src
            else:
                entry.update({
                    "file": image.filename,
                    "mime": image.mime,
                    "bytes": len(image.data),
                })
                if image.mime_unknown:
                    entry["mime_unknown"] = True
                entries.append(("{}/{}".format(book_key, image.filename), image.data))
                total_bytes += len(image.data)
            images_manifest.append(entry)

        manifest_chapters.append({
            "chapter_id": chapter["id"],
            "filename": filename,
            "title": chapter.get("title"),
            "sort_order": chapter.get("sort_order"),
            "position": index,
            "hash": sha256_nfc(result.md),
            "chars": result.chars,
            "blocks": result.blocks,
            "dividers": result.dividers,
            "images": images_manifest,
        })

        if total_bytes > _MAX_MD_ZIP_BYTES:
            raise HTTPException(
                status_code=413,
                detail='Eksport przekracza {} MB na rozdziale "{}".'.format(
                    _MAX_MD_ZIP_BYTES // (1024 * 1024), chapter.get("title") or "(bez tytułu)"
                ),
            )

    manifest = {
        "format": _MD_FORMAT,
        "version": _MD_FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "project_title": project.get("title"),
        "book_key": book_key,
        "chapters": manifest_chapters,
    }
    entries.append((
        "{}/_tiolibri/manifest.json".format(book_key),
        json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
    ))

    # twarda asercja: zadna nazwa w ZIP-ie nie moze sie powtorzyc
    paths = [path for path, _ in entries]
    if len(paths) != len(set(paths)):
        raise HTTPException(status_code=500, detail="Kolizja nazw plików w eksporcie")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, payload in entries:
            zf.writestr(path, payload)
    buf.seek(0)

    log_activity(
        project_id=project_id,
        user_id=user["id"],
        action_type="project.export_md",
        details={"chapter_count": len(selected), "book_key": book_key},
    )

    zip_name = "{}.zip".format(book_key)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                'attachment; filename="{}"; filename*=UTF-8\'\'{}'.format(zip_name, quote(zip_name, safe=""))
            ),
        },
    )


def _unique_md_name(book_key: str, index: int, pad: int, title: str, used: set) -> str:
    stem = "{}-{:0{}d}-{}".format(book_key, index, pad, slugify(title))
    candidate = stem
    suffix = 2
    while candidate in used:
        candidate = "{}-{}".format(stem, suffix)
        suffix += 1
    used.add(candidate)
    return "{}.md".format(candidate)


# ---------------------------------------------------------------------------
# POST /projects/import
# ---------------------------------------------------------------------------

@router.post("/import")
async def import_project(
    file: UploadFile = File(...),
    user: dict = Depends(verify_supabase_jwt),
):
    # Size guard
    content = await file.read(_MAX_IMPORT_SIZE_BYTES + 1)
    if len(content) > _MAX_IMPORT_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {_MAX_IMPORT_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    try:
        buf = io.BytesIO(content)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            if len(names) > _MAX_ZIP_ENTRIES:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid .tiolibri file: too many entries",
                )
            for required in ("manifest.json", "project.json", "chapters.json"):
                if required not in names:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Invalid .tiolibri file: missing {required}",
                    )
                if zf.getinfo(required).file_size > _MAX_UNCOMPRESSED_ENTRY_BYTES:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Invalid .tiolibri file: {required} exceeds size limit",
                    )

            manifest = json.loads(zf.read("manifest.json"))
            if manifest.get("version") != _FORMAT_VERSION:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unsupported format version: {manifest.get('version')}. Expected {_FORMAT_VERSION}.",
                )

            project_data = json.loads(zf.read("project.json"))
            chapters_data = json.loads(zf.read("chapters.json"))

        if not isinstance(chapters_data, list):
            raise HTTPException(status_code=422, detail="Invalid .tiolibri file: chapters.json must be a list")
        if len(chapters_data) > _MAX_CHAPTERS_PER_IMPORT:
            raise HTTPException(
                status_code=422,
                detail=f"Too many chapters in import (max {_MAX_CHAPTERS_PER_IMPORT})",
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse .tiolibri file: {exc}")

    # Create new project owned by importing user
    new_project_id = str(uuid.uuid4())
    original_title = project_data.get("title") or "Untitled"
    new_project_row = {
        "id": new_project_id,
        "user_id": user["id"],
        "title": f"{original_title} (import)",
        "subtitle": project_data.get("subtitle"),
        "author": project_data.get("author"),
        "language": project_data.get("language", "pl"),
        "status": "draft",
        "style_preset": project_data.get("style_preset", "classic"),
        "typography_settings": project_data.get("typography_settings"),
        "cover_image_url": project_data.get("cover_image_url"),
    }

    proj_resp = supabase.table("projects").insert(new_project_row).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=500, detail="Failed to create imported project")

    new_project = proj_resp.data[0]

    # Insert chapters with new IDs
    if chapters_data:
        new_chapters = []
        for ch in chapters_data:
            new_chapters.append({
                "project_id": new_project_id,
                "title": ch.get("title"),
                "sort_order": ch.get("sort_order", 0),
                "processed_html": ch.get("processed_html"),
                "status": ch.get("status", "draft"),
            })
        supabase.table("chapters").insert(new_chapters).execute()

    log_activity(
        project_id=new_project_id,
        user_id=user["id"],
        action_type="project.import_from_tiolibri",
        details={
            "original_title": original_title,
            "chapter_count": len(chapters_data),
            "format_version": manifest.get("version"),
        },
    )

    return new_project


# ---------------------------------------------------------------------------
# Helpers
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
