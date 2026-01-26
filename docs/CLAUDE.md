# TIOLIBRI - Context for AI Assistants

> **Cel tego pliku:** Wklej mnie na początku sesji w VS Code/Claude, żebym wiedział czym jest projekt i jak nad nim pracować.

---

## 🎯 Wizja Projektu

**TIOLIBRI** to aplikacja webowa do tworzenia profesjonalnych e-booków (EPUB + PDF) z plików HTML eksportowanych z Google Docs.

**Dla kogo:** Autorzy, wydawcy, copywriterzy którzy:
- Piszą w Google Docs (wygodne, kolaboracja)
- Potrzebują e-booka bez znajomości InDesign/Calibre
- Chcą kontrolę nad stylem (fonty, kolory, layout)

**MVP:** Upload HTML → wybierz preset stylu → pobierz EPUB + PDF

---

## 🛠 Stack Techniczny

| Warstwa | Technologia | Hosting |
|---------|-------------|---------|
| **Frontend** | React 19 + Vite + Tailwind 4 + React Router 7 | Vercel |
| **Auth + DB** | Supabase (PostgreSQL) | Supabase Cloud (EU) |
| **Storage** | Supabase Storage | Supabase Cloud (EU) |
| **Backend** | Python + FastAPI | Railway/Render (później) |
| **Generator EPUB** | ebooklib | — |
| **Generator PDF** | WeasyPrint | — |

**Kluczowe zależności:**
- `@supabase/supabase-js 2.91`
- `react-router-dom 7.13`
- `tailwindcss 4.1`

---

## 📁 Struktura Projektu

```
tiolibri-frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # Reusable: Button, Input, Card, Modal
│   │   └── layout/       # Sidebar, Header, PageWrapper
│   ├── features/         # Feature-based organization
│   │   ├── auth/         # Login, Signup, useAuth hook
│   │   ├── projects/     # Dashboard, ProjectList, CRUD
│   │   ├── editor/       # Upload, ChapterList, Metadata
│   │   ├── styles/       # StylePanel, presety
│   │   ├── preview/      # Live preview rozdziałów
│   │   └── generate/     # Wywołanie API, Download
│   ├── lib/
│   │   ├── supabase.js   # Supabase client (singleton)
│   │   ├── api.js        # Fetch wrappers dla Python API
│   │   └── utils.js      # Helpers (formatDate, slugify, etc.)
│   ├── App.jsx           # React Router setup
│   └── index.css         # Tailwind + global styles
└── docs/
    ├── sessions/         # Logi sesji (YYYY-MM-DD.md)
    ├── CURRENT-STATE.md  # Źródło prawdy o stanie projektu
    ├── DECISIONS.md      # Architecture Decision Log
    └── CLAUDE.md         # Ten plik
```

---

## 🎨 Konwencje Kodowania

### Nazewnictwo
- **Komponenty:** PascalCase (`ProjectCard.jsx`)
- **Hooki:** `use` prefix (`useProjects.js`, `useAuth.js`)
- **Utils:** camelCase (`formatDate`, `uploadToSupabase`)
- **Foldery:** lowercase (`projects/`, `editor/`)

### Struktura komponentu
```jsx
// 1. Importy (React, biblioteki, komponenty, hooki, utils)
import { useState } from 'react';
import { useProjects } from './useProjects';
import Button from '@/components/ui/Button';

// 2. Komponent
export default function ProjectCard({ project }) {
  // a) Hooki state
  const [isOpen, setIsOpen] = useState(false);

  // b) Custom hooki
  const { deleteProject } = useProjects();

  // c) Handlers
  const handleDelete = async () => {
    await deleteProject(project.id);
  };

  // d) JSX
  return (
    <div className="card">
      {/* ... */}
    </div>
  );
}
```

