# TIOLIBRI – Sesja 14-15 – Docker + Custom Domains
**Data:** 2026-01-27
**Czas:** ~8h (z przerwą: 6:34 AM - 7:32 AM, 12:04 PM - 2:28 PM)

---

## Cel Sesji

- Naprawienie PDF generation na Railway (WeasyPrint + system libs)
- Konfiguracja custom domains (app + api)
- Full production setup z SSL

---

## Zrobione w Tej Sesji

### Part 1: Docker dla Railway (rano 6:34-7:32 AM)

#### Problem
- PDF generation: 500 error
- WeasyPrint: "cannot load library 'libgobject-2.0-0'"
- Railway Nixpacks nie instaluje systemowych bibliotek

#### Rozwiązanie: Dockerfile

Utworzono `tiolibri-api/Dockerfile`:
- Base: `python:3.11-bookworm` (nie slim - potrzeba pełnych libs)
- System packages: Cairo, Pango, GObject, GdkPixbuf, libffi-dev
- Polish fonts: `fonts-liberation`, `fonts-dejavu-core` (dla ąęćłńóśźż)
- Dynamic port: CMD z `${PORT:-8000}` dla Railway
- `.dockerignore` dla optymalizacji

#### Kroki Wykonane
1. Claude Code wygenerował Dockerfile z wszystkimi zależnościami
2. Usunięcie Procfile (konflikt z Dockerfile - Railway priorytetyzuje Procfile)
3. Push do GitHub
4. Railway auto-detect Dockerfile
5. Problem: Railway deployowało na port 8080, ale public domain wskazywała na 8000
6. Fix: Zmiana portu w Railway Networking na 8080
7. Test: `/health` endpoint 200 OK

#### Rezultat
- ✅ PDF generation działa w produkcji
- ✅ Polskie znaki wyświetlają się poprawnie (ąęćłńóśźż)
- ✅ WeasyPrint ma wszystkie system dependencies

---

### Part 2: Custom Domains (popołudnie 12:04-2:28 PM)

#### Cel
- Frontend: `app.tiolibri.com`
- Backend: `api.tiolibri.com`

#### DNS Configuration (OVH)

Dodano rekordy CNAME:
```
CNAME app.tiolibri.com → cname.vercel-dns.com
CNAME api.tiolibri.com → tiolibri-production.up.railway.app
```

