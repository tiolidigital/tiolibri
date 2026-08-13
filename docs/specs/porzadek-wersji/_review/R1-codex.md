# R1 — review speca PORZADEK-WERSJI

**Spec:** `docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md` v0.2
**Zakres:** review przed implementacją, Stadium A, Risk HIGH, MAX_ROUNDS=3
**Data:** 2026-08-13

## Werdykt

**Werdykt:** REQUEST_CHANGES

Sprawdziłem **11/11 kategorii** checklisty. **10 kategorii sprawdzonych, 1 N/A:** bramki
maszynowe spec-time — master nie zawiera wykonywalnej komendy, regexu ani fixture; deklarowany
test mutacyjny jest kryterium impl-time, ale jego uruchamialność jest osobnym blokerem niżej.

To nie jest NITS/NITS-EXT. Poprawki wymagają decyzji produktowych i architektonicznych,
rozszerzenia scope kilku faz, nowego wykonywalnego dowodu DB oraz ponownego sizingu. Kontrakt
bezpiecznego triggera w §3.4 jest poprawny: spec wymaga jednocześnie keep-setu z
`pinned = false` i `DELETE` ograniczonego do `pinned = false`. §3.2 również nazywa CHECK w DB
jako jedyną twardą walidację `note`/`role`, nie jako luźną uwagę. Te dwie kontrpróby przechodzą;
blockery leżą warstwę dalej.

## Co wymaga zmiany

### 1. BLOCKER — `Sizing: PASS` nie mierzy pełnego scope i pomija cztery osie kanonu

§5 mówi o „3 osiach §4.5” i pokazuje tylko pliki, LOC oraz czas (`MASTER:151-164`), podczas gdy
§4.5 wymaga również domen, migracji i decyzji architektonicznych. Liczba przypadków testowych nie
jest tu argumentem — problemem są **pliki i LOC dowodów**, które w ogóle nie zostały wpisane do
sumy. Zdanie „testy liczą się do tej samej sumy” (`:169`) nie zastępuje ich enumeracji ani estymaty.

To już daje konkretne braki:

- PHASE-2A wymaga mutacyjnego dowodu triggera, lecz sizing liczy wyłącznie migrację i
  `snapshots.py`; repo nie ma istniejącego harnessu testów DB, więc dowód musi mieć własny
  artefakt lub owner-attested run i jego LOC/plik;
- PHASE-1A nie budżetuje dowodu, że bezpośredni zapis przez PostgREST odrzuca `note` >300 i
  `role` spoza allowlisty;
- PHASE-1B nie zawiera `EditorPage.jsx`, choć źródłowy HANDOFF wymaga edycji notatki także z
  edytora, ani żadnych plików/LOC testów UI;
- decyzje z findingów 5–7 mogą dołożyć `export_import.py`, `snapshots.py`, testy lub osobny
  artefakt SQL do faz, których obecna tabela nie obejmuje.

Po domknięciu scope trzeba podać dla każdej fazy pełne osie §4.5, konkretne pliki produkcyjne
i dowodowe z jedną sumą LOC oraz ponownie wyliczyć PASS. Warunkowy wiersz PHASE-3 może pozostać
warunkowy; sam jego wpis w obu tabelach nie jest błędem.

### 2. BLOCKER — master nie jest spójny ze źródłem i nadal ma stale references

W jednym pliku współistnieją trzy niespójności:

- plan faz mówi o usunięciu **8** projektów (`:141`), a poprawiona §7 enumeruje **10 z 12**
  (`:204-214`), z czego `19c4a5fe` wymaga osobnego „tak” właściciela;
- HANDOFF ustanawia edycję notatki „inline z karty i z edytora” (`HANDOFF:77-81`) oraz filtr po
  roli (`HANDOFF:82-84`), ale PHASE-1B ma tylko kartę/dashboard/hook/modal i tylko sortowanie
  (`MASTER:140,158-160`); nie ma ani przeniesienia tych wymagań, ani jawnego odrzucenia;
