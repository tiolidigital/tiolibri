# PROACTIVE-INBOX — md-export

## 2026-08-07 — Codex R1

**Risk flag:** Globalna unikalność oparta na tytule książki jest pozorna; identyfikator
przestrzeni roboczej musi przeżyć dwa projekty o identycznym tytule.

*Status: zrealizowane w v0.3 (§`book_key` — slug tytułu + 8 znaków hex z `project_id`).
Zapisane jako klasa problemu, nie otwarty punkt: ta sama pułapka wróci wszędzie, gdzie klucz
zewnętrznego systemu wyprowadzamy z pola redagowanego przez użytkownika.*

## 2026-08-07 — Codex, impl R1

**Risk flag:** harness `bramka_all.py` zdejmuje `_` globalnie przy diagnostyce emfazy, więc
może ukryć zwykłe underscore w tekście nagłówka; po wdrożeniu (B) werdykt G3 ma opierać się
na literalnym porównaniu bez tej diagnostycznej normalizacji.

*Status: otwarty — do domknięcia w R2 razem z wdrożeniem (B). Diagnostyczna normalizacja
w harnessie była narzędziem DOWODU (pokazała, że różnica G3 to wyłącznie markery emfazy);
gdy (B) usunie markery u źródła, ta sama normalizacja stanie się maskownicą i musi zniknąć,
inaczej bramka przepuści nagłówek z prawdziwym `_` w tekście.*

## 2026-08-07 — Sonet, impl R2

*Domknięcie wpisu wyżej: `strip_em` **usunięte** z `harness/bramka_all.py`, G3 stoi na
porównaniu literalnym. Maska zdjęta — i od razu odsłoniła realny nagłówek z emfazą częściową
(rozdz. 1 Ewy), który przesądził o rozszerzeniu (B) do (B′). Status: **zamknięty**.*

**Risk flag:** `.DS_Store` (dwa) są *tracked* w tym repo, więc `.gitignore` ich nie zdejmie —
każdy commit fazy wymaga ręcznego pominięcia; `git rm --cached` to osobna decyzja właściciela.

**Praise:** wymuszenie bramki na materiale PRODUKCYJNYM zamiast na fixture'ach złapało kształt
`<h1>WSTĘP: <strong>…</strong></h1>`, którego żaden wymyślony test by nie miał.

## 2026-08-07 — Codex R2

**Risk flag:** harness bramki zależy od bezwzględnej ścieżki do checkoutu Redaktora i od żywych
danych w bazie; dowód jest odtwarzalny w obecnym środowisku, ale nie jest przenośnym testem CI.

*Status: otwarty, świadomie poza zakresem tej fazy. Bramka G1–G4 pozostaje procedurą
odtwarzalną ręcznie (`_impl/harness/` + „Uwagi operacyjne" w HANDOFF), nie testem w pipeline.
Przeniesienie do CI wymagałoby fixture'ów zamiast żywej bazy — czyli dokładnie tego, czego
ta faza świadomie nie chciała (patrz Praise wyżej). Do rozważenia przy kolejnym specu
dotykającym mostu TIOLIBRI ↔ Redaktor.*
