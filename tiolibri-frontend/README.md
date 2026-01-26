# TIOLIBRI Frontend

Generator e-booków z plików HTML - aplikacja webowa.

## Wymagania

- Node.js 18+
- npm 9+

## Instalacja

```bash
# Przejdź do folderu projektu
cd tiolibri-frontend

# Instalacja zależności
npm install

# Konfiguracja środowiska
# Uzupełnij wartości w .env.local
```

## Zmienne środowiskowe

Plik `.env.local` powinien zawierać:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```

## Uruchomienie

```bash
# Development
npm run dev

# Build produkcyjny
npm run build

# Podgląd build'a
npm run preview

# Linting
npm run lint

# Formatowanie kodu
npm run format
```

## Struktura projektu

```
src/
├── components/
│   ├── ui/              # Bazowe komponenty (Button, Input, Card, Modal)
│   └── layout/          # Sidebar, Header, PageWrapper
├── features/
│   ├── auth/            # Logowanie, autoryzacja
│   ├── projects/        # Zarządzanie projektami
│   ├── editor/          # Edytor rozdziałów
│   ├── styles/          # Panel stylów e-booka
│   ├── preview/         # Podgląd e-booka
│   └── generate/        # Generowanie EPUB
├── lib/
│   ├── supabase.js      # Klient Supabase
│   ├── api.js           # API calls
│   └── utils.js         # Funkcje pomocnicze
├── App.jsx
├── main.jsx
└── index.css
```

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Supabase** - Backend (auth, database, storage)

## Dokumentacja

- [docs/CURRENT-STATE.md](docs/CURRENT-STATE.md) - Aktualny stan projektu
- [docs/DECISIONS.md](docs/DECISIONS.md) - Decyzje architektoniczne
- [docs/sessions/](docs/sessions/) - Logi sesji deweloperskich

## Licencja

Prywatny projekt.
