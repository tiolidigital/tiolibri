# R4 — review speca PORZADEK-WERSJI

**Spec:** `docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md` v0.5.1  
**Stan wejściowy:** `spec: R4-codex-pending`, `impl: not-started`, `reset-po-spike: R3`  
**Data:** 2026-08-13

## Werdykt

**Werdykt:** REQUEST_CHANGES

Kanał S ma zapisany, realny dowód działania, ale nowy protokół nadal nie jest wykonywalnym kontraktem od początku do końca: §6.2 kasuje własne wyniki przy `ROLLBACK TO SAVEPOINT`, próba RLS nie tworzy deklarowanego udziału, a kanał H nie dowodzi sam siebie. Niżej są także niezależne braki UI, przypisania dowodów, pokrycia macierzy i ochrony danych. To nie jest zakres NITS/NITS-EXT.

Sprawdziłem **12/12 kategorii** checklisty: 11 kategorii merytorycznie, 1 jako N/A. **N/A:** bundling / mutation targets, bo spec nie definiuje pure-logic testów `it()`.

## Blokery — wszystkie znalezione w tej rundzie

### B1. `ROLLBACK TO SAVEPOINT fixture` kasuje także zebrane wyniki §6.2

W wywołaniu `[2]` savepoint powstaje przed krokami 2–7, a wyniki mają trafiać do temp table (`:1170-1174`). Kroki 4 i 6 wykonują `ROLLBACK TO SAVEPOINT fixture` (`:1185`, `:1187`). PostgreSQL cofa wtedy **wszystkie** zmiany po savepoincie, w tym inserty do `_wynik`; finalny `json_agg` nie może więc zachować kompletnego GREEN + mutacja #1 + reset + mutacja #2. Bramka S4 odrzuca tylko `NULL`/pustą listę, więc pojedynczy ocalały wynik może dać false-PASS zamiast wykazać brak wcześniejszych asercji.

Spec musi określić kształt, w którym rezultat każdej gałęzi zostaje zapisany **po** cofnięciu jej podtransakcji albo jest przenoszony poza zakres savepointu, oraz asertować dokładny zbiór kroków.

### B2. Mapa kanału §6.2 jest sprzeczna z własnym protokołem

