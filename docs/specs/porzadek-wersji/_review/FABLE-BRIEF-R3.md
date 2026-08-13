# Brief dla arbitra — spec `porzadek-wersji`, ESCALATED po R3 (STOP-and-SPIKE)

**Data:** 2026-08-13 · **Repo:** TIOLIBRI · **Stadium A** (master-draft, jeszcze bez podziału na fazy)
**Risk:** HIGH (plan faz: 8) → `MAX_ROUNDS = 3` · **Zużyte:** `N_EFF = 3` — budżet wyczerpany
**Kod i baza NIETKNIĘTE.** Przez trzy rundy powstały wyłącznie dokumenty.

---

## Cel speca (po co to w ogóle powstało)

Właściciel ma na dashboardzie 12 kafelków i **zgaduje, który z nich jest tą właściwą książką**.
Dwie autorki w produkcji (Bożena Muszyńska — grzyby, Ewa Stachowska — osteoporoza), kanoniczne
projekty to `d73dcc3b` i `507b3ee4`, reszta to stare wersje i kopie. Spec dokłada trzy metadane
(`note`, `role`, `book`), twardy inwariant „jedna AKTUALNA na książkę" w bazie, nazwane i przypinane
snapshoty (dziś ręczny snapshot znika po 15 automatach) oraz sprzątnięcie balastu.

---

## Który rdzeń padł i ile razy

**Rdzeń: wykonalny dowód §6 — bramka SQL/RLS przeciwko tej bazie, kończąca się PRAWDZIWYM kodem
wyjścia.** Pada **trzy rundy z rzędu**, za każdym razem o warstwę niżej:

| Runda | Zarzut Codexa | Odpowiedź speca |
|---|---|---|
| R1 #8 | test mutacyjny triggera nie ma uruchamialnego kontraktu dowodu | dopisany protokół §6 |
| R2 #6 | §6.2 nie może dowieść obu warunków **bez ryzyka dla danych** (podmiana funkcji WSPÓLNEJ na żywej bazie) | przepisane na jedną transakcję z `ROLLBACK` |
| R2 #7 | owner-attested §6 nie ma jednoznacznej funkcji PASS/FAIL | dopisany kontrakt `STEP=… RESULT=… EXIT=…` |
| R3 #1 | kanał B (SQL Editor) każe **człowiekowi ręcznie wpisać** `RESULT` i `EXIT` — to podpis, nie pomiar | — |
| R3 #2 | w przepisanym §6.2 krok 8 jest **niewykonalny** (fixture ginie z `ROLLBACK`), a `DISABLE TRIGGER` bierze `SHARE ROW EXCLUSIVE` → **blokuje zapisy na produkcji** na czas ręcznej sesji | — |
| R3 #3 | kanał A nie mówi, skąd wziąć JWT właściciela i udziałowca ani jak wystartować API | — |

Blokery nie maleją: **8, 8, 8** przez trzy rundy, przy specu rosnącym 678 → 1129 linii.
Convergence-ext nieprzyznane. Werdykty: 3 × REQUEST_CHANGES, przyjęte uwagi 9/9, 11/11, 10/10 —
Codex nie myli się co do faktów, każdy z nich zweryfikowany niezależnie w źródle.

---

## Twarde ograniczenie, o które to się rozbija (zmierzone, nie domniemane)

Pomiar `_review/.R3-probe.py`, `EXIT=0`, z tej maszyny przeciwko produkcyjnej bazie Supabase:

- PostgREST → **`PGRST205`** na `pg_policies` (katalog systemowy poza schema cache)
- PostgREST → **`PGRST202`** na cztery kandydatury funkcji SQL (brak RPC do surowego SQL-a)
- **brak `psql`** (`command -v psql` → EXIT 1)
- `tiolibri-api/venv` **bez `psycopg2` / `psycopg` / `asyncpg`** (jest tylko `supabase`)
- `.env` **bez URL-a połączenia libpq** (są `SUPABASE_URL`, klucze, `API_HOST`, `API_PORT`)

