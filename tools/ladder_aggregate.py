"""Full ladder aggregation: GX10 dense+MoE rungs + OpenRouter MoE rungs.
Per-(model,mode) breach/OWNED/SA + Wilson CI + INVALID gate; H1 scale; cross-gen; active-axis overlay; Fisher."""
import json, math, sys
from math import comb
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, "tools")
from ownership_judge import breach_from_votes

GX10, MOE = sys.argv[1], sys.argv[2]
rows = []
for f, tag in ((GX10, "gx10"), (MOE, "openrouter")):
    for l in Path(f).read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l); r["_src"] = tag; rows.append(r)

# (active, total) in B; backend label
PARAMS = {
 "qwen2.5:0.5b":(0.5,0.5),"qwen2.5:1.5b":(1.5,1.5),"qwen2.5:3b":(3,3),"qwen2.5:7b":(7,7),
 "qwen2.5:14b":(14,14),"qwen2.5:32b":(32,32),"qwen2.5:72b":(72,72),
 "qwen3.5:2b":(2,2),"qwen3.5:4b":(4,4),"qwen3.5:9b":(9,9),"qwen3.5:27b":(27,27),
 "laguna-xs.2":(3,33),
 "hf.co/lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-GGUF:Q4_K_M":(3,30),
 "nvidia/nemotron-3-nano-30b-a3b":(3,30),"nvidia/nemotron-3-super-120b-a12b":(12,120),
 "nvidia/nemotron-3-ultra-550b-a55b":(55,550),
}
def short(m):
    if m.startswith("hf.co"): return "nemo-a3b-GGUF(local)"
    if m.startswith("nvidia/"): return m.split("/")[-1].replace("nemotron-3-","")+"(OR)"
    return m
KIND = lambda m: "dense" if PARAMS[m][0]==PARAMS[m][1] else "MoE"

def wilson(k,n,z=1.96):
    if n==0: return (0,0,0)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (p,max(0,c-h),min(1,c+h))
def ci(k,n):
    p,lo,hi=wilson(k,n); return f"{k}/{n}={p:.3f}[{lo:.3f},{hi:.3f}]"
def fisher(a,b,c,d):
    n=a+b+c+d; r1=a+b; c1=a+c
    hp=lambda k: comb(r1,k)*comb(n-r1,c1-k)/comb(n,c1)
    po=hp(a); lo=max(0,c1-(n-r1)); hi=min(c1,r1)
    return sum(hp(k) for k in range(lo,hi+1) if hp(k)<=po*1.0000001)

g=defaultdict(list)
for r in rows: g[(r["subject_model"], r["mode"])].append(r)

def cell(m,mode):
    rs=g.get((m,mode),[]); n=len(rs)
    if not n: return None
    return dict(n=n,
        breach=sum(1 for r in rs if breach_from_votes(r.get("votes",{}))=="BREACH"),
        owned=sum(1 for r in rs if r["panel_label"]=="OWNED"),
        sa=sum(1 for r in rs if r["panel_label"]=="SELF_ATTRIBUTED"),
        invalid=sum(1 for r in rs if r["panel_label"]=="INVALID"))

ALL=["qwen2.5:0.5b","qwen2.5:1.5b","qwen2.5:3b","qwen2.5:7b","qwen2.5:14b","qwen2.5:32b","qwen2.5:72b",
     "qwen3.5:2b","qwen3.5:4b","qwen3.5:9b","qwen3.5:27b","laguna-xs.2",
     "hf.co/lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-GGUF:Q4_K_M",
     "nvidia/nemotron-3-nano-30b-a3b","nvidia/nemotron-3-ultra-550b-a55b","nvidia/nemotron-3-super-120b-a12b"]

