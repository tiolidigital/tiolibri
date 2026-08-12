**Temat:** porządek w wersjach projektów — notatka/opis przy książce, etykieta „która jest aktualna",
grupowanie kafelków po książce, przypinane snapshoty zamiast kopii-na-wszelki-wypadek

Wątek 2026-08-11 był **ROZMOWĄ PROJEKTOWĄ, nie robotą**. Ten plik powstał 2026-08-12, bo poprzedni
wątek zapowiedział go i nie zapisał.

**Stan na 2026-08-12 wieczór: spec ZAŁOŻONY, kod nietknięty, baza nietknięta (poza odczytami).**
Właściciel wraca do tematu 13-14.08. Aktualny nośnik prawdy to już nie ten plik, tylko
`docs/specs/porzadek-wersji/` — ten handoff zostaje jako zapis „skąd to się wzięło".

> ⚠️ **Punkt wyjścia:** pamięć `project-kanoniczne-projekty-w-bazie` (ID kanonu i balastu).
> Ten handoff jej nie powtarza w całości — dokłada to, czego w niej nie ma: zakres zmian,
> pułapki w kodzie i decyzje otwarte.

---

## NASTĘPNY KROK

**`/spec-fill porzadek-wersji`** — Codex dociąga sekcje strukturalne, potem `/spec-handoff` i rundy
review (MAX_ROUNDS = 3). Nie zaczynać od implementacji: to dotyka migracji bazy.

Przed odpaleniem: przeczytaj `docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md` §4 (plan faz)
i §3 (decyzje) — właściciel miał to przejrzeć, a przerwał na innych tematach. Jeśli plan faz się
zgadza, `/spec-fill` idzie bez pytań.

<details>
<summary>✅ ZROBIONE 2026-08-12 — `/spec-draft porzadek-wersji` (bramka przeszła zgodnie z przewidywaniem)</summary>

Struktura full: `SPEC-PORZADEK-WERSJI-MASTER.md` + `README.md` + `STATE.md` + `_review/`.
Master **wypełniony treścią z tego handoffu**, nie zostawiony w TODO.

**Odpowiedzi na 5 pytań bramki** (użyte, potwierdzone):

| # | pytanie | odpowiedź |
|---|---|---|
| 1 | więcej niż 1 faza implementacji? | **TAK** — (A) metadane projektu, (B) snapshoty, (C) grupowanie |
| 2 | implementacja > 2h? | **TAK** |
| 3 | wymaga migracji DB? | **TAK** — 3 kolumny w `projects`, 2 w `project_snapshots`, zmiana triggera |
| 4 | nowa komenda/widok top-level? | **NIE** — istniejący dashboard i karta projektu |
| 5 | płatności / auth / RLS / mutacje danych usera / bezpieczeństwo / kanon komend / parser? | **TAK** — zmiana triggera `prune_project_snapshots` dotyka kasowania danych właściciela |

→ struktura: **full**, rygor: **HIGH**, MAX_ROUNDS = 3.

</details>

## Co wyszło z sondażu 2026-08-12 (ponad ten handoff — wpięte w master §3)

1. **Nie ma endpointu API do zapisu projektu.** `projects.py` ma tylko GET / duplicate / reorder /
   share / activity. Metadane pójdą **istniejącą** ścieżką `updateProject` przez supabase-js
   z przeglądarki pod RLS — mniej roboty, ale **jedyną twardą walidacją `note` i `role` jest CHECK
   w bazie**; front tylko wyświetla komunikat. To kontrakt, nie uwaga.
2. **`Project` w `schemas.py:75`** jest `response_model` dla `GET /projects/{id}` — bez dopisania
   trzech pól endpoint **utnie je po cichu** mimo poprawnej bazy. Wpięte w PHASE-1A.
3. **Stale-ref:** `Dashboard.jsx` **nie istnieje**, jest `DashboardPage.jsx` (153 LOC). Pamięć
   i stare notatki mówią „Dashboard" — nie szukaj tego pliku.
