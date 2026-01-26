from supabase import create_client, Client
import os

def get_supabase_client() -> Client:
    """
    Tworzy klienta Supabase z service_role key.
    Service key bypasses RLS - backend ma pełny dostęp.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    
    return create_client(url, key)

# Singleton instance
supabase: Client = get_supabase_client()