- footer nadal kieruje do `/spec-fill porzadek-wersji` (`:220-229`) i ma niekanoniczną etykietę
  `Kopiuj dalej — w tym samym wątku`. Dla Stadium A właściwym krokiem był `/spec-handoff`, który
  już wykonano; przy obecnym `STATE.md: spec: R1-codex-pending` następnym ruchem jest
  `/spec-apply-review porzadek-wersji`. Footer przekracza też limit jednego zdania/200 znaków.

Trzeba ujednolicić liczbę kasowanych projektów, rozstrzygnąć brakujący scope z HANDOFF-u i
odświeżyć footer do bieżącego stanu. Sama znana stara instrukcja w HANDOFF-ie może pozostać jako
geneza, bo `STATE.md` już oznacza ją jako stale; master nie może jej jednak powtarzać.

### 3. BLOCKER — `AKTUALNA` nie ma rozstrzygniętego inwariantu ani pełnej logiki duplikatu

Cel mówi, że właściciel ma jednoznacznie widzieć właściwą wersję, a §3.3 uzasadnia reset duplikatu
tym, że inaczej powstaną dwie „aktualne”. Mimo to schemat pozwala oznaczyć dowolną liczbę projektów
tej samej książki jako `AKTUALNA`; CHECK waliduje słownik, nie liczność. Spec nie mówi, czy
jednoznaczność ma być twardym inwariantem DB, transakcją „ustaw nową i zdejmij starą”, czy świadomie
tylko konwencją UI. To decyzja architektoniczno-produktowa, której nie wolno zostawić implementacji.

Także reguła duplikatu jest pełna tylko dla źródła `AKTUALNA`. Nagłówek mówi, że kopia nie
dziedziczy `role` ani `note`, lecz nie definiuje wyniku dla źródła `ROBOCZA`, `ARCHIWUM` i `NULL`.
Nie ma też formatu/strefy czasowej `<data>` ani kolejności sortowania `ROBOCZA`/`ARCHIWUM`/`NULL`.
Trzeba podać tabelę wejście → wynik oraz rozstrzygnąć inwariant jednej wersji aktualnej; dopiero
wtedy da się zaprojektować migrację, UI i dowód bez zgadywania.

### 4. BLOCKER — `book` jest martwym polem po decyzji „nie” dla PHASE-3 i nie jest bezpiecznym kluczem grupowania

Jedyny zdefiniowany konsument `book` to warunkowe grupowanie w PHASE-3. PHASE-1B mówi o polu z
podpowiedziami, lecz nie mówi, gdzie wartość jest stale widoczna ani jak daje korzyść bez grupowania.
Jeśli właściciel po sprzątaniu powie „nie”, zostaje kolumna, formularz i ręcznie wpisane dane bez
funkcji produktowej. Uzasadnienie „żeby nie robić drugiego ręcznego uzupełniania” (`:146-149`) nie
jest prawdziwym kosztem alternatywy: odłożenie nullable kolumny do PHASE-3 oznacza jedną późniejszą
migrację i jedno uzupełnianie, nie dwa uzupełniania.

Ponadto wolny `TEXT NULL` nie ma kontraktu normalizacji. `Kości`, `kości`, `Kości `, pusty string
i `NULL` mogą tworzyć różne grupy, a zapis idzie z przeglądarki z pominięciem Pydantic. Właściciel
musi wybrać: (a) odłożyć `book` wraz z PHASE-3, albo (b) nadać mu samodzielną, widoczną funkcję już
w 1B. Jeśli pozostaje kluczem grupowania, spec musi ustalić trim/case/empty/null i wskazać, która
warstwa egzekwuje kanoniczną wartość.

### 5. BLOCKER — deklarowana „jedna ścieżka zapisu” nie pokrywa realnego UI, a plan rozszerza istniejący IDOR service-role

§3.2 przypina zapis metadanych do `useProjects.updateProject`. Tymczasem edytor ma własne
`EditorPage.handleUpdateProject` z bezpośrednim `.from('projects').update(...)`
(`EditorPage.jsx:224-236`), a `book` dodawane w `NewProjectModal` przejdzie jeszcze ścieżką
`createProject`/INSERT. Jeżeli wymaganie z HANDOFF-u „karta i edytor” pozostaje, implementator ma
do wyboru co najmniej dwie ścieżki, choć master twierdzi co innego. Trzeba rozstrzygnąć wspólny
helper albo jawnie opisać wszystkie legalne write-pathy i ich identyczne zachowanie błędów CHECK.

