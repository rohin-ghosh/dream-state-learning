import itertools, math
INF=10**9
controls=[160,160,160,160,192,192,224,224,INF]
parented=[288,192,256]
allv=controls+parented
def U(par,con):
    u=0.0
    for p in par:
        for c in con:
            if p>c: u+=1
            elif p==c: u+=0.5
    return u
obs=U(parented,controls)
n=len(allv); k=len(parented)
ge=0; tot=0
for idx in itertools.combinations(range(n),k):
    par=[allv[i] for i in idx]; con=[allv[i] for i in range(n) if i not in idx]
    u=U(par,con); tot+=1
    if u>=obs-1e-9: ge+=1
print("U_obs",obs,"max",k*(n-k),"exact one-sided p (permutation, ties as 0.5):",ge/tot, f"({ge}/{tot})")
# also: without 'never' treated as infinite (drop seed3)
controls2=[160,160,160,160,192,192,224,224]
allv2=controls2+parented; n2=len(allv2)
obs2=U(parented,controls2); ge=tot=0
for idx in itertools.combinations(range(n2),k):
    par=[allv2[i] for i in idx]; con=[allv2[i] for i in range(n2) if i not in idx]
    tot+=1
    if U(par,con)>=obs2-1e-9: ge+=1
print("drop-never: U",obs2,"p",ge/tot)
# only the 7 R2 controls (exclude old-writer lives R_B_seed0 160, R_B_seed1 224)
controls3=[192,224,192,INF,160,160,160]
allv3=controls3+parented; n3=len(allv3)
obs3=U(parented,controls3); ge=tot=0
for idx in itertools.combinations(range(n3),k):
    par=[allv3[i] for i in idx]; con=[allv3[i] for i in range(n3) if i not in idx]
    tot+=1
    if U(par,con)>=obs3-1e-9: ge+=1
print("R2-only controls (7): U",obs3,"p",ge/tot)
