TIOLIBRI - Current State
Ostatnia aktualizacja: 2026-02-05 (Sesja 16)
Status: 🎉 v2.0 MVP COMPLETE - Production + Chapter Reordering + Google Docs Converter

🎉 MVP Status
✅ Co DZIAŁA (100%):
EPUB generation - ebooklib + polskie znaki ✅

PDF generation - WeasyPrint + polskie znaki (ą,ę,ć,ł,ń,ó,ś,ź,ż) ✅

Supabase Storage upload - bucket book-exports + content-type headers ✅

Publiczne URLe - działają w przeglądarce ✅

Frontend download buttons - GenerateBooks component ✅

Cleanup - /tmp/ pliki usuwane po uploadzie ✅

API endpoint - POST /generate zwraca public URLs ✅

Typography Controls (v1.1) - pełna kontrola typografii ✅

Text alignment (left/justify)

Font size (12-24px, step 2)

Line height (1.2-2.5, lookup table)

Margins (top/bottom/left/right, em units)

Auto-save do Supabase z debounce (1s)

Per-project settings (JSONB)

Cover Upload (v1.3.1) - upload okładki do e-booków ✅

CoverUpload component z drag & drop

Validation (JPG/PNG, max 5MB, 2:3 aspect ratio)

Supabase Storage (bucket assets)

Auto-embed w EPUB (base64) i PDF (binary)

Per-project cover_image_url

Images in Text (v1.3.2) - obrazki inline w rozdziałach ✅

TipTap Image extension

Upload button w toolbarze

Supabase Storage (assets/{projectId}/images/)

Auto-embed w EPUB (local paths) i PDF (base64 data URIs)

Image deduplication w EPUB

Chapter Spacing (v1.3.3) - kontrola odstępów między rozdziałami ✅

Slider control (0.5-4em range)

Auto-save do typography_settings

CSS variable replacement (--chapter-spacing)

Działa w EPUB i PDF

UI Redesign (v1.4.1) - przeprojektowanie interfejsu na jasny motyw ✅

Light theme z białym tłem

Orange accent color #e3704a (zamiast #FF6542)

Gray highlights dla aktywnych elementów

Modernizacja ikon (SVG arrows dla Undo/Redo)

Konsystentna kolorystyka (gray dla UI controls, orange dla akcji)

Focus Mode (v1.4.2) - tryb pisania bez rozpraszaczy ✅

Button w EditorToolbar (prawy górny róg)

Ukrywa lewy panel (chapters) i prawy panel (inspector)

Editor rozszerza się na pełną szerokość

Conditional rendering dla sidebars

v1.7.2 FIX: Auto-hide preview gdy Focus Mode ON, disable preview toggle

Live Typography Preview (v1.4.3) - podgląd zmian typografii na żywo ✅

CSS custom properties (--editor-font-size, --editor-line-height, --editor-text-align)

Instant preview dla Font Size, Line Height, Text Align, Margins

Smooth transitions (200ms)

Chapter Spacing nie pokazuje się w preview (tylko między rozdziałami w final output)

Split View (v1.5.1) - live book preview obok edytora ✅

BookPreview component (nowy)

60% Editor / 40% Preview layout (ultrawide 3440x1440)

Toggle button "Show/Hide Preview" + keyboard shortcut Cmd+Shift+P

Live content updates podczas pisania

Book-like page rendering (700px width, white page, shadow, page numbers)

State persistence (localStorage)

v1.7.1 FIX: Responsive layout (ultrawide vs laptop)

Margins Alignment (v1.5.2) - preview używa dobrych proporcji A5 ✅

Preview: A5 proportions (700px = 14.8cm width, PX_PER_CM conversion)

PDF: @page margins only (body margin: 0)

Backend fix w pdf_generator.py + classic.css

Nuclear reset CSS dla book-content (usuwa domyślne marginesy)

v1.6 FIX: Bottom margin widoczny dzięki paginacji

Preset Selector Fix (v1.5.3) - naprawiony flow presetów ✅

Nowy plik: presets.js (centralne definicje fontFamily dla classic/modern/minimal)

