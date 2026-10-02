"""Last concrete page-review fixes; source paragraphs and book identity preserved."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'build_v11.py';s=p.read_text()
old="    s=s.replace('十、四本','十、四本')"
new="""    for a,b in [('八一、条','八、一条'),('二五、个','二、五个'),('三六、个','三、六个'),('五四、层','五、四层'),('五四、本','五、四本')]:
        s=s.replace(a,b)"""
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
old="    splitlog=[]\n    for i,p in enumerate(original):"
new="""    splitlog=[]
    structured=[
        ('六系列外公开材料示范：2006年“行星”定义—— 这一次专门检验“权限”','六、系列外公开材料示范：2006年“行星”定义——这一次专门检验“权限”','suffix'),
        ('七同一IAU 材料做一次近邻比较：新增判断到底在哪里','七、同一IAU材料的近邻比较：新增判断在哪里','suffix'),
        ('八这次系列外示范仍然不叫“验证”','八、这次系列外示范仍然不叫“验证”','prefix'),
        ('九迁移以后，模型现在最稳的身份','九、迁移以后，模型现在最稳的身份','prefix')]
    for marker,heading,side in structured:
        matches=[(i,p) for i,p in enumerate(original) if marker in p.text]
        assert len(matches)==1,(marker,len(matches))
        i,p=matches[0];prior=p.text
        if side=='suffix':
            assert prior.endswith(marker);parts=[prior[:-len(marker)].strip(),heading];styles=['Normal','Heading 3']
        else:
            assert prior.startswith(marker);parts=[heading,prior[len(marker):].strip()];styles=['Heading 3','Normal']
        joined=''.join(parts)
        for key,val in list(replacements.items()):
            if norm(val)==norm(prior):replacements[key]=joined
        replacements[prior]=joined
        for item,style in zip(parts[:-1],styles[:-1]):add_before(p,item,style)
        text(p,parts[-1]);p.style=styles[-1]
        splitlog.append({'old':joined,'parts':parts,'styles':styles,'source_paragraph':i})
        log.append({'paragraph':i,'kind':'粘连小标题拆分','old':prior,'new':joined})
    for i,p in enumerate(original):"""
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
old="    d.core_properties.title='陈凤讲波伏娃：普通人都能懂';d.core_properties.author='陈凤'"
new="""    # Update only the small edition line of the existing back cover, preserving its artwork.
    from PIL import Image,ImageDraw,ImageFont
    im=Image.open(source/'backcover.jpg').convert('RGB')
    x0,y0,x1,y1=140,1583,790,1645
    strip=im.crop((x0,1574,x1,1575)).resize((x1-x0,y1-y0))
    im.paste(strip,(x0,y0))
    fontpath=subprocess.check_output(['fc-match','-f','%{file}','Noto Sans CJK SC'],text=True)
    font=ImageFont.truetype(fontpath,31)
    ImageDraw.Draw(im).text((145,1583),'第288卷 · 数字阅读版 v1.1',font=font,fill=(169,186,192))
    target=book/'backcover.jpg';im.save(target,quality=95,subsampling=0)
    oldhash=sha(source/'backcover.jpg');changed=0
    for rel in d.part.rels.values():
        if 'image' in rel.reltype and hashlib.sha256(rel.target_part.blob).hexdigest()==oldhash:
            rel.target_part._blob=target.read_bytes();changed+=1
    assert changed==1,'One embedded back-cover image must be updated'
    d.core_properties.title='陈凤讲波伏娃：普通人都能懂';d.core_properties.author='陈凤'"""
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
p=root/'finalize_v11.py';s=p.read_text()
old="    splits=json.loads((qa/'readability-splits.json').read_text());splitmap={norm(x['old']):x['parts'] for x in splits}"
new="    splits=json.loads((qa/'readability-splits.json').read_text());splitmap={norm(x['old']):x['parts'] for x in splits};splitstyles={norm(x['old']):x.get('styles',[]) for x in splits}"
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
old="""                for item in chunks:
                    p=s.new_tag('p');p.string=item;node.append(p)"""
new="""                styles=splitstyles.get(norm(value),[])
                for j,item in enumerate(chunks):
                    name='h4' if styles and styles[j].startswith('Heading') else 'p'
                    p=s.new_tag(name);p.string=item;node.append(p)"""
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
old="            md.extend(p.get_text() for p in node.find_all('p',recursive=False))"
new="            md.extend(('#### ' if p.name=='h4' else '')+p.get_text() for p in node.find_all(['p','h4'],recursive=False))"
if new not in s:
    assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