Druga warstwa jest bezpieczeństwowa. `tiolibri-api/app/services/supabase_client.py:4-8,37-38`
używa service-role i omija RLS, a `GET /projects/{project_id}` w `projects.py:72-78` przyjmuje JWT,
lecz nie sprawdza właściciela ani udziału — `_user` jest nieużywany. Dopisanie `note`/`role`/`book`
do `Project` rozszerzy istniejący odczyt dowolnego znanego UUID o nowe dane właściciela. PHASE-1A
musi albo domknąć kontrolę dostępu przed rozszerzeniem response modelu, albo jawnie nie wystawiać
tych pól tym endpointem. Dodatkowo trzeba rozstrzygnąć, czy notatka właściciela jest widoczna dla
użytkowników współdzielonych; obecny RLS SELECT i endpoint shared zwracają cały wiersz.

### 6. BLOCKER — nowe metadane wypadają z backupu i restore snapshotu

Spec dodaje `note`/`role`/`book`, ale nie rozstrzyga ich udziału w dwóch istniejących mechanizmach
odzyskiwania:

- `.tiolibri` eksportuje ręcznie wybraną podlistę pól projektu w `export_import.py:87-97`, a import
  odtwarza inną podlistę w `:385-400`; nowych pól nie ma w żadnej;
- `_build_snapshot` wybiera własną podlistę pól w `snapshots.py:176-196`, a restore ma osobną
  allowlistę w `:97-107`; nowych pól również nie ma w żadnej.

Bez decyzji implementator nie wie, czy przywrócenie snapshotu ma cofnąć rolę/notatkę/książkę, a
backup po imporcie ma je zachować. To wpływa co najmniej na PHASE-1A, PHASE-2A i sizing. Jeśli
świadomą decyzją jest „metadane nie podlegają restore/backup”, master musi powiedzieć to wprost;
obecne określenia „snapshot całego projektu” i „backup” sugerują odwrotnie.

Jest też ryzyko sprzątania: `.tiolibri` zawiera bieżący projekt i aktywne rozdziały, ale nie
historię wersji, snapshoty ani pliki assetów. Twardy DELETE kasuje te dane kaskadowo. Ścieżkę
„eksport → usuń” trzeba opisać jako backup tego konkretnego podzbioru, nie pełną odwracalność,
i wymagać osobnego potwierdzenia dla `19c4a5fe`. „Przypięty żyje wiecznie” należy zawęzić do
retencji **dopóki istnieje projekt**.

### 7. BLOCKER — kontrakt `label`/`pinned` i endpointów nie realizuje obiecanego „jeden klik, ma nazwę, żyje”

`label TEXT` jest nullable i bez limitu/warunku niepustości, choć cel wymaga nazwy ręcznego
snapshotu. `pinned` ma DEFAULT `false`, więc nowo utworzony nazwany snapshot pozostaje podatny na
retencję, dopóki użytkownik osobno go nie przypnie. To nie realizuje miary sukcesu z `:45-47`
bez dodatkowej, nieopisanej decyzji (np. ręczny nazwany snapshot tworzony od razu jako pinned).

„Endpointy label/pin” (`:142`) nie definiują metod, body, walidacji, odpowiedzi ani autoryzacji.
Backend działa jako service-role, więc każdy endpoint musi sam sprawdzić zarówno `project_id`, jak
i `snapshot_id`; istniejący `_assert_project_access` pozwala także użytkownikom współdzielonym, a
spec mówi językiem właściciela. Trzeba ustalić owner-only vs shared, wymaganie nazwy, limit/trim,
stan `pinned` przy tworzeniu, idempotencję pin/unpin oraz zachowanie retencji po unpin (obecny
trigger odpala tylko po INSERT, więc nadmiar nieprzypiętych może żyć do następnego snapshotu).

### 8. BLOCKER — test mutacyjny triggera jest w dobrej fazie, ale nie ma uruchamialnego kontraktu dowodu

