import json,os,glob,re
H=os.path.expanduser("~")
for d in sorted(glob.glob(f"{H}/v6_out/R2_B_seed*")):
    L=os.path.basename(d); on={}; off={}
    for f in glob.glob(d+"/probe_ep*.json"):
        b=os.path.basename(f); m=re.match(r"probe_ep(\d+)(_adapterOFF)?\.json",b)
        if not m: continue
        (off if m.group(2) else on)[int(m.group(1))]=json.load(open(f))["mean"]
    pairs=[(e,on[e],off[e]) for e in sorted(on) if e in off]
    sl=len(glob.glob(d+"/sleep_*")); rej=len(glob.glob(d+"/sleep_*/adapter/REJECTED*")); done=len(glob.glob(d+"/sleep_*/adapter/DONE"))
    can=[]
    for lg in glob.glob(d+"/life.log"):
        can=[float(x) for x in re.findall(r"canary parseable-ACT rate=([0-9.]+)",open(lg).read())]
    print(L,"ep0=%.3f"%on.get(0,float("nan")),"pairs:",[(e,"%+.3f"%(a-b)) for e,a,b in pairs],"sleeps",sl,"done",done,"rej",rej,"canary min/mean %.2f/%.2f n=%d"%(min(can) if can else 0,sum(can)/len(can) if can else 0,len(can)))
