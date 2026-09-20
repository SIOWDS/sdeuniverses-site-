#!/usr/bin/env python3
"""Resolve only derived annual-catalog conflicts, preserving upstream entries."""
import json,subprocess
from pathlib import Path
import wechat_2025_publish_20260920 as publication
import wechat_2025_final_quality as quality
allowed={'public/wechat-picks/index.html','public/wechat-picks/2024/index.html','public/wechat-picks/2025/index.html'}
conflicts=set(subprocess.check_output(['git','diff','--name-only','--diff-filter=U'],text=True).splitlines())
if not conflicts or not conflicts<=allowed:
    raise RuntimeError('Unexpected concurrent file changes; stop rather than overwrite: '+repr(conflicts))
# During rebase, ours is the updated upstream. Read its complete catalog first.
subprocess.run(['git','checkout','--ours','--',*sorted(conflicts)],check=True)
manifest=json.loads(Path('public/wechat-picks/2025/batch-20260920/manifest.json').read_text())
stats=publication.integrate(manifest)
reportpath=Path('public/wechat-picks/2025/batch-20260920/report.json');report=json.loads(reportpath.read_text());report['annual_catalogs']=stats;report['concurrent_catalog_merge']={'files':sorted(conflicts),'method':'Preserve upstream catalog, integrate verified batch, assert all prior source links survive'};reportpath.write_text(json.dumps(report,ensure_ascii=False,indent=2))
quality.finish();publication.static()
subprocess.run(['git','add','--',*sorted(allowed),'public/wechat-picks/2025/batch-20260920/report.json'],check=True)
print('Concurrent annual entries preserved and verified.')
