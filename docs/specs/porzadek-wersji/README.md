# porzadek-wersji — TL;DR

Dashboard TIOLIBRI pokazuje 12 kafelków o mylnie podobnych tytułach, z których aktualne są dwa —
reszta to kopie robione „na wszelki wypadek". Tytuł jest jedynym nośnikiem informacji i jest
przycięty na karcie, więc nie da się zapisać, czym dana kopia właściwie jest.

Ten spec dokłada projektowi trzy pola: **notatkę** (wolny tekst właściciela), **etykietę wersji**
(`AKTUALNA` / `ROBOCZA` / `ARCHIWUM`) i **nazwę książki** — oraz uwiarygodnia snapshoty, które
aplikacja już robi co 6 h w tle, ale bez nazwy i z retencją kasującą też te ręczne. Po zmianie
„kopia przed Redaktorem" to przypięty, nazwany snapshot: jeden klik, żyje wiecznie i nie robi
kafelka na dashboardzie.

Grupowanie kafelków po książce jest zaprojektowane, ale zagatowane — decyzja dopiero po sprzątnięciu
balastu, bo na 2-4 kafelkach może się okazać niepotrzebne.

**Status:** master-draft
**Risk:** HIGH (migracja DB + trigger kasujący dane właściciela) → MAX_ROUNDS = 3
**Fazy:** PHASE-1A (metadane DB+API) → PHASE-1B (metadane UI) → *sprzątanie balastu* →
PHASE-2A (snapshoty DB+API) → PHASE-2B (snapshoty UI) → PHASE-3 (grupowanie, warunkowa)
**Źródło ustaleń:** `HANDOFF-porzadek-wersji-projektow.md`, pamięć `project-kanoniczne-projekty-w-bazie`
