# Sesja 14: Docker + Railway PDF Fix
**Data:** 2026-01-27
**Czas trwania:** ~1.5h
**Status:** ✅ SUCCESS - PDF działa w produkcji!

---

## 🎯 Cel Sesji
Fix PDF generation w produkcji na Railway - WeasyPrint zwracał 500 error przez brak system libraries.

---

## 🐛 Problem
```
POST /generate → 500 Internal Server Error
PDF generation failed: WeasyPrint dependencies missing
```

**Root cause:**
- Railway Nixpacks buildpack nie instalował Cairo/Pango/GObject
- `Procfile` nie działał z WeasyPrint system dependencies
- Port configuration (Railway używa dynamicznego $PORT)

---

## ✅ Rozwiązanie

### 1. Dockerfile dla Railway
Stworzony: `tiolibri-api/Dockerfile`

```dockerfile
FROM python:3.11-bookworm

# System dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Kluczowe elementy:**
- Base: `python:3.11-bookworm` (Debian 12)
- System libs: Cairo, Pango, GObject, GdkPixbuf
- Polish fonts: `fonts-liberation`, `fonts-dejavu-core` (ąęćłńóśźż)
- Dynamic port: `${PORT:-8000}` dla Railway

### 2. .dockerignore
Stworzony: `tiolibri-api/.dockerignore`

Excludes:
- `venv/`, `__pycache__/`
- `.env`, `.git/`
- `run_dev.sh`, `docs/`

### 3. Railway Configuration
Stworzony: `railway.toml` (root projektu)

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "tiolibri-api/Dockerfile"
```

**Usunięte:**
- `Procfile` (konfliktował z Dockerfile)
- Sekcja `[deploy]` z railway.toml (Railway używa CMD z Dockerfile)

### 4. Port Mapping
Railway auto-mapuje:
- Internal: `$PORT` (dynamiczny, np. 8080)
- External: `tiolibri-production.up.railway.app` (public domain)

---

## 🧪 Testing w Produkcji

### Test 1: Health Check
```bash
curl https://tiolibri-production.up.railway.app/health
# ✅ Response: 200 OK
```

### Test 2: EPUB Generation
```bash
POST /generate (format: epub)
# ✅ Response: 200 OK
# ✅ Public URL działa w przeglądarce
```

### Test 3: PDF Generation (Critical!)
```bash
POST /generate (format: pdf)
# ✅ Response: 200 OK
# ✅ PDF zawiera polskie znaki: ąęćłńóśźż
# ✅ Typography settings applied
# ✅ Images embedded
# ✅ Cover image embedded
```

---

## 📊 Wyniki

### Przed (Sesja 13)
- Frontend: ✅ Vercel
- Backend: ⚠️ Railway (EPUB OK, PDF 500 error)
- Status: 90% MVP (brak PDF w produkcji)

### Po (Sesja 14)
- Frontend: ✅ Vercel
- Backend: ✅ Railway (EPUB + PDF working)
- Status: 🎉 100% MVP COMPLETE!

---

## 📁 Pliki Zmienione

### Nowe pliki:
1. `tiolibri-api/Dockerfile` - Production-ready Docker image
2. `tiolibri-api/.dockerignore` - Exclude unnecessary files
3. `railway.toml` - Railway build configuration

### Usunięte pliki:
1. `tiolibri-api/Procfile` - Replaced by Dockerfile CMD

---

## 🎯 Tech Details

### WeasyPrint Dependencies (Linux)
```bash
# Required system libraries:
libcairo2           # 2D graphics
libpango-1.0-0      # Text layout
libpangocairo-1.0-0 # Pango + Cairo integration
libgdk-pixbuf2.0-0  # Image loading
libffi-dev          # Foreign Function Interface
shared-mime-info    # MIME type detection
```

### Polish Fonts
```bash
fonts-liberation    # Liberation Sans/Serif (metric-compatible z Arial/Times)
fonts-dejavu-core   # DejaVu Sans/Serif (Unicode support)
```

Oba zawierają glyphs dla: ą ć ę ł ń ó ś ź ż

### Railway Port Binding
Railway provides `$PORT` environment variable dynamically:
- Container listens on `$PORT` (e.g., 8080)
- Railway exposes public domain on standard HTTPS (443)
- No need for explicit port configuration in railway.toml

---

## 🏆 Achievement: MVP 100% Complete

### All Features Working in Production:
- ✅ User authentication (Supabase Auth)
- ✅ Projects CRUD
- ✅ WYSIWYG editor (TipTap)
- ✅ Typography controls (14 parameters)
- ✅ Cover upload
- ✅ Images in text
- ✅ SVG dividers
- ✅ Paginated preview
- ✅ EPUB export (ebooklib)
- ✅ PDF export (WeasyPrint + Polish fonts)
- ✅ Download (public URLs)

### Production URLs:
- **Frontend:** https://tiolibri.vercel.app
- **Backend:** https://tiolibri-production.up.railway.app
- **Database:** Supabase (EU region)

---

## 📈 Development Timeline

| Milestone | Sessions | Time | Status |
|-----------|----------|------|--------|
| MVP Core Features | 1-12 | ~21h | ✅ |
| Deploy (Vercel + Railway) | 13 | ~3h | ✅ |
| Docker + PDF Fix | 14 | ~1.5h | ✅ |
| **TOTAL** | **14** | **~25.5h** | **🎉 COMPLETE** |

---

## 💡 Lessons Learned

1. **Railway Dockerfile > Procfile** for complex dependencies
2. **System libraries** must be installed at OS level (apt-get)
3. **Dynamic port binding** (${PORT:-8000}) is critical for Railway
4. **railway.toml** minimal config - let Dockerfile handle the rest
5. **Polish fonts** require explicit package installation

---

## 🚀 What's Next?

### Optional Polish (~1-2h):
- Export progress indicator
- Toast notifications
- Error handling improvements
- Mobile responsive fixes

### Future Features:
- Table of Contents auto-generation
- Chapter reordering (drag & drop)
- Download history
- Custom fonts upload
- Footnotes/endnotes

---

## 🎉 Podsumowanie

**Problem:** WeasyPrint 500 error w produkcji (brak system dependencies)

**Rozwiązanie:** Dockerfile z explicit system libraries + Railway configuration

**Czas:** 1.5h

**Status:** SUCCESS - PDF generation działa z polskimi znakami! 🚀

---

*Ostatnia aktualizacja: 2026-01-27*
*MVP Status: 100% COMPLETE* ✅
