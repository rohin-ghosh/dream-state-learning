import re,sys
src=open(sys.argv[1]).read()
def strip(t):
    t=re.sub(r'(?<!\\)%.*','',t)
    t=re.sub(r'\\begin\{verbatim\}.*?\\end\{verbatim\}','',t,flags=re.S)
    t=re.sub(r'\\(?:cite[pt]?|ref|label|url)\{[^}]*\}','',t)
    t=re.sub(r'\$[^$]*\$',' N ',t)
    t=re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?','',t)
    t=re.sub(r'[{}~&]',' ',t)
    return t
main=src.split(r'\begin{abstract}')[1].split(r'\appendix')[0]
abstract=main.split(r'\end{abstract}')[0]
tables=re.findall(r'\\begin\{table\}.*?\\end\{table\}',main,flags=re.S)
tab_words=sum(len(strip(t).split()) for t in tables)
main_no_tab=re.sub(r'\\begin\{table\}.*?\\end\{table\}','',main,flags=re.S)
prose=len(strip(main_no_tab).split())
abs_w=len(strip(abstract).split())
app=src.split(r'\appendix')[1]
app_w=len(strip(app).split())
print(f"abstract {abs_w} words; main prose (incl abstract) {prose}; table words {tab_words}; n tables {len(tables)}; appendix words {app_w}")
for wpp,tabpg in [(750,1.0),(700,1.0),(750,0.6),(700,0.6)]:
    print(f"  est pages @ {wpp} w/p, tables {tabpg} pg: {0.55 + (prose-abs_w)/wpp + tabpg:.2f}")