BookPreview używa getPreset() helper

ChapterEditor dostał stylePreset prop + CSS custom property --editor-font-family

editor.css używa var(--editor-font-family)

EditorPage przekazuje preset do obu komponentów

Paginated Preview (v1.6) - preview z paginacją zamiast scroll ✅

HTML content splitting algorithm (~400 words/page)

Prev/Next navigation buttons

Page counter "Page X of Y"

Keyboard navigation (← → arrows)

Fixed page height (overflow: hidden)

3-div flexbox structure (top margin / content / bottom margin)

Bottom margin teraz widoczny i funkcjonalny

Page numbers at bottom center

Disclaimer banner (approximate page count)

Clean Chapter Headings (v1.6.1) - usunięte auto-generated headings ✅

Removed filename heading z PDF/EPUB generators

User kontroluje wszystkie headingi przez TipTap

No more "DominikanaROZDZIA1..." artifacts

Stable Page Breaks (v2.0.1) - stabilne podziały stron w PDF ✅

Each chapter wrapped in <div class="chapter">

First chapter: no page-break-before

Subsequent chapters: style="page-break-before: always;"

Removed h1-based page breaks (fragile with TipTap HTML)

Fix: Editing chapter 1 no longer causes chapter 2 to "jump" pages

Chapter Reordering (v2.0.2) - drag & drop kolejności rozdziałów ✅

Database: sort_order column in chapters table

Backend: POST /projects/{projectId}/chapters/reorder endpoint

Frontend: @dnd-kit integration w ChapterList

6-dot drag handle (⋮⋮) przy każdym rozdziale

Optimistic UI update + backend sync

PDF/EPUB generators używają sort_order

Keyboard navigation support (Tab + Space/Enter)

Error handling z rollback on failure

Google Docs Converter (v2.0.3) - zachowanie formatowania z Google Docs ✅

Frontend: htmlConverter.js utility (DOMParser-based)

Auto-detection: isGoogleDocsHtml() checks for markers

CSS parsing: Extracts .cX classes from <style> block

Semantic mapping: font-weight:700 → <strong>, font-style:italic → <em>

Blockquote detection: border-left + padding-left → <blockquote>

Artifact removal: strips <meta>, <style>, inline styles

Integration: useChapters.getChapterContent() auto-converts

Console logs: 🔄 Converting... / ✅ Conversion complete

Works with nested formatting (bold+italic)

SVG Dividers (v1.7) - dekoracyjne separatory tekstu ✅

Custom TipTap extension (Divider.js)

3 minimalist styles: stars (●●●), line (───❖───), dots (- - - )

Toolbar button z dropdown menu (visual preview)

Color inheritance (currentColor - kolor tekstu)

Insert at cursor position

DOM rendering fix dla preview compatibility

Works in editor + preview + PDF + EPUB

Responsive Preview (v1.7.1) - adaptive layout dla różnych ekranów ✅

Ultrawide (≥2560px): Side-by-side 60/40 layout

Laptop (<2560px): Full-screen toggle mode

"Back to Editor" button w full-screen preview

Auto-hide preview on small screens (default)

Resize listener z cleanup

Absolute positioning for full-screen mode

Focus Mode + Preview Fix (v1.7.2) - rozwiązane konflikty ✅

Auto-hide preview gdy Focus Mode activates

Hide preview toggle button when Focus Mode ON

Disable Cmd+Shift+P shortcut in Focus Mode

No more empty white panel conflict

Clean distraction-free writing experience

🎯 PDF Solution: WeasyPrint + Lazy Import
Problem był: macOS + uvicorn --reload nie przekazuje DYLD_LIBRARY_PATH do subprocessów

Rozwiązanie:

Lazy import WeasyPrint (import wewnątrz funkcji, nie na górze pliku)

macOS fix w kodzie: os.environ["DYLD_LIBRARY_PATH"] przed importem

Wrapper script run_dev.sh z export

Setup (macOS):

bash
# 1. Brew dependencies (jednorazowo)
brew install cairo pango glib gobject-introspection