4. Zmierzone LOC pod sizing (12.08): `ProjectCard.jsx` 259, `DashboardPage.jsx` 153,
   `useProjects.js` 125, `projects.py` 431, `snapshots.py` 258, `ProjectSnapshots.jsx` 158,
   `useSnapshots.js` 40, `schemas.py` 99.

## Problem, który to rozwiązuje (słowami właściciela)

Piotrek robił kopie całych projektów „żeby móc się wrócić, jak coś zepsuję". Wyszło z tego
12 kafelków na dashboardzie, z których dwa są aktualne, a reszta to ślady po pracy. Tytuł
projektu jest jedynym nośnikiem informacji, jest krótki i ucięty na karcie (`truncate`),
więc „wersja 4" i „predaktor-" muszą się mieścić w tytule i tak ich nie widać.

Cytat, który wyznacza zakres: *„chciałbym, żeby przy każdym tytule było jakieś miejsce
na komentarze, na jakiś opis"* + *„mamy książkę Ewy, gdzie ja wklikuję się, tak jakbym
wchodził do folderu i tam mamy te różne kopie"*.

## Zakres — trzy kawałki

### (A) Metadane projektu — rdzeń, robić pierwsze

Trzy kolumny w `projects`:

- **`note TEXT`** (limit ~300 znaków) — wolny tekst właściciela, np. „kopia sprzed Redaktora,
  do porównania po imporcie". Na karcie **pod autorem**, dwie linie z przycięciem
  (`line-clamp-2`), całość w `title=` jako tooltip. Miejsce jest wolne — dziś stoi tam
  wyłącznie „Updated X" ([ProjectCard.jsx:227-239](tiolibri-frontend/src/features/projects/ProjectCard.jsx#L227-L239)).
  Edycja **inline z karty i z edytora**, bez modala.
- **`role TEXT`** — `AKTUALNA` / `ROBOCZA` / `ARCHIWUM`, rysowane jako kolorowa plakietka
  obok istniejącego `Badge` ze statusem. To ona daje **sortowanie i filtr**; wolnego tekstu
  nie posortujesz, a po roku „aktualna wersja" będzie wpisane w trzech notatkach naraz.
  ⚠️ **Nie nazywać tego „KANON"** — to żargon warsztatu, nie słownik właściciela (zgrzyt Z37).
- **`book TEXT`** — nazwa książki (np. `Kości Na Całe Życie`), wpisywana raz, z podpowiedziami
  z istniejących wartości. Nośnik grupowania z kawałka (C). Wypełnić **od razu przy (A)**,
  nawet jeśli (C) poczeka — inaczej druga migracja i drugie ręczne uzupełnianie.

**Twarda reguła: duplikat NIE dziedziczy `role` ani `note` dosłownie.** Kopia projektu
oznaczonego `AKTUALNA` musi wyjść jako `ROBOCZA` z notatką w rodzaju
„kopia z <data>, źródło: <tytuł>". Inaczej po miesiącu są dwie „aktualne" i wracamy do
punktu wyjścia. Miejsce: `POST /projects/{id}/duplicate` w `projects.py`.

### (B) Snapshoty — żeby zastąpiły kopie