#### Vercel Setup
1. Add Domain: `app.tiolibri.com`
2. DNS verification (5-10 min propagation)
3. SSL certificate auto-generated (Let's Encrypt)
4. Update env: `VITE_API_URL=https://api.tiolibri.com`
5. Redeploy

#### Railway Setup
1. Add Custom Domain: `api.tiolibri.com`
2. Select port: 8080 (uvicorn)
3. Initial problem: Użytkownik dodał `api.tiolibri.pl` zamiast `.com` (typo!)
4. DNS propagation lokalnie OK (nslookup), Railway waiting
5. Fix: Usuń `.pl`, dodaj `.com`
6. SSL certificate auto-generated
7. Status: Active + zielony checkmark

#### Backend CORS Update

Zaktualizowano `main.py`:
```python
allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "https://tiolibri.vercel.app",
    "https://app.tiolibri.com"
]
```

#### UX Polish - Dynamic Page Titles

Claude Code dodał `useEffect` w komponentach:
- **LoginPage:** `"Login - TIOLIBRI"`
- **SignupPage:** `"Sign Up - TIOLIBRI"`
- **DashboardPage:** `"Dashboard - TIOLIBRI"`
- **EditorPage:** `"{project.title} - TIOLIBRI"` (dynamiczny)

---

## Troubleshooting (Challenges Podczas Sesji)

### Railway nie wykrywało Dockerfile
- **Problem:** Procfile miał wyższy priorytet
- **Fix:** Usunięcie Procfile naprawiło
- **Dodatkowe:** Port mismatch (8000 vs 8080) - zmiana w Networking
- **Workaround:** Dummy commit wymuszający rebuild

### SSL Certificate Error
- **Error:** `net::ERR_CERT_COMMON_NAME_INVALID`
- **Rozwiązanie:** Poczekać 10-15 min na Let's Encrypt generation

### DNS Propagation
- **Problem:** Railway UI pokazywało "Waiting for DNS update" przez 1h+
- **Lokalnie:** DNS działało (`nslookup` OK)
- **Root cause:** Użytkownik dodał `.pl` zamiast `.com` (typo)
- **Fix:** Usunięcie + ponowne dodanie z `.com`

---

## Aktualny Status Po Sesji

### Production URLs
- **Frontend:** https://app.tiolibri.com ✅
- **Backend:** https://api.tiolibri.com ✅
- **Backup:** https://tiolibri-production.up.railway.app ✅ (pozostawiony jako fallback)

### Funkcjonalność
- Login/Signup: ✅
- Dashboard: ✅
- Editor (WYSIWYG): ✅
- Typography controls: ✅
- Cover upload: ✅
- Images in text: ✅
- Paginated preview: ✅
- EPUB generation: ✅
- PDF generation: ✅ (polskie znaki działają)
- Download: ✅
- Custom domains: ✅
- SSL encryption: ✅

---

## Tech Stack Update

| Component | Technology | Deployment |
|-----------|-----------|------------|
| Frontend | React 19 + Vite + Tailwind | Vercel |
| Backend | Python 3.11 + FastAPI | Railway (Docker) |
| Database | Supabase PostgreSQL | Supabase Cloud |
| Storage | Supabase Storage | Supabase Cloud |
| PDF | WeasyPrint + Cairo/Pango | Docker container |
| DNS | OVH | - |
| SSL | Let's Encrypt | Auto-generated |
| Domains | app.tiolibri.com, api.tiolibri.com | - |

---

## Kluczowe Learnings

### Railway + Dockerfile
- Procfile ma pierwszeństwo nad Dockerfile
- Usunięcie Procfile wymusza Docker build
- `railway.toml` może powodować konflikty - lepiej używać tylko Dockerfile CMD

### DNS & Custom Domains
- CNAME propagacja: 5-30 min (zazwyczaj)
- Railway UI może pokazywać "waiting" mimo że DNS działa lokalnie
- `nslookup` to szybki sposób na weryfikację DNS
- Typo w nazwie domeny (`.pl` vs `.com`) = hours of debugging!

### Docker dla WeasyPrint
- `python:3.11-bookworm` (nie slim)
- Fonty polskie (`fonts-liberation`, `fonts-dejavu-core`) są kluczowe
- Dynamic port binding (`${PORT:-8000}`) dla Railway

---

## Time Breakdown

- Dockerfile creation: ~30 min
- Railway troubleshooting (port, Procfile): ~1h
- Custom domains setup: ~1h
- DNS propagation + debugging: ~2h (głównie czekanie + typo fix)
- CORS + env updates: ~20 min
- UX polish (page titles): ~15 min
- Testing + verification: ~30 min

**Total active time:** ~5.5h
**Total calendar time:** ~8h (z przerwami i czekaniem na DNS)

---

## Definition of Done - MVP

### ✅ 100% COMPLETE

- ✅ User może się zarejestrować i zalogować
- ✅ User może utworzyć projekt
- ✅ User może uploadować rozdziały HTML
- ✅ User może edytować rozdziały (WYSIWYG)
- ✅ User może kontrolować typografię (14 parametrów)
- ✅ User może wstawiać obrazki i dividers
- ✅ User może zobaczyć live paginated preview
- ✅ User może wygenerować EPUB + PDF
- ✅ User może pobrać wygenerowane pliki
- ✅ Aplikacja jest deployed na własnych domenach

---

## Next Steps (Opcjonalne)

### Quick Wins
- Export progress indicator
- Toast notifications
- Better error messages
- Mobile responsive polish

### Future Features
- Landing page na `tiolibri.com` (root domain)
- Table of Contents auto-generation
- Chapter reordering (drag & drop)
- Download history
- Custom fonts upload

### Infrastructure
- Monitoring (Sentry)
- Analytics (Plausible/Umami)
- Backup strategy
- CI/CD optimizations

---

## Pliki Utworzone/Zmodyfikowane

### Nowe pliki (Sesja 14)
- `tiolibri-api/Dockerfile` - Production Docker image
- `tiolibri-api/.dockerignore` - Docker build optimization
- `railway.toml` - Railway build config

### Zmodyfikowane pliki (Sesja 15)
- `tiolibri-api/app/main.py` - CORS update dla `app.tiolibri.com`
- `tiolibri-frontend/src/features/auth/LoginPage.jsx` - Dynamic title
- `tiolibri-frontend/src/features/auth/SignupPage.jsx` - Dynamic title
- `tiolibri-frontend/src/features/projects/DashboardPage.jsx` - Dynamic title
- `tiolibri-frontend/src/features/editor/EditorPage.jsx` - Dynamic title with project name

### Usunięte pliki
- `tiolibri-api/Procfile` - Konflikt z Dockerfile

---

## Podsumowanie

**Problem 1:** PDF generation nie działało (WeasyPrint missing libs)
**Rozwiązanie:** Dockerfile z pełnymi system dependencies

**Problem 2:** Generic domains (*.vercel.app, *.railway.app)
**Rozwiązanie:** Custom domains z OVH DNS + Let's Encrypt SSL

**Status:** 🎉 MVP 100% COMPLETE z production custom domains!

**URLs:**
- Frontend: https://app.tiolibri.com
- Backend: https://api.tiolibri.com

---

*Ostatnia aktualizacja: 2026-01-27*
*Sesje: 14-15 (Docker + Custom Domains)*
*Total dev time: 33.5h (from zero to production)*
