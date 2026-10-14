from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]; T=R/'tools/m398_unit'; O=R/'public/books/unit-20261015';O.mkdir(exist_ok=True,parents=True)
c=(T/'core.js').read_text().replace("BOOK='m-398'","BOOK=root.UNIT_CONFIG.book").replace("NAME='sde-publication-m398-v1'","NAME='sde-publication-'+BOOK+'-20261015'").replace('>40','>root.UNIT_CONFIG.count').replace('M398Core','BookUnitCore')
(O/'core.js').write_text(c)
s=(T/'app.js').read_text().replace('window.M398Core','window.BookUnitCore').replace("B='/books/m/398/'","B=window.UNIT_CONFIG.base").replace("+' / 40 章 ·","+' / '+manifest.tasks.length+' 个阅读单元 ·").replace('n>40','n>manifest.tasks.length').replace('本书四十章范围','本书阅读单元范围')
s=s.replace("manifest.tasks.slice(i*5,i*5+5)","manifest.tasks.filter(t=>t.part===i+1)")
start=s.index('let r=await fetch(t.sourceData')
end=s.index("\ntext($('source-version')",start)
s=s[:start]+'''let r=await fetch(B+'text/',{cache:'no-cache'});if(!r.ok)throw Error('原文无法载入。');let raw=await r.text();const htmlHash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw)))).map(v=>v.toString(16).padStart(2,'0')).join('');if(htmlHash!==manifest.sourceHtmlSha256)throw Error('正文版本已变化，请更新本书学习包后再问对。原文仍可直接阅读。');let doc=new DOMParser().parseFromString(raw,'text/html'),anchor=doc.getElementById(t.sourceId);if(!anchor)throw Error('本单元原文锚点缺失。');let body;if(t.scope==='element'){body=anchor.textContent;}else{let range=doc.createRange();range.setStartBefore(anchor);let next=t.nextId&&doc.getElementById(t.nextId);if(next)range.setEndBefore(next);else range.setEndAfter(anchor.parentElement.lastChild);let fragment=range.cloneContents();fragment.querySelectorAll("script,style,nav,footer").forEach(e=>e.remove());body=fragment.textContent;}body=body.replace(/\\s+/g,' ').trim();if(body.length<180)throw Error('原文内容不足，已阻止发送。');let s={title:t.chapterTitle,url:t.sourceUrl,text:body,sha256:htmlHash};if(token!==sourceToken)return;source=s;''' +s[end:]
s=s.replace("agentName:'判生',agentEpithet:'判断力的复合发生',bookMeta:'《AI时代的判断力发生学导论》 · 王德生、张琼 · 第398卷 · ISBN 979-8-90690-868-1 · 正文修订版v3.0'","agentName:manifest.agentName,agentEpithet:manifest.agentEpithet,bookMeta:manifest.bookMeta")
s=s.replace('这是第398卷配套学习任务','这是本书配套学习任务').replace('三方程对应真，六路径对应善，三原理对应美；E是特征纠缠而非简单环境。工具封装判断不等于工具具有意识。','SDE的S是显露、D是差异序列、E是特征纠缠，三者相互规定、共同发生。不得把SDE改写成主体、行动、环境，也不得把旧版本措辞当作最新理论。阅读到旧表述应指出版本语境。健康内容只作文本研读，不提供诊疗处方。')
s=s.replace("'m398-个人学习档案-'","C.BOOK+'-个人学习档案-'").replace("'m398-救援记录-'","C.BOOK+'-救援记录-'").replace("'sde-m398-learning'","'sde-'+C.BOOK+'-learning'")
s=s.replace('本章完整文本已载入浏览器','本阅读单元文本已载入浏览器').replace('第'+"'+lesson+'"+'章','阅读单元'+"'+lesson+'")
(O/'app.js').write_text(s);(O/'unit.css').write_text((T/'unit.css').read_text())
