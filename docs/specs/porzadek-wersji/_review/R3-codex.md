# R3 Codex review — `porzadek-wersji` v0.4.1

**Data:** 2026-08-13
**Zakres:** Stadium A, review przed implementacją, Risk HIGH, runda R3
**Źródło:** `SPEC-PORZADEK-WERSJI-MASTER.md` v0.4.1 (`master-draft`)

## Werdykt

**Werdykt:** REQUEST_CHANGES

Sprawdziłem 12/12 kategorii exhaustiveness: 11 jest oznaczonych jako sprawdzone, a jedna jako N/A —
`bundling / mutation targets`, ponieważ spec nie definiuje testów pure-logic w `it()`. To R3,
więc przy `N_EFF=3=MAX_ROUNDS` ten wynik prowadzi do eskalacji zgodnie z kanonem workflow.

Wersja 0.4.1 poprawnie naprawia cztery fakty preflightu, ale podział kanałów nie daje jeszcze
wykonalnego dowodu z realnym kodem wyjścia. Niezależnie od tego §6.2 ma niemożliwy postflight,
inwariant `pinned → label` można ominąć bezpośrednim INSERT-em, a proof RLS nie asertuje
`with_check`. Są to osobne podstawy RC, nie kolejne warstwy jednego zarzutu.

## Co wymaga zmiany

### 1. BLOCKER — kanał B produkuje ręczną deklarację wyniku, nie realny `EXIT`

Master najpierw wymaga owner-attested dowodów „z realnymi EXIT” (`:747-750`), ale dla SQL Editora
nakazuje wykonującemu ręcznie dopisać `RESULT=PASS|FAIL` i końcowe `EXIT=0|1`, po czym wprost mówi,
że kanał nie ma automatycznego kodu wyjścia (`:779-782`). Surowe wiersze wyniku mogą dowodzić
wartości `GOT`; ręcznie wpisane `RESULT` i `EXIT` nie dowodzą jednak, że wszystkie asercje zostały
policzone, ani nie są kodem wyjścia procesu. Błędne `GOT` może zostać podpisane `PASS`, a końcowa
linia nadal będzie wyglądała jak zielona bramka.

Wyjątek z promptu dopuszcza owner-attested plik tylko z **realnymi EXIT**. Brak kanonicznego
`CME-MANIFEST.md` zwalnia wyłącznie z blokowania za audyt C/M/E; nie znosi kontraktu bramki.
Kanał B musi więc dostać wykonywalną funkcję asercyjną, która sama daje wynik procesu, albo workflow
musi jawnie ratyfikować inną klasę dowodu. Wybór kanału/narzędzia jest decyzją procesu, więc nie
kwalifikuje się do self-fixu.

### 2. BLOCKER — §6.2 nie domyka cyklu życia fixture'u i mylnie opisuje izolację

Protokół ma trzy niezależne defekty (`:861-906`):

1. Projekt testowy powstaje wewnątrz transakcji (`:893-895`), a krok 7 robi pełny `ROLLBACK`.
   Krok 8 próbuje potem wykonać INSERT „na projekcie testowym poza transakcją” (`:905-906`), ale
   ten projekt już nie istnieje. Postflight jest niewykonalny dokładnie według speca.
2. Krok 1 zapisuje tylko `md5`, nie deklarację funkcji. Krok 5 nie może więc „przywrócić deklaracji
   z kroku 1” (`:899, :903`). `ROLLBACK TO SAVEPOINT fixture` sam cofa mutanta #1 i przywraca stan
   funkcji; obecny dodatkowy zapis jest jednocześnie niemożliwy i zbędny.
