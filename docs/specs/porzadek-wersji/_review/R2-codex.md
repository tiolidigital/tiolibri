# R2 Codex review — PORZĄDEK WERSJI master v0.3.1

## Werdykt

**Werdykt:** REQUEST_CHANGES

R1 domknęło dużo powierzchni, ale v0.3.1 nadal nie jest bezpieczna do implementacji. Najważniejsze
problemy są nośne: DB nie egzekwuje zadeklarowanej kanonizacji `book`, kontrakt owner-only snapshotów
da się ominąć przez istniejące RLS, PHASE-2A psuje aktualnego klienta przed PHASE-2B, a protokół
mutacyjny triggera ma niewykonalny fixture, nieizolowaną mutację i niedookreślony drugi RED.

Sprawdziłem 12/12 kategorii checklisty. Jedyna pozycja N/A to bundling `1 it() = 1 gałąź`, ponieważ
repo świadomie nie ma harnessu; adekwatność dwóch mutacji owner-attested sprawdziłem osobno pod §6.

## Co wymaga zmiany

### 1. BLOCKER — twarda bramka `book` nie egzekwuje kontraktu, na którym stoją indeksy

§3.1.1:91-93 deklaruje zwijanie **ciągów** białych znaków do jednej spacji i mówi, że DB odrzuca
wartość nieskanonizowaną. CHECK z §3.1:72 sprawdza jednak tylko długość oraz `book = btrim(book)`.
Bezpośredni zapis `book='Kości  Życie'` przechodzi CHECK, choć helper zmieniłby go na
`'Kości Życie'`. Indeks na `lower(book)` traktuje te wartości jako dwa różne klucze i pozwala obu
wierszom mieć `role='AKTUALNA'`.

Same dwa indeksy są poprawne dla kardynalności, którą naprawdę wyrażają: pierwszy pilnuje
**co najwyżej jednej** `AKTUALNA` na `(user_id, lower(book))` dla non-NULL, drugi domyka kubełek
NULL; wyścig dwóch klientów kończy się jednym `23505`. Nie gwarantują istnienia jednej wartości,
a §3.1.2:129-133 uczciwie akceptuje przejściowe zero po awarii drugiego zapisu. Problemem jest
niekanoniczny klucz wejściowy i mylące skróty „jedna”, nie kolejność indeksów.

DB musi egzekwować ten sam kontrakt co helper albo kontrakt normalizacji musi zostać świadomie
zawężony. §6.1 musi mieć kontrpróbę z wewnętrznym wielokrotnym białym znakiem; obecne
`' Kości '` sprawdza wyłącznie `btrim` i nie łapie tej luki.

### 2. BLOCKER — `normalizeProjectMeta` nie ma domkniętej semantyki patcha ani błędów

Sygnatura z §3.2:160-175 zostawia implementatorowi kilka rozbieżnych wyborów:

- nie mówi, że normalizowane są wyłącznie klucze **obecne** w patchu; bez tego zapis `note` może
  niechcący wyzerować `book` lub `role`;
- nie definiuje `undefined`/`null`/pustego stringa dla `note`, `role` i `book`, choć `role=null` jest
  konieczne do kroku „zdejmij starą”, a wszystkie trzy kolumny są nullable;
- „przycięcie `note` do 300” oznacza cichą utratę końcówki i przeczy obietnicy komunikatu przed
  round-tripem oraz §9.1, gdzie odrzucona wartość ma zostać w polu; trzeba rozstrzygnąć
  **odrzucenie vs obcięcie**;
- samo SQLSTATE nie wystarcza. `23514` obejmuje trzy nowe CHECK-i i istniejące CHECK-i tabeli,
  a `23505` nie oznacza automatycznie jednego z dwóch indeksów `AKTUALNA`. Bez nazw constraintów/
  indeksów i mapowania po nazwie implementacja może pokazać komunikat o notatce dla złej roli albo
  komunikat o `AKTUALNA` dla innego unique violation.

Trzy ścieżki mają dostać jeden kontrakt zachowania per pole oraz jedno mapowanie po konkretnych
constraintach. Inaczej „jeden helper” centralizuje nieokreśloność, a nie regułę.

### 3. BLOCKER — import jest czwartym writerem nowych pól, którego helper frontu nie obejmuje