PHASE-2A jest właściwym miejscem czasowym: trigger dopiero wtedy powstaje, więc test jest
kryterium impl-time, nie bramką R1 speca (LESSONS#15). Samo zdanie „usuń warunek → test MUSI
sczerwienieć” nie wystarcza jednak do wykonania. Repo nie ma lokalnego harnessu Postgresa ani testów
DB; sizing PHASE-2A przewiduje tylko dwa pliki. Nie wiadomo, czy mutacja ma działać w transakcji,
tymczasowym schemacie czy na zdalnej funkcji, jak zbudować >15 nieprzypiętych + przypięty fixture,
jak zagwarantować rewert bajtowy/DDL i gdzie zapisać rzeczywiste EXIT-y.

Spec fazy musi dostać wykonywalny, bezpieczny protokół: pozytywna kontrola obu predykatów, mutacja
produkcyjnej deklaracji `DELETE`, oczekiwany RED po mutacji, przywrócenie DDL i postflight. Jeśli
sandbox recenzenta nie udźwignie DB/REST, legalny jest owner-attested plik z realnymi EXIT zgodnie
z wyjątkiem z promptu. Ten artefakt należy uwzględnić w sizingu. Analogiczny impl-time proof musi
pokazać, że CHECK w DB, a nie wyłącznie frontend, odrzuca nielegalne `note` i `role`.

### 9. MAJOR — UI nie ma minimalnego kontraktu a11y, błędów i tokenów

Master wymaga inline edit, nowych badge'y, nazwy snapshotu oraz pin/unpin, ale nie definiuje:

- save/cancel/Enter/Escape, focus return i zachowania przy utracie fokusu dla inline edit;
- dostępnej nazwy i stanu `aria-pressed` dla pin/unpin oraz klawiaturowej obsługi nowych kontrolek;
- komunikatu po odrzuceniu przez DB CHECK i zachowania optimistic/local state po błędzie;
- mapowania ról/pinned na istniejący `Badge`/tokeny ani reguły, że stan nie jest kodowany wyłącznie
  kolorem.

Repo ma `Badge.jsx` z gotowymi wariantami oraz tokeny w `src/index.css`; bez wskazania wariantu
implementator dobierze kolory i fokus ad hoc. Nie potrzeba nowego widoku, ale każda faza UI musi
dostać minimalny, testowalny kontrakt stanów i dostępności.

## Dowody uruchomione w review

- `wc -l` na 8 plikach z §5 — **EXIT=0**; wynik dokładnie 259/153/125/431/258/158/40/99,
  zgodny z preflightem.
- sprawdzenie istnienia wszystkich cytowanych ścieżek + kotwic — **EXIT=0**; symbole
  `updateProject`, `duplicate_project`, `list_snapshots`, `prune_project_snapshots`, eksport i
  kolejność routerów istnieją. Znaleziony dodatkowo `EditorPage.handleUpdateProject`.
- strukturalna obecność `## Audyt C/M/E` i rekordów PASS w preflighcie — **EXIT=0**.
- brak `CME-MANIFEST.md` w repo i kanonie FABRYKI — **EXIT=0** dla asercji braku.
- `find` na `FABRYKA-redaktor/redaktor/praca` — **EXIT=0**, E = 14 katalogów `ewa-*`, 24
  `boz-*`, 109 plików `input.md`; liczby katalogów z §7 są zgodne i nie dowodzą pokrycia rozdziałów.
- ponowny odczyt Supabase przez `tiolibri-api/venv/bin/python` — **EXIT=1**, sandbox nie rozwiązuje
  hosta (`httpcore.ConnectError: nodename nor servname provided`). Dla DB/REST stosuję więc legalny
  wyjątek owner-attested: `R1-opus-preflight.md:23-26,64`, gdzie trzy realne probe mają EXIT=0.

## Audyt C/M/E — wyjątek bez wpływu na werdykt

Zgodnie z jawną instrukcją brak kanonicznego `CME-MANIFEST.md` **nie jest blokerem werdyktu**.
Mimo to skonfrontowałem C z dostępnym E:

- C = 38 katalogów (`14 ewa + 24 boz`), E z ponownego `find` = dokładnie ten sam zbiór liczbowy;
  §7 poprawnie nie wyprowadza z niego `36/36` ani pełnego pokrycia rozdziałów;
- C = 12 projektów, 31 snapshotów i brak nowych kolumn, E owner-attested z probe DB zawiera te
  liczby i kształt tabel;
- C = „ani jeden snapshot nie jest ręczny” (`MASTER:28`) nie ma w zapisanym E rozkładu
  `triggered_by`, a C = „żaden rozdział Ewy 4.0 nie zgadza się hashem z 3.0” (`:24-25`) odsyła do
  zewnętrznej pamięci bez wykonanego zbioru w preflighcie. Rekord `find-praca` także nie dowodzi
  treści, tylko liczb katalogów/plików; treść jest oznaczona jako dowód CONTRACTED poza specem.

Te luki nie są policzone jako blocker ani powód RC z uwagi na nakazany wyjątek. W następnej wersji
warto usunąć/zakresować dwa zdania bez E albo dołączyć owner-attested E, ale verdict pozostaje RC
niezależnie z findingów 1–9.

## Exhaustiveness checklist

- [✓ sprawdzone] **Budżet ROZMIARU:** FAIL — tabela pomija domeny/migracje/decyzje oraz pliki i LOC
  dowodów; po domknięciu scope nie można utrzymać obecnego PASS bez ponownego pomiaru.
- [✓ sprawdzone] **Spójność z masterem + stale references:** FAIL — 8 vs 10 kasowanych projektów,
  utracony editor/filter z HANDOFF-u i stale `/spec-fill` w footerze.
- [✓ sprawdzone] **Egzekwowalność:** FAIL — nierozstrzygnięte write-pathy, endpointy snapshotów,
  restore/backup i inwariant `AKTUALNA` wymagają zgadywania.
- [✓ sprawdzone] **Poprawność logiki + edge/nullish:** FAIL — brak mapowania duplikatu dla trzech
  wartości/NULL, normalizacji `book`, kontraktu label/pin i zachowania po unpin.
- [✓ sprawdzone] **Typy/sygnatury/argi/ścieżki:** istniejące cytaty PASS; FAIL kompletności scope
  przez pominięte `EditorPage.jsx`, `export_import.py` i listy pól snapshot/restore.
- [N/A — master nie deklaruje wykonywalnej bramki spec-time] **Bramki maszynowe:** kontrakt
  mutacyjny jest impl-time i nie ma jeszcze komendy/fixture; próby diagnostyczne z EXIT podano wyżej.
- [✓ sprawdzone] **Manifest pokrycia dowodu — C/M/E:** wykonany z wyjątkiem braku kanonu;
  rozbieżności C/E zapisane wyżej i zgodnie z instrukcją nie wpływają na verdict.
- [✓ sprawdzone] **SQL/RLS/migracja:** safe-trigger wymaga obu predykatów i jest zapisany poprawnie;
  FAIL przez brak runnable proof, nierozstrzygniętą unikalność roli, service-role auth i zakres pól.
- [✓ sprawdzone] **UI/a11y/tokeny:** FAIL — brak kontraktu interakcji, focus/keyboard, błędów CHECK
  i mapowania na istniejące badge/tokeny.
- [✓ sprawdzone] **Ryzyko/dane:** FAIL — twarde kasowanie opiera się na niepełnym backupie,
  pinned nie przeżywa usunięcia projektu, a rozszerzenie response modelu powiększa IDOR.
- [✓ sprawdzone] **Docs/proza spójność:** FAIL — stale footer, 8/10, „cały projekt/żyje wiecznie”
  oraz niepełne przeniesienie ustaleń źródłowych.

## Proactive suggestions (rzeczy o które nie pytano)

Brak proactive suggestions.

---

## Dla Piotrka — jedno zdanie

R1 zatrzymał implementację: bezpieczny trigger jest opisany dobrze, ale scope, sizing, odzyskiwanie danych i uprawnienia wymagają domknięcia.

**Kopiuj dalej:**
```
/spec-apply-review porzadek-wersji
```
