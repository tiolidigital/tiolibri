import json, pathlib, re, urllib.request, html
REPO = pathlib.Path("/Users/piotrmichalski/Library/Mobile Documents/com~apple~CloudDocs/SaaS Factory/TIOLIBRI")
env={}
for l in (REPO/"tiolibri-api/.env").read_text().splitlines():
    l=l.strip()
    if l and not l.startswith("#") and "=" in l:
        k,v=l.split("=",1); env[k.strip()]=v.strip().strip('"').strip("'")
SB,KEY=env["SUPABASE_URL"].rstrip("/"),env["SUPABASE_SERVICE_KEY"]
def call(u):
    r=urllib.request.Request(u)
    r.add_header("apikey",KEY); r.add_header("Authorization",f"Bearer {KEY}")
    return json.loads(urllib.request.urlopen(r,timeout=60).read())
p=[x for x in call(f"{SB}/rest/v1/projects?select=id,title,imprint") if x["id"].startswith("1f23458e")]
print(p[0]["id"],p[0]["title"],p[0]["imprint"].get("version") if p[0]["imprint"] else None)
ch=call(f"{SB}/rest/v1/chapters?project_id=eq.{p[0]['id']}&deleted_at=is.null&select=id,title,sort_order,processed_html&order=sort_order")
import sys
if len(sys.argv)>1:
  for c in ch:
    t=html.unescape(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",c["processed_html"] or "")))
    for w in sys.argv[1:]:
      n=len(re.findall(w,t,re.I))
      if n: print(c["sort_order"],c["title"][:40],"|",w,n)
  sys.exit()
for c in ch:
    t=re.sub(r"<[^>]+>"," ",c["processed_html"] or ""); t=html.unescape(re.sub(r"\s+"," ",t))
    print(f"\n## [{c['sort_order']}] {c['title']}  ({c['id'][:8]})")
    for m in re.finditer(r"[^.]{0,90}(?:[Rr]ozdzia\w*\s+\d+|[Rr]ozdz\.\s*\d+|szablon\w* tygodnia)[^.]{0,60}",t):
        print("   ->",m.group(0).strip())
