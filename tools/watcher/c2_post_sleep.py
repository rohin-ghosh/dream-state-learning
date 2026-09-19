import json,glob,os,time,datetime,re
r="/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life/stream/records"
def kind(d):
    dd=d.get("document",d)
    return dd.get("kind") or d.get("kind")
def doc(d): return d.get("document",d)
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
CAP=re.compile(r"(?<=[a-z,] )[A-Z][a-z]+")
seen=set(); start=time.time(); ups=0
for f in glob.glob(r+"/*.json"): seen.add(f)
print("watch start", datetime.datetime.now(datetime.UTC).strftime("%H:%M:%SZ"), "records seen", len(seen), flush=True)
while time.time()-start<3300:
    for f in sorted(glob.glob(r+"/*.json"), key=os.path.getmtime):
        if f in seen: continue
        seen.add(f)
        if f.endswith(".intent.json"): continue
        try: d=json.load(open(f))
        except Exception: continue
        k=kind(d); dd=doc(d); ts=datetime.datetime.fromtimestamp(os.path.getmtime(f),datetime.UTC).strftime("%H:%M:%SZ")
        if k=="UPDATE": ups+=1; continue
        if k=="REQUEST":
            msgs=dd.get("messages") or []
            last=msgs[-1].get("content","") if msgs else ""
            print(ts,"REQUEST tokens=%s n=%d |"%(dd.get("prompt_tokens"),len(msgs)), last[:140].replace("\n"," / "), flush=True)
        elif k=="RESPONSE":
            t=longest(dd); caps=len(CAP.findall(t)); fw=len(re.findall(r"[！-～]",t))
            print(ts,"RESPONSE len=%d midcaps=%d fullwidth=%d |"%(len(t),caps,fw), t[:220].replace("\n"," / "), flush=True)
        elif k=="INBOX":
            print(ts,"INBOX |", longest(dd)[:200].replace("\n"," / "), flush=True)
        elif k in ("SLEEP_COMPLETE","R184_LEARN_COMPLETE","LOADED","SLEEP_REQUEST","SLEEP_RECIPE","CHILD_COMPACTION","R184_TRANSITION","R194_MODE","R202_OPERATOR_RELEASE","WALL_EXTENDED"):
            print(ts,k,"| updates so far:",ups,"|",longest(dd)[:120].replace("\n"," / "), flush=True)
    time.sleep(20)
print("watch end", datetime.datetime.now(datetime.UTC).strftime("%H:%M:%SZ"), "updates:",ups)