# 2. Uruchamianie ZAWSZE przez:
cd tiolibri-api
./run_dev.sh
✅ Co Działa
Frontend
✅ Projekt frontend setup (React 19 + Vite + Tailwind 4)

✅ Struktura folderów (feature-based)

✅ Podstawowe pliki konfiguracyjne (ESLint, Prettier)

✅ Living Docs (sessions/, CURRENT-STATE.md, DECISIONS.md, CLAUDE.md)

✅ Bazowe komponenty UI (Button, Input, Textarea, Card, Badge, Modal)

✅ Auth flow (login/signup + email confirmation)

✅ Dashboard - lista projektów (CRUD)

✅ Dashboard - tworzenie projektu (modal)

✅ Editor - layout 3-kolumnowy (responsive)

✅ Editor - upload HTML (drag & drop → Supabase Storage)

✅ Editor - lista rozdziałów (select, delete, drag & drop reorder - v2.0.2)

✅ Editor - TipTap WYSIWYG (headings, bold, italic, lists, auto-save)

✅ Editor - Google Docs HTML converter (auto-detects, preserves formatting - v2.0.3)

✅ Editor - edycja metadata (title, author)

✅ Editor - style selector (3 presety) - FIXED v1.5.3

✅ Generowanie e-booków (GenerateBooks component)

✅ Download EPUB/PDF (public URLs)

✅ Typography Controls (TypographyControls + useTypography hook)

✅ Typography auto-save (debounce 1s → Supabase)

✅ CoverUpload component (drag & drop, preview, validation)

✅ useCover hook (cover URL state + auto-save)

✅ TipTap Image extension (@tiptap/extension-image)

✅ TipTap Divider extension (custom - v1.7)

✅ Image upload button w EditorToolbar

✅ Divider insert button w EditorToolbar (v1.7)

✅ Chapter spacing slider w TypographyControls

✅ UI Redesign - light theme z orange accent #e3704a

✅ Focus Mode - hide sidebars, full-width editor, conflict-free (v1.7.2)

✅ Live Typography Preview - CSS custom properties

✅ Redesigned ChapterUpload modal (cloud icon, Google Docs placeholder)

✅ BookPreview component - paginated preview (v1.6)

✅ Split view layout (60/40) z responsive breakpoints (v1.7.1)

✅ Centralized presets.js (fontFamily definitions)

✅ Chapter reordering (@dnd-kit integration - v2.0.2)

✅ Google Docs HTML converter (htmlConverter.js - v2.0.3)

✅ Deploy (Vercel - PRODUCTION)

Backend
✅ Python Backend setup (FastAPI + Uvicorn @ localhost:8002)

✅ Struktura projektu (routers/, services/, models/, presets/)

✅ Virtual environment (venv)

✅ Supabase Client (service_role key)

✅ Pydantic models (Project, Chapter, GenerateRequest, GenerateResponse)

✅ Test endpointy (GET /projects/{project_id}, GET /projects/{project_id}/chapters)

✅ POST /projects/{project_id}/chapters/reorder endpoint (v2.0.2)

✅ CORS dla frontendu (localhost:5173/5174 + app.tiolibri.com)

✅ Swagger UI (/docs)

✅ POST /generate endpoint

✅ Generator EPUB (ebooklib)

✅ Generator PDF (WeasyPrint + lazy import)

✅ CSS presets (classic/modern/minimal)

✅ Typography parameters (text_align, font_size, line_height, margins)

✅ CSS variable replacement (WeasyPrint compatibility)

✅ @page rule dla PDF margins

✅ Supabase Storage upload (storage3 + content-type)

✅ Cover image download & embed (EPUB + PDF)

✅ Inline images extraction & conversion (base64 for PDF, binary for EPUB)

✅ SVG dividers preservation (inline SVG in output - v1.7)

✅ Chapter spacing parameter (v1.3.3)

✅ Image deduplication in EPUB generator

✅ PDF margins fix - removed body margins, only @page margins (v1.5.2)

✅ Clean chapter headings - no filename artifacts (v1.6.1)

✅ Stable page breaks - chapter wrapper divs (v2.0.1)

