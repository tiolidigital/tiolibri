📘 TIOLIBRI — Blueprint v1.0
Wizja produktu
Aplikacja webowa do tworzenia profesjonalnych e-booków (EPUB + PDF) z plików HTML eksportowanych z Google Docs. Prosty interfejs dla nietechnicznych użytkowników, możliwość customizacji stylów, praca nad wieloma projektami jednocześnie.

Stack technologiczny
WarstwaTechnologiaGdzie hostowaneFrontendReact 18 + Vite + TailwindVercelAuth + BazaSupabase (PostgreSQL)Supabase Cloud (EU)Storage plikówSupabase StorageSupabase Cloud (EU)Backend (generator)Python + FastAPIRailway lub RenderGenerator EPUBebooklib—Generator PDFWeasyPrint—

Architektura
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│                   (React + Vite + Tailwind)                  │
│                        Vercel                                │
├─────────────────────────────────────────────────────────────┤
│  Dashboard → Lista projektów                                 │
│  Editor → Upload HTML, zarządzanie rozdziałami, style       │
│  Preview → Podgląd e-booka                                  │
│  Generate → Wywołanie API, pobranie plików                  │
└───────────────┬─────────────────────┬───────────────────────┘
                │                     │
                ▼                     ▼
┌───────────────────────┐   ┌─────────────────────────────────┐
│      SUPABASE         │   │      PYTHON MICROSERVICE        │
│  (Auth + DB + Storage)│   │         (FastAPI)               │
│                       │   │      Railway / Render           │
├───────────────────────┤   ├─────────────────────────────────┤
│ • Logowanie           │   │ • POST /generate                │
│ • Tabele: projects,   │   │   - Pobiera pliki z Supabase    │
│   chapters, styles    │   │   - Parsuje HTML                │
│ • Storage: uploads/,  │   │   - Generuje EPUB + PDF         │
│   outputs/, assets/   │   │   - Uploaduje do Supabase       │
└───────────────────────┘   │   - Zwraca linki do pobrania    │
                            └─────────────────────────────────┘

Model danych (Supabase PostgreSQL)
Tabela: projects
sqlCREATE TABLE projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  
  title TEXT NOT NULL DEFAULT 'Nowy projekt',
  author TEXT DEFAULT '',
  language TEXT DEFAULT 'pl',
  
  status TEXT DEFAULT 'draft', -- draft | in_progress | completed
  
  -- Referencja do aktywnego stylu
  style_preset TEXT DEFAULT 'classic', -- classic | modern | minimal | custom
  custom_styles JSONB DEFAULT '{}',    -- nadpisania dla custom
  
  -- Metadane
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own projects" ON projects
  FOR ALL USING (auth.uid() = user_id);
