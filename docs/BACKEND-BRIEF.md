# TIOLIBRI - Backend Development Brief

**Data:** 2026-01-24
**Status frontendu:** MVP ukończony
**Następny krok:** Python Backend (FastAPI + EPUB/PDF generation)

---

## Co Jest Zrobione

### Frontend (100% MVP)
- React 19 + Vite + Tailwind 4
- Auth flow (Supabase - login/signup)
- Dashboard (lista projektów, CRUD)
- Editor:
  - Upload HTML (drag & drop → Supabase Storage `uploads/`)
  - Lista rozdziałów
  - TipTap WYSIWYG editor (auto-save)
  - Style selector (3 presety: Classic, Modern, Minimal)
  - Generate button (disabled - czeka na backend)

### Supabase
- Tabele: `projects`, `chapters`, `assets`, `generated_files`
- Storage buckets: `uploads/`, `assets/`, `outputs/`
- RLS policies (user widzi tylko swoje dane)

---

## Co Teraz Budujemy: Python Backend

### Tech Stack Backend

| Warstwa | Technologia | Hosting |
|---------|-------------|---------|
| Framework | FastAPI | Railway lub Render |
| EPUB | ebooklib | — |
| PDF | WeasyPrint | — |
| Fetch z Supabase | supabase-py | — |

---

## API Endpoint (MVP)

### `POST /generate`

**Request:**
```json
{
  "project_id": "uuid",
  "formats": ["epub", "pdf"],
  "style_preset": "classic"
}
```

**Response:**
```json
{
  "success": true,
  "files": {
    "epub": "https://supabase.storage/.../book.epub",
    "pdf": "https://supabase.storage/.../book.pdf"
  },
  "stats": {
    "chapters": 5,
    "generation_time_seconds": 12
  }
}
```

### Flow:

1. Pobierz projekt z Supabase (`projects` table)
2. Pobierz rozdziały (`chapters` table ORDER BY sort_order)
3. Dla każdego rozdziału:
   - Jeśli `processed_html` istnieje → użyj tego
   - Jeśli nie → pobierz z Storage `uploads/{project_id}/{filename}`
4. Zastosuj styl (CSS dla Classic/Modern/Minimal)
5. Generuj EPUB (ebooklib)
6. Generuj PDF (WeasyPrint z EPUB HTML)
7. Upload do Storage `outputs/{project_id}/book.epub|pdf`
8. INSERT do `generated_files` table
9. Zwróć signed URLs

---

## Style Presety

### Classic
```css
body { font-family: Georgia, serif; }
h1 { font-family: 'Playfair Display', serif; font-size: 24pt; }
p { font-size: 11pt; line-height: 1.6; }
```

### Modern
```css
body { font-family: 'Inter', sans-serif; }
h1 { font-family: 'Montserrat', sans-serif; font-size: 22pt; }
p { font-size: 12pt; line-height: 1.5; }
```

### Minimal
```css
body { font-family: system-ui, sans-serif; }
h1 { font-size: 20pt; font-weight: bold; }
p { font-size: 11pt; line-height: 1.6; }
```

---

## Struktura Backend (do stworzenia)

```
tiolibri-api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + CORS
│   ├── routers/
│   │   └── generate.py            # POST /generate endpoint
│   ├── services/
│   │   ├── supabase_client.py     # Połączenie z Supabase
│   │   ├── epub_generator.py      # ebooklib logic
│   │   ├── pdf_generator.py       # WeasyPrint logic
│   │   └── html_processor.py      # Czyszczenie HTML z Google Docs
│   ├── models/
│   │   └── schemas.py             # Pydantic models
│   └── presets/
│       ├── classic.css
│       ├── modern.css
│       └── minimal.css
├── requirements.txt
├── Dockerfile
└── .env                           # SUPABASE_URL, SUPABASE_SERVICE_KEY
```

---

## Integracja z Frontendem

Frontend (EditorPage - Generate button):

```javascript
const handleGenerate = async () => {
  setIsGenerating(true)

  const response = await fetch(`${import.meta.env.VITE_API_URL}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_id: project.id,
      formats: ['epub', 'pdf'],
      style_preset: project.style_preset
    })
  })

  const data = await response.json()

  // Pokaż modal z linkami do pobrania
  setDownloadLinks(data.files)
  setIsGenerating(false)
}
```

---

## Supabase Credentials

- **Frontend używa:** `VITE_SUPABASE_ANON_KEY` (public, RLS-protected)
- **Backend potrzebuje:** `SUPABASE_SERVICE_KEY` (service_role, bypasses RLS)

**Gdzie znaleźć:**
Supabase Dashboard → Settings → API → service_role key

**WAŻNE:** Service key = full access - NIGDY nie commituj do repo!

---

## Definition of Done

Backend MVP gotowy gdy:

- [ ] `POST /generate` endpoint działa
- [ ] Generuje EPUB z rozdziałów
- [ ] Generuje PDF
- [ ] Upload do Supabase Storage (`outputs/`)
- [ ] Zwraca signed URLs
- [ ] Frontend może wywołać endpoint i pobrać pliki
- [ ] Działa lokalnie (localhost:8000)
- [ ] Deploy na Railway/Render

---

## Następne Kroki

1. Setup Python environment (venv)
2. Instalacja dependencies (FastAPI, ebooklib, WeasyPrint, supabase-py)
3. Supabase client (połączenie z service_role key)
4. `POST /generate` endpoint (struktura, Pydantic models)
5. EPUB generator (ebooklib logic)
6. PDF generator (WeasyPrint logic)
7. Test lokalnie (Postman/curl)
8. Integracja z frontendem (enable Generate button)
9. Deploy (Railway/Render + env vars)

---

## Kontekst dla AI

- Frontend jest DONE - nie trzeba go już ruszać
- Fokus 100% na backend
- Użytkownik ma doświadczenie z Python (nie pierwszyzna)
- Preferuje step-by-step guidance