✅ Deploy (Railway + Docker - PRODUCTION)

Supabase
✅ Tabele (projects, chapters, assets, generated_files)

✅ RLS policies na tabelach (16 policies)

✅ Typography settings (projects.typography_settings JSONB)

✅ Cover image URL (projects.cover_image_url)

✅ Storage buckets (uploads, assets, outputs, book-exports)

✅ RLS policies na book-exports

✅ Public bucket assets for cover images

✅ Auth (email + hasło)

✅ sort_order column w chapters table (v2.0.2)

🛠 Tech Stack
Warstwa	Technologia	Status
Frontend	React 19 + Vite + Tailwind 4	✅ Działa
Routing	React Router 7	✅ Działa
Editor	TipTap Core (MIT)	✅ Działa
Drag & Drop	@dnd-kit (v2.0.2)	✅ Działa
HTML Parser	DOMParser (native, v2.0.3)	✅ Działa
Backend	Python 3.11 + FastAPI	✅ Działa
EPUB	ebooklib	✅ Działa
PDF	WeasyPrint (Docker)	✅ Działa
HTML Parsing	BeautifulSoup4 + lxml	✅ Działa
Auth + DB	Supabase (PostgreSQL)	✅ Działa
Storage	Supabase Storage + storage3==0.8.1	✅ Działa
Deployment	Docker (Railway) + Vercel	✅ Działa
DNS	OVH	✅ Działa
SSL	Let's Encrypt (auto)	✅ Działa
📁 Struktura Projektu
text
TIOLIBRI/
├── docs/
│   ├── sessions/
│   │   ├── 2026-01-24-sesje-3-4-5.md
│   │   ├── 2026-01-24-sesja-6-mvp-complete.md
│   │   ├── 2026-01-25-sesja-7-typography-v1.1.md
│   │   ├── 2026-01-25-sesja-8-v1.3-content-features.md
│   │   ├── 2026-01-26-sesja-9-ui-redesign.md
│   │   ├── 2026-01-26-sesja-10-split-view-preview.md
│   │   ├── 2026-01-26-sesja-11-margins-deep-dive.md
│   │   └── 2026-01-26-sesja-12-paginated-preview-dividers.md
│   ├── CURRENT-STATE.md             # Ten plik
│   ├── DECISIONS.md
│   └── TIOLIBRI - BLUEPRINT.md
│
├── tiolibri-frontend/               # React frontend
│   ├── src/
│   │   ├── components/ui/           # Button, Input, Card, Modal, Badge
│   │   ├── features/
│   │   │   ├── auth/                # LoginPage, SignupPage, useAuth
│   │   │   ├── projects/            # Dashboard, ProjectCard, useProjects
│   │   │   └── editor/              # EditorPage, TipTap, GenerateBooks
│   │   │                            # TypographyControls, useTypography
│   │   │                            # BookPreview (v1.6 paginated)
│   │   │                            # ChapterList + DnD (v2.0.2)
│   │   │                            # extensions/Divider.js (v1.7)
│   │   ├── lib/                     # supabase.js, api.js, utils.js
│   │   │                            # presets.js (v1.5.3)
│   │   │                            # htmlConverter.js (v2.0.3)
│   │   └── App.jsx                  # Routing
│   └── package.json
│
└── tiolibri-api/                    # Python backend
    ├── app/
    │   ├── main.py                  # FastAPI app + load_dotenv()
    │   ├── storage.py               # Supabase Storage upload
    │   ├── routers/
    │   │   ├── projects.py          # Reorder endpoint (v2.0.2)
    │   │   └── generate.py          # POST /generate endpoint
    │   ├── services/
    │   │   ├── supabase_client.py   # Supabase Client
    │   │   ├── epub_generator.py    # ebooklib (v1.6.1 clean headings)
    │   │   └── pdf_generator.py     # WeasyPrint (v2.0.1 stable page breaks)
    │   ├── models/
    │   │   └── schemas.py           # Pydantic models (w/ sort_order)
    │   ├── utils/
    │   │   └── html_converter.py    # Google Docs converter (v2.0.3)
    │   ├── migrations/
    │   │   └── 002_add_sort_order.sql  # Database migration (v2.0.2)
    │   └── presets/                 # CSS files
    │       ├── classic.css          # margin: 0 (v1.5.2)
    │       ├── modern.css
    │       └── minimal.css
    ├── requirements.txt             # storage3, python-dotenv, etc.
    ├── run_dev.sh                   # macOS wrapper z DYLD_LIBRARY_PATH
    └── .env                         # SUPABASE_URL, SUPABASE_KEY
