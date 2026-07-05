import re, math
from collections import Counter
lines=open('pel3_065_001__rom.txt').read().split('\n')
data=[l for l in lines if ':' in l]
print("data lines:", len(data))
words={}
for l in data:
    a,b=l.split(':')
    a=a.replace(' ','')
    b=b.replace(' ','')
    py=int(a[:7],2); px=int(a[7:],2)
    assert len(b)==48, len(b)
    words[(py,px)]=b
print("address space:", len(words), "| PY max", max(k[0] for k in words), "| PX max", max(k[1] for k in words))
order=sorted(words)
bits=[words[k] for k in order]

# bit entropy per position
print("\nbit  P(1)   entropy")
ent=[]
for i in range(48):
    c=Counter(w[i] for w in bits)
    p=c['1']/len(bits)
    e=0 if p in (0,1) else -(p*math.log2(p)+(1-p)*math.log2(1-p))
    ent.append(e)
    bar='#'*int(e*40)
    print(f"{i+1:2d}  {p:.3f}  {e:.3f} {bar}")

# constant bits
const=[i+1 for i in range(48) if ent[i]==0]
print("\nconstant bits:", const if const else "none")

# duplicates / empty words
cnt=Counter(bits)
print("\ndistinct words:", len(cnt), "of", len(bits))
for w,n in cnt.most_common(5):
    print(f"  {n:5d}x  {w}")
