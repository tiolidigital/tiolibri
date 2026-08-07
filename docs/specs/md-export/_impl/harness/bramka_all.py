# G1-G4 na WSZYSTKICH 12 rozdzialach eksportu (a.out) — dowod szerszy niz wymaga spec.
import collections, glob, json, os, re, subprocess, sys, unicodedata
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI/tiolibri-api/.env")
from supabase import create_client

S = os.path.dirname(os.path.abspath(__file__))
root = glob.glob(os.path.join(S, "gate_all", "*"))[0]
manifest = json.load(open(os.path.join(root, "_tiolibri", "manifest.json")))
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

def norm(s):
    s = unicodedata.normalize("NFC", s).replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().casefold()

# R1 mial tu diagnostyczne `strip_em`, ktore zdejmowalo markery emfazy przed porownaniem G3.
# To bylo narzedzie DOWODU (pokazalo, ze cala roznica G3 to markery) — po wdrozeniu (B)
# markery nie powstaja u zrodla, wiec ta sama normalizacja stalaby sie MASKOWNICA: zdejmowala
# tez zwykly `_` z tekstu naglowka i przepuszczala prawdziwa rozbieznosc. G3 stoi wylacznie
# na porownaniu literalnym (PROACTIVE-INBOX 2026-08-07, Codex impl R1).
FM = re.compile(r"^\s*(---\s*$|\+\+\+\s*$|(title|author|chapter_id|book_key|position|sort_order|hash|chars|blocks|slug)\s*:)", re.I)

rows = []
for ch in manifest["chapters"]:
    md_path = os.path.join(root, ch["filename"])
    out = os.path.join(S, "chunks_tmp.json")
    subprocess.run(["node", "--experimental-strip-types", os.path.join(S, "chunkuj.mjs"), md_path, out],
                   check=True, capture_output=True)
    chunks = json.load(open(out))
    html = sb.table("chapters").select("processed_html").eq("id", ch["chapter_id"]).execute().data[0]["processed_html"]

    declared = ch["blocks"]
    actual = collections.Counter(c["typ"] for c in chunks)
    g1 = {k: actual.get(k, 0) for k in declared} == declared and set(actual) <= set(declared)
    g2 = (declared.get("kod") == 0 and declared.get("tabela") == 0
          and actual.get("kod", 0) == 0 and actual.get("tabela", 0) == 0)

    src = [(int(t.name[1]), norm(t.get_text()))
           for t in BeautifulSoup(html, "lxml").find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
           if norm(t.get_text())]
    cnk = []
    for c in chunks:
        if c["typ"] == "naglowek":
            m = re.match(r"^ {0,3}(#{1,6})\s*(.*)$", c["tekst"])
            cnk.append((len(m.group(1)), norm(m.group(2))))
    g3 = cnk == src
    g4 = not [c for c in chunks if FM.match(c["tekst"].split("\n", 1)[0])]

    rows.append((ch["position"], len(chunks), g1, g2, g3, g4,
                 sum(1 for a, b in zip(cnk, src) if a != b), len(cnk)))

print("poz | chunks | G1 | G2 | G3 | G4 | naglowki roznie/wszystkie")
for p, n, g1, g2, g3, g4, d, h in rows:
    f = lambda b: "PASS" if b else "FAIL"
    print("{:>3} | {:>6} | {} | {} | {} | {} | {}/{}".format(p, n, f(g1), f(g2), f(g3), f(g4), d, h))
agg = lambda i: all(r[i] for r in rows)
print("\nZBIORCZO 12/12: G1={} G2={} G3={} G4={}".format(agg(2), agg(3), agg(4), agg(5)))
print("chunkow lacznie:", sum(r[1] for r in rows))
