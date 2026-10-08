#!/usr/bin/env python3
"""Idempotent, reviewed fixes to candidate v1; retain original assertions."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def replace(name, old, new):
    p=ROOT/name;s=p.read_text(encoding='utf-8')
    if old in s:
        s=s.replace(old,new);p.write_text(s,encoding='utf-8')
    elif new not in s:raise RuntimeError('Patch context changed: '+name+' '+old[:65])

replace('test.py',
    "page.locator('#preview-btn').click();payload=",
    "page.locator('#preview-btn').click();page.wait_for_selector('dialog[open]');payload=")
replace('test.py',
    "page.locator('#preview-btn').click();page.locator('#api-key')",
    "page.locator('#preview-btn').click();page.wait_for_selector('dialog[open]');page.locator('#api-key')")
replace('test.py',
    "def check(name,cond):\n    assert cond,name\n    results.append({'test':name,'status':'PASS'})",
    "def check(name,cond):\n    results.append({'test':name,'status':'PASS' if cond else 'FAIL'})\n    (OUT/'engineering-report.json').write_text(json.dumps({'type':'engineering-and-synthetic-protocol-tests','realModelTested':False,'results':results,'count':len(results)},ensure_ascii=False,indent=2),encoding='utf-8')\n    assert cond,name")
replace('app.js',
    ";try{await C.append(reply);await C.removeDraft(draftId);}catch(e){pending.push(reply);",
    ";let stored=true;try{await C.append(reply);await C.removeDraft(draftId);}catch(e){stored=false;pending.push(reply);")
replace('app.js',
    "message('已保留第'+p.lesson+'章的本轮记录；模型建议不等于本人确认。');",
    "if(stored){message('已保留第'+p.lesson+'章的本轮记录；模型建议不等于本人确认。');}else{message('本轮回复尚未成功保存。请立即导出救援记录；不能把页面显示当成已存盘。',true);}")
replace('app.js',
    "if(token!==sourceToken)return;source=s;const hash=",
    "if(token!==sourceToken)return;const hash=")
replace('app.js',
    "if(hash!==s.sha256){source=null;throw Error('原文指纹不一致，已阻止发送。');}",
    "if(token!==sourceToken)return;if(hash!==s.sha256){source=null;throw Error('原文指纹不一致，已阻止发送。');}source=s;")
replace('app.js',
    "let drafts=await C.read('drafts');let dr=",
    "let drafts=await C.read('drafts');if(token!==sourceToken)return;let dr=")
replace('app.js',
    "await refresh();if(!recent('initial')&&dr?.fields)",
    "await refresh();if(token!==sourceToken)return;if(!recent('initial')&&dr?.fields)")
replace('core.js',
    "a.events.forEach(valid);const ids=new Map;",
    "a.events.forEach(valid);for(const d of a.drafts||[]){if(d.book&&d.book!==BOOK)throw Error('草稿书号不符；没有导入。');if(d.lesson!==undefined&&(!Number.isInteger(d.lesson)||d.lesson<1||d.lesson>40))throw Error('草稿题号不符；没有导入。');}const ids=new Map;")
print('Applied idempotent preview-wait, evidence, quota-reporting, source-race and draft-book fixes.')
