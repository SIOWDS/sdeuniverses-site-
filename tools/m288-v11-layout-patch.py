"""Final visual fixes: keep the part-10 reading map on its opener; valid Markdown tables."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'build_v11.py';s=p.read_text()
old="        for title in part['chapters']:add_before(target,title,'BookRoute')"
new="""        if part['anchor']=='part10':
            for route in ['第57—60章：教育、父母、婚姻与照护', '第61—64章：职场、身体与衰老、AI与自我叙述', '第65—68章：阅读、组织、决策与日常练习']:
                add_before(target,route,'BookRoute')
        else:
            for title in part['chapters']:add_before(target,title,'BookRoute')"""
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
p=root/'finalize_v11.py';s=p.read_text()
old="""            for i,row in enumerate(rows):
                md.append('| '+' | '.join(row)+' |')
                if i==0:md.append('| '+' | '.join(['---']*len(row))+' |')"""
new="""            table_lines=[]
            for i,row in enumerate(rows):
                table_lines.append('| '+' | '.join(row)+' |')
                if i==0:table_lines.append('| '+' | '.join(['---']*len(row))+' |')
            md.append('\\n'.join(table_lines))"""
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
