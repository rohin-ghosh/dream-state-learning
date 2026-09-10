#!/usr/bin/env python3
"""Estimate natural widths of every tabular in main.tex using Adobe Times-Roman AFM
metrics (== URW Nimbus Roman used by pdflatex's `times` package) for text, CM metrics
for math, cmtt for \\texttt. Compares against ICLR text width 5.5in = 396pt and the
article fallback (letter, 1in margins) 6.5in = 468pt.
"""
import re, sys

TEX = sys.argv[1] if len(sys.argv) > 1 else "/Users/rohing/dream-state/paper_fable/main.tex"
FONT_PT = float(sys.argv[2]) if len(sys.argv) > 2 else 9.0      # \small in a 10pt doc
TABCOLSEP = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0    # article default
ICLR = 396.0
ARTICLE = 468.0

# Adobe Times-Roman AFM advance widths (per 1000 em)
TIMES = {
 ' ':250,'!':333,'"':408,'#':500,'$':500,'%':833,'&':778,"'":333,'(':333,')':333,'*':500,
 '+':564,',':250,'-':333,'.':250,'/':278,'0':500,'1':500,'2':500,'3':500,'4':500,'5':500,
 '6':500,'7':500,'8':500,'9':500,':':278,';':278,'<':564,'=':564,'>':564,'?':444,'@':921,
 'A':722,'B':667,'C':667,'D':722,'E':611,'F':556,'G':722,'H':722,'I':333,'J':389,'K':722,
 'L':611,'M':889,'N':722,'O':722,'P':556,'Q':722,'R':667,'S':556,'T':611,'U':722,'V':722,
 'W':944,'X':722,'Y':722,'Z':611,'[':333,'\\':278,']':333,'^':469,'_':500,'`':333,
 'a':444,'b':500,'c':444,'d':500,'e':444,'f':333,'g':500,'h':500,'i':278,'j':278,'k':500,
 'l':278,'m':778,'n':500,'o':500,'p':500,'q':500,'r':333,'s':389,'t':278,'u':500,'v':500,
 'w':722,'x':500,'y':500,'z':444,'{':480,'|':200,'}':480,'~':541,
 '\u2013':500,'\u2014':1000,'\u2020':500,'\u2026':1000,'\u00d7':564,'\u2212':564,
 '\u2265':549,'\u2248':549,'\u2192':1000,'\u201c':444,'\u201d':444,'\u2018':333,'\u2019':333,
}
# Computer Modern math widths (per 1000 em), used inside $...$
CM = {'0':500,'1':500,'2':500,'3':500,'4':500,'5':500,'6':500,'7':500,'8':500,'9':500,
      '.':278,',':278,'+':778,'\u2212':778,'-':778,'=':778,'\u2265':778,'\u2248':778,
      '\u2192':1000,'\u00d7':778,'(':389,')':389,'/':500,' ':0,'\u2020':444}
TT_EM = 0.525  # cmtt

def text_width(s, table=TIMES, default=500):
    return sum(table.get(ch, default) for ch in s) / 1000.0 * FONT_PT

def math_width(s):
    # superscripts at script size (\small -> 6pt scripts): crude 0.7 factor
    sup = re.findall(r'\^\{([^}]*)\}', s)
    s = re.sub(r'\^\{[^}]*\}', '', s)
    w = sum(CM.get(ch, 500) for ch in s) / 1000.0 * FONT_PT
    for t in sup:
        w += sum(CM.get(ch, 500) for ch in t) / 1000.0 * FONT_PT * 0.7
    return w

REPL = [
    (r'\\onoff\{\}', 'ON$-$OFF'), (r'\\nm\b', 'not measured'),
    (r'\{,\}', ','), (r'\\%', '%'), (r'\\_', '_'), (r'\\#', '#'), (r'\\&', '&'),
    (r'\\ldots', '\u2026'), (r'\\dagger', '\u2020'), (r'\\approx', '\u2248'),
    (r'\\ge\b', '\u2265'), (r'\\to\b', '\u2192'), (r'\\times', '\u00d7'),
    (r'\\text\{([^}]*)\}', r'\1'), (r'\\max', 'max'),
    (r'\\emph\{([^}]*)\}', r'\1'), (r'\\textbf\{([^}]*)\}', r'\1'),
    (r'---', '\u2014'), (r'--', '\u2013'), (r"``", '\u201c'), (r"''", '\u201d'),
    (r'\\ ', ' '), (r'~', ' '),
]

def cell_width(cell):
    s = cell.strip()
    for pat, rep in REPL:
        s = re.sub(pat, rep, s)
    w = 0.0
    # \texttt{...}
    def tt(m):
        nonlocal w
        w += len(m.group(1)) * TT_EM * FONT_PT
        return ''
    s = re.sub(r'\\texttt\{([^}]*)\}', tt, s)
    # math
    def mth(m):
        nonlocal w
        w += math_width(m.group(1).replace('-', '\u2212'))
        return ''
    s = re.sub(r'\$([^$]*)\$', mth, s)
    s = re.sub(r'\\[a-zA-Z]+', '', s)   # any leftover commands
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'\s+', ' ', s).strip()
    w += text_width(s)
    return w

def parse_tabulars(src):
    out = []
    for m in re.finditer(r'\\begin\{tabular\}\{([^}]*)\}(.*?)\\end\{tabular\}', src, re.S):
        line = src[:m.start()].count('\n') + 1
        spec = m.group(1)
        ncols = len(re.findall(r'[lcr]|p\{[^}]*\}', spec))
        body = m.group(2)
        rows = []
        for raw in body.split('\\\\'):
            raw = re.sub(r'\\(top|mid|bottom)rule', '', raw).strip()
            if not raw:
                continue
            cells = re.split(r'(?<!\\)&', raw)
            rows.append(cells)
        out.append((line, ncols, rows))
    return out

def main():
    src = open(TEX).read()
    print(f"font {FONT_PT}pt, tabcolsep {TABCOLSEP}pt; ICLR width {ICLR}pt, article fallback {ARTICLE}pt\n")
    for line, ncols, rows in parse_tabulars(src):
        colmax = [0.0] * ncols
        widest = [''] * ncols
        for cells in rows:
            for i, c in enumerate(cells[:ncols]):
                w = cell_width(c)
                if w > colmax[i]:
                    colmax[i] = w
                    widest[i] = c.strip()[:40]
        content = sum(colmax)
        total = content + 2 * TABCOLSEP * ncols
        flag = 'OVERFLOW' if total > ICLR else 'fits'
        print(f"tabular @ line {line}: {ncols} cols, {len(rows)} rows (incl. header)")
        print(f"  content {content:6.1f}pt + padding {2*TABCOLSEP*ncols:5.1f}pt = {total:6.1f}pt  "
              f"-> ICLR {flag} by {total-ICLR:+.0f}pt ({total/ICLR*100:.0f}%); article: {'OVERFLOW' if total>ARTICLE else 'fits'}")
        for i in range(ncols):
            print(f"    col {i+1}: {colmax[i]:6.1f}pt  <- {widest[i]!r}")
        print()

main()
