import json,os,glob
H=os.path.expanduser("~")
L=f"{H}/v6_out/lineage3_self_s8000_e40"; print("== n1 self s8000 (replicate of n2 self s8000)")
for r in range(3):
    d=f"{L}/round_{r:03d}"
    try: E=json.load(open(d+"/exam.json")); A=json.load(open(d+"/admission_receipts.json"))
    except Exception: print("  r%d missing"%r); continue
    prev=E.get("prev",{}).get("mean") if isinstance(E.get("prev"),dict) else E.get("prev")
    adm=sum(x["admitted"] for x in A); dl=sum(x["post"]-x["pre"] for x in A)/len(A)
    print("  r%d: adm=%d/32 post-pre=%+.3f ON=%.3f OFF=%.3f PREV=%s d=%+.3f act=%.2f/%.2f %s"%(r,adm,dl,E["on"]["mean"],E["off"]["mean"],"-" if prev is None else "%.3f"%prev,E["on"]["mean"]-E["off"]["mean"],E["on"]["parseable_act_rate"],E["off"]["parseable_act_rate"],E["decision"]["reason"]))
for Lf in ["R2_B_seed0","R2_B_seed1","R2_B_seed5"]:
    r={}
    for f in sorted(glob.glob(f"{H}/v6_out/{Lf}/probe_ep0256*.json")): r[os.path.basename(f)[6:-5]]=round(json.load(open(f))["mean"],4)
    print(Lf, r, "sleeps", len(glob.glob(f"{H}/v6_out/{Lf}/sleep_*")), "rej", len(glob.glob(f"{H}/v6_out/{Lf}/sleep_*/adapter/REJECTED*")))
