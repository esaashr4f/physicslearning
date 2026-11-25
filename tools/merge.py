import json,glob,os,sys
S=sys.argv[1]; out=S+'/site/data'; os.makedirs(out,exist_ok=True)
qs=[]; conv={}
specmaps={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(S+'/specmap/p*.json')}
spec=json.load(open(S+'/spec/outcomes_clean.json'))
json.dump(spec,open(out+'/spec.json','w'),ensure_ascii=False,separators=(',',':'))
for f in sorted(glob.glob(S+'/analysis/p*.json')):
    a=json.load(open(f))
    for q in a['questions']:
        q=dict(q); q['paper']=a['paper']; q['slug']=a['slug']; q['q']=q['q'].replace(' ','')
        sm=specmaps.get(os.path.basename(f)[:-5],{})
        q['spec_points']=sm.get(q['q']) or sm.get(q['q'].replace(' ','')) or []
        qs.append(q)
with open(out+'/questions.json','w') as fh:
    fh.write('[\n'+',\n'.join(json.dumps(q,ensure_ascii=False) for q in qs)+'\n]\n')
reg={}
for f in sorted(glob.glob(S+'/regions/p*.json')):
    reg[os.path.basename(f)[:-5]]=json.load(open(f))
json.dump(reg,open(out+'/regions.json','w'),separators=(',',':'))
print(len(qs),'parts', sum(1 for q in qs if q['spec_points']),'mapped', os.path.getsize(out+'/questions.json')//1024,'KB questions', os.path.getsize(out+'/regions.json')//1024,'KB regions')

# ---- near misses, examiners' reports, moves ----
nm={'items':[],'leniencies':[],'general':[]}
for f in sorted(glob.glob(S+'/nearmiss/p*.json')):
    d=json.load(open(f)); p=int(os.path.basename(f)[1])
    for it in d.get('items',[]): it['paper']=p; nm['items'].append(it)
    for it in d.get('leniencies',[]): it['paper']=p; nm['leniencies'].append(it)
    for g in d.get('general',[]):
        if g not in nm['general']: nm['general'].append(g)
if nm['items']:
    json.dump(nm,open(out+'/nearmiss.json','w'),ensure_ascii=False,separators=(',',':'))
ex={}
for f in sorted(glob.glob(S+'/ercomments/p*.json')):
    ex[os.path.basename(f)[:-5]]=json.load(open(f))
if ex: json.dump(ex,open(out+'/examiners.json','w'),ensure_ascii=False,separators=(',',':'))
mv={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(S+'/moves/p*.json')}
if mv:
    qs=json.load(open(out+'/questions.json'))
    for q in qs:
        m=mv.get(f"p{q['paper']}-{q['slug']}",{}).get(q['q'])
        if m: q['moves']=m.get('moves',[]); q['scaffolded']=m.get('scaffolded'); q['steps']=m.get('steps'); q['moves_why']=m.get('why','')
    with open(out+'/questions.json','w') as fh:
        fh.write('[\n'+',\n'.join(json.dumps(x,ensure_ascii=False) for x in qs)+'\n]\n')
print('nearmiss',len(nm['items']),'examiner reports',len(ex),'moves files',len(mv))

# ---- assumed knowledge ----
km={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(S+'/knowmap/p*.json')}
if km:
    K=json.load(open(out+'/knowledge.json')); kind={i['id']:i['kind'] for i in K['items']}
    qs=json.load(open(out+'/questions.json'))
    for q in qs:
        m=km.get(f"p{q['paper']}-{q['slug']}",{}).get(q['q'])
        if m:
            q['needs']=m.get('needs',[]); q['assumed']=m.get('assumed',''); q['kgiven']=m.get('given',[]); q['knew']=m.get('new',[])
            q['reasonable']=not any(kind.get(i) in ('D','F') for i in q['needs'])
    with open(out+'/questions.json','w') as fh:
        fh.write('[\n'+',\n'.join(json.dumps(x,ensure_ascii=False) for x in qs)+'\n]\n')
    print('knowledge maps',len(km))

# ---- fine-grained sub-skills ----
stg={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(S+'/subtags/p*.json')}
if stg:
    qs=json.load(open(out+'/questions.json'))
    for q in qs:
        m=stg.get(f"p{q['paper']}-{q['slug']}",{}).get(q['q'])
        if m: q['sub']=m.get('sub',[]); q['subdetail']=m.get('detail','')
    with open(out+'/questions.json','w') as fh:
        fh.write('[\n'+',\n'.join(json.dumps(x,ensure_ascii=False) for x in qs)+'\n]\n')
    print('subtag files',len(stg))
