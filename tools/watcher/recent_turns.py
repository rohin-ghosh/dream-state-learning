import json,glob,os,sys,re,datetime,collections
root=sys.argv[1]; n=int(sys.argv[2]); pat=sys.argv[3] if len(sys.argv)>3 else ''
fs=sorted(glob.glob(root+'/stream/records/*'), key=os.path.getmtime)
hist=collections.Counter(); out=[]
kw=re.compile(pat,re.I) if pat else None
for f in fs:
    if f.endswith('.intent.json'): continue
    try: w=json.load(open(f)); d=w.get('document',w) if isinstance(w,dict) else {}
    except Exception: continue
    k=(d.get('kind') if isinstance(d,dict) else None) or (w.get('kind') if isinstance(w,dict) else None); hist[k]+=1
    ts=datetime.datetime.utcfromtimestamp(os.path.getmtime(f)).strftime('%H:%M:%SZ')
    if k=='INBOX':
        m=d.get('message',{}); out.append((ts,'INBOX',(m.get('speaker') or d.get('speaker') or '')+': '+str(m.get('text',''))[:320]))
    elif k=='RESPONSE':
        out.append((ts,'RESP',str(d.get('response',{}).get('raw',''))[:320]))
    elif k=='SLEEP_COMPLETE':
        out.append((ts,'SLEEP',json.dumps({x:d.get(x) for x in ('new_rows','trained_rows','optimizer_steps') if x in d})))
print('files',len(fs),'kinds',dict(hist.most_common(12)))
print('last file',os.path.basename(fs[-1])[:60] if fs else None)
if kw:
    hits=[o for o in out if o[1]=='INBOX' and kw.search(o[2])]
    print('KEYWORD INBOX hits',len(hits))
    for i,(ts,k,t) in enumerate(hits[-8:]):
        print(ts,k,'|',t.replace('\n',' / '))
        idx=out.index((ts,k,t))
        for j in range(idx+1,min(idx+4,len(out))):
            if out[j][1]=='RESP': print('   ->',out[j][0],out[j][2][:300].replace('\n',' / ')); break
print('--- last',n)
for ts,k,t in out[-n:]: print(ts,k,'|',t.replace('\n',' / '))
