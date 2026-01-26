# TIOLIBRI Frontend - Architecture Decisions

## Decision Log

### 001 - Framework Selection
**Date:** 2025-01-24
**Decision:** React 18 + Vite
**Rationale:**
- Fast development experience with Vite HMR
- React ecosystem maturity
- Easy integration with Supabase

---

### 002 - Styling Approach
**Date:** 2025-01-24
**Decision:** Tailwind CSS
**Rationale:**
- Utility-first approach speeds up development
- Consistent design system
- Small bundle size with purging
- Good documentation

---

### 003 - State Management
**Date:** TBD
**Decision:** TBD
**Options:**
- React Context (simple, built-in)
- Zustand (lightweight, minimal boilerplate)
- TanStack Query (for server state)

---

### 004 - Project Structure
**Date:** 2025-01-24
**Decision:** Feature-based folder structure
**Rationale:**
- Better scalability
- Co-located code (components, hooks, styles per feature)
- Easier to navigate as project grows

---

---

### 005 - WYSIWYG Editor for Chapter Quick Edits
**Date:** 2026-01-24
**Decision:** TipTap Core (MIT license)

**Kontekst:** Użytkownik potrzebuje możliwości szybkiej edycji literówek i drobnych poprawek w rozdziałach bez konieczności re-exportu z Google Docs.

**Alternatywy odrzucone:**
- Monaco Editor - za ciężki (~5MB), code-focused (dla programistów, nie autorów)
- Lexical - młodszy ekosystem, mniej tutoriali
- Quill - starszy API, mniej React-friendly
- Własny editor od zera - 2-3 tygodnie pracy, reinventing the wheel

**Dlaczego TipTap:**
- MIT license = FREE forever, komercyjne użycie OK
- WYSIWYG - użytkownik widzi finalny efekt
- React-native API (hooks, komponenty)
- Lightweight (~100KB dla MVP features)
- Extensible - dodajemy features stopniowo (bold/italic → images → tables)
- Używany przez Notion-like apps, GitBook, Linear

**Konsekwencje:**
- MVP: headings, bold, italic, lists (10 linii kodu setup)
- v1.1+: links, images (upload do Supabase Storage), tables
- Nie blokuje rozbudowy - extensions dodajemy on-demand
- Zero kosztów nawet przy 10,000 użytkowników

**Instalacja:**
```bash
npm install @tiptap/react @tiptap/starter-kit
```

---

## Pending Decisions

- [ ] State management library selection
- [ ] Form handling approach (React Hook Form vs Formik)
- [ ] E-book preview rendering strategy
- [ ] File upload approach (direct to Supabase vs through API)
