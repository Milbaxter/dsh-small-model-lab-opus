"""Only aggregate benchmark results leave the private Harbor job directory."""
import argparse,collections,json
from pathlib import Path
from summarize import bootstrap
p=argparse.ArgumentParser();p.add_argument('job',type=Path);args=p.parse_args()
job=json.loads((args.job/'result.json').read_text());s=job['stats']
output={'job':args.job.name,'complete':job.get('finished_at') is not None,'counts':{k:s[k] for k in ['n_completed_trials','n_errored_trials','n_running_trials','n_pending_trials']},'arms':{},'paired':{}}
rows=[]
for f in args.job.glob('*/result.json'):
 d=json.loads(f.read_text());
 if d.get('verifier_result') is None and not d.get('exception_info'):continue
 cfg=d.get('config',{});agent=cfg.get('agent',{});kw=agent.get('kwargs',{});a=kw.get('arm',agent.get('name','unknown'));rep=kw.get('rep',0)
 reward=(d.get('verifier_result') or {}).get('rewards',{});reward=reward.get('reward',0) if reward else 0
 task=d.get('task_name') or (cfg.get('task') or {}).get('path','')
 ctx=d.get('agent_result') or {}
 rows.append({'arm':a,'rep':rep,'task':str(task),'passed':float(reward),'error':bool(d.get('exception_info')),'tokens':(ctx.get('n_input_tokens') or 0)+(ctx.get('n_output_tokens') or 0),'cost':ctx.get('cost_usd') or 0})
for arm in sorted({r['arm'] for r in rows}):
 rr=[r for r in rows if r['arm']==arm];group=collections.defaultdict(list)
 for r in rr:group[r['task']].append(r['passed'])
 rates=[sum(v)/len(v) for v in group.values()]
 output['arms'][arm]={'runs':len(rr),'tasks':len(group),'pass_rate':sum(r['passed'] for r in rr)/len(rr),'ci95':bootstrap(rates),'errors':sum(r['error'] for r in rr),'cost_usd':sum(r['cost'] for r in rr),'tokens':sum(r['tokens'] for r in rr)}
 if arm!='standard':
  control={(r['task'],r['rep']):r for r in rows if r['arm']=='standard'};pairs=collections.defaultdict(list)
  for r in rr:
   b=control.get((r['task'],r['rep']))
   if b:pairs[r['task']].append(r['passed']-b['passed'])
  diffs=[sum(v)/len(v) for v in pairs.values()]
  if diffs:output['paired'][arm]={'tasks':len(diffs),'difference':sum(diffs)/len(diffs),'ci95':bootstrap(diffs)}
print(json.dumps(output,indent=2))
