# TIOLIBRI Backend - Session Log

**Data:** 2026-01-24
**Sesje:** 1-2 (Backend Setup + Supabase Integration)
**Czas:** ~2h

---

## Podsumowanie sesji

**Cel:** Setup Python Backend (FastAPI) + Supabase Integration

### Sesja 1 - Setup Backend

- Python virtual environment (venv)
- FastAPI + Uvicorn + python-dotenv
- Struktura projektu (app/routers, app/services, app/models, app/presets)
- Hello World endpoint (GET /, GET /health)
- CORS middleware (dla localhost:3000)
- Uruchomienie na localhost:8001
- Swagger UI działa (/docs)

### Sesja 2 - Supabase Integration

- supabase-py client (service_role key)
- Pydantic models (Project, Chapter, GenerateRequest, GenerateResponse)
- GET /projects/{project_id} - pobieranie projektu z Supabase
- GET /projects/{project_id}/chapters - pobieranie rozdziałów
- Test połączenia z Supabase - działa
- Fix: zaktualizowano model Project (author, language, status, custom_styles)

### Co zostało (TODO)

- POST /generate endpoint
- ebooklib + WeasyPrint
- CSS presets
- Deploy (Railway/Render)

---

## Zmiany w kodzie

### Sesja 1 - Nowe pliki

| Plik | Opis |
|------|------|
| `app/__init__.py` | Package marker |
| `app/main.py` | FastAPI app + CORS + hello world endpoints |
| `app/routers/__init__.py` | Package marker |
| `app/services/__init__.py` | Package marker |
| `app/models/__init__.py` | Package marker |
| `app/presets/__init__.py` | Package marker |
| `requirements.txt` | fastapi, uvicorn, python-dotenv |
| `.gitignore` | venv, __pycache__, .env, IDE, OS files |
| `.env` | SUPABASE_URL, SUPABASE_SERVICE_KEY (template) |

### Sesja 2 - Nowe pliki

| Plik | Opis |
|------|------|
| `app/services/supabase_client.py` | Supabase Client (service_role key) |
| `app/models/schemas.py` | Pydantic models (Project, Chapter, GenerateRequest, GenerateResponse) |
| `app/routers/projects.py` | GET /projects/{project_id}, GET /projects/{project_id}/chapters |

### Sesja 2 - Zmodyfikowane pliki

| Plik | Zmiana |
|------|--------|
| `requirements.txt` | Dodano supabase==2.9.0 |
| `app/main.py` | Podłączono projects router |
| `.env` | Uzupełniono Supabase credentials |

---

## Dependencies

```txt
fastapi==0.115.12
uvicorn[standard]==0.34.0
python-dotenv==1.0.1
supabase==2.9.0
```

---

## Znane bugi / TODO

- [ ] POST /generate endpoint (główna funkcja backendu)
- [ ] ebooklib - generowanie EPUB
- [ ] WeasyPrint - generowanie PDF
- [ ] CSS presets (classic.css, modern.css, minimal.css)
- [ ] HTML processor - czyszczenie HTML z Google Docs
- [ ] Upload do Supabase Storage (outputs/ bucket)
- [ ] INSERT do generated_files table
- [ ] Deploy na Railway/Render

---

## Kontekst dla następnej sesji

- **Zacząć od:** POST /generate endpoint + ebooklib setup
- **Port:** 8001 (8000 zajęty przez inny projekt)
- **Frontend gotowy** (czeka na backend) - Generate button disabled
- **Supabase połączony** i działa - można pobierać projekty i rozdziały

### Komendy do uruchomienia

```bash
cd tiolibri-api
source venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

### Testowe endpointy

- GET http://localhost:8001/ - Hello World
- GET http://localhost:8001/health - Health check
- GET http://localhost:8001/docs - Swagger UI
- GET http://localhost:8001/projects/{project_id} - Pobierz projekt
- GET http://localhost:8001/projects/{project_id}/chapters - Pobierz rozdziały

---

*Następna sesja: Backend Sesja 3 - POST /generate + EPUB/PDF generation*