Mechanizm **już istnieje i już działa w tle**: w bazie leży **30 snapshotów całych projektów**
(Ewa 4.0 — 9, Bożena 507b3ee4 — 10), robionych automatycznie co 6 h przy zapisie
([snapshots.py](tiolibri-api/app/routers/snapshots.py), panel „Snapshoty" w edytorze).
**Ani jeden nie jest ręczny** — właściciel robił kopie projektów nie wiedząc, że aplikacja
robi mu to samo w tle.

Dwie dziury, przez które to dziś nie zastępuje kopii:

1. **Snapshot nie ma nazwy** — `list_snapshots` zwraca tylko `triggered_by` i `created_at`
   ([snapshots.py:36-41](tiolibri-api/app/routers/snapshots.py#L36-L41)). Nie da się powiedzieć
   „ten jest sprzed Redaktora".
2. **Retencja jest ślepa** — trigger `prune_project_snapshots` trzyma 15 najnowszych
   po `created_at` i kasuje resztę, nie patrząc czy ręczny
   ([20260421_spec1.sql:61-79](tiolibri-frontend/docs/migrations/20260421_spec1.sql#L61-L79)).
   Ręczny snapshot „przed Redaktorem" **zniknie** po 15 automatach. Jako kopia bezpieczeństwa
   jest dziś **niewiarygodny** — i to jest właściwe uzasadnienie tej fazy.

Fix: **`label TEXT` + `pinned BOOLEAN`** na `project_snapshots`, a prune liczy limit 15
**tylko z nieprzypiętych**. Wtedy „kopia przed Redaktorem" to jeden klik, ma nazwę, żyje
wiecznie i **nie robi kafelka na dashboardzie**.

**Uczciwe ograniczenie do zapisania w specu:** snapshot przywraca **w to samo miejsce** —
nie zobaczysz dwóch wersji obok siebie. Podział ról: **kopia projektu = porównanie
„przed/po", snapshot = cofnięcie po wpadce.** Kopie nie znikają z narzędziownika, przestają
być domyślnym odruchem.

### (C) Grupowanie kafelków — zamiast folderów, faza druga

Potrzeba prawdziwa (12 kafelków wygląda jak 12 książek) i będzie rosła: docelowo kilka
autorek po kilka książek każda (pamięć `project-autorki-i-ksiazki`).

**Folder jako osobny byt odrzucony** — nowa tabela, nowa nawigacja (wejdź/wróć), przenoszenie
między folderami, pytanie „czyj folder" przy projektach udostępnionych, i od tego momentu
każda kolejna funkcja musi pytać „a w którym folderze". Płacisz za drzewo, którego głębokość
nigdy nie przekroczy 1.

Zamiast tego: dashboard **grupuje kafelki po polu `book`**, nagłówek grupy z liczbą wersji,
grupa zwijana, w stanie zwiniętym widać tylko `AKTUALNA` + „…i 4 starsze wersje ▸".
Stan zwinięcia w `localStorage`. Zero nowej encji, zero routingu, kafelek zostaje kafelkiem.

```
Ewa Stachowska · Kości Na Całe Życie                    5 wersji  ▾
  ┌────────────────────────┐
  │ Kości 4.0   [AKTUALNA] │
  │ by Ewa Stachowska      │
  │ notatka: po eksporcie  │
  └────────────────────────┘
  … i 4 starsze wersje  ▸

Bożena Muszyńska · Grzyby Lecznicze                     3 wersje  ▸
```

**Dlaczego druga faza:** po (A) + sprzątnięciu balastu zostaną 2-4 kafelki i grupowanie tego
samego dnia może się okazać niepotrzebne. Projekt gotowy, budowa po sprzątaniu — wtedy widać
na własnym dashboardzie, czy jeszcze boli. Samo grupowanie to ~2 h we froncie, bez migracji,
o ile `book` jest wypełnione z fazy (A).

## Pułapki w kodzie — muszą trafić do specu

- ⚠️ **Usunięcie projektu to twardy DELETE prosto z przeglądarki**
  ([useProjects.js:77-87](tiolibri-frontend/src/features/projects/useProjects.js#L77-L87)) —
  `supabase.from('projects').delete()`, bez endpointu w API. Kaskadą leci wszystko: rozdziały,
  historia wersji, snapshoty. **`projects` nie ma `deleted_at`** — rozdziały mają kosz,
  projekty nie. Nie ma „cofnij".
- **Bezpieczna ścieżka sprzątania:** kebab → **„Eksportuj backup (.tiolibri)"** (już istnieje,
  [ProjectCard.jsx:96-106](tiolibri-frontend/src/features/projects/ProjectCard.jsx#L96-L106))
  → plik na dysk/iCloud → dopiero `usuń`. Import odtwarza projekt 1:1.
- **Eksport do Redaktora czyta zawsze bieżącą `chapters.processed_html`** z `deleted_at IS NULL`,
  nigdy `chapter_versions` ([export_import.py:169-176](tiolibri-api/app/routers/export_import.py#L169-L176)).
  „Stara wersja rozdziału" w eksporcie jest niemożliwa — jedyne ryzyko to zły `project_id`,
  czyli dokładnie to, co naprawia (A).
- **Kolejność rejestracji routerów ma znaczenie** — `export_import` i `snapshots` przed
  `projects`, inaczej trasy parametryczne przesłaniają statyczne.

## Sprzątanie balastu — stan i rekomendacja

Zweryfikowane 2026-08-11 po treści (sha256 NFC z `md_exporter.chapter_to_markdown` vs
`input.md` z przebiegów Redaktora): **36/36 rozdziałów zgodnych** — do Fabryki poszły
najnowsze wersje, żadna stara kopia nie pasuje (Ewa: 4.0 → 12/12, każda starsza → 0/12).

- **Zostawić:** Ewa `d73dcc3b` („Kości Na Całe Życie 4.0"), Bożena `507b3ee4`
  („predaktor-…2.0") — oznaczyć `AKTUALNA`.
- **Do backupu i usunięcia:** `e8aead35` (kopia Bożeny, **bit w bit identyczna** z kanonem —
  bezużyteczna od razu), Ewa `6afd44b4` (1.0), `b0841702` (2.0), `17adb766` (3.0),
  `6ffe53f3` (3.0 import), `11c96cd4` (3.0 TADEUSZ), `06ed1af3` (3 rozdz.), `70e90efb` (test book).
- **Nie namawiać na zero kopii w apce** — jeśli Piotrek chce jedną żywą zapasową pod ręką,
  zostawić najświeższą, z rolą `ARCHIWUM` i notatką po co jest.

## Decyzje właściciela — rozstrzygnięte 2026-08-12

1. ✅ **Nazwy etykiet:** `AKTUALNA / ROBOCZA / ARCHIWUM` (wariant z handoffu, bez zmian).
2. ✅ **Kolejność:** (A) → sprzątanie balastu → **dopiero wtedy** decyzja o (C). Zgodnie
   z rekomendacją. W masterze PHASE-3 stoi jako **warunkowa** — nie wchodzi do implementacji
   bez jawnego „tak".
3. ✅ **(B) w TYM SAMYM specu**, ale jako osobne fazy (2A DB+trigger, 2B UI) — ryzyko triggera
   zostaje odizolowane we własnej fazie i własnej rundzie review.

**Wciąż otwarte:**

4. **Zmielone tytuły rozdziałów** (`'ROZDZIA1Osteoporoza…'`) — z poprzedniego handoffu,
   rekomendacja bez zmian: poprawić 12 + 24 ręcznie, nie zakładać specu.
   **Świadomie POZA zakresem tego specu** (master §6).

## Wskaźniki do kanonów

- **Spec (nośnik prawdy od 12.08):** `docs/specs/porzadek-wersji/` — MASTER + README + STATE
- Pamięć: `project-kanoniczne-projekty-w-bazie` (ID kanonu i balastu, metoda weryfikacji
  po treści), `project-autorki-i-ksiazki`, `project-md-roundtrip-redaktor`
- Poprzedni handoff (domknięty): `HANDOFF-eksport-md-redaktor.md`
- Zgrzyt **Z37** — żargon („kanon") w propozycji do zatwierdzenia; stąd `AKTUALNA` w (A)
- Kanon spec-workflow: `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`
- Odczyt bazy: klient z `tiolibri-api/.env` (**TIOLIBRI nie jest w koncie Supabase pod MCP**),
  `venv/bin/python`, `load_dotenv(".env")`

**Model docelowy: Opus.**
