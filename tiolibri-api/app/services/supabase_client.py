from supabase import create_client, Client
import os

def get_supabase_client() -> Client:
    """
    Tworzy klienta Supabase z service_role key.
    Service key bypasses RLS - backend ma pełny dostęp.
    Używaj do operacji na DB (SECURITY DEFINER pattern).
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

    return create_client(url, key)


def get_supabase_auth_client() -> Client:
    """
    Oddzielny klient z anon key, używany WYŁĄCZNIE do walidacji
    tokenów JWT użytkowników (supabase.auth.get_user(token)).

    Trzymanie tego osobno od service-role clienta to wymóg bezpieczeństwa:
    nie mieszamy kontekstu "backend z pełnym dostępem" z "kontekstem usera".
    """
    url = os.getenv("SUPABASE_URL")
    # Accept either SUPABASE_ANON_KEY or the legacy SUPABASE_KEY name.
    anon_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not anon_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY (or SUPABASE_KEY) in .env")

    return create_client(url, anon_key)


# Singletons
supabase: Client = get_supabase_client()
supabase_auth: Client = get_supabase_auth_client()
