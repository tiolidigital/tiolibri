#!/usr/bin/env python3
"""Ustawia imprint.version = "1.0" w projekcie „Grzyby lecznicze" (fe9cba47), reszta imprintu bez zmian."""
import os, json
from dotenv import load_dotenv
load_dotenv("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI/tiolibri-api/.env")
from supabase import create_client
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
P = "fe9cba47-9760-4a40-8030-d5bc5e70b512"
imp = sb.table("projects").select("imprint").eq("id", P).execute().data[0]["imprint"] or {}
print("przed:", json.dumps(imp, ensure_ascii=False))
sb.table("projects").update({"imprint": {**imp, "version": "1.0"}}).eq("id", P).execute()
print("po:   ", json.dumps(sb.table("projects").select("imprint").eq("id", P).execute().data[0]["imprint"], ensure_ascii=False))
