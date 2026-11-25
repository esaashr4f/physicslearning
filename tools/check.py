import json,glob,os,re,sys
S=sys.argv[1]
def norm(l): return re.sub(r'\s','',l)
def lowest(units):
    labs=[u['label'] for u in units]; return labs
tot={'qp':[0,0],'ms':[0,0]}
for f in sorted(glob.glob(S+'/analysis/p*.json')):
    a=json.load(open(f)); key=os.path.basename(f)[:-5]
    r=json.load(open(S+'/regions/'+key+'.json'))
    want=[norm(q['q']) for q in a['questions']]
    line=key
    for side in ('qp','ms'):
        have=set(u['label'] for u in r[side]['units'] if u['segs'])
        # a wanted part is covered if its label or any ancestor label is present
        def cov(w):
            m=re.match(r'(\d+)((?:\([a-z]+\))*)',w); 
            if not m: return False
            q=m.group(1); parts=re.findall(r'\([a-z]+\)',m.group(2))
            for k in range(len(parts),-1,-1):
                if q+''.join(parts[:k]) in have: return k
            return False
        c=[cov(w) for w in want]
        exact=sum(1 for w,x in zip(want,c) if x is not False and (q:=w) and x==len(re.findall(r'\([a-z]+\)',w)))
        anyc=sum(1 for x in c if x is not False)
        tot[side][0]+=exact; tot[side][1]+=len(want)
        miss=[w for w,x in zip(want,c) if x is False]
        line+=f"  {side}: exact {exact}/{len(want)} any {anyc}" + (f" miss {miss[:6]}" if miss else "")
    print(line)
print(tot)
