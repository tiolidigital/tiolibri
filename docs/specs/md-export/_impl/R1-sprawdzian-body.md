# R1 — sprawdzian odbiorczy wejść body (§Plan wdrożenia krok 2)

**Data:** 2026-08-07
**Backend:** żywy uvicorn `127.0.0.1:8000` (venv Python 3.9.6), nie `TestClient`
**Projekt:** `d73dcc3b-74ed-4d23-8cbb-d600c8f5306f` („Kości Na Całe Życie 4.0", 12 rozdziałów)
**Rozdział do wariantu (d):** `54929ca6-d18b-43a9-8052-808d29196e0f` (rozdz. 8, suplementacja)
**Token:** prawdziwy `access_token` Supabase właściciela projektu (`kontakt@przestudio.pl`),
wybity przez `admin/generate_link` → `auth/v1/verify` — `verify_supabase_jwt` waliduje go
u dostawcy, więc to jest pełna ścieżka autoryzacji, nie obejście.

## Tabela z kroku 2 — cztery obowiązkowe wiersze

| # | Żądanie | Oczekiwane | **Otrzymane** | Werdykt |
|---|---|---|---|---|
| a | `POST …/export-md` **bez `-d`** | 200, ZIP ze wszystkimi rozdziałami | **200**, `application/zip`, 95 047 B, 13 plików (12 × `.md` + manifest) | **PASS** |
| b | `-d '{"chapter_ids": null}'` | 200, jw. | **200**, `application/zip`, 95 046 B, 13 plików | **PASS** |
| c | `-d '{"chapter_ids": []}'` | 400 „wybrano zero rozdziałów" | **400**, `{"detail":"Wybrano zero rozdziałów"}` | **PASS** |
| d | `-d '{"chapter_ids": ["54929ca6-…"]}'` | 200, ZIP z jednym rozdziałem | **200**, `application/zip`, 14 594 B, 2 pliki (1 × `.md` + manifest) | **PASS** |

**Wariant (a) — ten, dla którego cały sprawdzian istnieje — wraca 200, nie 422.**
`Optional[ExportMdRequest] = None` w sygnaturze jest więc faktycznie egzekwowane na żywym
routerze, nie tylko widoczne w `inspect.signature`.

**(a) ≡ (b):** listy nazw plików w obu ZIP-ach **identyczne** (`diff` na `unzip -Z1` — zero różnic).
Różnica 1 bajta w rozmiarze pochodzi wyłącznie z pola `exported_at` w manifeście
(`…T16:19:38.783116+00:00` vs `…T16:19:39.774504+00:00`) i jej efektu na deflate. Obie drogi
do `None` zbiegają się w jedną gałąź — zgodnie z §Endpoint.

## Pozostałe wiersze tabeli §Endpoint (ponad wymagane cztery)

| # | Żądanie | Oczekiwane | **Otrzymane** | Werdykt |
|---|---|---|---|---|
| e | `chapter_ids: ["00000000-0000-4000-8000-000000000000"]` (poprawny UUID spoza projektu) | 404 z listą nierozpoznanych ID | **404**, `{"detail":"Nierozpoznane rozdziały: 00000000-0000-4000-8000-000000000000"}` | **PASS** |
| f | `chapter_ids: ["nie-uuid"]` | 422 (walidacja Pydantic) | **422**, `uuid_parsing` na `body.chapter_ids.0` | **PASS** |
| g | projekt bez rozdziałów → 400 | 400 „projekt nie ma rozdziałów" | **NIE WYKONANE** — patrz niżej | — |

**Dlaczego (g) nie wykonane:** żaden z 8 projektów właściciela nie ma zera nieusuniętych
rozdziałów (najmniejszy — „test book" — ma 1). Wykonanie tego wiersza wymagałoby **założenia
projektu-atrapy w produkcyjnej bazie**, a to jest zapis do produkcji poza zakresem sprawdzianu
odbiorczego, którego spec nie zamawia (tabela kroku 2 obejmuje wiersze a–d). Gałąź jest
w kodzie — `export_import.py:177-178`, `if not chapters: raise HTTPException(400, …)` —
i leży **przed** filtrem `chapter_ids`, więc nie ma jak jej ominąć. **Do decyzji Codexa/Piotrka,
czy chcą ją odpalić na atrapie.**

## Wynik

**6/6 wykonanych wierszy PASS**, w tym wszystkie cztery obowiązkowe (a–d).
Jeden wiersz (g) świadomie niewykonany, powód nazwany wyżej.