3. `ALTER TABLE ... DISABLE/ENABLE TRIGGER` bierze `SHARE ROW EXCLUSIVE`, który koliduje z lockiem
   zwykłego INSERT-u. Równoległy auto-snapshot nie „używa starej deklaracji” (`:861-865`), tylko
   może czekać aż ręczna sesja SQL Editor zakończy całą transakcję. To zmienia profil ryzyka z
   „niewidoczny mutant” na produkcyjną blokadę zapisów o czasie zależnym od operatora. Potwierdza to
   [kanon `ALTER TABLE` PostgreSQL](https://www.postgresql.org/docs/current/sql-altertable.html).

Arytmetyka samego triggera jest poprawna: model wykonany lokalnie dał GREEN `15/pin żyje`, mutant
DELETE `15/pin znika`, mutant keep-set `14/pin żyje`, `EXIT=0`. Fixture ma już wymagane kolumny
`snapshot` i `triggered_by`. Te poprawne warstwy nie naprawiają niemożliwego kroku 8 ani ryzyka locka.

### 3. BLOCKER — kanał A nadal wymaga zgadywania tożsamości i sposobu uruchomienia API

Kanał A przypisuje skryptowi operacje jako service-role, JWT właściciela, JWT udziałowca oraz HTTP
do API (`:774-777`, `:808-810`), lecz nie podaje:

- skąd skrypt ma uzyskać dwa JWT i jak zapewnić relację udziału dla R3;
- bazowego URL API ani komendy/warunku uruchomienia serwera;
- nazw i pełnych ścieżek wymaganych skryptów `.py`.

`SUPABASE_ANON_KEY` nie jest JWT użytkownika. W `.env` są `API_HOST`, `API_PORT`, URL Supabase
i klucze, ale nie ma poświadczeń/tożsamości właściciela i udziałowca. Implementator nie może z tego
jednoznacznie wykonać kroków 8-9, R2-R3 ani I1-I3. To jest luka egzekwowalności, nie brak lokalnego
dostępu Codexa do bazy.

### 4. BLOCKER — sizing pomija obowiązkowe artefakty wykonawcze i skutek read-only UI

§6.0 wymaga „jednego pliku `.py` na fazę” (`:784-799`), ale konkretne listy §5 zawierają wyłącznie
kod i pliki `PROOF-*.md`. Brakuje co najmniej skryptów dla PHASE-1A-db, PHASE-1A-api i PHASE-2A-api;
nie są policzone ani jako pliki, ani LOC (`:598-623`, `:696-701`). Wklejenie outputu do proofu nie
zastępuje źródła komendy uruchamianej z pełnej ścieżki.

Dodatkowo naprawa zachowania udziałowca z uwagi 8 wymaga przekazania istniejącego `isOwner`
z `EditorPage.jsx` do `ProjectSnapshots.jsx` albo innej, dziś nieopisanej architektury. Lista
PHASE-2B ma tylko `ProjectSnapshots.jsx`, `useSnapshots.js` i proof (`:703-718`). Po domknięciu
inwariantu DB, dowodów importu i protokołu §6 trzeba ponownie policzyć pliki/LOC/domeny/migracje.
U9 mierzy poprawnie zadeklarowaną tabelę, ale nie wykrywa pominiętych plików.

### 5. BLOCKER — DB nie egzekwuje deklarowanego inwariantu „przypięty ma nazwę”

§3.4.2 obiecuje bez wyjątków, że każdy `pinned=true` ma niepusty `label` (`:337-342`). Migracja
deklaruje jednak tylko CHECK samego labela: `label IS NULL OR (...)` (`:320-325`). Polityka INSERT
po zmianie wpuszcza właściciela bezpośrednio przez PostgREST (`:411-435`). Właściciel może więc
ominąć backend, podać wymagane `snapshot`/`triggered_by` i wstawić `pinned=true, label=NULL`.

Serwerowa nazwa zastępcza chroni POST/PATCH API, ale nie jest twardą bramką dla równoległego wejścia,
które master sam uznaje za realne. Spec musi albo przenieść implikację `pinned → label` do DB i jej
dowodu, albo osłabić deklarowany inwariant. To zmienia migrację i kryteria akceptacji, więc jest RC.

### 6. BLOCKER — proof RLS odczytuje `with_check`, ale go nie asertuje

R1 wybiera `qual, with_check`, lecz oczekiwanie sprawdza owner predicate wyłącznie w `qual`
(`:831-839`). Polityka z poprawnym `USING`, ale dowolnym/permisywnym `WITH CHECK`, przejdzie R1,
R2 i R3: oba przebiegi zmieniają tylko `note`, więc nie próbują zmienić właściciela. Bezpośredni
PostgREST writer mógłby nadal ustawić `user_id` na wartość poza kontraktem owner-only.

R1 musi asertować obie strony polityki, a R4 powinien równie policzalnie określić kardynalność,
`cmd`, role i `with_check` INSERT-u. Samo „INSERT owner-only” jest słabsze od tabeli kolumn, którą
zapytanie już pobiera.

### 7. BLOCKER — dowód importu nie pokrywa kontraktu importu

Kontrakt §3.6.1 rozstrzyga długość `book`, długość `note`, zły typ obu pól i ignorowanie `role`
(`:514-520`). I1-I3 sprawdzają tylko kompatybilność starego pliku, jedną poprawną kanonizację oraz
za długie `note` (`:845-851`). Implementacja może przepuszczać `book >120`, rzucać 500 dla typu
liczbowego albo importować `role`, a cały zadeklarowany proof nadal będzie zielony.

Nie ma dziury w samym podziale writerów: trzy ścieżki nowych metadanych z przeglądarki korzystają
ze wspólnego helpera, a import ma osobną walidację backendową. Dziura jest w dowodzie tej osobnej
ścieżki — brakujące gałęzie muszą dostać policzalne przypadki i brak projektu po błędzie.

### 8. BLOCKER — owner-only snapshot API zostawia udziałowcowi aktywne martwe kontrolki

Po D5 POST, PATCH i restore są owner-only, a GET pozostaje dostępny udziałowcowi (`:372-407`).
Master nie mówi jednak, że udziałowiec widzi listę read-only bez create/pin/unpin/restore. Aktualny
`EditorPage.jsx:656` montuje `ProjectSnapshots` bez istniejącego `isOwner`, a aktualny komponent
renderuje „Zapisz snapshot teraz” i „Przywróć” bezwarunkowo (`ProjectSnapshots.jsx:57-58, :96-155`).
PHASE-2B dodałby kolejne bezwarunkowe przyciski pin/unpin.

To nie jest tylko polish: spec świadomie odbiera udziałowcowi istniejący restore, więc pozostawienie
kontrolki daje przewidywalne 403/404 i ślepy zaułek. §9 oraz PHASE-2B muszą określić wariant read-only,
fokus i brak kontrolek mutujących dla udziału; sizing musi uwzględnić szew w `EditorPage.jsx`.

### 9. MINOR — absolutne twierdzenie o „trzech realnych writerach” jest stale

§3.2 mówi, że realne ścieżki zapisu do `projects` z przeglądarki są trzy (`:167-180`). Kod ma także
zapisy w `useCover.js`, `useTypography.js` oraz inne update'y w `EditorPage.jsx`. Dalszy kontrakt
poprawnie dotyczy trzech ścieżek **nowych pól** `note/role/book`, więc wystarczy zawęzić twierdzenie
do writerów tych metadanych; w obecnym brzmieniu audyt ścieżek jest fałszywy.

### 10. OBSERVATION — C/M/E nie da się adversarialnie odczytać z zachowanego E

Brak kanonicznego `CME-MANIFEST.md` potwierdzony (`find` bez trafień), więc zgodnie z instrukcją ta
uwaga sama nie blokuje werdyktu. Merytorycznie są jednak dwa rozjazdy:

- rekord `probe-db-2026-08-13` scala wiele wykonań R1-R3 w jeden `dowod`, zamiast jednego rekordu
  na artefakt;
- zachowano źródło `.R3-probe.py`, ale nie surowy output biegu. Wartości `31/31 auto`, `12 projektów`
  oraz PGRST205/PGRST202 są powtórzone w samym preflighcie, czyli w M, a nie odczytywalne niezależnie
  z E „tego samego dowodu”. Nie można więc adversarialnie potwierdzić kompletności 31/31 ani
  czterech RPC wyłącznie z zachowanych artefaktów.

Rekord `wc-l-sizing` przeszedł niezależną konfrontację C/M/E: wszystkie 12 baz ma dokładnie wartości
podane w §5. Brak raw E dla sond DB pozostaje uwagą procesu, nie podstawą tego RC.

## Co przechodzi głęboki atak

- `projects_book_canon` opisuje postać kanoniczną, a dwa indeksy częściowe domykają **at-most-one**
  dla `(user_id, lower(book))` oraz osobnego koszyka `book IS NULL`. Stan zero jest jawnie kupiony;
  spec nie obiecuje at-least-one.
- Helper §3.2 zachowuje semantykę partial patch i nie dopisuje nieobecnych kluczy. Import jest jawnie
  oddzielnym writerem i ma backendowy kontrakt kanonizacji; problemem jest tylko niepełny proof.
- Arytmetyka §6.2 jest zgodna z realną deklaracją triggera w
  `tiolibri-frontend/docs/migrations/20260421_spec1.sql:61-79`: GREEN 15, mutant #1 usuwa pin,
  mutant #2 zostawia 14 nieprzypiętych. Transakcyjny DDL cofa mutanty; nie rozwiązuje locka i kroku 8.
- Trzy named CHECK-i `projects`, oba indeksy, mapowanie istniejących wariantów `Badge`, tekstowe
  rozróżnienie stanów, `aria-pressed`, stabilne nazwy pin/unpin oraz guard Escape/blur są określone
  wystarczająco jednoznacznie.
- §7/§7.1 uczciwie nazywa twardy DELETE, nie udaje pełnej odwracalności `.tiolibri`, wymaga backupu,
  oględzin D4 i kompletnego rekordu przed każdym usunięciem. Nie znalazłem nowej dziury tej rundy.

## Uruchomione bramki i pomiary

- Health-check Stadium A: U1-U8, A1, A2 i contract statusów — każdy `EXIT=0`.
- U9 na realnym masterze — `EXIT=0`; mutant `PHASE-2A-db`, `Pliki 2→9` — `SIZING-FAIL`, `EXIT=1`.
  Parser odrzuca legalny wiersz ponad limitem i nie daje już vacuous PASS na tym layoucie.
- `wc -l` 12 baz z §5 — `EXIT=0`: `259, 153, 125, 431, 258, 158, 40, 99, 766, 450, 106, 75`;
  wszystkie wartości zgodne z masterem.
- Skan 22 kotwic Markdown — `total=22 bad=0`, `EXIT=0`; ścieżki i kluczowe symbole odczytane w kodzie.
- Sonda lokalnego kanału SQL: `command -v psql` → `EXIT=1`; import `supabase` obecny, `psycopg`,
  `psycopg2`, `asyncpg` nieobecne; skrypt sondy zakończył `EXIT=0`. Nazwy kluczy `.env` potwierdzają
  brak URL-a libpq, bez ujawniania wartości.
- Model arytmetyki fixture'u: GREEN `15/1`, mutant DELETE `15/0`, mutant keep-set `14/1` — `EXIT=0`.
- Bramki wymagające żywej DB/REST i obiektów tworzonych dopiero przez migracje nie zostały wykonane
  w sandboxie. Jest to wyjątek owner-attested wskazany w promptcie; brak lokalnego Dockera/DB nie jest
  podstawą werdyktu. RC wynika z niewykonalnego kontraktu przyszłych bramek, nie z ich lokalnego braku.

## Exhaustiveness checklist

- [✓ sprawdzone] **Budżet ROZMIARU (LOC/pliki/domeny/migracje):** formalna tabela i U9 PASS, ale
  merytoryczny FAIL przez pominięte skrypty `.py`, `EditorPage.jsx` i skutki nowych blockerów.
- [✓ sprawdzone] **Spójność z masterem + brak stale references:** lifecycle, Risk i R3 są zgodne;
  stale absolutne twierdzenie o trzech browser writerach opisano w uwadze 9.
- [✓ sprawdzone] **Egzekwowalność:** FAIL — ręczny `EXIT` kanału B, brak tożsamości/startu kanału A,
  niemożliwy postflight i niepełne przypadki importu.
- [✓ sprawdzone] **Poprawność logiki + edge/nullish:** arytmetyka triggera, `book IS NULL`, partial patch
  i PATCH snapshotu sprawdzone; FAIL dla lifecycle fixture'u i DB-owego `pinned=true,label=NULL`.
- [N/A — spec nie zawiera testów pure-logic w `it()`; oba cele mutacyjne SQL sprawdzono w logice,
  arytmetyce i izolacji transakcyjnej.] **Bundling / mutation targets (1 it()=1 gałąź?).**
- [✓ sprawdzone] **Typy/sygnatury/argi/ścieżki:** 22/22 kotwice istnieją; sygnatury endpointów,
  writerów, fixture NOT NULL, nazwy funkcji/triggera/polityk i warianty Badge potwierdzone.
- [✓ sprawdzone] **Bramki maszynowe uruchomione w sandboxie:** wszystkie wykonalne statyczne bramki,
  U9 z kontrpróbą, `wc`, kotwice, capability probe i model fixture'u mają jawne EXIT powyżej.
- [✓ sprawdzone] **Manifest pokrycia dowodu C/M/E:** wszystkie 5 rekordów przejrzane adversarialnie;
  `wc` zgodne, raw E sond DB niezachowane, wykonania scalone. Brak kanonu czyni to nieblokującym.
- [✓ sprawdzone] **SQL/RLS/migracja:** FAIL — brak implikacji `pinned→label`, niepełne `with_check`,
  syntetyczny EXIT, niewykonalny postflight i nieuwzględniony lock; CHECK-i/indeksy `projects` PASS.
- [✓ sprawdzone] **UI/a11y/tokeny:** tokeny/Badge, tekst stanów, focus i aria pinów PASS; FAIL dla
  nieokreślonego read-only snapshot UI udziałowca i martwych kontrolek owner-only.
- [✓ sprawdzone] **Ryzyko/dane:** FAIL — ręczna transakcja SQL może blokować snapshot INSERT-y;
  mutant jest rollbackowany, a protokół twardego DELETE w §7.1 jest wystarczająco ostrożny.
- [✓ sprawdzone] **Docs/proza spójność:** FAIL dla sprzeczności realny/ręczny EXIT, kroku 5/8,
  twierdzenia o równoległej sesji i liczby writerów; pozostałe kontrakty są spójne.

## Proactive suggestions (rzeczy o które nie pytano)

- **Workflow:** Szablon SQL Editor proof powinien kanonicznie rozdzielić surowy transcript, SQL-side assertion i prawdziwy kod wyjścia; dziś „owner-attested” miesza te trzy pojęcia.

---

## Dla Piotrka — jedno zdanie

R3 zatrzymało wdrożenie: dowód SQL i kilka twardych zabezpieczeń nadal mają luki, więc spec trafia do decyzji właściciela przed implementacją.

**Kopiuj dalej:**
```
/spec-apply-review porzadek-wersji
```
