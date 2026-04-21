from typing import Optional
from app.services.supabase_client import supabase


def log_activity(
    project_id: str,
    user_id: str,
    action_type: str,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """Insert a row into activity_log. Errors are swallowed so they never
    break the primary operation that triggered the log."""
    try:
        supabase.table("activity_log").insert({
            "project_id": project_id,
            "user_id": user_id,
            "action_type": action_type,
            "target_id": target_id,
            "details": details or {},
        }).execute()
    except Exception:
        pass
