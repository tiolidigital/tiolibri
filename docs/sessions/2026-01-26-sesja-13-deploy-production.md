TIOLIBRI – Sesja 13 – Deploy Production (Vercel + Railway)
Data: 2026-01-26
Czas: ~3h

Cel sesji
- Wdrożenie frontendu TIOLIBRI na Vercel.
- Wdrożenie backendu FastAPI na Railway.
- Spięcie wszystkiego z istniejącym projektem Supabase.
- Przeprowadzenie pierwszych E2E testów produkcyjnych.

Zrobione w tej sesji
Frontend (Vercel)
- Utworzenie repozytorium GitHub `tiolibri` i wrzucenie całego monorepo (docs, tiolibri-frontend, tiolibri-api).
- Konfiguracja projektu na Vercel:
  - Root: `tiolibri-frontend`
  - Framework: Vite
  - Build command: `npm run build`
  - Output: `dist`
- Ustawienie env:
  - `VITE_SUPABASE_URL` – produkcyjny URL Supabase.
  - `VITE_SUPABASE_ANON_KEY` – anon public key z tego samego projektu.
- Dodanie `VITE_API_URL`:
  - `VITE_API_URL=https://tiolibri-production.up.railway.app`
- Naprawa błędów builda Vite:
  - Poprawione JSX w `EditorPage.jsx` (zagnieżdżenie divów, domknięcia).
- Ostatecznie:
  - `https://tiolibri.vercel.app` działa.
  - Login / dashboard / edycja działają na produkcji.

Backend (Railway)
- Import repo `tiolibri` z GitHub do Railway.
- Skonfigurowanie subfolderu backendu:
  - Root / project path: `tiolibri-api`
- Dodanie pliku `Procfile`:
  - `web: uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Wyrównanie portów:
  - Dev: `run_dev.sh` zmieniony na port 8000.
  - Railway: nasłuch na 8000.
- Konfiguracja zmiennych środowiskowych:
  - `SUPABASE_URL` – Project URL Supabase.
  - `SUPABASE_SERVICE_KEY` – service_role secret (DB).
  - `SUPABASE_KEY` – ten sam service_role secret (dla storage3).
- Rozwiązanie błędów startu:
  - ValueError: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY → dodane właściwe env.
  - AttributeError: 'NoneType' in storage3 headers → ustawione `SUPABASE_KEY`.
- Wygenerowanie public domain:
  - Port 8000, domena: `https://tiolibri-production.up.railway.app`
- Healthcheck:
  - `GET /health` zwraca `{"status": "healthy"}`.
  - `GET /` zwraca komunikat „TIOLIBRI API is running!”.

Integracja front–backend
- W `tiolibri-frontend/src/lib/api.js`:
  - `API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`.
- Czyszczenie hardcoded URL:
  - W `GenerateBooks.jsx` usunięto `fetch('http://localhost:8002/generate', ...)`.
  - Wszystkie wywołania używają teraz `API_URL`.
- Aktualizacja `.env.local`:
  - `VITE_API_URL=http://localhost:8000` do dev.
- Vercel env:
  - `VITE_API_URL=https://tiolibri-production.up.railway.app`
- Potwierdzenie w Network:
  - Request `generate` leci na `https://tiolibri-production.up.railway.app/generate`.

CORS i bezpieczeństwo
- W `tiolibri-api/app/main.py`:
  - Dodano `https://tiolibri.vercel.app` do `allow_origins`.
  - CORS działa – requesty z produkcyjnego frontu dochodzą do API.

Status generacji
- EPUB:
  - Generacja działa (ebooklib, Supabase Storage) – brak błędów.
- PDF:
  - `500 Internal Server Error` podczas generacji.
  - Błąd WeasyPrint:
    - „PDF generation failed: cannot load library 'libgobject-2.0-0' … cannot open shared object file”.
  - Root cause:
    - Brak systemowych bibliotek GObject/Cairo/Pango w środowisku Railway.

Aktualny status po sesji
- Frontend:
  - Deployed na Vercel: `https://tiolibri.vercel.app`
  - Login / dashboard / edycja / upload / paginated preview – działają.
- Backend:
  - Deployed na Railway: `https://tiolibri-production.up.railway.app`
  - `/` i `/health` OK.
  - Projekty / rozdziały / Supabase Storage – działają.
- Integracja:
  - Front używa produkcyjnego API URL przez `VITE_API_URL`.
  - CORS skonfigurowany.
- Eksport:
  - EPUB – OK w produkcji.
  - PDF – FAIL (brak libgobject-2.0-0).

Plan na kolejną sesję
1. PDF / WeasyPrint na Railway:
   - Dodać `Dockerfile` w `tiolibri-api` bazujący na `python:3.11-slim` (lub podobnym).
   - Zainstalować systemowe biblioteki:
     - `libcairo2`, `libpango-1.0-0`, `libgdk-pixbuf2.0-0`, `libffi-dev`, `libgobject-2.0-0`, plus zależności fon­tów.
   - Przełączyć serwis Railway na deploy z Dockerfile.
   - Przetestować PDF generację w produkcji, sprawdzić wielkość obrazków i polskie znaki.
2. Dokończenie testów E2E:
   - Pełny flow na produkcji: signup → projekt → upload → edycja → EPUB/PDF → pobranie.
   - Test na desktop + mobile (różne przeglądarki).
3. Lekki polish (opcjonalnie):
   - Wizualny progress indicator przy eksporcie.
   - Lepiej opisane błędy dla generacji (np. toast z info, gdy PDF padnie).
4. Post-deploy:
   - Monitoring błędów (Sentry / logi Railway).
   - Ewentualne ustawienie custom domain dla frontu i backendu.