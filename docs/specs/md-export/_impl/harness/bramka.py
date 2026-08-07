# Bramka kontraktowa G1-G4 (SPEC-MD-EXPORT v0.4.1 §Krok 4) — zerowa tolerancja.
import collections
import glob
import json
import os
import re
import sys
import unicodedata

from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI/tiolibri-api/.env")
from supabase import create_client

CHAPTER_ID = "54929ca6-d18b-43a9-8052-808d29196e0f"
SCRATCH = os.path.dirname(os.path.abspath(__file__))

manifest = json.load(open(glob.glob(os.path.join(SCRATCH, "gate/*/_tiolibri/manifest.json"))[0]))
mch = manifest["chapters"][0]
chunks = json.load(open(os.path.join(SCRATCH, "chunks.json")))

sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
html = sb.table("chapters").select("processed_html").eq("id", CHAPTER_ID).execute().data[0]["processed_html"]

results = []


def norm(s):
    # normalizacja jak K-NAG: NFC, biale znaki zwiniete, case-insensitive
    s = unicodedata.normalize("NFC", s).replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().casefold()


# --- G1: rozklad typow chunkow == manifest.chapters[i].blocks, dla KAZDEGO typu
declared = mch["blocks"]
actual = collections.Counter(c["typ"] for c in chunks)
actual_full = {k: actual.get(k, 0) for k in declared}
g1_ok = actual_full == declared and set(actual) <= set(declared)
results.append(("G1", g1_ok, "manifest={} | chunks={} | typy spoza manifestu={}".format(
    declared, actual_full, sorted(set(actual) - set(declared)) or "brak")))

# --- G2: blocks.kod == 0 i blocks.tabela == 0 i zero chunkow tych typow
g2_ok = (declared.get("kod") == 0 and declared.get("tabela") == 0
         and actual.get("kod", 0) == 0 and actual.get("tabela", 0) == 0)
results.append(("G2", g2_ok, "manifest kod={} tabela={} | chunks kod={} tabela={}".format(
    declared.get("kod"), declared.get("tabela"), actual.get("kod", 0), actual.get("tabela", 0))))

# --- G3: ciag naglowkow (liczba -> poziom -> tekst) chunks.json == <h1..h6> w HTML
src_h = []
for tag in BeautifulSoup(html, "lxml").find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
    txt = norm(tag.get_text())
    if txt:  # konwerter pomija pusty naglowek (§Tabela regul) — pusty nie ma odpowiednika
        src_h.append((int(tag.name[1]), txt))

chunk_h = []
for c in chunks:
    if c["typ"] != "naglowek":
        continue
    m = re.match(r"^ {0,3}(#{1,6})\s*(.*)$", c["tekst"])
    chunk_h.append((len(m.group(1)), norm(m.group(2))))

empty_src = sum(1 for tag in BeautifulSoup(html, "lxml").find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                if not norm(tag.get_text()))
g3_ok = chunk_h == src_h
first_diff = "brak"
if not g3_ok:
    for idx in range(max(len(chunk_h), len(src_h))):
        a = chunk_h[idx] if idx < len(chunk_h) else None
        b = src_h[idx] if idx < len(src_h) else None
        if a != b:
            first_diff = "poz {}: chunks={!r} vs html={!r}".format(idx, a, b)
            break
results.append(("G3", g3_ok, "liczba: chunks={} html={} (puste <hN> w HTML pominiete: {}) | pierwsza roznica: {}".format(
    len(chunk_h), len(src_h), empty_src, first_diff)))

# --- G4: zaden chunk nie jest frontmatterem ani metadanymi
FM = re.compile(r"^\s*(---\s*$|\+\+\+\s*$|(title|author|chapter_id|book_key|position|sort_order|hash|chars|blocks|slug)\s*:)",
                re.IGNORECASE)
offenders = []
for i, c in enumerate(chunks):
    head = c["tekst"].split("\n", 1)[0]
    if FM.match(head):
        offenders.append((i, c["typ"], head[:60]))
# dodatkowo: pierwszy chunk nie moze byc separatorem YAML, a zaden chunk nie moze zawierac
# kluczy manifestu w formie metadanych
g4_ok = not offenders
results.append(("G4", g4_ok, "podejrzane chunki: {}".format(offenders or "brak")))

print("=" * 78)
print("BRAMKA KONTRAKTOWA G1-G4 — rozdz. 8 Ewy ({}), {} chunkow".format(mch["title"], len(chunks)))
print("=" * 78)
for name, ok, detail in results:
    print("{}  {}  {}".format(name, "PASS" if ok else "FAIL", detail))
print("=" * 78)
print("WERDYKT: {}".format("PASS (4/4)" if all(r[1] for r in results) else "FAIL"))
sys.exit(0 if all(r[1] for r in results) else 1)
