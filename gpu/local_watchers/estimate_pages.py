#!/usr/bin/env python3
"""Line-based page estimate of the main text of main.tex under ICLR geometry.
ICLR: textwidth 396pt, textheight 648pt, normalsize 10pt/11pt, small 9pt/10pt,
section skip ~29pt, subsection ~22pt, paragraph run-in +6.5pt, abstract in quote (346pt).
Times AFM metrics for text; CM for math; cmtt for \\texttt.
"""
import re, math, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/scratchpad')
import measure_tables as M

TEX = "/Users/rohing/dream-state/paper_fable/main.tex"
W = 396.0; H = 648.0
BODY_PT, BODY_LEAD = 10.0, 11.0
SMALL_PT, SMALL_LEAD = 9.0, 10.0
PARINDENT = 15.0

def strip_latex(s):
    s = re.sub(r'(?<!\\)%.*', '', s)
    s = re.sub(r'\\label\{[^}]*\}', '', s)
    s = re.sub(r'\\footnote\{.*?\}(?=\s|$)', '', s, flags=re.S)
    s = re.sub(r'\\S\\ref\{[^}]*\}', '\u00a74.2', s)
    s = re.sub(r'Appendix~\\ref\{[^}]*\}', 'Appendix B', s)
    s = re.sub(r'Table~\\ref\{[^}]*\}', 'Table 2', s)
    s = re.sub(r'\\ref\{[^}]*\}', '2', s)
    s = re.sub(r'\\citep\{([^}]*)\}', lambda m: '(' + '; '.join('Park et al., 2023' for _ in m.group(1).split(',')) + ')', s)
    s = re.sub(r'\\citet\{[^}]*\}', 'Park et al. (2023)', s)
    s = re.sub(r'\\cite\{[^}]*\}', 'Park et al. (2023)', s)
    s = re.sub(r'\\(begin|end)\{(enumerate|itemize|quote|abstract)\}', '', s)
    s = re.sub(r'\\item\s*', '', s)
    s = re.sub(r'\\(section\*?|subsection|paragraph|title|author|maketitle|newcommand)\b.*', '', s)
    return s

def para_width(text, pt):
    """glyph width of a paragraph at font size pt (uses measure_tables cell_width machinery)."""
    M.FONT_PT = pt
    return M.cell_width(strip_latex(text))

def lines_for(text, pt, width, indent=PARINDENT, extra_first=0.0):
    w = para_width(text, pt) + indent + extra_first
    return max(1, math.ceil(w / width * 1.03))   # 3% for justification/hyphenation slack

def main(reflow=False):
    src = open(TEX).read()
    body = src.split(r'\begin{document}')[1].split(r'\appendix')[0]
    # remove bibliography commands
    body = re.sub(r'\\IfFileExists\{iclr2027_conference\.bst\}.*', '', body)
    body = re.sub(r'\\bibliography\{refs\}', '', body)
    # pull out tables
    tables = re.findall(r'\\begin\{table\}.*?\\end\{table\}', body, re.S)
    body_wo = re.sub(r'\\begin\{table\}.*?\\end\{table\}', '', body, flags=re.S)
    # abstract
    abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', body_wo, re.S).group(1)
    body_wo = body_wo.replace(abstract, '')
    height = 0.0
    log = []
    # title block (title 2 lines \Large\bf + spacing + anonymous author block)
    height += 100; log.append(('title block', 100))
    # abstract: heading + quote-indented text at normalsize
    n = lines_for(abstract, BODY_PT, W - 50, indent=0)
    h = 22 + n * BODY_LEAD + 16
    height += h; log.append((f'abstract ({n} lines)', h))
    # footnote in results
    fn = re.search(r'\\footnote\{(.*?)\}\s*$', body_wo, re.S | re.M)
    fns = re.findall(r'\\footnote\{([^}]*)\}', body_wo)
    for f in fns:
        n = lines_for(f, 8.0, W, indent=0)
        h = 12 + n * 9.5
        height += h; log.append((f'footnote ({n} lines)', h))
    # paragraphs
    in_enum = False
    for para in re.split(r'\n\s*\n', body_wo):
        p = para.strip()
        if not p or p.startswith('%'):
            continue
        if re.match(r'\\section\*?\{', p):
            height += 29; log.append((p[:40], 29))
            rest = re.sub(r'\\section\*?\{[^}]*\}\s*(\\label\{[^}]*\})?', '', p).strip()
            if rest:
                n = lines_for(rest, BODY_PT, W)
                height += n * BODY_LEAD; log.append((f'  section body ({n} lines)', n * BODY_LEAD))
            continue
        if re.match(r'\\subsection\{', p):
            height += 22; log.append((p[:40], 22)); continue
        if re.match(r'\\begin\{enumerate\}', p) or '\\item' in p:
            items = [i for i in re.split(r'\\item', p) if i.strip() and not re.match(r'\s*\\(begin|end)', i.strip())]
            tot = 8
            for it in items:
                n = lines_for(it, BODY_PT, W - 25, indent=0)
                tot += n * BODY_LEAD + 2
            height += tot; log.append((f'enumerate ({len(items)} items)', tot)); continue
        extra = 0.0; skip = 0.0
        m = re.match(r'\\paragraph\{([^}]*)\}', p)
        if m:
            M.FONT_PT = BODY_PT
            extra = M.cell_width(strip_latex(m.group(1))) * 1.05 + 10  # bold run-in + 1em
            skip = 6.5
            p = p[m.end():]
        n = lines_for(p, BODY_PT, W, extra_first=extra)
        h = skip + n * BODY_LEAD
        height += h; log.append((f'para ({n} lines) ' + strip_latex(p)[:30], h))
    # tables
    for t in tables:
        cap = re.search(r'\\caption\{(.*)\}\s*\n\s*\\label', t, re.S).group(1)
        ncap = lines_for(cap, SMALL_PT, W, indent=0)
        tb = re.search(r'\\begin\{tabular\}\{[^}]*\}(.*?)\\end\{tabular\}', t, re.S).group(1)
        tb = re.sub(r'\\(top|mid|bottom)rule', '', tb)
        nrows = len([r for r in tb.split('\\\\') if r.strip()])
        extra_rows = 0; extra_cap = 0
        if reflow:
            # Table1: values to note (+2 caption lines); Table2: key in caption (+1), Table3: 2 wrapped rows, Table4: 3 wrapped rows
            extra_cap = {101: 2, 127: 1, 167: 0, 190: 0}.get(src[:src.find(t)].count('\n') + 1 + t.count('\n', 0, t.find('tabular')), 1)
            extra_rows = 2
        h = 20 + 10 + (ncap + extra_cap) * SMALL_LEAD + 8 + (nrows + extra_rows) * SMALL_LEAD
        height += h; log.append((f'table ({nrows} rows, {ncap}+{extra_cap} caption lines)', h))
    pages = height / H
    print(f"{'REFLOWED' if reflow else 'AS AUTHORED'}: total {height:.0f}pt = {pages:.2f} pages of 648pt (no Figure 1; +0.35 with a real figure -> {pages+0.35:.2f})")
    return log, height

if __name__ == '__main__':
    log, h = main(False)
    for k, v in log:
        print(f"  {v:6.1f}pt  {k}")
    print()
    main(True)
