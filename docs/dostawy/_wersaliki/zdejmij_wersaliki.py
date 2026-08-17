#!/usr/bin/env python3
"""Zdejmuje wersaliki z naglowkow H1/H2/H3 ksiazki Ewy (projekt 1f23458e).

Zasada dzialania — bez regexowej magii:
  * tabela ZAMIANY trzyma JAWNIE pelny goly tekst naglowka: przed -> po
    (48 naglowkow z CAPS przejrzanych recznie, 38 zmienianych, 10 zostaje);
  * podmiana idzie TOKEN PO TOKENIE i tylko w segmentach tekstowych naglowka,
    wiec wewnetrzny markup (<strong>, <img>, <a>) i encje zostaja nietkniete;
  * po podmianie goly tekst jest porownywany z oczekiwanym — rozjazd = STOP.

Bez argumentu = PODGLAD (nic nie pisze). Z --wykonaj = zapis do bazy.

    tiolibri-api/venv/bin/python3 docs/dostawy/_wersaliki/zdejmij_wersaliki.py
    tiolibri-api/venv/bin/python3 docs/dostawy/_wersaliki/zdejmij_wersaliki.py --wykonaj
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

from pobierz import PROJEKT, naglowki, rest, wczytaj_env

TU = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3]

# ---------------------------------------------------------------- tabela zamian
# Klucz = goly tekst naglowka w bazie. Wartosc = tekst docelowy.
# Liczba tokenow MUSI sie zgadzac po obu stronach (zmieniamy tylko wielkosc liter).
ZAMIANY = {
    # --- H1: "ROZDZIAŁ N:" / "WSTĘP:" / "ZAKOŃCZENIE:" -> jak w R7 i R9, ktore
    #     juz dzis sa pisane normalnie. Czlon po dwukropku zostaje z wielkiej.
    "WSTĘP: Jak zaczęła się moja historia z osteoporozą.":
        "Wstęp: Jak zaczęła się moja historia z osteoporozą.",
    "ROZDZIAŁ 1: Osteoporoza – co to oznacza dla Twojego organizmu?":
        "Rozdział 1: Osteoporoza – co to oznacza dla Twojego organizmu?",
    "ROZDZIAŁ 2: Co działa najlepiej – fakty naukowe.":
        "Rozdział 2: Co działa najlepiej – fakty naukowe.",
    "ROZDZIAŁ 3: Fundament – składniki budulcowe.":
        "Rozdział 3: Fundament – składniki budulcowe.",
    "ROZDZIAŁ 4: Sojusznicy zdrowych kości.":
        "Rozdział 4: Sojusznicy zdrowych kości.",
    "ROZDZIAŁ 5: Mikrobiota jelitowa a zdrowie kości.":
        "Rozdział 5: Mikrobiota jelitowa a zdrowie kości.",
    "ROZDZIAŁ 6: Co może przeszkadzać Twoim kościom.":
        "Rozdział 6: Co może przeszkadzać Twoim kościom.",
    "ROZDZIAŁ 8: Suplementacja – co działa, co nie, i jak to robić dobrze.":
        "Rozdział 8: Suplementacja – co działa, co nie, i jak to robić dobrze.",
    "ROZDZIAŁ 10: Sen, słońce, stres – pozostałe filary.":
        "Rozdział 10: Sen, słońce, stres – pozostałe filary.",
    "ZAKOŃCZENIE: Co teraz? I gdzie się spotkamy za kilka lat.":
        "Zakończenie: Co teraz? I gdzie się spotkamy za kilka lat.",

    # --- H2/H3: hasla-skladniki
    "WAPŃ – ile naprawdę potrzebujesz i skąd go brać.":
        "Wapń – ile naprawdę potrzebujesz i skąd go brać.",
    "WITAMINA D3 – optymalne poziomy, źródła, suplementacja.":
        "Witamina D3 – optymalne poziomy, źródła, suplementacja.",
    "WITAMINA K2 – zapomniany bohater metabolizmu kości?":
        "Witamina K2 – zapomniany bohater metabolizmu kości?",
    "MAGNEZ – partner wapnia w mineralizacji.":
        "Magnez – partner wapnia w mineralizacji.",
    "BIAŁKO – ile i jakie dla kości po 40+.":
        "Białko – ile i jakie dla kości po 40+.",
    "WITAMINA C – rola w budowie kości.":
        "Witamina C – rola w budowie kości.",
    "KRZEM – gdzie go znaleźć w pożywieniu.":
        "Krzem – gdzie go znaleźć w pożywieniu.",
    "SÓL: Ile to za dużo?":
        "Sól: Ile to za dużo?",
    "KOFEINA – czy rezygnować z kawy?":
        "Kofeina – czy rezygnować z kawy?",
    "ALKOHOL – wpływ na metabolizm kości.":
        "Alkohol – wpływ na metabolizm kości.",
    "CUKIER – zdrowe węglowodany są potrzebne.":
        "Cukier – zdrowe węglowodany są potrzebne.",
    "NAPOJE GAZOWANE – ograniczaj.":
        "Napoje gazowane – ograniczaj.",

    # --- H2/H3: wymagajace uwagi (przecinki, nawiasy, cudzyslowy, lacznik)
    "BOR, CYNK, FOSFOR: Co mówią dowody?":
        "Bor, cynk, fosfor: Co mówią dowody?",
    "FITOESTROGENY (IZOFLAWONY): Nadzieja czy mit?":
        "Fitoestrogeny (izoflawony): Nadzieja czy mit?",
    "CO Z INNYMI „CUDOWNYMI” SKŁADNIKAMI?":
        "Co z innymi „cudownymi” składnikami?",
    "OŚ JELITO-KOŚĆ – jak mikrobiota reguluje wchłanianie wapnia.":
        "Oś jelito-kość – jak mikrobiota reguluje wchłanianie wapnia.",
    "PROBIOTYKI DLA KOŚCI – co mówią badania":
        "Probiotyki dla kości – co mówią badania",
    "PRAKTYCZNE WSKAZÓWKI – jak wspierać mikrobiotę dla zdrowia kości.":
        "Praktyczne wskazówki – jak wspierać mikrobiotę dla zdrowia kości.",
    "PRAKTYCZNA WSKAZÓWKA – strategia 3×1.":
        "Praktyczna wskazówka – strategia 3×1.",
    "WAPŃ – Fundament, ale nie taki prosty.":
        "Wapń – fundament, ale nie taki prosty.",
    "KIEDY brać wapń – to ma znaczenie.":
        "Kiedy brać wapń – to ma znaczenie.",
    "WITAMINA D3 – hormon, nie witamina.":
        "Witamina D3 – hormon, nie witamina.",
    "KIEDY i JAK brać witaminę D3.":
        "Kiedy i jak brać witaminę D3.",
    "GOTOWY SCHEMAT – Twój dzienny plan suplementacji.":
        "Gotowy schemat – Twój dzienny plan suplementacji.",
    "SCENARIUSZ 1: Jesz około 600–700 mg Ca z diety":
        "Scenariusz 1: Jesz około 600–700 mg Ca z diety",
    "SCENARIUSZ 2: Jesz mniej niż 500 mg Ca z diety":
        "Scenariusz 2: Jesz mniej niż 500 mg Ca z diety",
    "SCENARIUSZ 3: Masz niedobór witaminy D (poniżej 20 ng/mL)":
        "Scenariusz 3: Masz niedobór witaminy D (poniżej 20 ng/mL)",
    "PODSUMOWANIE: Co robić teraz?":
        "Podsumowanie: Co robić teraz?",
}

# Naglowki z CAPS, ktore ZOSTAJA bez zmian — wypisane jawnie, zeby raport
# pokazywal, ze byly rozwazone, a nie przeoczone.
ZOSTAJE = {
    # emfaza autorki w srodku zdania, nie krzyk naglowkowy
    "Czego NIE znajdziesz w tym e-booku.": "emfaza autorki",
    "Co zrobić PO przeczytaniu?": "emfaza autorki",
    "Czego NIE suplementować (chyba że masz konkretny niedobór).": "emfaza autorki",
    "Interakcje – czego NIE łączyć.": "emfaza autorki",
    # skroty
    "SCFA – krótkołańcuchowe kwasy tłuszczowe i zdrowie kości.": "skrót SCFA",
    "Czym są SCFA i skąd się biorą?": "skrót SCFA",
    "Jak SCFA wspierają kości?": "skrót SCFA",
    "Jak zwiększyć produkcję SCFA?": "skrót SCFA",
    "Pluskwica groniasta, berberyna, DHEA.": "skrót DHEA",
    "Zrób densytometrię (badanie DEXA).": "skrót DEXA",
}

# chapters.title — dwa tytuly zmielone przez stary upload; poprawny wariant
# wziety z H1 w tresci rozdzialu. Tu podmiana jest calosciowa, bo liczba
# tokenow sie nie zgadza (1 -> 2, 1 -> 3).
TYTULY_TWARDE = {
    "Zastrzeeniemedyczne": "Zanim zaczniesz",
    "Literaturaizrodanaukowe.md": "Literatura i źródła naukowe",
}


def nowy_tytul(stary):
    """Zdejmuje wersaliki z chapters.title, zachowujac \xa0 i polpauzy.

    Lookup idzie po tekscie znormalizowanym (title bywa z niedzielaca spacja,
    np. 'z\\xa0osteoporozą'), ale sama podmiana jest tokenowa na oryginale,
    wiec niedzielace spacje przezywaja.
    """
    if stary in TYTULY_TWARDE:
        return TYTULY_TWARDE[stary]
    znorm = re.sub(r"\s+", " ", stary.replace("\xa0", " ").replace("&nbsp;", " ")).strip()
    docelowy = ZAMIANY.get(znorm)
    if docelowy is None or docelowy == znorm:
        return stary
    return podmien_w_naglowku(stary, znorm, docelowy)


def podmien_w_naglowku(fragment_html, tekst_przed, tekst_po):
    """Podmienia tokeny w segmentach TEKSTOWYCH fragmentu, omijajac tagi.

    Oryginal i cel roznia sie wylacznie wielkoscia liter, wiec tokeny paruja
    sie 1:1. Buduje mape tylko dla tokenow, ktore faktycznie sie zmieniaja.
    """
    tok_przed = tekst_przed.split()
    tok_po = tekst_po.split()
    if len(tok_przed) != len(tok_po):
        raise ValueError(
            f"rozna liczba tokenow ({len(tok_przed)} vs {len(tok_po)}): {tekst_przed!r}"
        )
    mapa = {a: b for a, b in zip(tok_przed, tok_po) if a != b}
    if not mapa:
        return fragment_html

    # rozbij na tagi i tekst; podmieniaj tylko w tekscie
    czesci = re.split(r"(<[^>]*>)", fragment_html)
    for i, cz in enumerate(czesci):
        if cz.startswith("<"):
            continue
        for a, b in sorted(mapa.items(), key=lambda kv: -len(kv[0])):
            czesci[i] = re.sub(
                r"(?<![0-9A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż])" + re.escape(a)
                + r"(?![0-9A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż])",
                b.replace("\\", "\\\\"),
                czesci[i],
            )
    return "".join(czesci)


def goly_tekst(poziom, wnetrze):
    """Goly tekst naglowka — ta sama normalizacja co w pobierz.naglowki()."""
    for _, _, g in naglowki(f"<{poziom}>{wnetrze}</{poziom}>"):
        return g
    return None


def przetworz_html(html):
    """Zwraca (nowy_html, [(poziom, przed, po)])."""
    zmiany = []

    def zamien(m):
        tag_otw, poziom, wnetrze = m.group(1), m.group(2).lower(), m.group(3)
        goly = goly_tekst(poziom, wnetrze)
        if goly is None or goly not in ZAMIANY:
            return m.group(0)

        docelowy = ZAMIANY[goly]
        nowe_wnetrze = podmien_w_naglowku(wnetrze, goly, docelowy)

        sprawdz = goly_tekst(poziom, nowe_wnetrze)
        if sprawdz != docelowy:
            raise ValueError(
                f"weryfikacja padla:\n  chcialem: {docelowy!r}\n  wyszlo  : {sprawdz!r}"
            )

        zmiany.append((poziom, goly, docelowy))
        return f"{tag_otw}{nowe_wnetrze}</{m.group(2)}>"

    nowy = re.sub(r"(<(h[1-6])\b[^>]*>)(.*?)</\2>", zamien, html, flags=re.S | re.I)
    return nowy, zmiany


def main():
    wykonaj = "--wykonaj" in sys.argv
    env = wczytaj_env()

    dane = json.loads((TU / "backup-przed.json").read_text(encoding="utf-8"))
    rozdzialy = dane["rozdzialy"]

    # bramka: to co w backupie musi byc tym, co jest teraz w bazie
    biezace = rest(
        env,
        f"chapters?project_id=eq.{PROJEKT}&deleted_at=is.null"
        f"&select=id,title,sort_order,processed_html&order=sort_order.asc",
    )
    if len(biezace) != len(rozdzialy):
        sys.exit(f"STOP: baza ma {len(biezace)} rozdzialow, backup {len(rozdzialy)}")
    for a, b in zip(rozdzialy, biezace):
        if a["id"] != b["id"] or (a["processed_html"] or "") != (b["processed_html"] or ""):
            sys.exit(f"STOP: rozdzial {a['sort_order']} zmienil sie w bazie od czasu backupu")

    plan = []
    razem_zmian = 0
    for r in rozdzialy:
        html = r["processed_html"] or ""
        nowy_html, zmiany = przetworz_html(html)
        nowy_title = nowy_tytul(r["title"])
        if not zmiany and nowy_title == r["title"]:
            continue
        plan.append(
            {"id": r["id"], "sort_order": r["sort_order"], "html": nowy_html,
             "title": nowy_title, "title_przed": r["title"], "zmiany": zmiany}
        )
        razem_zmian += len(zmiany)

    # ---- raport
    for p in plan:
        print(f"== [{p['sort_order']:2}]")
        if p["title"] != p["title_przed"]:
            print(f"   title: {p['title_przed']!r}\n       -> {p['title']!r}")
        for poziom, przed, po in p["zmiany"]:
            print(f"   {poziom}: {przed}\n     -> {po}")
        print()

    print(f"rozdzialow do zapisu : {len(plan)}")
    print(f"naglowkow zmienionych: {razem_zmian}")
    print(f"naglowkow zostawionych swiadomie: {len(ZOSTAJE)}")
    for t, powod in ZOSTAJE.items():
        print(f"   ZOSTAJE ({powod}): {t}")

    # ---- bramka fail-closed: zaden CAPS-naglowek nie moze zostac nieobsluzony
    wzor_caps = re.compile(r"[A-ZĄĆĘŁŃÓŚŹŻ]{2,}")
    sieroty = []
    for p in plan:
        for _, _, goly in naglowki(p["html"]):
            if wzor_caps.search(goly) and goly not in ZOSTAJE:
                sieroty.append((p["sort_order"], goly))
        # to samo dla chapters.title — z niego powstaje TOC w EPUB i lista w edytorze
        t = re.sub(r"\s+", " ", p["title"].replace("\xa0", " ")).strip()
        if wzor_caps.search(t) and t not in ZOSTAJE:
            sieroty.append((p["sort_order"], f"title: {t}"))
    if sieroty:
        print("\nSTOP: naglowki z CAPS poza tabela i poza lista ZOSTAJE:")
        for so, t in sieroty:
            print(f"   [{so}] {t}")
        sys.exit(1)

    if not wykonaj:
        print("\nPODGLAD — nic nie zapisano. Dodaj --wykonaj zeby zapisac.")
        return

    for p in plan:
        ciało = json.dumps({"processed_html": p["html"], "title": p["title"]},
                           ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{env['SUPABASE_URL']}/rest/v1/chapters?id=eq.{p['id']}",
            data=ciało,
            method="PATCH",
            headers={
                "apikey": env["SUPABASE_SERVICE_KEY"],
                "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            if resp.status not in (200, 204):
                sys.exit(f"STOP: zapis rozdzialu {p['sort_order']} zwrocil {resp.status}")
        print(f"zapisano [{p['sort_order']:2}] {p['title']}")

    # ---- weryfikacja odczytem
    po = rest(
        env,
        f"chapters?project_id=eq.{PROJEKT}&deleted_at=is.null"
        f"&select=id,title,sort_order,processed_html&order=sort_order.asc",
    )
    wg_id = {r["id"]: r for r in po}
    bledy = []
    for p in plan:
        r = wg_id.get(p["id"])
        if r is None:
            bledy.append(f"[{p['sort_order']}] zniknal z bazy")
        elif (r["processed_html"] or "") != p["html"]:
            bledy.append(f"[{p['sort_order']}] processed_html nie zgadza sie co do znaku")
        elif r["title"] != p["title"]:
            bledy.append(f"[{p['sort_order']}] title != {p['title']!r}")
    if bledy:
        print("\nWERYFIKACJA PADLA:")
        for b in bledy:
            print("  " + b)
        sys.exit(1)
    print(f"\nWERYFIKACJA OK: {len(plan)}/{len(plan)} rozdzialow zgodnych co do znaku.")


if __name__ == "__main__":
    main()