Tabela: chapters
sqlCREATE TABLE chapters (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  
  title TEXT NOT NULL DEFAULT 'Rozdział',
  sort_order INTEGER NOT NULL DEFAULT 0,
  
  -- Ścieżka do pliku HTML w Supabase Storage
  source_file_path TEXT,  -- uploads/{project_id}/{filename}.html
  
  -- Przetworzona treść (cache)
  processed_html TEXT,
  
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS (przez projekt)
ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own chapters" ON chapters
  FOR ALL USING (
    project_id IN (SELECT id FROM projects WHERE user_id = auth.uid())
  );
Tabela: assets
sqlCREATE TABLE assets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  
  name TEXT NOT NULL,           -- np. "ewa", "divider"
  type TEXT NOT NULL,           -- image | divider
  file_path TEXT NOT NULL,      -- assets/{project_id}/{filename}
  
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own assets" ON assets
  FOR ALL USING (
    project_id IN (SELECT id FROM projects WHERE user_id = auth.uid())
  );
Tabela: generated_files
sqlCREATE TABLE generated_files (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  
  format TEXT NOT NULL,         -- epub | pdf
  file_path TEXT NOT NULL,      -- outputs/{project_id}/{filename}
  file_size INTEGER,
  
  generated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE generated_files ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own files" ON generated_files
  FOR ALL USING (
    project_id IN (SELECT id FROM projects WHERE user_id = auth.uid())
  );
```

---

## Supabase Storage Buckets
```
storage/
├── uploads/          # Surowe pliki HTML z Google Docs
│   └── {project_id}/
│       ├── chapter_01.html
│       └── chapter_02.html
│
├── assets/           # Obrazki, dividery SVG
│   └── {project_id}/
│       ├── ewa.jpg
│       └── divider.svg
│
└── outputs/          # Wygenerowane e-booki
    └── {project_id}/
        ├── book.epub
        └── book.pdf
```

---

## Struktura frontendu (React)
```
tiolibri-frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── ui/                    # Bazowe komponenty
│   │   │   ├── Button.jsx
│   │   │   ├── Input.jsx
│   │   │   ├── Modal.jsx
│   │   │   ├── Card.jsx
│   │   │   ├── Dropdown.jsx
│   │   │   └── FileUpload.jsx     # Drag & drop upload
│   │   │
│   │   └── layout/
│   │       ├── Sidebar.jsx        # Nawigacja
│   │       ├── Header.jsx
│   │       └── PageWrapper.jsx
│   │
│   ├── features/
│   │   ├── auth/
│   │   │   ├── LoginPage.jsx
│   │   │   └── useAuth.js         # Hook do auth
│   │   │
│   │   ├── projects/
│   │   │   ├── ProjectList.jsx    # Dashboard - lista projektów
│   │   │   ├── ProjectCard.jsx
│   │   │   ├── NewProjectModal.jsx
│   │   │   └── useProjects.js     # Hook do CRUD projektów
│   │   │
│   │   ├── editor/
│   │   │   ├── EditorPage.jsx     # Główny widok edycji
│   │   │   ├── ChapterList.jsx    # Lista rozdziałów (sortowalna)
│   │   │   ├── ChapterUpload.jsx  # Upload HTML
│   │   │   ├── AssetManager.jsx   # Zarządzanie obrazkami
│   │   │   ├── MetadataPanel.jsx  # Tytuł, autor, język
│   │   │   └── useEditor.js
│   │   │
│   │   ├── styles/
│   │   │   ├── StylePanel.jsx     # Panel wyboru stylów
│   │   │   ├── PresetSelector.jsx # Wybór presetu
│   │   │   ├── StyleSliders.jsx   # Suwaki (font size, colors)
│   │   │   ├── presets/           # Definicje presetów
│   │   │   │   ├── classic.js
│   │   │   │   ├── modern.js
│   │   │   │   └── minimal.js
│   │   │   └── useStyles.js
│   │   │
│   │   ├── preview/
│   │   │   ├── PreviewPanel.jsx   # Podgląd renderowanego HTML
│   │   │   └── usePreview.js
│   │   │
│   │   └── generate/
│   │       ├── GenerateButton.jsx
│   │       ├── GenerateProgress.jsx  # Pasek postępu
│   │       ├── DownloadPanel.jsx     # Linki do pobrania
│   │       └── useGenerate.js        # Wywołanie API Pythona
│   │
│   ├── lib/
│   │   ├── supabase.js            # Klient Supabase
│   │   ├── api.js                 # Wywołania do Python API
│   │   └── utils.js
│   │
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css                  # Tailwind imports
│
├── .env.local                     # VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
├── package.json
├── tailwind.config.js
└── vite.config.js
```

---

## Struktura backendu (Python FastAPI)
```
tiolibri-api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, CORS, routes
│   │
│   ├── routers/
│   │   └── generate.py            # POST /generate endpoint
│   │
│   ├── services/
│   │   ├── supabase_client.py     # Połączenie z Supabase
│   │   ├── html_processor.py      # Czyszczenie HTML z Google Docs
│   │   ├── epub_generator.py      # Generowanie EPUB
│   │   ├── pdf_generator.py       # Generowanie PDF
│   │   └── image_optimizer.py     # Skalowanie obrazków
│   │
│   ├── models/
│   │   └── schemas.py             # Pydantic models (request/response)
│   │
│   └── presets/
│       ├── classic.css
│       ├── modern.css
│       └── minimal.css
│
├── requirements.txt
├── Dockerfile                     # Dla Railway/Render
└── .env                           # SUPABASE_URL, SUPABASE_SERVICE_KEY

API Endpoints (Python)
POST /generate
Request:
json{
  "project_id": "uuid",
  "formats": ["epub", "pdf"],
  "style_preset": "classic",
  "custom_styles": {
    "font_body": "Georgia",
    "font_heading": "Playfair Display",
    "font_size_base": "11pt",
    "color_heading": "#2c3e50"
  }
}
Response:
json{
  "success": true,
  "files": {
    "epub": "https://supabase.storage/.../book.epub",
    "pdf": "https://supabase.storage/.../book.pdf"
  },
  "stats": {
    "chapters": 12,
    "images": 5,
    "generation_time_seconds": 24
  }
}
```

### `POST /preview`

Generuje szybki podgląd HTML (bez pełnego EPUB/PDF) do wyświetlenia w przeglądarce.

---

## Presety stylów (MVP)

### Classic
- Font body: Georgia / Literata
- Font headings: Playfair Display
- Rozmiar: 11pt
- Kolory: ciemny granat (#2c3e50), stonowane

### Modern
- Font body: Inter / Source Sans Pro
- Font headings: Montserrat
- Rozmiar: 12pt
- Kolory: czerń + akcenty (#3498db)

### Minimal
- Font body: system-ui
- Font headings: system-ui bold
- Rozmiar: 11pt
- Kolory: tylko czerń i szarości

---

## Flow użytkownika (MVP)
```
1. LOGIN
   └── Supabase Auth (email + hasło lub magic link)
   
2. DASHBOARD
   ├── Lista projektów (karty)
   ├── [+ Nowy projekt]
   └── Klik na projekt → EDITOR

3. EDITOR
   ├── Lewy panel: Lista rozdziałów
   │   ├── Drag & drop do zmiany kolejności
   │   ├── [+ Upload HTML] 
   │   └── [+ Dodaj obrazki]
   │
   ├── Środek: Podgląd (live preview aktywnego rozdziału)
   │
   └── Prawy panel: Ustawienia
       ├── Tytuł, Autor
       ├── Preset stylu (dropdown)
       ├── Suwaki customizacji
       └── [GENERUJ E-BOOK]

4. GENEROWANIE
   ├── Modal z progress barem
   ├── "Generowanie EPUB... ✓"
   ├── "Generowanie PDF... ✓"
   └── Przyciski [Pobierz EPUB] [Pobierz PDF]
```

---

## Etapy rozwoju

| Etap | Zakres | Czas (szacunek) |
|------|--------|-----------------|
| **MVP** | Auth, projekty, upload rozdziałów, 3 presety, generowanie EPUB+PDF | 2-3 tygodnie |
| **v1.1** | Własne presety (zapisz/wczytaj), drag & drop reordering rozdziałów, bulk upload | +1 tydzień |
| **v1.2** | Pełny edytor CSS (Monaco), live preview, więcej opcji typografii | +2 tygodnie |
| **v2.0** | Multi-user, zaproszenia do projektu, role (owner/editor/viewer) | +2-3 tygodnie |

---

## Jak zacząć z Sonnetem w VSC

**Krok 1: Stwórz repo i strukturę**
```
Stwórz projekt React + Vite + Tailwind o nazwie "tiolibri-frontend" 
ze strukturą folderów jak w blueprincie. Na razie puste pliki.
```

**Krok 2: Supabase setup**
```
Potrzebuję komendy SQL do stworzenia tabel w Supabase 
dla projektu Tiolibri (projects, chapters, assets, generated_files).
Weź schemat z blueprintu.
```

**Krok 3: Auth flow**
```
Zaimplementuj logowanie przez Supabase Auth (email + hasło).
Komponent LoginPage.jsx + hook useAuth.js.
Po zalogowaniu przekieruj na /dashboard.
```

**Krok 4: Dashboard**
```
Stwórz stronę /dashboard która wyświetla listę projektów 
użytkownika z Supabase. Karty z tytułem, autorem, statusem.
Przycisk "Nowy projekt" otwiera modal.
...i tak dalej, krok po kroku.