🛣 Routing
Frontend
Path	Komponent	Dostęp
/login	LoginPage	Publiczny
/signup	SignupPage	Publiczny
/dashboard	DashboardPage	Protected
/editor/:projectId	EditorPage	Protected
/	→ redirect /dashboard	-
Backend API
Method	Path	Opis	Status
GET	/	Hello World	✅
GET	/health	Health check	✅
GET	/projects/{project_id}	Pobierz projekt	✅
GET	/projects/{project_id}/chapters	Pobierz rozdziały	✅
POST	/generate	Generuj EPUB/PDF → Supabase Storage	✅
✅ Deploy Complete (v1.8)
Production Deployment (Sesja 13-14)
✅ Deploy frontend (Vercel)

✅ Deploy backend (Railway + Docker)

✅ HTTPS + SSL (auto przez Vercel/Railway)

✅ Environment variables w produkcji

✅ PDF generation w produkcji (WeasyPrint + system libs)

⏳ Co Jest TODO (Post-MVP)

Optional Polish (Pre-Deploy)
⏳ Export progress indicator (~15min)

⏳ Toast notifications (~15min)

⏳ Loading states (~15min)

⏳ Error handling messages (~20min)

Total: ~1h

Future Features (Post-Deploy)
⏳ Table of Contents generator (auto z H1/H2)

⏳ Chapter reordering (drag & drop)

⏳ Download history

⏳ Custom fonts upload

⏳ Footnotes/Endnotes

⏳ Block quotes styling

⏳ Drop caps

🐛 Known Limitations (Zaakceptowane)
⚠️ Preview vs PDF Width Mismatch (~10-15%)
Issue: Przy tych samych margin settings, tekst w PDF jest ~10-15% węższy niż w preview

Root cause: WeasyPrint rendering differences (font metrics, box model)

Tested: Nuclear reset CSS, font changes (Georgia), margin fixes - różnica pozostaje

Status: WeasyPrint limitation - zaakceptowane jako "representative preview" (nie pixel-perfect)

Impact: Preview pokazuje ~45-50 znaków/linia, PDF ~40-45 znaków/linia

Acceptable: Różnica jest przewidywalna i konsystentna

⚠️ Pagination Accuracy
Issue: ~400 words/page to estimate - prawdziwy page break zależy od font size, line height, margins

Solution: Disclaimer banner "Approximate page count - actual PDF layout may differ"

Status: Expected behavior - preview jest approximation, nie pixel-perfect

⏱ Czas Realizacji
MVP (Sesje 1-6): ~6h

Typography v1.1 (Sesja 7): ~2h

Content Features v1.3 (Sesja 8): ~1.5h

UI Redesign v1.4 (Sesja 9): ~2h

Split View v1.5 (Sesja 10): ~2h 20min

Margins Deep Dive v1.5 (Sesja 11): ~2h 10min

Paginated Preview + Dividers v1.6-v1.7.2 (Sesja 12): ~4h 30min

Production Deploy (Sesja 13): ~3h

Docker + Custom Domains (Sesje 14-15): ~8h

Page Breaks + Reordering + Google Docs (Sesja 16): ~3h

Total dev time: ~36.5h (from zero to v2.0 production) 🚀

🎯 Definition of Done - MVP
✅ User może się zarejestrować i zalogować

✅ User może utworzyć projekt

✅ User może uploadować rozdziały HTML

✅ User może edytować rozdziały (full WYSIWYG editor)

✅ User może kontrolować typografię (14 parametrów)

✅ User może wstawiać obrazki i dividers

