#!/usr/bin/env python3
"""Pobiera rozdzialy projektu z bazy i robi backup + inwentarz naglowkow.

Kanonem jest BAZA (nie pliki dry-run) — po redakcji doszly PNG, literatura,
disclaimer, ktorych dry-run nie zna.

Odpalac z venv API:
    tiolibri-api/venv/bin/python3 docs/dostawy/_wersaliki/pobierz.py
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TU = Path(__file__).resolve().parent
PROJEKT = "1f23458e-b63a-4b29-a912-cced19ce3e47"


def wczytaj_env():
    env = {}
    for linia in (REPO / "tiolibri-api" / ".env").read_text(encoding="utf-8").splitlines():
        linia = linia.strip()
        if not linia or linia.startswith("#") or "=" not in linia:
            continue
        k, v = linia.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def rest(env, sciezka):
    req = urllib.request.Request(
        f"{env['SUPABASE_URL']}/rest/v1/{sciezka}",
        headers={
            "apikey": env["SUPABASE_SERVICE_KEY"],
            "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def naglowki(html):
    """Zwraca [(poziom, tekst_z_markupem, tekst_goly)] w kolejnosci wystapienia."""
    out = []
    for m in re.finditer(r"<(h[1-6])\b[^>]*>(.*?)</\1>", html, re.S | re.I):
        wewnatrz = m.group(2)
        goly = re.sub(r"<[^>]*>", "", wewnatrz)
        goly = (
            goly.replace("&nbsp;", " ")
            .replace(" ", " ")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
        )
        goly = re.sub(r"\s+", " ", goly).strip()
        if goly:
            out.append((m.group(1).lower(), wewnatrz, goly))
    return out


def main():
    env = wczytaj_env()
    if not env.get("SUPABASE_URL") or not env.get("SUPABASE_SERVICE_KEY"):
        sys.exit("BLAD: brak SUPABASE_URL / SUPABASE_SERVICE_KEY w tiolibri-api/.env")

    projekt = rest(env, f"projects?id=eq.{PROJEKT}&select=*")
    if not projekt:
        sys.exit(f"BLAD: projekt {PROJEKT} nie istnieje")
    projekt = projekt[0]

    rozdzialy = rest(
        env,
        f"chapters?project_id=eq.{PROJEKT}&deleted_at=is.null"
        f"&select=id,title,sort_order,processed_html&order=sort_order.asc",
    )

    backup = {"projekt": projekt, "rozdzialy": rozdzialy}
    (TU / "backup-przed.json").write_text(
        json.dumps(backup, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(f"projekt : {projekt['title']}")
    print(f"rozdzialy: {len(rozdzialy)}")
    znakow = sum(len(r.get("processed_html") or r.get("content") or "") for r in rozdzialy)
    print(f"znakow HTML: {znakow}")
    print(f"backup  : {(TU / 'backup-przed.json').relative_to(REPO)}\n")

    # inwentarz naglowkow: tylko te, ktore maja jakikolwiek ciag >=2 wielkich liter
    wzor_caps = re.compile(r"[A-ZĄĆĘŁŃÓŚŹŻ]{2,}")
    inwentarz = []
    for r in rozdzialy:
        html = r.get("processed_html") or r.get("content") or ""
        print(f"== [{r['sort_order']:2}] title: {r['title']}")
        for poziom, _, goly in naglowki(html):
            flaga = "CAPS" if wzor_caps.search(goly) else "    "
            print(f"   {flaga} {poziom}: {goly}")
            inwentarz.append(
                {
                    "sort_order": r["sort_order"],
                    "chapter_id": r["id"],
                    "poziom": poziom,
                    "tekst": goly,
                    "ma_caps": bool(wzor_caps.search(goly)),
                }
            )
        print()

    (TU / "inwentarz-naglowkow.json").write_text(
        json.dumps(inwentarz, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    ile_caps = sum(1 for x in inwentarz if x["ma_caps"])
    print(f"RAZEM naglowkow: {len(inwentarz)}, z ciagiem CAPS: {ile_caps}")


if __name__ == "__main__":
    main()
