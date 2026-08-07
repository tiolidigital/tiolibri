# R3 — review speca MD-EXPORT

**Spec:** `docs/specs/md-export/SPEC-MD-EXPORT.md` v0.4.1  
**Zakres:** review przed implementacją, light, Risk STANDARD  
**Data:** 2026-08-07

## Werdykt

**Werdykt:** NITS

Spec jest implementowalny bez zgadywania, a pięć uwag R2 zostało domkniętych. Jedyny NIT był
lokalnym stale footerem speca: nadal opisywał stan „po R1” i kierował do ponownego handoffu mimo
statusu `R3-codex-pending`. Poprawiłem go na aktualny stan i następną akcję
`/spec-apply-review md-export` (9 linii diffu, bez zmiany kontraktu produktu).

## Wyniki review

- Aparatura `blocks`: uruchomiłem prawdziwy `segmentuj()` z gałęzi `redaktor` na F1–F11;
  `REAL_SEGMENTUJ_EXIT=0`. Implementacja algorytmu ze speca dała `PASS=11 FAIL=0`,
  `SPEC_BLOCKS_EXIT=0`. F1–F9 potwierdzają dziewięć konsekwencji, a F10/F11 obalają starą
  kolejność i potwierdzają znaczenie kolejności konsumenta.
- Sygnatura endpointu: TestClient na Pythonie 3.9.6 potwierdził brak body / `null` / `[]` /
  UUID / nie-UUID oraz kontrpróbę bez `Optional`; `PASS=6 FAIL=0`, `SIGNATURE_EXIT=0`.
- Strukturalny preflight: `FACT all=18 valid=18 invalid=0 blocked=0`, `EXIT=0`; `CME section=1
  all=8 valid=8 invalid=0 fail=0 typ_both=0 dup=0`, `EXIT=0`.
- Rekord CONTRACTED nie przenosi blokera R2: nie ma pola `E`, ma `mierzalne-od`, a uruchomione
  części kontraktu są przypisane rekordom MEASURED. Bez projektowego `CME-MANIFEST.md` osąd pięciu
  reguł nie jest blokerem; cienka bramka strukturalna przechodzi. Zastrzeżenie nieblokujące:
  rekord `preflight-R3-blocks-vs-prawdziwy-chunker` opisuje dwa przebiegi (Node i Python), choć
  rygor „rekord per artefakt” sugerowałby ich rozdzielenie, gdy kanon zostanie kiedyś dodany.
- G2 jest niesprzeczne: twarde zera dotyczą wyłącznie `kod` i `tabela`; `lista` jest rozliczana
  tylko przez G1.

## Exhaustiveness checklist

- [✓ sprawdzone] **Budżet ROZMIARU:** 5 plików / ~582 LOC / 1 domena / 0 migracji; osie plików
  i czasu PASS, LOC ma jawną dyspensę właściciela oraz wzrost ~67→~82 LOC z podanym źródłem.
- [✓ sprawdzone] **Spójność z masterem + stale references:** stan, limit rund, źródła, SHA i liczby
  są spójne; jedyny stale footer poprawiony w ramach NITS.
- [✓ sprawdzone] **Egzekwowalność:** algorytm, endpoint, limity, błędy, plan i G1–G4 wyznaczają
  implementację oraz odbiór bez nierozstrzygniętej decyzji.
- [✓ sprawdzone] **Poprawność logiki + edge/nullish:** sprawdzone `None` vs `[]`, brak body, UUID,
  kolejność gałęzi, zagnieżdżone listy, lookahead, obrazy pominięte i limity.
- [✓ sprawdzone] **Bundling / mutation targets:** fixture'y `blocks` są rozłączne per konsekwencja
  i asertują cały słownik; F10/F11 są kontrpróbami mutującymi kolejność gałęzi.
- [✓ sprawdzone] **Typy/sygnatury/argi/ścieżki:** Python 3.9.6, `Optional[...]`, route i istniejące
  symbole/ścieżki zweryfikowane; dwa nowe pliki nie istnieją, ich katalogi nadrzędne istnieją.
- [✓ sprawdzone] **Bramki maszynowe:** prawdziwy `segmentuj()`, algorytm Python, TestClient,
  FACT i strukturalny C/M/E uruchomione; wszystkie właściwe przebiegi zakończyły się `EXIT=0`,
  a F10/F11 oraz brak `Optional` dały oczekiwaną stronę czerwoną.
- [✓ sprawdzone] **Manifest pokrycia dowodu:** brak kanonicznego `CME-MANIFEST.md`, więc audyt
  adversarialny nie blokuje; struktura 8/8 rekordów przechodzi, typy MEASURED/CONTRACTED są
  rozłączne, a deklaracje pomiarowe zostały skonfrontowane z zapisanym i odtworzonym wykonaniem.
- [N/A — **SQL/RLS/migracja:** spec jest read-only, reużywa istniejącą kontrolę dostępu i nie
  zmienia schematu ani polityk.]
- [✓ sprawdzone] **UI/a11y/tokeny:** pojedynczy przycisk ma blokadę double-submit, `aria-busy`,
  komunikat błędu i instrukcję; modal oraz jego focus contract są jawnie poza zakresem.
- [N/A — **Ryzyko/dane:** check L6 dotyczy `Risk: HIGH`; ten spec ma `Risk: STANDARD` i zero
  mutacji danych produkcyjnych.]
- [✓ sprawdzone] **Docs/proza spójność:** terminologia, liczby, G1/G2, inferencje vs pomiary oraz
  footer po self-fixie są spójne.

## Proactive suggestions (rzeczy o które nie pytano)

Brak proactive suggestions.

---

## Dla Piotrka — jedno zdanie

Spec przeszedł ostatnią rundę z jednym poprawionym drobiazgiem i jest gotowy do zatwierdzenia przed implementacją.

**Kopiuj dalej:**
```
/spec-apply-review md-export
```