Tabela przypisania mówi „krok 1 i 7 read-only, kroki 2-6 zapis” (`:958`), lecz krok 7 wykonuje `CREATE OR REPLACE FUNCTION` i `INSERT` (`:1188`), więc nie przejdzie przez `/read-only`. Pominięte są też kroki 8–10. Diagram czterech wywołań (`:1164-1178`) wkłada do `[2]` „kroki 2-6 (... mutacja #2)”, choć mutacja #2 jest krokiem 7, a nie mówi, w którym wywołaniu ma zostać wykonany krok 9. Implementator musi zgadywać granice transakcji i endpointy dla operacji na produkcyjnej funkcji.

### B3. R3 nie sprawdza użytkownika z udziałem

R3 deklaruje claims „użytkownika z udziałem” i oczekuje `UPDATE=0` (`:1076`), ale źródłem UUID ma być tylko „dowolny inny `user_id` odczytany z `projects`” (`:1100-1101`). To dowodzi zachowania obcego właściciela, nie użytkownika mającego wiersz `project_shares` do projektu testowego. Zapisane E P10 także mierzy właściciel 8 / arbitralny obcy 0, bez udziału.

Fixture musi w tej samej rolniętej transakcji utworzyć realny udział, potwierdzić widoczność projektu dla tej tożsamości i dopiero potem asertować `UPDATE=0`.

### B4. PHASE-0 nie testuje kanału H, mimo że go dostarcza

PHASE-0 tworzy `_proof/tozsamosci.py` dla H (`:671-673`), a §6.0 nazywa S i H dwoma programowymi kanałami (`:903`). Jednak „kanał dowodzi sam siebie” (`:991`) ma C1–C7 wyłącznie dla S, a tabela przypisania oznacza §6.0a jako S-only (`:953`). Nie ma kryterium uruchamiającego uvicorn, zakładającego i kasującego użytkownika, pobierającego top-level `hashed_token`, tworzącego/usuwającego udział ani weryfikującego użyteczny JWT. Pierwsze użycie H w 1A-api diagnozowałoby jednocześnie produkt i niesprawdzony bootstrap.

### B5. Trwałe zapisy kanału H nie mają gwarantowanego cleanupu na ścieżce błędu

§6.0 przyznaje, że H tworzy trwałe projekty/tożsamości/udziały (`:981-984`), a reguła wspólna wymaga `EXIT=1` także dla wyjątku transportu (`:968-973`). Cleanup jest opisany wyłącznie jako końcowy postflight (`:974-976`, `:1111`, `:1135`). Spec nie wymaga `finally`/równoważnego cleanupu po częściowym utworzeniu zasobów. Błąd HTTP między utworzeniem użytkownika a postflightem może więc zakończyć proces kodem 1 i zostawić śmieci w produkcji. Dla Risk HIGH implementacja nie może tego rozstrzygać domysłem.

### B6. Brakuje właścicielskiej kontrolki zmiany `role`, a `book` nie ma przypisanej edycji na karcie

Spec obiecuje ręczne nadanie `AKTUALNA` „jednym kliknięciem” (`:104-106`) i zapis `role`/`book` z karty/dashboardu (`:181-190`). Plan 1B-karta wymienia jednak tylko plakietkę roli i edycję notatki (`:585`, `:755-761`), a 1B-dashboard filtr/sort i `book` w modalu (`:586`, `:775-781`). Nigdzie nie ma selektora/przycisku zmiany lub zdjęcia roli ani jawnego właściciela edycji istniejącego `book`, choć §9.1 obejmuje inline edit `book` (`:1336-1344`). Cel produktu nie jest osiągalny z opisanego UI.

### B7. Podział 1B nie określa wiążącej kolejności ani nie liczy szwu integracyjnego

`normalizeProjectMeta` powstaje dopiero w PHASE-1B-dashboard (`:776-777`), ale PHASE-1B-karta ma używać go w `EditorPage` i przy zapisie karty (`:758`, kontrakt `:210-223`). Spec nie ustala kolejności tych równoległych nazwą faz ani nie przenosi helpera wcześniej. Ponadto obecny `DashboardPage` nie pobiera `updateProject` z hooka i nie przekazuje callbacku do `ProjectCard`; żadna rozpiska 1B nie nazywa tego szwu. Implementacja karty przed dashboardem nie ma helpera, a nawet po nim karta nie ma opisanej drogi zapisu. Trzeba ustalić kolejność/właściciela integracji i przeliczyć pliki/LOC.

### B8. Obowiązkowe kroki dowodu nie mają właściciela ani budżetu

Przypisanie globalne wymaga R1–R5 (`:955`), lecz `proof_1a_db.py` obejmuje tylko kroki 1–7, 10 i R1/R2/R3 (`:693-697`), a `proof_2a_db.py` tylko §6.2 (`:795-801`). R5 nie należy więc do żadnego artefaktu 1A, a R4 do żadnego artefaktu 2A. Podobnie `proof_1a_api.py` deklaruje kroki 8–9 (`:718-720`), pomijając 9a z odpowiedzią ownera (`:1109`). Nominalna tabela U9 jest zielona, ale pliki/LOC nie obejmują całego wymaganego zakresu, więc werdykt sizingu `:867-872` nie jest kompletny.

### B9. „Pełna tabela” duplikatu ma próbę tylko dla jednego z czterech wejść

Kontrakt §3.3 wylicza źródła `AKTUALNA`, `ROBOCZA`, `ARCHIWUM`, `NULL` i dla każdego wymaga `ROBOCZA` + wygenerowanej notatki + odziedziczonego `book` (`:305-325`). Krok 8 uruchamia wyłącznie źródło `AKTUALNA` (`:1107`). Implementacja może poprawnie obsłużyć tę jedną gałąź, a dla pozostałych kopiować rolę/notatkę i nadal przejść dowód.

### B10. Sześć archiwów nie daje deklarowanego pełnego pokrycia złego typu

Wiersz kontraktu obejmuje osobno `note` **i** `book` złego typu (`:566`). I5 sprawdza wyłącznie `book=123` (`:1126`), a tytuł §6.1b i proza twierdzą „pełne pokrycie” (`:1113-1118`). Jedno archiwum z dwoma błędnymi polami także nie wystarczy, bo walidator może zatrzymać się na pierwszym. Potrzebna jest niezależna kontrpróba złego typu `note` i ponowny sizing skryptu/artefaktu.

### B11. Klik-proof nie pokrywa większości wymagań faz UI

K1–K6 dotyczą niemal wyłącznie notatki i uprawnień, K7 tylko wariantu read-only snapshotów (`:1226-1234`). Brak obowiązkowych wyników dla:

- ustawienia/zdjęcia `role`, zmiany `book`, filtrów i sortowania oraz przekazania `book` z `NewProjectModal`;
- wymaganej nazwy ręcznego snapshotu, pin/unpin, nazwy zastępczej, `aria-pressed`, pełnego `aria-label` i zachowania fokusu z §9.3–9.4;
- warunkowej PHASE-3: grupowania, zwijania, `aria-expanded` i trwałości `localStorage`.

Same pliki `PROOF-1B-dashboard.md`, `PROOF-2B.md` i `PROOF-3.md` nie definiują, co ma przejść. Implementacja może pominąć te wymagania i uzyskać komplet zielonych K1–K7.

### B12. Protokół twardego DELETE ma niemożliwy warunek kompletności

Kolumna `wynik` ma zawierać datę usunięcia oraz liczbę kafelków **przed i po** (`:1287-1294`), więc nie da się jej wypełnić przed DELETE. Chwilę później spec mówi „Bez kompletnego wiersza projekt nie jest usuwany”, po czym „wypełnij wiersz, potem usuń, potem dopisz `wynik`” (`:1301-1302`). Przy operacji nieodwracalnej trzeba rozdzielić jawny stan `READY_TO_DELETE` (wszystkie pola możliwe przed akcją) od kompletnego rekordu po akcji. Obecne brzmienie jest jednocześnie niewykonalne i podatne na dowolną interpretację.

## Uwagi nieblokujące niezależnie od blokerów

1. Nagłówek twierdzi, że spec jest gotowy do `/spec-handoff` (`:11`), podczas gdy `STATE.md` ma `R4-codex-pending`; footer także nadal podaje `/spec-handoff` (`:1465`). Po tym werdykcie właściwym ruchem jest `/spec-apply-review porzadek-wersji`.
2. Sekcja „jedno zdanie” ma 772 znaki i dwa zdania (`:1452-1461`), przekraczając twardy limit 200 znaków z workflow §4.7.
3. §3.5 i §10 nadal nazywają §6 „owner-attested” (`:521`, `:1444`), choć §6 jawnie znosi ręcznie poświadczany kanał (`:890-892`). To stale wording, nie powód RC sam w sobie.
4. Surowy R4 E ma w P2 `EXPECT=200`, `GOT=HTTP 201`, `RESULT=PASS`; skrypt prawidłowo dopuszcza 200/201, ale etykieta `EXPECT` w artefakcie jest stara i myląca.

## Uruchomione bramki i dowody

| Kontrola | Wynik |
|---|---|
| `_review/.R4-probe-ksztalt.py` uruchomiony lokalnie | **EXIT=1** — DNS sandboxu nie rozwiązuje `api.supabase.com`; P1–P11 `FAIL` transportowe, brak zapisu do DB |
| `_review/.R4-probe-selftest.py` uruchomiony lokalnie | **EXIT=1** — ten sam błąd DNS, traceback przed zapytaniem |
| owner-attested raw `_review/.R4-probe-out.txt` | zaakceptowany wyłącznie przez wyjątek z promptu: `KROKOW=11 PASS=11 FAIL=0 EXIT=0`; obejmuje DO/diagnostics, pusty `json_agg`, `pg_policies`, hash funkcji/trigger i RLS owner/obcy |
| owner-attested raw `_review/.R4-selftest-out.txt` | `4/4 RESULT=PASS`, `BLEDOW=0`, `EXIT=0`; kontrpróba wykazuje false-PASS starej reguły i FAIL nowej dla `wynik=null` |
| U9 na realnym specu | **EXIT=0** |
| U9, mutant `PHASE-0 Pliki=9` przy limicie 8 | `SIZING-FAIL`, **EXIT=1** |
| FACT gate preflightu | `all=17 valid=17 blocked=0 invalid=0 corrected=1 malformed=0 extracted=1 migrated_missing=0`, **EXIT=0** |
| strukturalny gate C/M/E | `section=1 all=5 valid=5 invalid=0 fail=0 both=0 dup=0 none=0`, **EXIT=0** |
| 12 baz `wc -l` z §5 | **12/12 zgodne**: 259/153/125/431/258/158/40/99/766/450/106/75 |
| cytowane repo-root paths i kotwice `#L…` | wszystkie pliki istnieją, wszystkie początki zakresów mieszczą się w plikach |
| parse AST czterech probe'ów R3/R4 | **4/4 EXIT=0** |

Lokalne `EXIT=1` kanału S samo w sobie **nie jest RC**: zachodzi jawny wyjątek owner-attested dla sandboxu bez sieci/DB. Blokery B1–B3 wynikają z treści protokołu i zbioru faktycznie wykonanego, nie z braku DNS.

## Audyt C/M/E — merytoryczny, nieblokujący z reguły 1

`CME-MANIFEST.md` nie istnieje ani w tym repo, ani w kanonie FABRYKI (`rg --files … | rg 'CME-MANIFEST.md'` → **EXIT=1**). Zatem poniższe rozjazdy nie są samodzielną podstawą werdyktu; gate strukturalny mimo to przeszedł.

- `probe-ksztaltow-v05`: zapisane R4 E rzeczywiście ma P1–P11 i 11/11 PASS. Nie ma jednak surowego artefaktu pierwszego biegu z 6 FAIL/EXIT=1, choć rekord E go deklaruje; część R3 dopisana do tego samego E nie daje się odczytać z raw, bo `.R3-probe2-kanal.py` i `.R3-probe3-rls.py` tylko drukują obserwacje i nie mają akumulatora asercji ani `sys.exit` zależnego od wyniku.
- Ten sam rekord mówi, że kanał H jest „pokryty smoke-testem §6.0a”, lecz §6.0a jest jawnie S-only. To rozjazd C/M/E oraz niezależny bloker B4.
- `selftest-bramki-S4`: M i raw E są zgodne — 4 wiersze wykonane, 4 PASS, `EXIT=0`; zakres nie obejmuje kompletności wyników traconych przez savepoint w B1.
- `wc-l-sizing`: M i wykonany E są zgodne 12/12, ale dowodzą wyłącznie baz istniejących plików, nie kompletności scope'u. Brakujące kroki B8 pozostają poza estymatą.
- `protokol-dowodu-§6` twierdzi, że wykonalność każdego kształtu została zmierzona, podczas gdy P3 mierzy pojedynczy blok `DO`, nie wielogałęziowy kształt §6.2 z savepointem; to C szersze od E.
- R4 manifest nie ma osobnych rekordów dla cytowanych uruchomień: 31/31 `triggered_by=auto`, pomiaru 10 writerów w 4 plikach, 23 polityk oraz wcześniejszego kanału H z `md-export`. Te wartości można znaleźć w starszej prozie/preflightach, lecz nie są skonfrontowane w bieżącym M z niezależnie zachowanym raw E.

## Exhaustiveness checklist

- [✓ sprawdzone] **budżet ROZMIARU** — U9 real `EXIT=0`, mutant `EXIT=1`; nominalnie każda faza ma ≤8 plików, ≤500 LOC, ≤2 domeny, ≤1 migrację. Merytorycznie FAIL przez nieprzypisane kroki i szwy B4/B7/B8/B10/B11, więc sizing wymaga ponownego policzenia.
- [✓ sprawdzone] **spójność z masterem + brak stale references** — ścieżki i kotwice istnieją; FAIL przez B2 oraz stale status/footer/„owner-attested”.
- [✓ sprawdzone] **egzekwowalność** — FAIL: B1–B12 wymagają zgadywania albo dopuszczają false-PASS.
- [✓ sprawdzone] **poprawność logiki + edge/nullish** — FAIL: cofanie wyników savepointem, niepełne przypadki typu/roli i sprzeczny stan kompletności DELETE; zachowanie `json_agg(NULL)` zweryfikowane.
- [N/A — spec nie definiuje pure-logic testów `it()`, więc reguła 1 `it()` = 1 gałąź i mutation targets nie ma zastosowania.] **bundling / mutation targets**
- [✓ sprawdzone] **typy/sygnatury/argi/ścieżki** — 12 cytowanych plików i wszystkie linkowane początki zakresów istnieją; symbole istniejące znalezione, `normalizeProjectMeta` poprawnie jest dopiero planowany. FAIL na niewymienionych szwach B6–B8, nie na nieistniejącej kotwicy.
- [✓ sprawdzone] **bramki maszynowe uruchomione** — wyniki i EXIT w tabeli wyżej; lokalny kanał S `EXIT=1` z DNS objęty wyjątkiem, owner raw przyjęty. Statyczne bramki/kontrpróby wykonane, bez polegania na opisie flag.
- [✓ sprawdzone] **manifest pokrycia dowodu C/M/E** — struktura PASS, audyt adversarialny wykazał rozjazdy wyżej; zgodnie z regułą 1 nie są samodzielnym blokerem.
- [✓ sprawdzone] **SQL/RLS/migracja** — FAIL: B1–B3 i B8; zapisany preflight potwierdza tylko wykonalność części kształtów przed migracją.
- [✓ sprawdzone] **UI/a11y/tokeny** — FAIL: B6, B7, B11. Mapowanie do istniejących wariantów `Badge` i tekstowe etykiety są spójne, ale kontrolki i ich dowód nie są domknięte.
- [✓ sprawdzone] **ryzyko/dane (Risk HIGH)** — FAIL: B5 i B12. Transakcje S kończą się rollbackiem; kanał H i twarde DELETE nadal mają niedomknięte ścieżki awarii.
- [✓ sprawdzone] **docs/proza spójność** — FAIL: B2, deklaracje „pełne”, stale status/footer i limit jednego zdania.

## Proactive suggestions (rzeczy o które nie pytano)

- **Workflow:** Szablon dowodu z SAVEPOINT powinien wymuszać zapis wyniku po rollbacku podtransakcji; temp table podlega temu samemu cofnięciu co fixture.

---

## Dla Piotrka — jedno zdanie

R4 zatrzymuje spec: kanał działa w zapisanym dowodzie, ale protokół gubi wyniki, a kilka wymagań nadal nie ma wykonawczej ścieżki ani pełnej próby.

**Kopiuj dalej:**
```
/spec-apply-review porzadek-wersji
```
