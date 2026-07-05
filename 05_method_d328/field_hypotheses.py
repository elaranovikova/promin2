lines=open('pel3_065_001__rom.txt').read().split('\n')
data=[l for l in lines if ':' in l]
W={}
for l in data:
    a,b=l.split(':'); a=a.replace(' ',''); b=b.replace(' ','')
    W[(int(a[:7],2),int(a[7:],2))]=b

def fld(w,s,e): return int(w[s-1:e],2)   # 1-based, inclusive

# hypothesis: some 6-bit field = next PX (sequential px+1)
print("6-bit fields vs. (px+1) mod 64:")
best=[]
for s in range(1,44):
    hit=sum(1 for (py,px),w in W.items() if fld(w,s,s+5)==(px+1)%64)
    best.append((hit/len(W),s))
for r,s in sorted(best,reverse=True)[:6]:
    print(f"  bits {s:2d}-{s+5:2d}: {r*100:5.1f}%")

print("\n7-bit fields vs. current PY (hold the page):")
best=[]
for s in range(1,43):
    hit=sum(1 for (py,px),w in W.items() if fld(w,s,s+6)==py)
    best.append((hit/len(W),s))
for r,s in sorted(best,reverse=True)[:6]:
    print(f"  bits {s:2d}-{s+6:2d}: {r*100:5.1f}%")

# distribution of the candidate fields
print("\nvalue distribution bits 43-48 (top 8):")
from collections import Counter
c=Counter(fld(w,43,48) for w in W.values())
for v,n in c.most_common(8): print(f"   {v:2d}: {n}")
print("  values in use:", len(c), "of 64")

print("\nvalue distribution bits 29-37 (9 bits, top 8):")
c=Counter(fld(w,29,37) for w in W.values())
for v,n in c.most_common(8): print(f"   {v:3d}: {n}")
print("  values in use:", len(c), "of 512")
