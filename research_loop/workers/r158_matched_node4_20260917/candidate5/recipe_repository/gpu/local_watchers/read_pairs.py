import json,os,glob,re
H=os.path.expanduser("~")
for d in sorted(glob.glob(H+"/v6_out/R3_B_seed*"))+sorted(glob.glob(H+"/v6_out/R4_B_seed*")):
    if not os.path.isdir(d): continue
    on={};off={}
    for f in glob.glob(d+"/probe_ep*.json"):
        m=re.match(r"probe_ep(\d+)(_adapterOFF)?\.json",os.path.basename(f))
        if m: (off if m.group(2) else on)[int(m.group(1))]=json.load(open(f))["mean"]
    pairs=[(e,on[e],off[e]) for e in sorted(on) if e in off]
    rej=len(glob.glob(d+"/sleep_*/adapter/REJECTED*")); done=len(glob.glob(d+"/sleep_*/adapter/DONE"))
    print(os.path.basename(d),"commits=%d rej=%d"%(done,rej),"pairs:",[(e,"%.3f/%.3f"%(a,b)) for e,a,b in pairs][-6:],"harmful=%d"%sum((a-b)<-0.03 for _,a,b in pairs))
