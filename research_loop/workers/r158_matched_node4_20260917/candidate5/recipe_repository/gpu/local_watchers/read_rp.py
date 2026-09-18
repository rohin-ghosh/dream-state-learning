import json,os,glob
H=os.path.expanduser("~")
for d in sorted(glob.glob(f"{H}/v6_out/RP_B_seed*")):
    print("==",os.path.basename(d))
    for m in sorted(glob.glob(d+"/sleep_*/parent_brief.json")):
        M=json.load(open(m)); mm=M["metrics"]
        print("  ",m.split("/")[-2],"ritual=%s flags=%s"%(mm.get("ritual"),mm.get("flags")),{k:mm[k] for k in mm if k in ("modal_first_act_share","predict_sd","predict_distinct","note_consecutive_jaccard","recall_modal_share")},"intervened=%s hits=%s"%(M["intervened"],M["hits"]))
        if M.get("text"): print("   BRIEF:",M["text"][:900].replace("\n"," / "))
    for s in sorted(glob.glob(d+"/sleep_*/adapter")): print("  ",s.split("/")[-2],[x for x in os.listdir(s) if x in ("DONE","REJECTED_CANARY","CANDIDATE")])
