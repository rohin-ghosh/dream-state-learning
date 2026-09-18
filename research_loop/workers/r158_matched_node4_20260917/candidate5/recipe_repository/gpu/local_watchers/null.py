import statistics as st, math
from math import erf, sqrt
# OFF (base, seed 777, 40 eids) values itemized in COORDINATION.md
off = {
 "scout7004_srv(l290)":0.433,"scout7004_self(l291)":0.425,"scout7005_srv(l292)":0.454,"scout7005_self(l293)":0.396,
 "s8000_par_n2_r0(l384)":0.342,"s8000_par_n2_r1(l385)":0.329,"s8000_par_n2_r2(l386)":0.383,
 "s8000_self_n2_r0(l387)":0.421,"s8000_self_n2_r1(l388)":0.404,"s8000_self_n2_r2(l389)":0.308,
 "s8000_self_n1_r0(l406)":0.450,
 "s8004_par_n2_r0(l454)":0.392,"s8004_par_n2_r1(l454)":0.433,"s8004_par_n2_r2(l454)":0.387,
 "s8004_self_n1_r1(l454)":0.425,"s8005_par_n1_r2(l460)":0.338,
}
v=list(off.values()); n=len(v)
sd=st.stdev(v); psd=st.pstdev(v)
print(f"n={n} OFF replicates itemized; mean={st.mean(v):.3f} sample SD={sd:.4f} pstdev={psd:.4f} range {min(v):.3f}-{max(v):.3f}")
six=[0.342,0.329,0.383,0.421,0.404,0.308]
print(f"reviewer's 6 same-node OFF values: sample SD={st.stdev(six):.4f}")
print(f"pstdev bias factor n=8: {math.sqrt(7/8):.3f}  n=6: {math.sqrt(5/6):.3f}")
Phi=lambda z:0.5*(1+erf(z/sqrt(2)))
# expected max of N iid std normals (numerical)
def emax(N,steps=200000):
    lo,hi=-8,8; h=(hi-lo)/steps; s=0
    for i in range(steps):
        z=lo+(i+0.5)*h; pdf=math.exp(-z*z/2)/sqrt(2*math.pi)
        s+= z*N*Phi(z)**(N-1)*pdf*h
    return s
em27=emax(27); em9=emax(9)
print(f"E[max of 27 std normals]={em27:.3f}; of 9: {em9:.3f}")
for s1,label in [(0.030,"band node2"),(0.044,"band node1"),(0.045,"OFF-replicate SD"),(sd,"pooled OFF itemized")]:
    sd_d=s1*sqrt(2)
    p=1-Phi(0.03/sd_d)
    print(f"[{label}] single SD={s1:.3f} -> SD(ON-OFF)={sd_d:.3f}; HARM_TOL=0.03 is {0.03/sd_d:.2f} diff-SD; "
          f"P(diff>+0.03)=P(diff<-0.03)={p:.2f}; E[max of 27]={em27*sd_d:+.3f}; E[max of 9 r0]={em9*sd_d:+.3f}; "
          f"z(+0.167)={0.167/sd_d:.1f}; z(-0.312)={-0.312/sd_d:.1f}; z(-0.238)={-0.238/sd_d:.1f}")
# binomial tails
from math import comb
def ptail(n,k,p): return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))
for p in (0.24,0.30,0.32):
    print(f"p_null={p}: parented P(X>=8/27)={ptail(27,8,p):.2f}  P(X>=8 harmful)={ptail(27,8,p):.2f} | self P(>=11/24 harmful)={ptail(24,11,p):.3f}  P(<=4/24 positive)={1-ptail(24,5,p):.2f}")
# parented r0 mean
r0=[0.167,-0.008,0.008,0.121,-0.017,0.100,0.100,-0.138,-0.104]
print(f"parented r0 (n=9): mean={st.mean(r0):+.3f} SD={st.stdev(r0):.3f} SE={st.stdev(r0)/3:.3f}")
par_means=[-0.046,-0.003,0.011,0.078,-0.053,0.000,0.101,-0.118,-0.108]
self_means=[-0.010,-0.035,-0.079,-0.058,0.022,-0.050,0.039,0.006]
print(f"lineage means parented: mean={st.mean(par_means):+.3f} SD={st.stdev(par_means):.3f} SE={st.stdev(par_means)/3:.3f}")
print(f"lineage means self:     mean={st.mean(self_means):+.3f} SD={st.stdev(self_means):.3f} SE={st.stdev(self_means)/sqrt(8):.3f}")
