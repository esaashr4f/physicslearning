import json,glob,os,sys
S=sys.argv[1]; out=S+'/site/data'; os.makedirs(out,exist_ok=True)
qs=[]; conv={}
for f in sorted(glob.glob(S+'/analysis/p*.json')):
    a=json.load(open(f))
    for q in a['questions']:
        q=dict(q); q['paper']=a['paper']; q['slug']=a['slug']; q['q']=q['q'].replace(' ','')
        qs.append(q)
with open(out+'/questions.json','w') as fh:
    fh.write('[\n'+',\n'.join(json.dumps(q,ensure_ascii=False) for q in qs)+'\n]\n')
reg={}
for f in sorted(glob.glob(S+'/regions/p*.json')):
    reg[os.path.basename(f)[:-5]]=json.load(open(f))
json.dump(reg,open(out+'/regions.json','w'),separators=(',',':'))
print(len(qs),'parts', os.path.getsize(out+'/questions.json')//1024,'KB questions', os.path.getsize(out+'/regions.json')//1024,'KB regions')
