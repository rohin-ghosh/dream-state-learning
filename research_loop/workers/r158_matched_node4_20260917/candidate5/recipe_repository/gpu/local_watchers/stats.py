from math import comb, sqrt
import itertools
def fisher2(a,b,c,d):
    # table [[a,b],[c,d]] rows=arm, cols=(harm, not harm); two-sided via sum of tables with prob <= observed
    n=a+b+c+d; r1=a+b; c1=a+c
    def p(x): 
        return comb(r1,x)*comb(n-r1,c1-x)/comb(n,c1)
    p0=p(a)
    lo=max(0,c1-(n-r1)); hi=min(r1,c1)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=p0+1e-12)
print("pair-level R2 9/82 vs R3 0/35:", round(fisher2(9,73,0,35),3))
print("life-level R2 3/9 vs R3 0/4:", round(fisher2(3,6,0,4),3))
print("life-level R2 3/9 vs RP 0/3:", round(fisher2(3,6,0,3),3))
print("life-level R2 3/9 vs R3+RP 0/7:", round(fisher2(3,6,0,7),3))
print("classroom harmful writes 8/27 vs 11/24:", round(fisher2(8,19,11,13),3))
print("classroom positive writes 8/27 vs 4/24:", round(fisher2(8,19,4,20),3))
print("lineage means>=0 4/9 vs 3/8:", round(fisher2(4,5,3,5),3))
# paired-by-seed lineage means from COORDINATION line 467
par = {"8000n2":-0.046,"8001n2":-0.003,"8000n1":+0.011,"8001n1":+0.078,"8002n2":-0.053,"8003n2":0.000,"8004n2":+0.101,"8005n2":-0.118,"8005n1":-0.108}
self_= {"8000n2":-0.010,"8001n2":-0.035,"8000n1":-0.079,"8002n2":-0.058,"8003n2":+0.022,"8001n1":-0.050,"8004n1":+0.039,"8005n2":+0.006}
# pairing by seed (cross-node for 8004; 8005n1 parented has no self partner)
pairs=[("8000n2","8000n2"),("8001n2","8001n2"),("8000n1","8000n1"),("8001n1","8001n1"),("8002n2","8002n2"),("8003n2","8003n2"),("8004n2","8004n1"),("8005n2","8005n2")]
d=[par[p]-self_[s] for p,s in pairs]
m=sum(d)/len(d); sd=sqrt(sum((x-m)**2 for x in d)/(len(d)-1)); t=m/(sd/sqrt(len(d)))
print("paired diffs:",[round(x,3) for x in d]); print("mean",round(m,3),"sd",round(sd,3),"t",round(t,2))
# permutation on lineage means (unpaired), 9 vs 8
allv=list(par.values())+list(self_.values()); obs=sum(par.values())/9-sum(self_.values())/8
cnt=0;tot=0
for idx in itertools.combinations(range(17),9):
    a=[allv[i] for i in idx]; b=[allv[i] for i in range(17) if i not in idx]
    diff=sum(a)/9-sum(b)/8; tot+=1
    if abs(diff)>=abs(obs)-1e-12: cnt+=1
print("unpaired lineage-mean diff",round(obs,3),"perm p",round(cnt/tot,3))
# sign test: paired diffs positive count
print("paired diffs >0:", sum(1 for x in d if x>0), "of", len(d))
