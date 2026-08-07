# PROACTIVE-INBOX — md-export

## 2026-08-07 — Codex R1

**Risk flag:** Globalna unikalność oparta na tytule książki jest pozorna; identyfikator
przestrzeni roboczej musi przeżyć dwa projekty o identycznym tytule.

*Status: zrealizowane w v0.3 (§`book_key` — slug tytułu + 8 znaków hex z `project_id`).
Zapisane jako klasa problemu, nie otwarty punkt: ta sama pułapka wróci wszędzie, gdzie klucz
zewnętrznego systemu wyprowadzamy z pola redagowanego przez użytkownika.*
