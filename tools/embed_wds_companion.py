#!/usr/bin/env python3
# 把 WDS 陪读浮层嵌入含 <article> 正文的文章页（幂等：已挂则跳过）。
import glob, sys
INJECT = ('\n<!-- WDS 陪读浮层 -->\n'
          '<script>window.WDS_READ={selector:"article"};</script>\n'
          '<script src="/taste/wds-companion/wds-read.js" defer></script>\n')
patterns = sys.argv[1:] or ['public/column/**/index.html']
done=[]; skip=0; skipna=0
for pat in patterns:
    for f in sorted(glob.glob(pat, recursive=True)):
        h=open(f,encoding='utf-8').read()
        if 'wds-read.js' in h: skip+=1; continue
        if '<article' not in h or '</body>' not in h: skipna+=1; continue
        parts=h.rsplit('</body>',1)
        open(f,'w',encoding='utf-8').write(parts[0]+INJECT+'</body>'+parts[1])
        done.append(f)
print(f"嵌入 {len(done)} 篇 · 已挂跳过 {skip} · 无article或body跳过 {skipna}")
for f in done[:3]: print("  例:", f)
