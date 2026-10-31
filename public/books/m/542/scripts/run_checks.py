"""Run every finite check script in the package with isolated interpreter (-I) and record results
in review/model_tests.json. Standard library only. Passing = scripts exit 0 with no assertion failure.
It verifies finite constructions and seeded thought-experiment simulations, NOT general proofs or empirical results."""
import subprocess, sys, json, hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
SCRIPTS=['scripts/verify_models.py','scripts/A06_checks.py','scripts/A07_checks.py','scripts/A08_checks.py','scripts/A09_sim.py',
 'review/v0.6_review_passes/R3_check.py','review/v0.6_review_passes/R4_checks_ch29_33.py','review/v0.6_review_passes/R4_checks_ch34_41.py']
res=[]
for s in SCRIPTS:
    r=subprocess.run([sys.executable,'-I',str(P/s)],capture_output=True,text=True,cwd=P)
    res.append({'script':s,'exit_code':r.returncode,'passed':r.returncode==0,'sha256':hashlib.sha256((P/s).read_bytes()).hexdigest(),'last_line':(r.stdout.strip().splitlines() or [''])[-1][:160]})
old=json.loads((P/'review/model_tests.json').read_text())
out={'date':'2026-10-31','version':'0.6','scope':old['scope'],'passed':all(x['passed'] for x in res),
 'check_groups':old['check_groups'],'v06_script_results':res,'checks':old['checks'],
 'note':'v0.5的72组复算沿用；v0.6新增脚本为各角色线与审校者的有限复算/固定种子构想模拟，不是一般命题认证、独立评审或现实实验。'}
(P/'review/model_tests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'passed':out['passed'],'scripts':len(res)},ensure_ascii=False))
sys.exit(0 if out['passed'] else 1)
