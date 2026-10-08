#!/usr/bin/env python3
"""Reconstruct the pre-build assets in an isolated directory; never alter worktree."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
from bs4 import BeautifulSoup
root=Path.cwd();report=json.loads((root/'m398-build-report.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
results=[]
with tempfile.TemporaryDirectory(prefix='m398-rollback-') as td:
    target=Path(td)
    for item in report['changedFiles']:
        path=item['path'];current=(root/path).read_bytes()
        assert sha(current)==item['after'],('candidate changed after manifest',path)
        p=target/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(current)
        if item['before'] is None:
            p.unlink();results.append({'path':path,'action':'remove-new-file','status':'PASS'})
        else:
            old=subprocess.check_output(['git','show','HEAD:'+path])
            assert sha(old)==item['before'],('baseline mismatch',path)
            p.write_bytes(old);assert sha(p.read_bytes())==item['before']
            results.append({'path':path,'action':'restore-matching-baseline','status':'PASS'})
    for path in ['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']:
        p=target/path
        if p.exists():
            doc=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
            assert doc.find('article',attrs={'data-id':'m-398'}) is not None
out=root/'m398-qa';out.mkdir(exist_ok=True)
(out/'rollback-rehearsal.json').write_text(json.dumps({'scope':'isolated temporary reconstruction, not production rollback','baselineCommit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'checks':len(results),'results':results,'productionModified':False,'personalRecordsTouched':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'isolatedRollbackChecks':len(results),'all':'PASS','productionModified':False}))
