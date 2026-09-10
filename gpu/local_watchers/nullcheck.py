import statistics as st, math
from math import erf, sqrt
Phi = lambda z: 0.5*(1+erf(z/sqrt(2)))
# OFF replicates, same base model, same EXAM_SEED, lines 384-389
par_off=[0.342,0.329,0.383]; self_off=[0.421,0.404,0.308]
def sd(x): return st.stdev(x)
ss = sum((v-st.mean(par_off))**2 for v in par_off)+sum((v-st.mean(self_off))**2 for v in self_off)
pooled = math.sqrt(ss/4)
print("OFF replicate SD: parent %.3f self %.3f pooled(sample,df=4) %.3f pooled(pstdev-style) %.3f"%(sd(par_off),sd(self_off),pooled,math.sqrt(ss/6)))
# all OFF values quoted in notes (40-eid exams, base model, seed 777)
off_all=[0.433,0.425,0.454,0.396, 0.342,0.329,0.383, 0.421,0.404,0.308, 0.450]
print("all quoted OFF (n=%d): mean %.3f sd %.3f min %.3f max %.3f"%(len(off_all),st.mean(off_all),sd(off_all),min(off_all),max(off_all)))
print("noise band 40-eid means 0.416/0.412, 80-eid 0.410")
# pstdev bias
for n in (6,8): print("n=%d pstdev/stdev = %.3f (%.1f%% low)"%(n,math.sqrt((n-1)/n),100*(1-math.sqrt((n-1)/n))))
# SD(diff) and tail probabilities
for s1 in (0.030,0.033,0.044,0.047):
    sd_d = s1*math.sqrt(2)
    p = 1-Phi(0.03/sd_d)
    # expected max of 27 std normals ~ integrate
    import random
    random.seed(0); N=200000
    mx = [max(random.gauss(0,sd_d) for _ in range(27)) for _ in range(20000)]
    emax = st.mean(mx); p167 = sum(m>=0.167 for m in mx)/len(mx)
    print("single SD %.3f -> SD(diff) %.3f ; 0.03 = %.2f SD ; P(|d|>0.03 one tail)=%.3f ; E[max of 27]=%.3f ; P(max>=0.167)=%.3f"%(s1,sd_d,0.03/sd_d,p,emax,p167))
# parented round-0 writes (9 lineages)
r0=[0.167,-0.008,0.008,0.121,-0.017,0.100,0.100,-0.138,-0.104]
print("parented r0 n=%d mean %.3f sd %.3f se %.3f"%(len(r0),st.mean(r0),sd(r0),sd(r0)/3))
# all 27 parented writes reconstructed from notes
par27=[0.167,0.008,-0.312, -0.008,0.012,-0.012, 0.008,-0.012,0.037, 0.121,0.096,0.017, -0.017,-0.029,-0.113, 0.100,0.000,-0.100, 0.100,0.054,0.150, -0.138,-0.150,-0.067, -0.104,0.017,-0.238]
print("parented 27: >+0.03 %d, <-0.03 %d, mean %.3f sd %.3f"%(sum(v>0.03 for v in par27),sum(v<-0.03 for v in par27),st.mean(par27),sd(par27)))
self24=[-0.025,-0.013,0.008, -0.133,-0.008,0.037, -0.075,-0.096,-0.067, -0.096,-0.071,-0.008, 0.029,0.071,-0.033, -0.075,-0.008,-0.067, 0.129,0.021,-0.033, -0.083,0.083,0.017]
print("self 24: >+0.03 %d, <-0.03 %d, mean %.3f sd %.3f"%(sum(v>0.03 for v in self24),sum(v<-0.03 for v in self24),st.mean(self24),sd(self24)))
# binomial: 8/27 vs null p in [0.24,0.33]