✅ User może zobaczyć live paginated preview

✅ User może przeciągnąć rozdziały (drag & drop reordering) - v2.0.2

✅ User może uploadować Google Docs HTML (auto-preserve formatting) - v2.0.3

✅ User może wygenerować EPUB + PDF (stable page breaks) - v2.0.1

✅ User może pobrać wygenerowane pliki

✅ Aplikacja jest deployed (Vercel + Railway)

Progress: 11/11 = 🎉 100% v2.0 COMPLETE!

📊 Feature Completeness
Category	Features Implemented	Completion
Core Editing	Rich text, Auto-save, Focus Mode, Reordering	100%
Typography	14 controls, Live preview, Presets	100%
Media	Cover, Images, SVG Dividers	100%
Preview	Paginated, Responsive, Real-time	100%
Export	EPUB, PDF, Stable page breaks	100%
Import	Google Docs HTML converter (auto-format)	100%
UX Polish	Light theme, Shortcuts, Drag & drop	100%
Deployment	Vercel + Railway (Docker + PDF)	100%
Overall: 🎉 100% Complete - v2.0 PRODUCTION READY!

Ten plik jest źródłem prawdy o stanie projektu. Aktualizuj go po każdej sesji.

🚀 Production Status (v1.9)
Deploy Complete - All Systems Operational with Custom Domains

✅ Frontend Vercel – LIVE
  - Primary URL: https://app.tiolibri.com (custom domain)
  - Fallback: https://tiolibri.vercel.app
  - React 19 + Vite + Tailwind 4
  - Auto-deploy z git push
  - SSL: Let's Encrypt (auto)

✅ Backend Railway – LIVE (Docker + WeasyPrint)
  - Primary URL: https://api.tiolibri.com (custom domain)
  - Fallback: https://tiolibri-production.up.railway.app
  - Dockerfile: python:3.11-bookworm + system libs
  - System dependencies: Cairo, Pango, GObject, GdkPixbuf
  - Polish fonts: fonts-liberation, fonts-dejavu-core
  - Dynamic port binding: ${PORT:-8000}
  - SSL: Let's Encrypt (auto)

✅ Custom Domains (Sesja 15)
  - DNS Provider: OVH
  - Frontend: app.tiolibri.com → Vercel (CNAME)
  - Backend: api.tiolibri.com → Railway (CNAME)
  - SSL Certificates: Auto-generated (Let's Encrypt)
  - CORS: Updated for app.tiolibri.com
  - Status: LIVE w produkcji

✅ Integracja Supabase – LIVE
  - Production project (EU region)
  - Environment variables configured
  - RLS policies active
  - Storage buckets: uploads, assets, book-exports

✅ Eksport E-booków – WORKING
  - EPUB: ebooklib ✅
  - PDF: WeasyPrint + Polish fonts (ąęćłńóśźż) ✅
  - Public URLs: Supabase Storage ✅
  - Typography: All 14 parameters applied ✅
  - Images: Embedded in EPUB + PDF ✅
  - Cover: Embedded in EPUB + PDF ✅
  - Dividers: SVG preserved ✅

✅ UX Polish (Sesja 15)
  - Dynamic page titles (Login/Signup/Dashboard/Editor)
  - Browser tab shows context-aware titles
  - Editor shows project name in title

Progress: 10/10 = 🎉 100% MVP COMPLETE!

Docker Files (Sesja 14):
- tiolibri-api/Dockerfile - Production image with WeasyPrint
- tiolibri-api/.dockerignore - Optimize build context
- railway.toml - Railway build configuration

DNS Configuration (Sesja 15):
- CNAME: app.tiolibri.com → cname.vercel-dns.com
- CNAME: api.tiolibri.com → tiolibri-production.up.railway.app
- TTL: Auto (OVH default)
- Propagation: 5-30 minutes

Next Steps (Optional Polish):
- Export progress indicator (~15min)
- Toast notifications (~15min)
- Loading states (~15min)
- Error handling messages (~20min)
- Landing page na tiolibri.com (root domain)
Total optional polish: ~1h