### Tailwind
- **Używaj:** utility-first, responsywne (`sm:`, `md:`, `lg:`)
- **Unikaj:** inline styles, custom CSS (chyba że konieczne)
- **Kolory:** trzymaj się palety (zdefiniowanej później w tailwind.config.js)

### Supabase
- **Zawsze:** sprawdzaj `error` po każdym query
- **RLS:** polegaj na Row Level Security (nie filtruj w JS)
- **Storage:** używaj `supabase.storage` z signed URLs dla prywatnych plików

---

## 🗄 Schema Bazy Danych (Supabase)

### Tabele
```sql
projects       # Projekty użytkowników
├── id (uuid)
├── user_id (uuid → auth.users)
├── title, author, language
├── status (draft | in_progress | completed)
├── style_preset (classic | modern | minimal | custom)
└── custom_styles (jsonb)

chapters       # Rozdziały w projekcie
├── id (uuid)
├── project_id (uuid → projects)
├── title, sort_order
├── source_file_path (link do HTML w Storage)
└── processed_html (cache)

assets         # Obrazki, dividery
├── id (uuid)
├── project_id (uuid → projects)
├── name, type (image | divider)
└── file_path (link do Storage)

generated_files  # Wygenerowane e-booki
├── id (uuid)
├── project_id (uuid → projects)
├── format (epub | pdf)
└── file_path (link do Storage)
```

### Storage Buckets
- `uploads/` - surowe HTML z Google Docs
- `assets/` - obrazki, dividery SVG
- `outputs/` - gotowe EPUB/PDF

**RLS:** Użytkownik widzi tylko swoje pliki (`user_id = auth.uid()`)

---

## ✅ Co Już Działa

*Aktualizowane przez: CURRENT-STATE.md (źródło prawdy)*

Na tę chwilę (2026-01-24):
- [x] Projekt frontend setup (React + Vite + Tailwind)
- [x] Struktura folderów
- [x] Podstawowe pliki konfiguracyjne (ESLint, Prettier)
- [ ] Supabase setup
- [ ] Auth flow
- [ ] Dashboard
- [ ] Editor
- [ ] Python API

---

## 🚫 Ważne Decyzje / NIE RÓB TEGO

### Odrzucone rozwiązania
*(będzie wypełniane przez DECISIONS.md)*

### Nie rób:
- ❌ Nie twórz własnego parsera HTML - użyj biblioteki
- ❌ Nie przechowuj całych plików HTML w bazie - tylko ścieżki do Storage
- ❌ Nie buduj edytora WYSIWYG - to nie Google Docs v2
- ❌ Nie łącz projektów różnych użytkowników (na razie)

---

## 🎯 Obecny Priorytet

*Aktualizowane przez: CURRENT-STATE.md*

[Sonnet uzupełni na końcu sesji]

---

## 💬 Jak Ze Mną Pracować

### Dobre prompty
```
✅ "Stwórz komponent Button w src/components/ui/ z wariantami: primary, secondary, ghost"
✅ "Zaimplementuj hook useProjects do CRUD projektów przez Supabase"
✅ "Dodaj walidację formularza logowania (email + min 6 znaków hasło)"
```

### Złe prompty
```
❌ "Zrób dashboard" (zbyt ogólne)
❌ "Napraw błąd" (jaki błąd? gdzie?)
```

### Na końcu sesji
Zawsze uruchom prompty:
1. **Session Log** - zapisz co zrobiliśmy
2. **CURRENT-STATE update** - zaktualizuj stan projektu
3. **Decision Check** - czy podjęliśmy ważną decyzję?

---

## 📚 Dodatkowe Zasoby

- **Blueprint:** TIOLIBRI-BLUEPRINT.md (pełna specyfikacja)
- **Supabase Docs:** https://supabase.com/docs
- **Tailwind Docs:** https://tailwindcss.com/docs

---

*Ostatnia aktualizacja: 2026-01-24*
*Wersja: MVP Setup*
*Kontakt z właścicielem: Wklej aktualizacje z sesji do docs/sessions/*
