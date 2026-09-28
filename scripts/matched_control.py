"""Actual best-of-up-to-five standard attempts under a shared inference budget.

The paired primary standard run is attempt 0. Extra independent attempts use fresh
homes and seeds, but share its 100k-token / 20-call budget. Only aggregate reports
are exposed. This script requires the gateway's budget-group support.
"""
import argparse,concurrent.futures,json,sqlite3
from pathlib import Path
from types import SimpleNamespace
from runner import single

p=argparse.ArgumentParser();p.add_argument('--bank',type=Path,required=True);p.add_argument('--comparison',required=True);p.add_argument('--sweep',required=True);p.add_argument('--split',default='held-out');p.add_argument('--workers',type=int,default=4);opts=p.parse_args()
root=Path(__file__).resolve().parent.parent;state=root/'.local';bank=json.loads(opts.bank.read_text())
tasks={t['id']:t for t in bank if t['split']==opts.split}
primary=[json.loads(f.read_text()) for f in (state/'runs').glob(opts.comparison+'-*/result.json')]
primary=[r for r in primary if r['arm']=='standard' and r['split']==opts.split]
assert len(primary)==len(tasks)*5,'Need complete k=5 standard comparison before control'

def run_control(first):
 task=tasks[first['task']];rep=first['rep'];group=f'{opts.sweep}-{task["id"]}-{rep}';dest=state/'runs'/f'{opts.sweep}-{task["id"]}-matched-{rep}'
 if (dest/'result.json').exists():return
 with sqlite3.connect(state/'spend.sqlite') as c:
  c.execute('insert or ignore into budget_groups values(?,?,?)',(group,100000,20))
  c.execute('insert or ignore into budget_members values(?,?)',(first['run'],group))
 attempts=[first]
 for n in range(1,5):
  with sqlite3.connect(state/'spend.sqlite') as c:
   count,tokens=c.execute('select count(*),coalesce(sum(input+output),0) from calls where run in (select run from budget_members where group_id=?)',(group,)).fetchone()
   global_cost=c.execute('select coalesce(sum(case when state="done" then cost else reserve end),0) from calls').fetchone()[0]
  if count>=20 or tokens>=100000 or global_cost>=17.75:break
  sweep=f'raw-{opts.sweep}-attempt{n}';seed=rep+100*n;rid=f'{sweep}-{task["id"]}-standard-{seed}'
  with sqlite3.connect(state/'spend.sqlite') as c:c.execute('insert or ignore into budget_members values(?,?)',(rid,group))
  args=SimpleNamespace(sweep=sweep,seed_offset=n*100,state=state,root=root,bank=opts.bank.resolve(),external_profile=None)
  attempts.append(single(args,task,'standard',rep))
 result={**first,'run':dest.name,'arm':'matched','passed':any(r['passed'] for r in attempts),'attempts':len(attempts),'failure_tag':None if any(r['passed'] for r in attempts) else 'REASONING','error':None}
 for key in ['calls','input_tokens','output_tokens','cost_usd','seconds','steps','tool_calls','tool_errors','compactions']:result[key]=sum(r.get(key,0) for r in attempts)
 dest.mkdir(parents=True,exist_ok=True);tmp=dest/'result.tmp';tmp.write_text(json.dumps(result));tmp.rename(dest/'result.json')

with concurrent.futures.ThreadPoolExecutor(max_workers=opts.workers) as pool:list(pool.map(run_control,primary))
print('Matched-budget control completed; use aggregate summarizer.')
