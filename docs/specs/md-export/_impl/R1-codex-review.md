## Werdykt

**Werdykt:** REQUEST_CHANGES

## Co działa / Co wymaga zmiany

Implementacja jest funkcjonalnie daleko zaawansowana: build frontendu przechodzi, 110/110 nowych
testów konwertera przechodzi, sprawdzian żywego endpointu zaliczył 6/6 wykonanych wariantów,
a prawdziwy `segmentuj()` konsumenta potwierdził G1, G2 i G4 na 1141 chunkach z 12 rozdziałów.
Routery pozostają w wymaganej kolejności (`export_import`, `snapshots`, potem `projects`), a zmiana
nie dokłada zakazanego `.select()` po `update()`.

### BLOCKER 1 — G3 pozostaje czerwone; poprawne wyjście to (B)

Diagnoza Soneta o sprzeczności wewnątrz speca jest prawdziwa. Tabela reguł nakazuje bez wyjątku
`<strong>`/`<em>` → markery Markdown, natomiast G3 porównuje tekst Markdowna z `get_text()` HTML-a
i dopuszcza wyłącznie normalizację whitespace/case. Dla `<h2><strong>Tekst</strong></h2>` nie da
się jednocześnie wyemitować `## **Tekst**` i uzyskać literalnej równości z `Tekst`. Wynik 29/30
różnic w rozdziale 8 oraz 0/30 po zdjęciu markerów potwierdza dokładnie tę sprzeczność, nie utratę
nagłówków ani poziomów.

Należy wybrać **(B)**: nie emitować markerów emfazy, gdy emfaza obejmuje całą znaczącą treść
nagłówka; emfaza częściowa ma zostać. (A) naprawiłoby wyłącznie harness przez osłabienie G3,
pozostawiając markery w edytowalnych chunkach nagłówkowych. K-NAG traktuje te markery jako część
tekstu, więc ich zgubienie/przesunięcie przez W2 może zatrzymać późny `apply`. (B) usuwa
redundantny artefakt Google Docs u źródła i zachowuje informacyjną emfazę częściową. Potrzebne są
testy pełnej oraz częściowej emfazy w nagłówku i ponowny przebieg G3 na wymaganym rozdziale.

To nie jest self-fix NITS: zmienia kontrakt konwersji i wymaga testów, więc zgodnie z
LESSONS#1 wątpliwość i zmiana kontraktowa prowadzą do REQUEST_CHANGES.

### BLOCKER 2 — sizing nie ma ważnej dyspensy na faktyczny rozmiar

Obowiązkowy pomiar objął pliki untracked: `md_exporter.py` ma 540 LOC, a
`test_md_exporter.py` 368 LOC. Łączny churn pięciu plików implementacji to ok. **1159 LOC**
(1157 dodań + 2 usunięcia), wobec zapisanej i autoryzowanej dyspensy **~582 LOC**. Oś plików
trzyma 5/5, ale dyspensa na ~82 LOC ponad limit nie jest zgodą na dalsze ~577 LOC.

Według §4.5 jest to obecnie **REQUEST_CHANGES**, nie automatycznie zaakceptowany wyjątek:
reguła jest twarda, a `/spec-impl` powinien zatrzymać przekroczenie i eskalować. Jednocześnie
remedium jest decyzją właściciela: może jawnie rozszerzyć dyspensę do zmierzonego rozmiaru,
jeżeli świadomie preferuje jedną kohezywną fazę, albo zażądać redukcji/splitu. Recenzent nie może
sam rozszerzyć autoryzacji. To jest zgodne z LESSONS#17: testy są w tej samej sumie, a wzrost
macierzy wymaga jawnego ponownego potwierdzenia.

### Odstępstwo parsera — uzasadnione, nieblokujące

Warunkowe użycie `html.parser` dla dokumentu ≥10 MB jest uzasadnionym odstępstwem od litery
„BeautifulSoup + lxml”. Test reprodukuje istotny tryb awarii: lxml po cichu usuwa długi atrybut
`src`, przez co wymagane `>10 MB → 413` staje się nieegzekwowalne. Fallback przywraca kontrakt
fail-closed, nie dodaje zależności i jest ograniczony do dużych dokumentów.

Nie ma dowodu pełnej równoważności parserów na dowolnym uszkodzonym HTML-u — `html.parser` i lxml
mogą inaczej naprawiać malformed markup. Nie traktuję tego jako regresji blokującej: wejście to
zaufany `processed_html`, reguły konwersji mają 110 zielonych testów, a wyjście z 12 realnych
rozdziałów przeszło G1/G2/G4. W R2 warto dodać małą próbę parytetu obu parserów na reprezentatywnym
HTML-u wokół ścieżki fallbacku; nie należy wracać do lxml bez rozwiązania limitu atrybutu.

### Kryteria, edge cases i regresja

- [x] Build: `cd tiolibri-frontend && npm run build` — PASS, 0 błędów.
- [x] Testy baseline-relatywnie: fail@teraz = {`test_polish_pdf.py` — collection error,
  brak `libgobject-2.0-0`}; fail@HEAD = ten sam zbiór. Zatem fail@teraz ⊆ fail@HEAD.
  `pytest -q test_md_exporter.py` = **110 passed** (+110 przypadków fazy).
- [x] Scope discipline: pięć plików implementacji odpowiada osi plików speca; artefakty
  `_impl/harness/` i raporty są dowodami wymaganych sprawdzianów. Zmiana `.DS_Store` jest
  niezwiązana z implementacją i nie powinna wejść do commita.
- [x] Endpoint: brak body/null/[]/wybrane/obce ID/nie-UUID działają zgodnie z kontraktem;
  gałąź projektu bez rozdziałów jest obecna przed filtrem. Brak produkcyjnej atrapy nie jest
  blokerem i nie uzasadnia zapisu do produkcji.
- [x] Limit obrazu 10 MB, limit 80 MB, 409 dla pustego `processed_html`, unikalność nazw,
  manifest, obrazy, escaping, listy, separatory i NFC mają implementację oraz pokrycie.
- [ ] Kryterium G3 — FAIL do czasu wdrożenia (B) i ponownego przebiegu.
- [ ] Sizing — brak decyzji właściciela obejmującej faktyczne ~1159 LOC.
- [x] Kolejność rejestracji routerów w `main.py` — poprawna.
- [x] supabase-py: nie dodano `.select()` po `.update().eq()`.
- [x] TipTap: zmiana nie dodaje `this.editor` ani pluginu transakcyjnego.
- [x] Bez over-engineeringu: własny licznik bloków jest wymagany przez G1, a dodatkowe pola
  `pad` i `mime_unknown` wynikają z jawnych kontraktów ZIP-a/manifestu.

## Proactive suggestions (rzeczy o które nie pytano)

- **Workflow:** checkpoint sizingu po napisaniu dwóch nowych plików powinien był zatrzymać R1
  przed kosztownymi sprawdzianami; to konkretny przypadek LESSONS#17 pkt 3.
- **Risk flag:** harness `bramka_all.py` zdejmuje `_` globalnie przy diagnostyce emfazy, więc
  może ukryć zwykłe underscore w tekście nagłówka; po wdrożeniu (B) werdykt G3 ma opierać się
  na literalnym porównaniu bez tej diagnostycznej normalizacji.

---

## Dla Piotrka — jedno zdanie

Wybierz B i jawnie zatwierdź ~1159 LOC albo każ split; parser fallback jest uzasadniony, a reszta bramek i regresji przechodzi.

**Kopiuj dalej — w tym samym wątku:**
```
/spec-apply-impl-review md-export
```
