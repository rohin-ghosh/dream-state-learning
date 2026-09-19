import json,glob,os,time,datetime,re
r="/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical7/life/stream/records"
def kind(d):
    dd=d.get("document",d); return dd.get("kind") or d.get("kind")
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
seen=set(glob.glob(r+"/*.json")); start=time.time()
print("P7 watch armed", datetime.datetime.now(datetime.UTC).strftime("%H:%M:%SZ"), flush=True)
while time.time()-start<2700:
    for f in sorted(glob.glob(r+"/*.json"), key=os.path.getmtime):
        if f in seen: continue
        seen.add(f)
        if f.endswith(".intent.json"): continue
        try: d=json.load(open(f))
        except Exception: continue
        k=kind(d); dd=d.get("document",d); ts=datetime.datetime.fromtimestamp(os.path.getmtime(f),datetime.UTC).strftime("%H:%M:%SZ")
        if k in ("INBOX","RESPONSE"):
            t=longest(dd); print(ts,k,f"cjk={len(re.findall(r'[㐀-鿿가-힯]',t))} |",t[:400].replace("\n"," / "),flush=True)
        elif k in ("SLEEP_COMPLETE","LOADED","R205_CONSOLE_REPLY"):
            extra=""
            if k=="SLEEP_COMPLETE": extra=f"trained {len(dd.get('presentations') or {})} excluded {len(dd.get('excluded_rows') or [])}"
            print(ts,k,extra,flush=True)
    time.sleep(20)
print("P7 watch end", datetime.datetime.now(datetime.UTC).strftime("%H:%M:%SZ"))
