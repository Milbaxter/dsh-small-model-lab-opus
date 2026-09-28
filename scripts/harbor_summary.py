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
 actor_status='missing_actor_record'
 for af in f.parent.rglob('dsh-result.json'):
  for line in af.read_text().splitlines():
   try:actor=json.loads(line)
   except Exception:actor_status='invalid_actor_json';continue
   err=actor.get('error') or json.dumps([e for e in actor.get('events',[]) if e.get('type')=='turn/end'])
   actor_status='budget_stop' if 'BUDGET_LIMIT' in err else 'provider_rate_limit' if 'RATE_LIMIT' in err else 'actor_error' if not actor.get('ok') or actor.get('finish')=='error' else 'normal_finish'
 rows.append({'arm':a,'rep':rep,'task':str(task),'passed':float(reward),'error':bool(d.get('exception_info')),'actor_status':actor_status,'tokens':(ctx.get('n_input_tokens') or 0)+(ctx.get('n_output_tokens') or 0),'cost':ctx.get('cost_usd') or 0})
for arm in sorted({r['arm'] for r in rows}):
 rr=[r for r in rows if r['arm']==arm];group=collections.defaultdict(list)
 for r in rr:group[r['task']].append(r['passed'])
 rates=[sum(v)/len(v) for v in group.values()]
 output['arms'][arm]={'runs':len(rr),'tasks':len(group),'repetitions':sorted(set(len(v) for v in group.values())),'complete_k5':len(group)==4 and all(len(v)==5 for v in group.values()),'pass_rate':sum(r['passed'] for r in rr)/len(rr),'ci95':bootstrap(rates),'errors':sum(r['error'] for r in rr),'actor_finishes':dict(collections.Counter(r['actor_status'] for r in rr)),'cost_usd':sum(r['cost'] for r in rr),'tokens':sum(r['tokens'] for r in rr)}
 if arm!='standard':
  control={(r['task'],r['rep']):r for r in rows if r['arm']=='standard'};pairs=collections.defaultdict(list)
  for r in rr:
   b=control.get((r['task'],r['rep']))
   if b:pairs[r['task']].append(r['passed']-b['passed'])
  diffs=[sum(v)/len(v) for v in pairs.values()]
  if diffs:output['paired'][arm]={'tasks':len(diffs),'paired_runs':sum(map(len,pairs.values())),'complete_k5':len(diffs)==4 and all(len(v)==5 for v in pairs.values()),'difference':sum(diffs)/len(diffs),'ci95':bootstrap(diffs)}
print(json.dumps(output,indent=2))
