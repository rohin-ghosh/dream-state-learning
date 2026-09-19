import json,glob,os,sys,re,datetime,time
pats=sys.argv[1:]
def doc(d): return d.get("document",d) if isinstance(d,dict) else {}
def kind(d): return doc(d).get("kind") or d.get("kind")
def longest(d):
    best=""
    def w(x):
        nonlocal best
        if isinstance(x,str):
            if len(x)>len(best): best=x
        elif isinstance(x,dict):
            for v in x.values(): w(v)
        elif isinstance(x,list):
            for v in x: w(v)
    w(d); return best
now=time.time()
roots=set()
for p in pats:
    for r in glob.glob(p):
        if os.path.isdir(r+"/stream/records"): roots.add(r)
for r in sorted(roots):
    recs=sorted([f for f in glob.glob(r+"/stream/records/*.json") if not f.endswith(".intent.json")], key=lambda f:int(os.path.basename(f).split(".")[0]))
    if not recs: continue
    age=(now-os.path.getmtime(recs[-1]))/60
    if age>90: print(f"## {r.split('/local-rohing/')[-1]} — last record {age:.0f} min ago (stale)"); continue
    ks=[]
    for f in recs[-400:]:
        try: d=json.load(open(f)); ks.append((os.path.getmtime(f),kind(d),doc(d)))
        except Exception: pass
    sleeps=sum(1 for t,k,d in ks if k in("SLEEP_COMPLETE",))
    resp=[(t,longest(d)) for t,k,d in ks if k=="RESPONSE"]
    par=[(t,longest(d)) for t,k,d in ks if k=="INBOX" and "Tool result" not in longest(d) and "spool" not in longest(d)]
    tool=[(t,longest(d)) for t,k,d in ks if k=="INBOX" and "Tool result" in longest(d)]
    reqs=[d for t,k,d in ks if k=="REQUEST"]
    tok=reqs[-1].get("prompt_tokens") if reqs else None
    birth=""
    for t,k,d in ks:
        if k=="REQUEST":
            m=d.get("messages") or []
            if len(m)>1: birth=m[1].get("content","")[:160].replace("\n"," "); break
    cjk=sum(len(re.findall(r"[㐀-鿿가-힯]",x)) for t,x in resp[-3:])
    print(f"## {r.split('/local-rohing/')[-1]} — last record {age:.0f} min ago | sleeps in last 400 recs {sleeps} | tokens {tok} | parent turns {len(par)} (last {((now-par[-1][0])/60 if par else -1):.0f} min) | tool results {len(tool)} | CJK last3 {cjk}")
    print("   birth/identity:", birth[:160])
    if par: print("   last parent:", par[-1][1][:220].replace("\n"," / "))
    if tool: print("   last tool:", tool[-1][1][:120].replace("\n"," / "))
    for t,x in resp[-2:]: print("   RESP", datetime.datetime.fromtimestamp(t,datetime.UTC).strftime("%H:%M")+"Z:", x[:260].replace("\n"," / "))
