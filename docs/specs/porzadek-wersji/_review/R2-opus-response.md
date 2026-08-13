# R2-opus-response — REQUEST_CHANGES przyjęte

**Data:** 2026-08-13
**Werdykt Codexa:** REQUEST_CHANGES (parser: 1 dopasowanie, format kanoniczny)
**Master:** 0.3.1 → **0.4**
**Budżet rund:** `N=2`, `reset-po-spike=0`, `rundy-rdzenia=0` → `N_EFF=2 < MAX_ROUNDS=3` (Risk HIGH)

## Bramki proceduralne

**STOP-and-SPIKE (Krok 4) — NIE dotyczy.** Rdzeń R2 nie jest rdzeniem R1. R1 pytał, czy inwariant
„jedna AKTUALNA" w ogóle istnieje; v0.3 dała dwa indeksy częściowe, a R2 **wprost je potwierdza**
(„Same dwa indeksy są poprawne dla kardynalności, którą naprawdę wyrażają") i atakuje warstwę
niżej: kanoniczność KLUCZA, na którym stoją. To jest wzorzec z LESSONS#21 pkt 5 — naprawa u źródła
przenosi atak warstwę niżej, R1 pyta „czy jest reguła", R2 pyta „czy klucz reguły jest szczelny".
Osiem z jedenastu uwag dotyczy ponadto powierzchni, która powstała **dopiero w v0.3** (import jako
czwarty writer, szew 2A→2B, RLS snapshotów, semantyka `PATCH`, przeplot Escape/blur) — czyli
materiału recenzowanego po raz pierwszy, nie wariantu, który już przegrał.

**Zakaz rundy potwierdzającej (Krok 4a) — NIE dotyczy.** Delta wobec `.base-R2.md` jest niezerowa
(przepisane §3.1, §3.2, §3.4.2a, §3.4.3, §3.4.3a, §3.6.1, §4, §5, §6, §7.1, §8, §9.1, §9.3).

**Świeżość Risk (Z3).** Stempel `**Risk:** HIGH (plan faz: 5)` → `(plan faz: 8)`. Sam Risk **bez
zmian: HIGH** — przesłanki są te same (migracja DB + trigger kasujący dane właściciela), zmieniła
się wyłącznie liczba przegródek. `MAX_ROUNDS = 3` bez zmian.

**Miernik wzrostu (Z18).** `plan-faz-bazowy` nie było zapisane w `STATE.md` (spec sprzed konwencji).
Bazy **nie ustawiam** — to decyzja właściciela. Fakt do zważenia: 5 → 8 faz, wzrost **wyłącznie
z cięcia**, nie z nowego zakresu produktowego (§4).

## Uwagi — decyzje

Klasyfikacja L-C: **[P]** produkt / **[A]** aparatura / **[D]** docs.

### 1. `book` — CHECK nie egzekwuje kanonizacji `[P]`

**Decyzja: ZAAKCEPTOWANE.** Uwaga jest trafna i nośna — to najpoważniejszy bloker tej rundy.
`book = btrim(book)` łapie wyłącznie brzegi, więc `'Kości  Życie'` (dwie spacje) przechodziło CHECK,
podczas gdy helper zapisałby `'Kości Życie'`. `lower(book)` widzi dwa różne klucze → **dwa wiersze
z `role='AKTUALNA'` na tę samą książkę**, czyli dokładnie stan, przed którym broni §3.1.2.

CHECK dostał nazwę `projects_book_canon` i wyrażenie opisujące postać kanoniczną wprost:
`^[^[:space:]]+( [^[:space:]]+)*$`. §6.1 dostał **krok 5 — kontrpróbę kolidującą** z wielokrotną
spacją wewnątrz wartości (LESSONS#13: `' Kości '` z v0.3 przeszłoby także przy słabszym CHECK-u,
więc niczego nie dowodziło).

Przyjmuję też — bez zmiany w specu — obserwację Codexa, że indeksy same nie gwarantują *istnienia*
jednej `AKTUALNA`, tylko **co najwyżej jednej**. §3.1.2 mówi to uczciwie od v0.3 (przejściowe zero
po awarii drugiego zapisu jest jawnie kupione).

**Świadoma asymetria:** `label` snapshotu zostaje na `btrim`. Nie jest kluczem, nie ma indeksu po
`lower()`, nie niesie inwariantu — podwójna spacja w nazwie to defekt wyświetlania, nie rozjazd
tożsamości. Zapisane w §3.1.1 jako decyzja, żeby nie czytało się jak przeoczenie.

### 2. `normalizeProjectMeta` — brak semantyki patcha i błędów `[P]`

**Decyzja: ZAAKCEPTOWANE w całości, cztery osobne rzeczy.**

- **Patch częściowy** — §3.2 mówi teraz wprost: normalizowane są wyłącznie klucze **obecne**
  w `patch`, helper nigdy nie dopisuje klucza. Bez tego zapis notatki z karty zerował `book`.
- **Nullish per pole** — tabela `undefined` / `null` / `''` / wartość dla trzech kolumn.
  `role = null` jest wprost potrzebne do kroku „zdejmij starą" z §3.1.2.
- **`note`: ODRZUCENIE, nie obcięcie.** Codex ma rację, że „przycięcie do 300" przeczyło §9.1
  (wartość zostaje w polu do poprawki) i obietnicy komunikatu przed round-tripem. Obcięcie
  zapisywałoby coś, czego właściciel nie napisał, i nie mówiło mu o tym.
- **Mapowanie po NAZWIE constraintu, nie po SQLSTATE.** Trzy CHECK-i dostały nazwy
  (`projects_note_len`, `projects_role_dict`, `projects_book_canon`), indeksy już je miały.
  Doszedł wiersz „nazwa spoza tabeli → komunikat surowy z bazy": pokazanie komunikatu o notatce
  przy naruszeniu cudzego constraintu jest gorsze niż przyznanie się do nieznanego błędu.

### 3. Import jako czwarty writer `[P]`

**Decyzja: ZAAKCEPTOWANE.** Trafienie w lukę, której nie widziałem: §3.2 opisuje trzy ścieżki
**z przeglądarki**, a import wchodzi service-role INSERT-em z pliku użytkownika i żadna z nich go
nie chroni. Nowa §3.6.1 — tabela pięciu wejść, `422` z komunikatem wskazującym pole, dowód na
trzech archiwach (stare bez pól / poprawne / `note` 5000 znaków).

Jedno rozstrzygnięcie ponad uwagę: dla wartości **nadmiarowo obielonych** import **kanonizuje**
zamiast odrzucać (`' Kości  Życie '` → `'Kości Życie'`). Odrzucanie cudzego archiwum za spację
byłoby nieproporcjonalne, a stan końcowy jest ten sam co ze ścieżki przeglądarki. `422` zostaje dla
tego, czego kanonizacja nie naprawia: długości i typu.

Kompatybilność wsteczna (stare archiwum bez pól → `NULL`, import przechodzi) jest zapisana jako
wymóg, nie jako efekt uboczny.

### 4. Autoryzacja — trzy luki `[P]`

**Decyzja: ZAAKCEPTOWANE, wszystkie trzy.**

1. **RLS `UPDATE` na `projects` bez DDL i bez asercji.** Racja: `supabase-schema.sql:130-135` to
   historyczny SQL, nie stan żywej bazy. PHASE-1A-db **przedeklarowuje politykę idempotentnie**
   i §6.1 asertuje ją na `pg_policies` **plus parą wykonania** owner PASS / udział 0 wierszy.
   Dopisałem rzecz, której Codex nie nazwał, a która przesądza o wartości tego kroku: RLS na
   `UPDATE` **nie rzuca wyjątku**, tylko nie widzi wiersza — więc asercja musi być na LICZBIE
   zmienionych wierszy. Test oczekujący komunikatu o odmowie byłby zielony także po skasowaniu
   polityki (LESSONS#21).
2. **INSERT na `project_snapshots` omija owner-only `POST`.** Potwierdzone w kodzie:
   `20260421_spec1.sql:240-242` daje INSERT każdemu z `user_has_project_access`. Nowa §3.4.3a
   zawęża politykę do właściciela w PHASE-2A-db. Koszt zerowy — **żadna ścieżka frontu nie wstawia
   dziś snapshotów bezpośrednio**, jedynym producentem jest `POST` przez API.
   Uzupełnienie z własnego sprawdzenia: `project_snapshots` **nie ma polityki `FOR UPDATE`**, więc
   `pinned`/`label` już dziś nie da się przestawić z przeglądarki. To jest stan pożądany i §6.1
   ma go potwierdzić pomiarem — **brak polityki jest tu kontraktem**, więc jego zniknięcie musi być
   wykrywalne.
3. **Restore poza tabelą endpointów.** Racja. Rozstrzygnięte jako **D5: restore staje się
   owner-only**. Uzasadnienie w §8: dziś udziałowiec nie może zmienić tytułu projektu (RLS), ale
   może cofnąć cały projekt do stanu sprzed sześciu godzin — niespójność już obecna w kodzie,
   którą ten spec odsłania. ⚠️ To **jedyna decyzja mastera, która zabiera istniejącą możliwość**,
   więc jest w §8 wyłożona z jawną ścieżką weta jedną linią.

**PHASE-1B/2B a udziałowiec:** dopisane do §3.2.1 — widzi wartości, **nie dostaje kontrolek
edycji**. Kontrolka, której kliknięcie zawsze kończy się odmową bazy, to ślepy zaułek (ta sama
zasada co §9.4). „RLS, nie UI" faktycznie nie określało zachowania produktu.

### 5. Szew PHASE-2A → PHASE-2B `[P]`

**Decyzja: ZAAKCEPTOWANE.** Potwierdzone w kodzie:
[useSnapshots.js:23-25](tiolibri-frontend/src/features/editor/useSnapshots.js#L23-L25) wysyła
`POST` **bez body**. Wymagane `label` w 2A dawało `422` na przycisku „Zapisz snapshot teraz" —
produkt zepsuty między dwoma commitami, każdy z własnym lifecycle.

Wybrany szew: **`label` zostaje opcjonalne po stronie serwera**, a brak nazwy uzupełnia nazwa
zastępcza (§3.4.2a). Wymagalność nazwy jest kontraktem **UI** i wchodzi z PHASE-2B. Odrzucone:
przenoszenie minimalnego klienta do 2A (rozmywa granicę domen db/api/ui, którą właśnie porządkuję
w §4) oraz endpoint przejściowy do usunięcia w 2B (dług zaplanowany z góry).

Ten sam mechanizm domyka uwagę 8 — jedno rozwiązanie, dwa problemy.

### 6. §6.2 — dowód mutacyjny niewykonalny i niebezpieczny `[A]`

**Decyzja: ZAAKCEPTOWANE, wszystkie cztery wady.** To była najgorsza rzecz w v0.3.1: protokół
kazał podmienić **globalną** funkcję na żywej bazie, a fixture'u „16 nieprzypiętych" przy aktywnym
`AFTER INSERT` **nie da się zbudować**.

Przepisane w całości: **jedna transakcja zakończona `ROLLBACK`**. To rozwiązuje oba problemy naraz
i nie jest sztuczką — w Postgresie DDL jest transakcyjny, więc mutant jest **niewidoczny dla
innych sesji** (równoległy auto-snapshot właściciela używa starej deklaracji), a `ROLLBACK` cofa
mutanta, fixture i skutki uboczne. Setup fixture'u przez `ALTER TABLE … DISABLE TRIGGER` wewnątrz
tej samej transakcji. Reset między mutacjami przez `SAVEPOINT`. Nazwa schema-qualified
(`public.prune_project_snapshots`).

Najważniejsze domknięcie — **drugi RED jest teraz policzalny**. Codex ma rację, że mutant keep-setu
nie kasuje przypiętego, więc asercja „przypięty żyje" go nie łapie. Fixture ustala jawne
`created_at` i czyni przypięty **najnowszym** wierszem: wtedy zajmuje slot keep-setu i nieprzypiętych
zostaje **14**, nie 15. Gdyby był najstarszy — mutant przeszedłby zielono. Zapisane w specu wraz
z tym „gdyby", bo to jest cała wartość tego kroku (LESSONS#13).

### 7. Owner-attested bez funkcji PASS/FAIL `[A]`

**Decyzja: ZAAKCEPTOWANE.** Uwaga celna: surowy klient zwraca `EXIT=1` dla **poprawnie odrzuconego**
`23514`, więc „wklej realne EXIT" dopuszczało dwa sprzeczne odczyty tego samego zapisu.

Nowa §6.0 — jeden kształt dowodu dla wszystkich faz: skrypt asercyjny (nie surowy klient, nie
`curl`), `RUN_ID` w każdej wartości testowej, jedna linia na krok w formacie
`STEP=… EXPECT=… GOT=… RESULT=PASS|FAIL`, reguła **`EXIT=0` wtedy i tylko wtedy, gdy wszystkie
kroki `PASS`**, oraz policzalny postflight (0 wierszy z `RUN_ID`, licznik = baseline).
§6.1 objęło nośne RLS z uwagi 4. §6.3 zapisuje **sekwencję i liczbę żądań**, nie listę słów.

To nadal jest jednorazowy dowód owner-attested — nie wprowadzam harnessu (LESSONS#7).

### 8. `PATCH` — przypięty bez nazwy, nullish body `[P]`

**Decyzja: ZAAKCEPTOWANE.** Rozstrzygnięte jako **D6: stabilna nazwa zastępcza**
(`<typ> <YYYY-MM-DD HH:MM>` z `triggered_by` i `created_at`, Europe/Warsaw, generowana w backendzie
jak data w §3.3) — nie odrzucenie żądania. Odrzucenie kosztowałoby właściciela drugi krok dokładnie
w chwili, w której ratuje sobie pracę. Nazwa nadana ręcznie **nigdy nie jest nadpisywana**.
§9.3 dostał wymóg, żeby UI używało tej samej nazwy **przed** kliknięciem — inaczej przycisk mówi
co innego niż wynik.

Semantyka ciała rozpisana w tabeli: `{}` → `200` bez zmian; `label:null` przy wierszu pozostającym
`pinned` → `422` (złamałoby inwariant); `label:null` + `pinned:false` → `200`; pusty string → `422`
(do kasowania służy jawny `null`).

### 9. Escape / blur — nierozstrzygnięta kolejność `[P]`

**Decyzja: ZAAKCEPTOWANE.** Realna kolizja: `Escape` przywraca fokus, co wywołuje `blur` na polu,
a `blur` zapisuje — czyli anulowanie zapisywało anulowaną wartość. Symetrycznie `Enter` + klik obok
= dwa zapisy.

§9.1 dostało kontrakt „jedna intencja = jeden zapis": flaga `intencja` (`null`/`zapis`/`anulowanie`),
`Escape` zamyka pole **przed** przeniesieniem fokusu, `blur` zapisuje wyłącznie przy `intencja === null`.
Klik-proof (§6.3, K2 i K3) przechodzi **oba przeploty** i zapisuje **liczbę żądań** — drugi zapis
jest w UI niewidoczny, więc dowód „wygląda dobrze" byłby bezwartościowy.

### 10. Sizing — przechodzi parser, ale nie jest wiarygodną prognozą `[A]`

**Decyzja: ZAAKCEPTOWANE, z konsekwencją większą niż uwaga.** Trzy zarzuty, wszystkie trafne:
PHASE-3 jako jedyna nie miała „Pliki konkretnie"; PHASE-1B stało na 89% osi czasu z odłożeniem
splitu do preflightu implementacji (co Codex słusznie nazywa nie-sizingiem przed review);
1A/2A nie liczyły scope'u dołożonego w tej rundzie.

Po doliczeniu RLS + asercji, walidacji importu, zawężenia INSERT-a i **transakcyjnego** dowodu
mutacyjnego: PHASE-1A ≈ 105 min, PHASE-2A ≈ 85 min przy limicie 90. Obie ponad próg ~80%
(LESSONS#17 — faza wchodząca w R1 przy suficie nie ma miejsca na przyjęcie blokerów review).

**Plan cięty po granicy domen: 5 faz → 8.** `1A-db`/`1A-api`, `1B-karta`/`1B-dashboard`,
`2A-db`/`2A-api`, `2B`, `3`. Każda ma jedną domenę, najwyżej jedną migrację i własny artefakt
dowodu. Najwyższe wykorzystanie osi czasu = **78%**. PHASE-3 ma listę plików. Budżet
`PROOF-2A-mutacja.md` podniesiony 100 → 220 LOC, bo dwa pełne biegi z surowym wyjściem i rewertem
to nie streszczenie protokołu — Codex miał rację, że tamta liczba z niczego nie wynikała.

Roboty nie przybyło. Przybyło uczciwych przegródek.

### 11. Twardy DELETE bez bramki operacyjnej `[P]`

**Decyzja: ZAAKCEPTOWANE.** Racja: „to nie faza" nie zmniejsza skutku, a `19c4a5fe` miało ochronę,
której dziewięć „rozstrzygniętych" pozycji nie miało — mimo że ryzyko tam nie jest mniejsze, tylko
rozstrzygnięte.

Nowa §7.1 — `SPRZATANIE-LOG.md`, wiersz na projekt wypełniany **przed** usunięciem: pełny UUID
skopiowany z paska adresu **otwartego** projektu (nie z kafelka), tytuł, nazwa i rozmiar archiwum,
`manifest_ok` = archiwum **otwarte** i `manifest.project_id` zgodny, jawna akceptacja utraty trzech
niebackupowanych klas, wynik z liczbą kafelków przed/po. Bez kompletnego wiersza projekt nie jest
usuwany.

`manifest_ok` jest tam z konkretnego powodu: pobranie może się nie udać po cichu (0-bajtowy plik),
a wtedy „backup" jest pusty, a DELETE trwały.

### 12. C/M/E — rekord MEASURED scala cztery artefakty `[A]`

**Decyzja: ZAAKCEPTOWANE jako uwaga do preflightu, nie do speca.** Codex ma rację i słusznie nie
podniósł tego do RC (kanoniczny `CME-MANIFEST.md` nie istnieje — „kanon przed egzekucją").
Preflight R3 rozbije pierwszy rekord na cztery, po jednym na `probe.py`, `probe2.py`, `probe3.py`,
`probe_r2.py`. Master bez zmian z tego tytułu.

### 13. Dwa stale opisy rundy `[D]`

**Decyzja: ZAAKCEPTOWANE.** Nagłówek mówił „4 fakty CORRECTED" wobec 26 faktów / **6 CORRECTED**
w preflighcie i STATE; footer nazywał plik „master v0.3". Oba poprawione, footer przepisany pod v0.4.

## Sweep przeprowadzony (LESSONS#3 pkt 1)

Zmiana przekroczyła 100 LOC i przenumerowała fazy, więc sweep po starych nazwach:

```
rg -n 'PHASE-1A\b|PHASE-1B\b|PHASE-2A\b' SPEC-PORZADEK-WERSJI-MASTER.md
```
→ pozostają wyłącznie wystąpienia w prozie historycznej („PHASE-1A ≈ 105 min", „wersja 0.3
planowała"), gdzie stara nazwa jest **cytatem stanu sprzed cięcia**, nie odsyłaczem. Wszystkie
odsyłacze normatywne wskazują nazwy z §4 (`-db`/`-api`/`-karta`/`-dashboard`).

```
rg -n 'v0\.3|plan faz: 5|4 fakty|btrim\(book\)' SPEC-PORZADEK-WERSJI-MASTER.md
```
→ `btrim(book)` występuje wyłącznie w akapicie tłumaczącym, **dlaczego** to za mało; reszta pusta.

## Audyt C/M/E tej rundy

Fakty nowe w tej rundzie i ich status: `project_snapshots` INSERT policy — **MEASURED**
(`20260421_spec1.sql:240-242`, odczytane); brak polityki `FOR UPDATE` na `project_snapshots` —
**MEASURED** (brak dopasowania w pliku migracji); `useSnapshots.createSnapshot` bez body —
**MEASURED** ([useSnapshots.js:23-25](tiolibri-frontend/src/features/editor/useSnapshots.js#L23-L25));
treść triggera `prune_project_snapshots` bez filtra `pinned` — **MEASURED**
(`20260421_spec1.sql:61-79`); transakcyjność DDL w Postgresie i zachowanie keep-setu przy mutacji #2
— **CONTRACTED** (wyprowadzenie z semantyki, do potwierdzenia wykonaniem w PHASE-2A-db).

## L-C — klasa uwag

**8×[P], 4×[A], 1×[D].** Uwagi klasy PRODUKT dominują (kanonizacja klucza, kontrakt helpera,
import, autoryzacja, szew faz, `PATCH`, przeplot Escape/blur, bramka przed DELETE) — runda R3
jest uzasadniona i nie jest rundą o rusztowanie poprzedniej rundy.

## Następny krok

`spec: R2-opus-pending` → `/spec-handoff porzadek-wersji` (TARGET=R3 wylicza sam handoff).
`N_EFF=2 < MAX_ROUNDS=3`, więc runda R3 mieści się w budżecie i jest ostatnią przed progiem
eskalacji.

---

## Dla Piotrka — jedno zdanie

Codex zatrzymał spec drugi raz i miał rację jedenaście razy na jedenaście — najgroźniejsze było to,
że dowód bezpieczeństwa triggera kazał podmienić funkcję **wspólną dla wszystkich projektów** na
żywej bazie; przepisałem go na jedną transakcję z rollbackiem, a przy okazji plan urósł z 5 do 8 faz,
bo po domknięciu zakresu dwie z nich przestały się mieścić w limicie czasu.

**Kopiuj dalej — w nowym wątku:**
```
/spec-handoff porzadek-wersji
```
