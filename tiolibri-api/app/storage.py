from storage3 import create_client
import os
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

storage_client = create_client(
    f"{SUPABASE_URL}/storage/v1",
    {"apiKey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
    is_async=False
)

def upload_to_supabase(file_path: str, file_type: str, project_id: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project_id}_{timestamp}.{file_type}"
    storage_path = f"{project_id}/{filename}"
    
    # Ustaw content-type
    content_type = "application/epub+zip" if file_type == "epub" else "application/pdf"
    
    with open(file_path, 'rb') as f:
        bucket = storage_client.from_('book-exports')
        bucket.upload(
            storage_path, 
            f.read(),
            {"content-type": content_type}
        )
    
    public_url = bucket.get_public_url(storage_path)
    return public_url

