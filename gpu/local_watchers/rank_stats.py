import math
from statistics import mean, stdev
d=[0.060,0.064,-0.015,0.011,0.091]
n=len(d); m=mean(d); s=stdev(d); se=s/math.sqrt(n); t=m/se
# t critical values df=4
t90=2.132; t95=2.776
print(f"paired: mean={m:.4f} sd={s:.4f} se={se:.4f} t={t:.2f} df=4")
print(f"90% CI: [{m-t90*se:+.4f}, {m+t90*se:+.4f}]  95% CI: [{m-t95*se:+.4f}, {m+t95*se:+.4f}]")
# two-sided p via t-dist survival (df=4) numeric
def t_sf(t,df):
    # incomplete beta via numeric integration
    import math
    x=df/(df+t*t)
    # regularized incomplete beta I_x(df/2, 1/2) /2
    a=df/2; b=0.5
    # numeric integration of beta pdf
    N=200000
    tot=0.0
    for i in range(N):
        u=(i+0.5)/N*x
        tot+=u**(a-1)*(1-u)**(b-1)
    tot*=x/N
    B=math.gamma(a)*math.gamma(b)/math.gamma(a+b)
    return 0.5*tot/B
p2=2*t_sf(t,4)
print(f"two-sided p={p2:.3f}, one-sided p={p2/2:.3f}")
# unpaired
r8=[0.413,0.440,0.468,0.491,0.343]; r16=[0.473,0.504,0.453,0.502,0.434]
m8,m16=mean(r8),mean(r16); s8,s16=stdev(r8),stdev(r16)
sp=math.sqrt((s8**2+s16**2)/2); se_u=sp*math.sqrt(2/5); tu=(m16-m8)/se_u
print(f"unpaired: r8 {m8:.3f} (sd {s8:.3f}) r16 {m16:.3f} (sd {s16:.3f}) diff={m16-m8:+.3f} t={tu:.2f} df=8 two-sided p={2*t_sf(tu,8):.3f}")
# MDE at n=5 paired, sd 0.043, 80% power alpha .05 two-sided approx (t crit 2.776 + t for power ~0.94 df4 -> use ~1.0 for rough)
print(f"rough MDE (80% power, two-sided .05, n=5, sd={s:.3f}): {(2.776+0.941)*se:.3f}")
# equivalence margin 0.03: is 90% CI inside [-0.03,0.03]?
lo,hi=m-t90*se,m+t90*se
print(f"TOST at +/-0.03: inside? {lo>-0.03 and hi<0.03}")
