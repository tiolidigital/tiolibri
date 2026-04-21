from typing import Optional
from fastapi import HTTPException, Header
from app.services.supabase_client import supabase_auth


async def verify_supabase_jwt(
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    FastAPI dependency: validates the Supabase JWT from Authorization header.

    Uses a dedicated anon-key Supabase client (supabase_auth) to validate the
    token — never the service-role client, to keep user-auth context isolated
    from backend-privileged ops.

    Returns the user dict on success.
    Always raises 401 (not 422) when the header is missing/malformed/expired,
    so the API surface is consistent from the caller's perspective.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        response = supabase_auth.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {"id": response.user.id, "email": response.user.email}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