§3.6:347 każe dodać `note` i `book` do `new_project_row` w
`export_import.py:388-397`. Dane pochodzą z ZIP-a użytkownika, a nie z trzech ścieżek przeglądarki
z §3.2. Plik z `book=' Kości '`, podwójną spacją, złym typem albo `note` >300 trafi w service-role
insert bez normalizacji frontu; CHECK da wyjątek klienta Supabase zamiast zdefiniowanego wyniku
importu.

Spec musi określić walidację/kanonizację backendową, status i komunikat (np. 422) oraz dowód dla
starego/poprawnego i niepoprawnego archiwum. Asymetria `role` jest opisana dobrze: import go nie
niesie i nowy projekt startuje bez `AKTUALNA`.

### 4. BLOCKER — kontrakt autoryzacji nie jest prawdziwy na wszystkich realnych wejściach

Są trzy osobne luki, wszystkie w aktualnym zakresie SQL/backendu:

1. §3.2.1:206-210 opiera owner-only zapis `projects` na RLS UPDATE, lecz PHASE-1A nie deklaruje
   DDL/asercji polityki, a §6.1 nie czyta `pg_policies` ani nie wykonuje pary owner PASS / shared
   FAIL. Repozytoryjne `supabase-schema.sql:130-135` jest tylko historycznym SQL-em, nie dowodem
   stanu żywej bazy.
2. Obecna polityka `20260421_spec1.sql:240-242` pozwala każdemu użytkownikowi z udziałem robić
   bezpośredni INSERT do `project_snapshots`. Po dodaniu kolumn współdzielony użytkownik może ominąć
   owner-only `POST` i wstawić `label`/`pinned=true` przez PostgREST. Nowy helper backendu nie jest
   twardą bramką dla tego wejścia.
3. Tabela endpointów §3.4.3 pomija istniejący
   `POST /projects/{project_id}/snapshots/{snapshot_id}/restore`. Dziś route używa
   `_assert_project_access` (`snapshots.py:74-80`) i service-role aktualizuje także pola `projects`
   (`:97-107`), choć browserowy RLS UPDATE jest owner-only. Trzeba jawnie zdecydować, czy restore
   udziałowca zostaje legalny, staje się owner-only, czy ma węższą allowlistę — oraz wpisać to do
   tabeli i dowodu.

PHASE-1B/2B musi też powiedzieć, czy udziałowiec widzi kontrolki read-only, czy próbę zapisu i błąd.
Samo „RLS, nie UI” nie określa zachowania produktu, a w przypadku snapshot POST RLS obecnie wręcz
nie realizuje deklaracji.

### 5. BLOCKER — granica PHASE-2A → PHASE-2B zostawia zepsuty produkt po merge

PHASE-2A zmienia istniejący POST tak, że body z `label` jest obowiązkowe (§3.4.3:285,289-291).
Aktualny klient `useSnapshots.js:23-25` wysyła POST bez body, a formularz nazwy dochodzi dopiero
w PHASE-2B. Po samym merge 2A przycisk „Zapisz snapshot teraz” zawsze dostanie 422.

Każda faza ma osobny lifecycle i commit, więc potrzebny jest jawny kompatybilny stan po 2A:
przejściowo kompatybilny endpoint, przeniesienie minimalnego klienta do 2A albo inny ratyfikowany
szew. Tego nie wolno zostawić implementatorowi, bo wybór zmienia granice faz i kontrakt produktu.

### 6. BLOCKER — §6.2 nie może obecnie dowieść obu warunków triggera bez ryzyka dla danych

Protokół ma cztery niezależne wady:

- przy aktywnym row-level `AFTER INSERT` nie da się zbudować fixture'u „16 nieprzypiętych”: już
  szesnasty INSERT uruchomi retencję i zostawi 15. Brakuje legalnej procedury setupu;
- `CREATE OR REPLACE FUNCTION` zmienia funkcję używaną przez **wszystkie** projekty. Osobny projekt
  testowy izoluje wiersze fixture'u, ale nie izoluje równoległych INSERT-ów właściciela. Commitnięty
  mutant DELETE może skasować przypięty snapshot innego projektu;
- pierwsza mutacja celowo kasuje jedyny przypięty fixture, po czym krok 7 każe powtórzyć kontrolę
  „przypięty żyje” bez jego odtworzenia;
- drugi bieg jest tylko „analogiczny”. Usunięcie `pinned=false` z keep-setu przy zachowanym
  `DELETE pinned=false` nie kasuje przypiętego; gdy przypięty jest dostatecznie nowy, zajmuje slot
  keep-setu i RED to **14**, nie 15 nieprzypiętych. Gdy jest za stary, mutant może przejść zielono.
  Potrzebne są dokładne timestampy/kolejność, reset fixture'u i policzalny oczekiwany RED.

