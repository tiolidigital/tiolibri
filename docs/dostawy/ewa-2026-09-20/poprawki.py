#!/usr/bin/env python3
"""Szesc poprawek tekstowych w ksiazce Ewy (zlecenie FABRYKI 2026-09-20).

Kazda poprawka to dokladne podstawienie w processed_html; skrypt przerywa,
jesli wzorzec nie wystepuje DOKLADNIE raz. --zapisz wysyla PATCH do bazy.
"""
import json, pathlib, sys, urllib.request

REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
PROJEKT = "1f23458e-b63a-4b29-a912-cced19ce3e47"
env = {}
for line in (REPO / "tiolibri-api/.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
SB, KEY = env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_KEY"]

POPRAWKI = [
    # (sort_order, opis, szukane, zamiennik)
    (8, "1. koniec r. 6 – zapowiedz jadlospisow",
     "W następnej części e-booka otrzymasz konkretny plan działania: gotowe jadłospisy, przepisy i wskazówki dotyczące suplementacji.",
     "W następnych rozdziałach znajdziesz mapę drogową diety oraz wskazówki dotyczące suplementacji. Gotowe przepisy i plan na 30 dni czekają na Ciebie w dwóch aplikacjach dołączonych do tego e-booka."),
    (9, "2. koniec r. 7 – zapowiedz przepisow",
     "W kolejnej części, w rozdziale ósmym – przejdziemy do praktyki. Zobaczysz konkretne jadłospisy, przepisy, plan suplementacji i 30-dniowy plan działania.",
     "W kolejnym rozdziale przejdziemy do suplementacji: co, kiedy i w jakiej formie, razem z gotowym dziennym planem. Konkretne przepisy i plan działania na 30 dni znajdziesz w dwóch aplikacjach dołączonych do tego e-booka."),
    (2, "3. mapa e-booka – bonus na dwie aplikacje",
     "Ten e-book składa się z <strong>10 rozdziałów + bonus</strong>.",
     "Ten e-book składa się z <strong>10 rozdziałów</strong>, a razem z nim otrzymujesz dwie aplikacje na telefon: plan na 30 dni i 21 przepisów. Link do obu przychodzi w mailu z e-bookiem."),
    (12, "4. numer w tytule podsumowania (wchodzi tez do spisu tresci)",
     "<h2><strong>Podsumowanie rozdziału 11.</strong></h2>",
     "<h2><strong>Podsumowanie rozdziału 10.</strong></h2>"),
    (10, "5. przypis BMJ na zaproszenie do kontaktu",
     "<p>Źródło: Olivier Massé, Claudia Mei Mercurio, Sébastien Dupuis, Maya Al Sahwi, Alexandra Arruda, Gabriel Dallaire, Katherine Desforges, Nicolas Dugré, David Williamson. <strong>Calcium, vitamin D, or combined supplementation to prevent fractures and falls: systematic review and meta-analysis</strong>. <em>BMJ</em>, 2026; 393: e088050 DOI: 10.1136/bmj-2025-088050</p>",
     "<p>Metaanalizę opublikowało w 2026 roku <em>The BMJ</em>, jedno z najbardziej cenionych czasopism medycznych na świecie. Jeśli chcesz poznać szczegóły tego badania, napisz do mnie na kontakt@profesorstachowska.pl, a prześlę Ci wszystko, co o nim wiem.</p>"),
    (10, "6. naglowek ramki bez 'ostatniej chwili'",
     "<p>Ważne z ostatniej chwili</p>",
     "<p>Co mówią najnowsze badania</p>"),
]

zapis = "--zapisz" in sys.argv
rozdzialy = json.loads((pathlib.Path(__file__).parent / "backup-chapters-przed.json").read_text())
wg_sort = {c["sort_order"]: dict(c) for c in rozdzialy}

for so, opis, szukane, zamiennik in POPRAWKI:
    h = wg_sort[so]["processed_html"]
    n = h.count(szukane)
    if n != 1:
        sys.exit(f"STOP: {opis} – wzorzec wystepuje {n} razy w sort_order {so}, oczekiwano 1")
    wg_sort[so]["processed_html"] = h.replace(szukane, zamiennik)
    print(f"OK  {opis}  (sort_order {so}, {len(h)} -> {len(wg_sort[so]['processed_html'])} znakow)")

zmienione = sorted({so for so, *_ in POPRAWKI})
print(f"\nrozdzialy do zapisu: {zmienione}")
if not zapis:
    print("PROBA – nic nie zapisano. Uruchom z --zapisz.")
    sys.exit(0)

for so in zmienione:
    c = wg_sort[so]
    req = urllib.request.Request(
        f"{SB}/rest/v1/chapters?id=eq.{c['id']}&project_id=eq.{PROJEKT}",
        data=json.dumps({"processed_html": c["processed_html"]}).encode(), method="PATCH")
    for k, v in {"apikey": KEY, "Authorization": f"Bearer {KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"}.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=60) as r:
        wiersze = json.loads(r.read())
    assert len(wiersze) == 1, f"sort_order {so}: zapis dotknal {len(wiersze)} wierszy"
    print(f"zapisano sort_order {so} ({wiersze[0]['title'][:40]})")
