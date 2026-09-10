import json,os
H=os.path.expanduser("~")
for L in ["R2_B_seed0","R2_B_seed1"]:
    A=json.load(open(f"{H}/v6_out/{L}/absorption_8sleeps.json"))
    print("==",L,"sleeps",A["sleeps"],"base_ctrl_nll %.2f"%A["base_control_nll"])
    print("  base_nll per sleep:",{k:round(v,2) for k,v in A["base_nll"].items()})
    for k in sorted(A["adapters"],key=int):
        e=A["adapters"][k]
        print("  adapter@%s abs=%+.2f ctrl=%+.2f ret=%s"%(k,e["absorption"],e["control_delta"],{j:round(v,2) for j,v in e["retention"].items()}))
