import re,sys
src=open('main.tex',encoding='utf8').read()
# strip verbatim blocks and comments for brace/env checks
body=re.sub(r'\\begin\{verbatim\}.*?\\end\{verbatim\}','VERB',src,flags=re.S)
body=re.sub(r'(?<!\\)%.*','',body)
body_nv=re.sub(r'\\verb(.)(.*?)\1','VERB',body)
# brace balance
depth=0;bad=[]
for i,ch in enumerate(body_nv):
    if ch=='{' and body_nv[i-1]!='\\': depth+=1
    elif ch=='}' and body_nv[i-1]!='\\': depth-=1
    if depth<0: bad.append(i); depth=0
print('brace depth at end:',depth,'negative dips:',len(bad))
# environments
stack=[];errs=[]
for m in re.finditer(r'\\(begin|end)\{([^}]*)\}',body_nv):
    k,e=m.group(1),m.group(2)
    if k=='begin': stack.append(e)
    else:
        if not stack or stack[-1]!=e: errs.append((e,stack[-1] if stack else None))
        else: stack.pop()
print('env errors:',errs,'unclosed:',stack)
# $ balance per paragraph (rough)
for n,para in enumerate(body_nv.split('\n\n')):
    d=para.replace('\\$','').count('$')
    if d%2: print('odd $ count in paragraph',n,':',para[:80].replace('\n',' '))
# labels / refs
labels=set(re.findall(r'\\label\{([^}]*)\}',src))
refs=set(re.findall(r'\\(?:ref|eqref|pageref)\{([^}]*)\}',src))
print('undefined refs:',sorted(refs-labels))
print('unused labels:',sorted(labels-refs))
# cites
bib=open('refs.bib',encoding='utf8').read()
keys=set(re.findall(r'^@\w+\{([^,]+),',bib,flags=re.M))
cites=set()
for m in re.finditer(r'\\cite[tp]?\*?(?:\[[^\]]*\])?\{([^}]*)\}',src):
    for k in m.group(1).split(','): cites.add(k.strip())
print('cites missing from refs.bib:',sorted(cites-keys))
print('TODO cites:',sorted(c for c in cites if c.startswith('TODO')))
# tabular column counts
for m in re.finditer(r'\\begin\{tabular\}\{([^}]*)\}(.*?)\\end\{tabular\}',body_nv,flags=re.S):
    ncol=len(re.findall(r'[lcr]',re.sub(r'\{[^}]*\}','',m.group(1))))
    for row in m.group(2).split('\\\\'):
        r=re.sub(r'\\multicolumn\{(\d+)\}\{[^}]*\}\{[^}]*\}',lambda mm:'&'.join(['X']*int(mm.group(1))),row)
        r=re.sub(r'\\multirow\{[^}]*\}\{[^}]*\}\{[^}]*\}','X',r)
        r=re.sub(r'\\(toprule|midrule|bottomrule|hline)','',r).strip()
        if not r: continue
        amps=r.count('&')
        if amps!=ncol-1: print('tabular col mismatch: expected',ncol,'got',amps+1,'::',r[:90].replace('\n',' '))
# unescaped % or & or _ in text (outside math/texttt) -- rough: report lines with bare _ outside \texttt/\verb/math
for ln,line in enumerate(body_nv.split('\n'),1):
    s=re.sub(r'\$[^$]*\$','',line); s=re.sub(r'\\texttt\{[^}]*\}','',s); s=re.sub(r'\\(?:label|ref|cite[tp]?|url)\{[^}]*\}','',s)
    if re.search(r'(?<!\\)_',s): print('bare underscore line',ln,':',s.strip()[:100])