Czyli: **kanał, w którym spec obiecuje dowód, dziś nie istnieje.** Spec odpowiedział na to
„kanałem B" — człowiek wkleja SQL do Supabase SQL Editora i sam dopisuje `RESULT=PASS` i `EXIT=0`.
Codex odrzucił to jako niedowód i ma rację: błędne `GOT` można podpisać `PASS`, a bramka i tak
będzie wyglądała na zieloną.

---

## Pytanie do arbitra

**Czy wymóg „każda bramka §6 kończy się realnym kodem wyjścia" jest przy Risk HIGH wykonalny
w tym środowisku — a jeśli tak, jakim kanałem?**

Trzy wyjścia, o które proszę wprost:

1. **Rdzeń trzyma, recenzent się myli** — owner-attested transcript z SQL Editora JEST dowodem
   przy Risk HIGH, jeśli spełni warunek X (proszę nazwać X). Wtedy §6 dostaje szablon i jedziemy
   dalej rundą R4.
2. **Rdzeń pada, przeprojektuj** — wymóg jest słuszny, trzeba **zdobyć kanał**: spike na realnych
   danych, który zmierzy kandydatów (`psycopg2-binary` w venv + connection string z panelu Supabase
   / `supabase db execute` z CLI / `psql` z brew) oraz tożsamości (JWT właściciela i udziałowca,
   relacja udziału, start API). Dopiero potem §6 pisze się **raz**.
3. **Złe jest WYMAGANIE** — dowód mutacyjny triggera i asercje RLS to za duży rygor jak na to,
   co ten spec ma dać właścicielowi (przestać zgadywać, który kafelek to książka). Wtedy pytanie
   wraca do właściciela jako pytanie o ZAKRES, nie o technikę.

Skłaniam się do **2**, ale świadomie tego nie rozstrzygam: gdyby odpowiedź była oczywista,
runda R4 by wystarczyła.

---

## Ograniczenia, których nie wolno naruszyć

- **Trigger `trg_prune_project_snapshots` kasuje dane właściciela** — to nie jest test na pustej
  bazie. Dowód mutacyjny musi być odwracalny i nie może blokować zapisów produkcyjnych
  (uwaga R3 #2 mówi, że obecny wariant blokuje).
- **Baza jest produkcyjna i jedna.** Nie ma środowiska staging; nie ma Dockera z lokalnym Postgresem.
- **Właściciel nie programuje.** Wszystko, co „wykona operator ręcznie", jest realnym kosztem
  i realnym źródłem błędu — to jest dokładnie zarzut R3 #1.
- Kanał B nie jest wymyślony: `20260421_spec1.sql:3` mówi wprost, że migracje w tym repo stosuje
  się przez Supabase SQL Editor. To JEST sposób, w jaki ta baza jest dziś zmieniana.

---

## Materiały

- Spec: `docs/specs/porzadek-wersji/SPEC-PORZADEK-WERSJI-MASTER.md` v0.4.1 (§6 = protokół dowodu)
- Runda R3: `_review/R3-codex.md` (review), `_review/R3-opus-response.md` (decyzje 10/10 + zakres spike'u)
- Rundy wcześniejsze: `_review/R1-codex.md`, `R1-opus-response.md`, `R2-codex.md`, `R2-opus-response.md`
- Pomiar kanału: `_review/.R3-probe.py`, preflight `_review/R3-opus-preflight.md`
- Kanon workflow: `/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA/docs/specs/spec-workflow/`

---

Odpowiedz plikiem zaczynającym się od `# WERDYKT`, z sekcjami: Werdykt / Uzasadnienie /
Co zostaje owner-attested / Czego nie rozstrzygam / Dla Ciebie to znaczy.
Ostatnia sekcja jest OBOWIĄZKOWA i pisana po ludzku, do właściciela-nieprogramisty:
(1) czy coś jest zepsute TERAZ, (2) czy on ma cokolwiek zrobić, (3) JEDNA następna
czynność — z gotowym tekstem do wklejenia i adresem (ten wątek / nowy wątek + model).