Obie mutacje powinny być wykonane w izolowanej bazie albo w jednej transakcji kończącej się
rollbackiem, z semantyką oczekiwanych błędów/savepointów. Zapis i ponowny odczyt
`pg_get_functiondef` wraz z kontrolnym INSERT-em jest wystarczający do potwierdzenia przywrócenia
**treści i zachowania funkcji**; sam nie usuwa jednak niebezpiecznego okna globalnego mutanta.
Nazwa `public.prune_project_snapshots` powinna być rozstrzygana schema-qualified.

### 7. BLOCKER — owner-attested §6 nie ma jeszcze jednoznacznej funkcji PASS/FAIL

Brak runnera nie jest uwagą — wybór owner-attested jest zgodny z LESSONS#7. Problemem jest to, że
artefakt ma wkleić „realne EXIT”, ale protokół dopuszcza Python **albo** curl i nie mówi, jak wynik
oczekiwanie odrzucony ma przełożyć się na werdykt komendy. Surowy klient może zwrócić `EXIT=1` dla
poprawnie odrzuconego `23514`; skrypt asercyjny powinien wtedy zwrócić `EXIT=0`. Dziś oba zapisy
mogą wyglądać jak poprawny dowód.

Każdy krok musi mieć: dokładny fixture/run-id, komendę, asercję na odpowiedź/SQLSTATE i regułę
`EXIT=0 iff oczekiwanie spełnione`, plus policzalny postflight (zero pozostawionych wierszy lub
powrót do zapisanego baseline'u). §6.1 musi dodatkowo objąć nośne RLS z uwagi 4. §6.3 powinien
zapisać osobno sekwencję Escape→blur i wynik, a nie tylko listę słów „Escape, fokus”. To nadal jest
jednorazowy dowód owner-attested, nie wprowadzenie harnessu.

### 8. BLOCKER — PATCH pozwala stworzyć stan bez dostępnej nazwy i nie definiuje nullish body

Auto- i pre-restore snapshoty mają `label=NULL`, a §3.4.3 pozwala niezależnie ustawić
`pinned=true`. §9.3 buduje nazwę przycisku z `<label>`, więc legalnie przypięty auto-snapshot ma
`aria-label` z `null`/pustką. To przeczy dostępności i obietnicy „przypięty ma nazwę”.

Trzeba zdecydować, czy pinowanie bez label jest odrzucane, wymaga jednoczesnego label, czy używa
stabilnej nazwy zastępczej (np. typ + data). Body `{"label"?: str, "pinned"?: bool}` musi też
rozstrzygać: pusty obiekt, jawne `label:null`, pusty string i możliwość zdjęcia etykiety z
przypiętego ręcznego snapshotu. Obecny CHECK dopuszcza NULL i sam nie niesie tego inwariantu.

### 9. MAJOR — `Escape` i `blur=zapis` mają nierozstrzygniętą kolejność zdarzeń

§9.1 jednocześnie wymaga anulowania na Escape, powrotu fokusu oraz zapisu na blur. Przeniesienie
fokusu może wywołać blur po handlerze Escape i zapisać właśnie anulowaną wartość; analogicznie
Enter może wykonać zapis i drugi zapis na blur. Spec musi określić guard/supresję następnego bluru
i zasadę „jedna intencja = jeden zapis”, a klik-proof musi przejść oba przeploty.

### 10. MAJOR — sizing przechodzi parser, ale nie jest kompletną ani wiarygodną prognozą

Tabela zbiorcza naprawia ślepotę U9 i jej liczby są spójne z czterema rozpiskami. Nie dowodzi jednak
realności prognoz:

- PHASE-3 deklaruje 3 pliki/~180 LOC, ale jako jedyna nie ma sekcji „Pliki konkretnie”, więc nie da
  się odtworzyć ani sumy, ani domeny;
- PHASE-1B ma 80/90 min (89% limitu, nie deklarowane ~80%) dla pięciu plików kodu, trzech złożonych
  interakcji inline, filtrów/sortowania i klik-proof. Odkładanie splitu do preflightu implementacji
  nie jest sizingiem przed review;
- PHASE-1A/2A nie liczą zmian RLS, importu, auth restore ani bezpiecznego dwumutacyjnego proofu z
  uwag wyżej. Po domknięciu scope'u trzeba ponownie policzyć pliki/LOC/czas; szczególnie budżet
  `PROOF-2A-mutacja.md ~100 LOC` nie wynika z dwóch pełnych biegów z raw outputem i rewertem.

U9 poprawnie mówi wyłącznie „zadeklarowane liczby nie przekraczają zadeklarowanych limitów”. Nie
może zastąpić konkretnej listy plików i estymaty wynikającej z pełnego kontraktu.

### 11. MAJOR — ręczne twarde DELETE nie ma operacyjnej bramki przed nieodwracalną utratą

§3.5 uczciwie mówi, że `.tiolibri` nie niesie historii, snapshotów ani assetów, a §7 usuwa dziewięć
projektów na podstawie dowodu zakontraktowanego poza tym specem. Nazwanie §7 „nie fazą” nie zmniejsza
skutku: to właśnie ta lista prowadzi do nieodwracalnej czynności na danych właściciela.

Przed każdym DELETE potrzebny jest policzalny rekord: pełny project ID/tytuł, poprawnie pobrane i
otwieralne archiwum z pasującym `manifest.project_id`, jawna akceptacja utraty trzech niebackupowanych
klas oraz wynik usunięcia. `19c4a5fe` ma osobny STOP/oględziny i to jest poprawne; dziewięć
„rozstrzygniętych” pozycji nie ma równoważnej ochrony wykonawczej przed pomyleniem kafelka lub
nieudanym downloadem.

### 12. OBSERVATION — C/M/E jest treściowo zgodne, lecz rekord MEASURED scala artefakty

Odczytane E zgadza się z nośną prozą: 12 projektów = 2+9+1, 31 snapshotów z datą pomiaru, bazy LOC
12 plików oraz brak nowych kolumn. Twierdzenia o hashach i przyszłym §6 są poprawnie nazwane
CONTRACTED; nie znalazłem nośnego rozjazdu C↔E.

Pierwszy rekord MEASURED scala jednak cztery wykonania (`probe.py`, `probe2.py`, `probe3.py`,
`probe_r2.py`) w jeden `dowod`, co nie spełnia podanej reguły „rekord per artefakt wykonania”. Nie
podnoszę tego samodzielnie do RC, ponieważ kanoniczny `CME-MANIFEST.md` nie istnieje i obowiązuje
„kanon przed egzekucją”; aktualne blokery mają niezależne podstawy w kontrakcie i kodzie.

### 13. MINOR — master ma dwa stale opisy rundy

- nagłówek speca:8 mówi „4 fakty CORRECTED”, podczas gdy preflight i STATE mają 26 faktów,
  **6 CORRECTED**;
- footer speca:673 nadal nazywa plik „master v0.3”, choć review dotyczy v0.3.1.

To poprawki lokalne, ale przy REQUEST_CHANGES powinny wejść razem z naprawą treści.

## Uruchomione bramki i pomiary

- Health-check Stadium A: `U1`–`U8`, `A1`, `A2` oraz contract statusów — każdy `EXIT=0`.
- U9 na realnym masterze: `layoutB=0 haslim=1 rows=5 viol=0`, `EXIT=0`.
- U9 na realnym tekście z jedną mutacją `PHASE-2A Pliki 3→9`: `rows=5 viol=1`,
  `SIZING-FAIL`, `EXIT=1`. Bramka odrzuca zły wkład i nie jest już vacuous.
- `wc -l` dla wszystkich 12 baz z §5: `EXIT=0`; wartości 259, 153, 125, 431, 258, 158, 40,
  99, 766, 450, 106, 75 — zgodne ze specem/preflightem.
- Skan 22 kotwic Markdown `plik#Lx[-Ly]`: `total=22 bad=0`, `EXIT=0`; symbole w kluczowych
  kotwicach (`get_project`, helpery access, snapshot POST/restore, eksport/import, trigger) odczytane
  w kodzie. Kontrakt `Badge` 9 wariantów + 2 rozmiary: `EXIT=0`.
- Brak harnessu potwierdzony: brak `tiolibri-api/tests`, brak pytest w requirements, brak frontendowych
  zależności testowych i skryptu test — cztery kontrole `EXIT=0`; deklaracja pytest w
  `.claude/spec-config.json` istnieje (`EXIT=0`). Nie jest to uwaga do zakresu speca.
- Struktura preflightu: `facts=26`, `corrected=6`, `blocked=0`, `cme=5`, `EXIT=0`.
- Bramki wymagające żywej DB/REST nie były ponownie uruchamiane w sandboxie bez dostępu do bazy.
  Zgodnie z wyjątkiem przyjąłem owner-attested E z `R2-opus-preflight.md`; brak lokalnego przebiegu
  DB nie jest podstawą werdyktu.

## Exhaustiveness checklist

- [✓ sprawdzone] **Budżet rozmiaru:** U9 PASS i sumy czterech faz są spójne; FAIL merytoryczny dla
  braku listy plików PHASE-3 oraz prognoz przed domknięciem scope'u (uwaga 10).
- [✓ sprawdzone] **Spójność z masterem + stale references:** lifecycle/Risk/MAX_ROUNDS są zgodne;
  dwa stale opisy wersji/rundy w uwadze 13.
- [✓ sprawdzone] **Egzekwowalność:** FAIL — helper, auth, granica 2A/2B i owner-attested PASS/FAIL
  wymagają zgadywania (uwagi 2, 4, 5, 7).
- [✓ sprawdzone] **Poprawność logiki + edge/nullish:** FAIL — kanonizacja `book`, partial patch,
  import, trigger fixture, PATCH label oraz Escape/blur (uwagi 1-3, 6, 8-9). Sekwencja stare→nowe
  uczciwie zachowuje at-most-one i jawnie kupuje stan zero.
- [N/A — repo nie ma `it()` ani runnera; bundling testów automatycznych nie występuje, a dwa cele
  mutacyjne owner-attested oceniono w uwadze 6.] **Bundling / mutation targets.**
- [✓ sprawdzone] **Typy/sygnatury/argi/ścieżki:** 22/22 kotwice istnieją; liczby pól i sygnatury
  potwierdzone. Braki kontraktowe są w uwagach 2, 3 i 8, nie w istnieniu ścieżek.
- [✓ sprawdzone] **Bramki maszynowe uruchomione:** wyniki i EXIT powyżej; realny PASS oraz mutant
  FAIL U9 wykonane. DB objęte jawnym wyjątkiem owner-attested.
- [✓ sprawdzone] **Manifest pokrycia dowodu C/M/E:** pięć reguł przejrzane; brak kanonu nie blokuje,
  nośne C↔E zgodne, rule „rekord per artefakt” naruszona nieblokująco (uwaga 12).
- [✓ sprawdzone] **SQL/RLS/migracja:** FAIL — DB CHECK nie niesie kanonizacji, polityka snapshot INSERT
  omija owner-only, żywy RLS UPDATE nie ma dowodu, a mutant triggera nie jest izolowany.
- [✓ sprawdzone] **UI/a11y/tokeny:** mapowanie na istniejący Badge jest poprawne i tekst nie koduje
  stanu samym kolorem; FAIL dla shared controls, unlabeled pin oraz Escape/blur (uwagi 4, 8, 9).
- [✓ sprawdzone] **Ryzyko/dane:** FAIL — globalny mutant DDL i twarde DELETE bez pre-delete recordu
  są nieproporcjonalne do dostępnego rewertu (uwagi 6 i 11).
- [✓ sprawdzone] **Docs/proza spójność:** FAIL dla stale metadanych i twierdzeń silniejszych od
  rzeczywistych CHECK/RLS; pozostałe asymetrie backup/restore oraz ograniczenie retencji po unpin są
  opisane uczciwie.

## Proactive suggestions (rzeczy o które nie pytano)

- **Workflow:** U9 powinno twardo kończyć FAIL przy `rows=0`; obecny master omija vacuous PASS układem dokumentu, ale parser nadal akceptuje pusty pomiar.
- **Risk flag:** Wspólny szablon owner-attested DB proof powinien wymuszać transakcję rollback, run-id, asercję oraz `EXIT=0 iff PASS` bez dodawania runnera do feature.
- **Praise:** Jawne rozdzielenie backupu od restore i nazwanie przejściowego stanu „zero AKTUALNA” to dobre wzorce uczciwego opisu kupionego ryzyka.

---

## Dla Piotrka — jedno zdanie

R2 zatrzymało spec przed implementacją: trzeba domknąć normalizację, autoryzację snapshotów, bezpieczny dowód triggera i granice faz.

**Kopiuj dalej:**
```
/spec-apply-review porzadek-wersji
```
