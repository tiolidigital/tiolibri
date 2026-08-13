# R3-opus-response — REQUEST_CHANGES → STOP-and-SPIKE

**Data:** 2026-08-13
**Werdykt Codexa:** REQUEST_CHANGES (8 BLOCKER + 1 MINOR + 1 OBSERVATION)
**Master:** v0.4.1 — **NIE zbumpowany**, treść merytoryczna nietknięta (uzasadnienie w „Zmiany w specu")

---

## Bramki komendy

```
parser werdyktu:  1 linia `**Werdykt:** REQUEST_CHANGES`  → OK
budżet rund:      N=3 reset=0 rundy-rdzenia=0 → N_EFF=3, delta-runda=0, cap=3 (Risk HIGH)
prior convergence-ext: puste (nie przedłużano)
bramka 4a:        delta prozy wobec .base-R3.md = 0 (spec nietknięty od wysyłki R3)
proactive drain:  1 obserwacja (workflow=1, inne=0) → RETRO.md
gate cross-fazowy §4.8: N/A (Stadium A, 0 katalogów PHASE-*)
```

**STOP-and-SPIKE:** R3 — rdzeń: **wykonalny dowód §6 — bramka SQL/RLS z realnym kodem wyjścia
w kanale, który na tej maszynie istnieje**; pada 3× z rzędu (R1 #8, R2 #6/#7, R3 #1/#2/#3).

**L-C:** 3×[P], 6×[A], 1×[D]. Uwagi PRODUKT są obecne i uzasadniałyby rundę R4 — ale budżet
`N_EFF=3=MAX_ROUNDS` jest wyczerpany, a bramka STOP-and-SPIKE (Krok 5 pkt 4) wyprzedza pkt 5/6.

**Convergence-ext: NIE przyznane.** Warunek „blokery MALEJĄ" nie jest spełniony:
R1 = 8 BLOCKER, R2 = 8 BLOCKER, R3 = 8 BLOCKER. Spec urósł 678 → 1129 linii, liczba blokerów
stoi. To nie jest domykanie, to jest odbijanie się od tej samej ściany.

---

## Uwagi — decyzje

Wszystkie fakty mechaniczne Codexa **zweryfikowane niezależnie w źródle** (master + kod), tak jak
w R1 i R2. Potwierdzone **10/10**.

### 1. Kanał B produkuje ręczną deklarację wyniku, nie realny `EXIT` `[A]`

**Decyzja:** ZAAKCEPTOWANE — **wykonanie wstrzymane do spike'u.**

Zweryfikowane: §6.0 wymaga „`EXIT=0` wtedy i tylko wtedy, gdy wszystkie kroki mają `RESULT=PASS`"
(`:790-793`) i mówi wprost, że dla kanału B reguły „obowiązują tak samo, **ręcznie**" (`:783-784`).
Ręcznie wpisany `EXIT` nie jest kodem wyjścia procesu — to podpis pod wynikiem, nie pomiar.
Codex ma rację, że wyjątek owner-attested z promptu dopuszcza **realne** EXIT, a nie deklarowane.

To jest rdzeń STOP-and-SPIKE. Naprawa wymaga **ustalenia kanału, który istnieje**, a nie trzeciego
przepisania prozy §6 — patrz „Co ma rozstrzygnąć spike".

### 2. §6.2 nie domyka cyklu życia fixture'u i mylnie opisuje izolację `[A]`

**Decyzja:** ZAAKCEPTOWANE w całości — trzy niezależne defekty, wszystkie potwierdzone.

- **Krok 8 jest niewykonalny.** Master: „Wszystko dzieje się na **osobnym projekcie testowym**
  założonym **w tej samej transakcji**" (`:889`), krok 7 = `ROLLBACK` całej transakcji (`:904`),
  krok 8 = „kontrolny INSERT na projekcie testowym **poza transakcją**" (`:905`). Projekt już
  nie istnieje. Postflight jest niemożliwy dokładnie wg litery speca.
- **Krok 5 jest jednocześnie niemożliwy i zbędny.** Krok 1 zapisuje `md5(...)`, czyli hash —
  „przywrócenie deklaracji z kroku 1" (`:903`) nie ma z czego odtworzyć ciała funkcji.
  A `ROLLBACK TO SAVEPOINT fixture` i tak cofa mutanta #1, bo `SAVEPOINT` stoi przed krokami 2-6.
- **Opis izolacji jest nieprawdziwy dla `ALTER TABLE`.** Master argumentuje „DDL jest transakcyjny,
  więc równoległy auto-snapshot używa starej deklaracji" (`:861-865`). To jest prawda dla
  `CREATE OR REPLACE FUNCTION`, ale `ALTER TABLE … DISABLE/ENABLE TRIGGER` bierze
  `SHARE ROW EXCLUSIVE`, który **koliduje z `ROW EXCLUSIVE` zwykłego INSERT-u**. Równoległy
  auto-snapshot nie „użyje starej deklaracji" — **zaczeka**, aż transakcja się zakończy.
  W kanale B tę transakcję trzyma otwartą **człowiek wklejający do SQL Editora**. To zamienia
  „niewidoczny mutant" na **blokadę zapisów na produkcji o czasie zależnym od operatora**.
  Klasa [A] wg artefaktu, ale skutek jest w [ryzyko/dane] — i to jest najpoważniejsza pojedyncza
  rzecz w tej rundzie.

### 3. Kanał A wymaga zgadywania tożsamości i sposobu uruchomienia API `[A]`

**Decyzja:** ZAAKCEPTOWANE. §6 przypisuje skryptowi operacje jako service-role, JWT właściciela,
JWT udziałowca i HTTP do API, ale spec nie mówi, skąd wziąć oba JWT, jak zapewnić relację udziału,
pod jakim URL-em stoi API ani jak je wystartować. `SUPABASE_ANON_KEY` nie jest tokenem użytkownika.
Bez tego kroki 8-9, R2-R3 i I1-I3 są nieegzekwowalne — implementator musiałby zgadywać.

To luka **egzekwowalności speca**, nie brak dostępu Codexa do bazy. Wchodzi do zakresu spike'u:
kanał musi zostać zmierzony razem z tożsamościami, którymi się go używa.

### 4. Sizing pomija obowiązkowe artefakty wykonawcze i skutek read-only UI `[P]`

**Decyzja:** ZAAKCEPTOWANE. Zweryfikowane: §6.0 wymaga „jeden plik `.py` na fazę" (`:783`),
a listy §5 zawierają **wyłącznie** pliki kodu i `PROOF-*.md` — sprawdzone dla PHASE-1A-db
(`:600-604`), PHASE-1A-api (`:616-623`) i PHASE-2B (`:713-717`). W całym §5 nie ma **ani jednego**
skryptu dowodowego `.py`. Nie są policzone ani jako pliki, ani jako LOC.

Drugi człon też trafiony: naprawa uwagi 8 wymaga przekazania `isOwner` do `ProjectSnapshots`,
czyli dotknięcia `EditorPage.jsx`, którego lista PHASE-2B nie zawiera.

⚠️ **Ta uwaga nie da się domknąć przed spike'em** — Codex sam pisze, że przeliczenie musi nastąpić
„po domknięciu inwariantu DB, dowodów importu i protokołu §6". Liczba i rozmiar skryptów `.py`
zależą od tego, jaki kanał wyjdzie ze spike'u.

### 5. DB nie egzekwuje deklarowanego inwariantu „przypięty ma nazwę" `[P]`

**Decyzja:** ZAAKCEPTOWANE — i to jest **nowa dziura produktowa**, nie warstwa pod czymś starym.

Zweryfikowane w trzech miejscach naraz:
- §3.4.2 obiecuje „każdy `pinned = true` ma niepusty `label` — **bez wyjątków**" (`:342`);
- §3.4.1 deklaruje CHECK **wyłącznie na kształcie labela**:
  `CHECK (label IS NULL OR (char_length(label) BETWEEN 1 AND 120 AND label = btrim(label)))`
  (`:323-324`) — dla `label = NULL` warunek jest **prawdziwy**, niezależnie od `pinned`;
- §3.4.3a **sam** wprowadza politykę INSERT dopuszczającą **właściciela** prosto przez PostgREST
  (`EXISTS (SELECT 1 FROM projects WHERE id = project_id AND user_id = auth.uid())`, `:428-429`).

Czyli właściciel może ominąć backend, podać `snapshot`/`triggered_by` i wstawić
`pinned=true, label=NULL`. Nazwa zastępcza z D6 chroni POST/PATCH przez API — nie chroni wejścia,
które master **sam uznaje za realne** (cały §3.4.3a stoi na tym, że ta droga istnieje).

**Kierunek naprawy (do wykonania po decyzji właściciela):** dołożyć drugi nazwany CHECK
`projects_snapshot_pin_named`: `NOT pinned OR (label IS NOT NULL AND char_length(btrim(label)) >= 1)`
i dołożyć mu krok dowodowy (mutacja: INSERT `pinned=true, label=NULL` → oczekiwany `23514`).
Alternatywa — osłabić §3.4.2 do „egzekwowane na ścieżce API" — jest gorsza: inwariant tej fazy
istnieje po to, żeby przypięty snapshot dało się rozpoznać na liście.

### 6. Proof RLS odczytuje `with_check`, ale go nie asertuje `[A]`

**Decyzja:** ZAAKCEPTOWANE. Zweryfikowane: R1 wybiera `policyname, cmd, permissive, roles, qual,
with_check`, a oczekiwanie brzmi „dokładnie 1 polityka, `PERMISSIVE`, rola `authenticated`/`public`,
**`qual` zawiera `auth.uid() = user_id`**" (`:835`). O `with_check` nie ma ani słowa — mimo że
zapytanie już go pobiera. Polityka z poprawnym `USING` i permisywnym `WITH CHECK` przechodzi R1,
a R2/R3 jej nie złapią, bo oba zmieniają wyłącznie `note` i nie próbują przestawić `user_id`.

R4 ma ten sam problem w słabszej formie: „INSERT owner-only, brak polityki `UPDATE`" (`:838`) to
proza tam, gdzie zapytanie zwraca tabelę kolumn — kardynalność, `cmd`, role i `with_check` dają
się asertować policzalnie.

### 7. Dowód importu nie pokrywa kontraktu importu `[A]`

**Decyzja:** ZAAKCEPTOWANE. Kontrakt §3.6.1 ma **pięć** rozstrzygnięć (`:514-520`): pola nieobecne →
`NULL`; obecne i legalne → kanonizacja; `book` >120 / `note` >300 → `422` bez powstania projektu;
zły typ → `422`; `role` → ignorowane bez błędu. Dowód I1-I3 (`:846-851`) pokrywa **trzy**:
kompatybilność starego pliku, jedną kanonizację i za długie `note`.

Nieprzykryte: `book` po kanonizacji >120, zły typ obu pól, ignorowanie `role`. Implementacja może
przepuszczać za długi `book`, rzucać `500` na liczbie zamiast `422` albo importować `role` — i cały
zadeklarowany proof zostanie zielony.

### 8. Owner-only snapshot API zostawia udziałowcowi aktywne martwe kontrolki `[P]`

**Decyzja:** ZAAKCEPTOWANE. Zweryfikowane w żywym kodzie, co do linii:
- `EditorPage.jsx:96` **ma** już `const isOwner = project?.user_id === user?.id` i przekazuje go
  do innych komponentów (`:393`, `:667`);
- `EditorPage.jsx:656` montuje `<ProjectSnapshots projectId={…} onRestored={…} />` — **bez** `isOwner`;
- `ProjectSnapshots.jsx:57` ma sygnaturę `({ projectId, onRestored })`, a przyciski
  „+ Zapisz snapshot teraz" (`:100-104`) i „Przywróć" (`:136-139`) renderują się **bezwarunkowo**.

D5 świadomie **zabiera** udziałowcowi restore. Zostawienie mu klikalnego „Przywróć", które zwróci
403, to nie kwestia polish — to ślepy zaułek w jedynej funkcji, którą ta faza reklamuje.
PHASE-2B dołożyłaby do tego kolejne bezwarunkowe pin/unpin.

**Kierunek naprawy:** §9 i PHASE-2B dostają wariant read-only listy dla udziału (brak kontrolek
mutujących, nie disabled z tooltipem), a sizing PHASE-2B dostaje `EditorPage.jsx` jako czwarty plik.

### 9. Absolutne twierdzenie o „trzech realnych writerach" jest stale `[D]`

**Decyzja:** ZAAKCEPTOWANE. §3.2 twierdzi: „Realne ścieżki zapisu do `projects` z przeglądarki
są trzy" (`:169-170`). Pomiar w kodzie (`rg "from\('projects'\)"`) daje 10 trafień w 4 plikach,
w tym zapisy w `useCover.js:17,43` i `useTypography.js:30,56`, których §3.2 nie wymienia.

Kontrakt dalej jest poprawny, bo dotyczy writerów **nowych pól** `note`/`role`/`book` — wystarczy
zawęzić twierdzenie do tego zakresu. W obecnym brzmieniu audyt ścieżek jest po prostu fałszywy.

### 10. C/M/E — nie da się adversarialnie odczytać z zachowanego E `[A]`, nieblokujące

**Decyzja:** ZAAKCEPTOWANE jako uwaga procesu. Trafne: `_review/.R3-probe.py` zachowuje **źródło**
sondy, ale nie jej **wyjście**, więc `31/31 auto`, `12 projektów` i `PGRST205/PGRST202` są dziś
odczytywalne wyłącznie z preflightu (M), a nie z artefaktu dowodu (E). Przy następnym pomiarze DB
zapisuję surowy output obok skryptu, a rekord `probe-db-2026-08-13` rozbijam na jeden rekord
per artefakt.

---

## Zmiany w specu

**BRAK — master pozostaje bajtowo w v0.4.1**, zmieniona wyłącznie linia `**Status:**` (bookkeeping
rundy). To jest świadoma decyzja, nie zaniechanie:

1. **STOP-and-SPIKE zamraża spec.** Pięć z dziesięciu uwag (1, 2, 3, 6, 7) to ten sam rdzeń —
   protokół dowodu §6. Przepisanie go po raz **trzeci** bez ustalenia, jaki kanał realnie istnieje,
   utrwaliłoby wariant, który już dwa razy przegrał. Dokładnie temu ta bramka służy.
2. **Uwagi produktowe są sprzężone z §6.** Naprawa #5 dokłada CHECK **i krok dowodowy**; naprawa #7
   dokłada przypadki **dowodu**; #4 wymaga przeliczenia sizingu **po** ustaleniu liczby skryptów.
   Żadnej z nich nie da się domknąć uczciwie przed spike'em.
3. **Wersji nie bumpuję bez zmiany treści** — bump 0.4.1 → 0.5 przy nietkniętej prozie byłby
   fałszywym śladem w historii speca.

Kierunki naprawy każdej uwagi są zapisane wyżej na tyle konkretnie, że po spike'u są transkrypcją,
nie ponowną analizą.

---

## Co ma rozstrzygnąć spike (SZEROKI, na realnych danych)

Rdzeń sporu: **nie istnieje ustalony kanał, w którym asercja SQL/RLS przeciwko tej bazie kończy się
prawdziwym kodem wyjścia.** Zmierzone w preflighcie R3 (`.R3-probe.py`, EXIT=0): PostgREST zwraca
`PGRST205` na `pg_policies` i `PGRST202` na cztery kandydatury funkcji SQL; `psql` nie ma; venv nie
ma `psycopg2`/`asyncpg`; `.env` nie ma URL-a połączenia. Spec odpowiedział na to „kanałem B",
w którym asercję wykonuje i podpisuje człowiek — i Codex to odrzucił jako niedowód.

Spike ma być **szeroki**, bo wąski (tylko §6.2) już raz przegrał:

1. **Wylistuj wszystkich producentów i konsumentów spornego kontraktu** — czyli KAŻDĄ bramkę §6:
   R1-R4 (`pg_policies`), kroki 1-7/10 §6.1, kroki 8-9 (HTTP do API z JWT), I1-I3 (import),
   cały §6.2 (transakcyjny DDL + mutacje).
2. **Sprawdź ≥1 realny przykład z KAŻDEJ**, nie tylko z tej, na której pękło.
3. **Kandydaci kanału do zmierzenia** (dowolny, który da realny EXIT — to jest pytanie empiryczne,
   nie projektowe): `pip install psycopg2-binary` w `tiolibri-api/venv` + connection string z panelu
   Supabase (Session/Transaction pooler); `supabase` CLI (`supabase db execute`); `psql` z brew.
   Dla każdego zapisz, co przeszło i co odmówiło, z kodem wyjścia.
4. **Osobno zmierz tożsamości** dla kroków 8-9/R2-R3: skąd JWT właściciela i JWT udziałowca
   (kanon: `reference_jwt_do_recznych_sprawdzianow` w MEMORY), jak zakładany jest udział, pod jakim
   URL-em startuje API.
5. **Dopiero z ustalonym kanałem** §6 pisze się raz — i wtedy uwagi 1, 2, 3, 6, 7 domykają się
   razem, bo wszystkie mówią to samo zdanie z różnych stron.

Ryzyko locka z uwagi 2 rozstrzyga się przy okazji: jeśli kanał jest skryptem, transakcja trwa
sekundy zamiast minut wklejania, a `DISABLE TRIGGER` przestaje być zagrożeniem dla produkcji.

---

## Stan

- `spec: ESCALATED` (STOP-and-SPIKE, `N_EFF=3=MAX_ROUNDS`, Risk HIGH)
- Brief dla arbitra: `_review/FABLE-BRIEF-R3.md` (D13)
- **Kod i baza nadal NIETKNIĘTE.** Przez trzy rundy powstały wyłącznie dokumenty.

---

## Dla Piotrka — jedno zdanie

Trzecia runda z rzędu przewróciła się na tym samym: spec obiecuje dowód z bazy, którego na tej
maszynie **nie ma czym uruchomić** — więc zamiast pisać go po raz czwarty, trzeba raz sprawdzić,
czy da się w ogóle podłączyć do bazy narzędziem, które samo mówi PASS/FAIL.

**Kopiuj dalej — w tym samym wątku:**
```
(nic — czekaj na werdykt arbitra / decyzję o spike'u)
```

---

## DOMKNIECIE PO SPIKE'U — 2026-08-13, master **0.5**

Sekcja „Zmiany w specu" wyzej mowila: **BRAK, master zamrozony do czasu spike'u**. Spike domkniety
(`_review/SPIKE-R3-kanal.md`), wiec kierunki naprawy zostaly **wykonane** — 10/10 uwag, jeden bump.

| # | Klasa | Co weszlo do v0.5 |
|---|---|---|
| 1 | [A] | kanal „owner-attested SQL Editor" **zniesiony**; `EXIT` liczy proces, nie czlowiek |
| 2 | [A] | §6.2 przeprojektowana: `DISABLE TRIGGER` **usuniety**, rewert **mierzony** hashem w kroku 6, postflight na swiezym fixture (krok 10) |
| 3 | [A] | §6.0 kanal H: uvicorn, GoTrue admin, tozsamosc testowa zakladana i kasowana; `SUPABASE_ANON_KEY` jawnie nie jest tokenem uzytkownika |
| 4 | [P] | sizing przeliczony ze skryptami `.py`; plan faz 8 → 10 (PHASE-0-kanal, PHASE-1A-import); 2B dostala `EditorPage.jsx` |
| 5 | [P] | CHECK `snapshots_pin_named` (§3.4.1) + krok dowodowy 9 (§6.2) + zapis „nazwa i przypiecie jednym `UPDATE`-em" (§3.4.2a) |
| 6 | [A] | R1 asertuje `with_check`; nowy krok **R5** — wykonawcza kontrproba `42501` |
| 7 | [A] | import: 3 → **6** archiwow, po jednym na kazde rozstrzygniecie §3.6.1 (+ podwojna asercja status i licznik) |
| 8 | [P] | §9.5 — panel snapshotow read-only dla udzialu; klik-test **K7**; kontrolki nie istnieja, nie sa wyszarzone |
| 9 | [D] | §3.2 zawezone do writerow **nowych pol**, z pomiarem 10 trafien w 4 plikach |
| 10 | [A] | §6.0 regula 5: artefakt niesie **surowe wyjscie ORAZ skrypt** — rekord E czytelny adversarialnie |

**Stan po domknieciu:** `spec: R3-opus-pending`, `reset-po-spike: R3`, master **v0.5**,
kod i baza **nietkniete**. Nastepny krok: `/spec-handoff porzadek-wersji` (TARGET=R4).
