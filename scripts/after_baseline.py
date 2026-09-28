"""Run the preregistered first dev candidate after complete P2; no hidden decisions.

Detached controller: validates freeze, executes smoke then interleaved k=5 dev.
It never launches hidden evaluation or promotes. Status contains no task records.
"""
import json,os,sqlite3,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;STATE=ROOT/'.local';BANK=Path('/opt/dsh-tasks-opus/bank.json')
def status(stage,**extra):
 p=STATE/'p3-controller-status.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps({'stage':stage,'time':time.time(),**extra},indent=2));tmp.replace(p)
def rows(sweep):return [json.loads(f.read_text()) for f in (STATE/'runs').glob(sweep+'-*/result.json')]
def cost():
 with sqlite3.connect(STATE/'spend.sqlite') as c:return c.execute('select coalesce(sum(case when state="done" then cost else reserve end),0) from calls').fetchone()[0]
def sweep(name,extra):
 status('running '+name)
 with (STATE/(name+'.log')).open('ab') as log:
  subprocess.run(['python3',str(ROOT/'scripts/runner.py'),'--bank',str(BANK),'--sweep',name,'--split','dev','--workers','4',*extra],cwd=ROOT,stdout=log,stderr=log,check=True)
try:
 status('waiting for complete P2')
 while len(rows('p2-baseline'))<960:
  if cost()>=12:raise RuntimeError('Budget review required before launching candidate')
  time.sleep(30)
 subprocess.run(['python3',str(ROOT/'scripts/check_freeze.py'),str(BANK.parent),str(ROOT/'evidence/task-bank-lock.json')],check=True)
 subprocess.run(['python3',str(ROOT/'scripts/summarize.py'),'--sweep','p2-baseline'],cwd=ROOT,stdout=(STATE/'p2-baseline-summary.json').open('w'),check=True)
 if cost()>=12:raise RuntimeError('Budget review required before launching candidate')
 sweep('p3-01-smoke',['--arms','search-disabled','--per-family','2','--k','1'])
 smoke=rows('p3-01-smoke')
 if len(smoke)!=8 or any(r['failure_tag']=='INFRA' for r in smoke):raise RuntimeError('Smoke incomplete or infrastructure failure; review required')
 sweep('p3-01-dev',['--arms','standard','search-disabled','--k','5'])
 subprocess.run(['python3',str(ROOT/'scripts/summarize.py'),'--sweep','p3-01-dev'],cwd=ROOT,stdout=(STATE/'p3-01-dev-summary.json').open('w'),check=True)
 status('dev complete; awaiting gate review',runs=len(rows('p3-01-dev')),cost_usd=cost())
except Exception as e:
 status('review required',error=str(e));raise