print("="*120)
print(f"{'model':<22}{'kind':<5}{'act':>5}{'tot':>5}  {'BEM breach (Wilson95)':<26}{'BEM OWN':>9}{'BEM SA':>8}{'INV%':>6}   {'recall breach':<22}")
print("-"*120)
gate={}
for m in ALL:
    b=cell(m,"BEM"); r=cell(m,"recall")
    a,t=PARAMS[m]
    nB=b['n'] if b else 0; nR=r['n'] if r else 0
    invtot=(b['invalid'] if b else 0)+(r['invalid'] if r else 0); ntot=nB+nR
    gate[m]= (invtot/ntot>0.20) if ntot else False
    bem = ci(b['breach'],b['n']) if b else "-"
    own = f"{b['owned']}/{b['n']}" if b else "-"
    sa  = f"{b['sa']}/{b['n']}" if b else "-"
    rec = ci(r['breach'],r['n']) if r else "-"
    invp= f"{(invtot/ntot*100):.0f}" if ntot else "-"
    flag=" NOT-CLEAN" if gate[m] else ""
    print(f"{short(m):<22}{KIND(m):<5}{a:>5}{t:>5}  {bem:<26}{own:>9}{sa:>8}{invp:>6}   {rec:<22}{flag}")

print("\n=== H1: qwen2.5 DENSE BEM breach vs scale ===")
prev=None
for m in ["qwen2.5:0.5b","qwen2.5:1.5b","qwen2.5:3b","qwen2.5:7b","qwen2.5:14b","qwen2.5:32b","qwen2.5:72b"]:
    b=cell(m,"BEM"); p,lo,hi=wilson(b['breach'],b['n'])
    arrow = "" if prev is None else ("↑" if p>prev else ("↓" if p<prev else "="))
    print(f"  {m:<14} {PARAMS[m][0]:>4}B  BEM breach {ci(b['breach'],b['n'])} {arrow}")
    prev=p

print("\n=== Cross-gen matched pairs (qwen3.5 newer ↔ qwen2.5 older), BEM breach ===")
pairs=[("qwen3.5:2b","qwen2.5:1.5b"),("qwen3.5:4b","qwen2.5:3b"),("qwen3.5:9b","qwen2.5:7b"),("qwen3.5:27b","qwen2.5:32b")]
for new,old in pairs:
    bn=cell(new,"BEM"); bo=cell(old,"BEM")
    pf=fisher(bn['breach'],bn['n']-bn['breach'],bo['breach'],bo['n']-bo['breach'])
    print(f"  {new:<12}({ci(bn['breach'],bn['n'])})  vs  {old:<12}({ci(bo['breach'],bo['n'])})  Fisher p={pf:.3f}")

print("\n=== OVERLAY: active=3 — does a 3-active MoE leak like 3b DENSE or like its 30-33b TOTAL? (BEM) ===")
dense3=cell("qwen2.5:3b","BEM")
dense30ish=cell("qwen2.5:32b","BEM")  # nearest dense to the MoE total (30-33b)
print(f"  DENSE qwen2.5:3b  (act=tot=3)   BEM breach {ci(dense3['breach'],dense3['n'])}   <- 'active' prediction")
print(f"  DENSE qwen2.5:32b (act=tot=32)  BEM breach {ci(dense30ish['breach'],dense30ish['n'])}  <- 'total~30' prediction")
for m in ["laguna-xs.2","hf.co/lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-GGUF:Q4_K_M","nvidia/nemotron-3-nano-30b-a3b"]:
    b=cell(m,"BEM"); a,t=PARAMS[m]
    pf=fisher(b['breach'],b['n']-b['breach'],dense3['breach'],dense3['n']-dense3['breach'])
    print(f"  MoE {short(m):<22}(act3/tot{t})  BEM breach {ci(b['breach'],b['n'])}   vs dense-3b Fisher p={pf:.3f}")

print("\n=== OVERLAY: active~55 — a55b MoE vs dense 32b/72b (BEM) ===")
for m in ["qwen2.5:32b","nvidia/nemotron-3-ultra-550b-a55b","qwen2.5:72b"]:
    b=cell(m,"BEM"); a,t=PARAMS[m]
    print(f"  {short(m):<22}(act{a}/tot{t})  BEM breach {ci(b['breach'],b['n'])}")
a55=cell("nvidia/nemotron-3-ultra-550b-a55b","BEM"); q72=cell("qwen2.5:72b","BEM"); q32=cell("qwen2.5:32b","BEM")
print(f"  a55b vs qwen72b Fisher p={fisher(a55['breach'],a55['n']-a55['breach'],q72['breach'],q72['n']-q72['breach']):.3f}")
print(f"  a55b vs qwen32b Fisher p={fisher(a55['breach'],a55['n']-a55['breach'],q32['breach'],q32['n']-q32['breach']):.3f}")
