#!/usr/bin/env python3
"""Aggregate-only hidden-split reporting and paired task bootstrap."""
import argparse, collections, json, random, statistics
from pathlib import Path

def bootstrap(values):
 rng=random.Random(9282026)
 if not values:return None
 values=sorted(values) # The seeded CI must not depend on filesystem traversal order.
 draws=sorted(sum(rng.choices(values,k=len(values)))/len(values) for _ in range(10000))
 return [draws[249],draws[9749]]

def main():
 p=argparse.ArgumentParser();p.add_argument('--state',type=Path,default=Path('.local'));p.add_argument('--sweep',required=True);p.add_argument('--include-sweep',action='append',default=[]);p.add_argument('--control',default='standard');p.add_argument('--dev-details',action='store_true');args=p.parse_args()
 files={f for sweep in [args.sweep,*args.include_sweep] for f in (args.state/'runs').glob(sweep+'-*/result.json')}
 rows=[json.loads(f.read_text()) for f in sorted(files)]
 summary={'sweep':args.sweep,'runs':len(rows),'cost_usd':sum(r['cost_usd'] for r in rows),'arms':{},'paired':{}}
 if args.include_sweep:summary.update(included_sweeps=args.include_sweep,cost_note='Analytical run-cost sum may reuse primary attempts in matched controls. Use the gateway ledger for actual experiment spend.')
 for arm in sorted({r['arm'] for r in rows}):
  summary['arms'][arm]={}
  for split in sorted({r['split'] for r in rows}):
   rr=[r for r in rows if r['arm']==arm and r['split']==split]
   if not rr:continue
   groups=collections.defaultdict(list)
   for r in rr:groups[r['task']].append(int(r['passed']))
   rates=[sum(v)/len(v) for v in groups.values()]
   solved=sum(r['passed'] for r in rr);tok=sum(r['input_tokens']+r['output_tokens'] for r in rr)
   summary['arms'][arm][split]={'runs':len(rr),'tasks':len(groups),'repetitions':sorted(set(len(v) for v in groups.values())),'passed':solved,'pass_rate':solved/len(rr),'task_bootstrap_ci':bootstrap(rates),'tokens':tok,'tokens_per_solve':tok/solved if solved else None,'cost_usd':sum(r['cost_usd'] for r in rr),'mean_seconds':statistics.mean(r['seconds'] for r in rr),'mean_calls':statistics.mean(r['calls'] for r in rr),'compactions':sum(r.get('compactions',0) for r in rr),'tool_errors':sum(r.get('tool_errors',0) for r in rr),'failures':dict(collections.Counter(r['failure_tag'] for r in rr if not r['passed'])),'families':{f:{'n':sum(r['family']==f for r in rr),'passed':sum(r['passed'] for r in rr if r['family']==f)} for f in sorted({r['family'] for r in rr})}}
   if arm!=args.control:
    ctrl={(r['task'],r['rep']):r for r in rows if r['arm']==args.control and r['split']==split}
    pairs=collections.defaultdict(list)
    for r in rr:
     b=ctrl.get((r['task'],r['rep']))
     if b:pairs[r['task']].append(int(r['passed'])-int(b['passed']))
    diffs=[sum(v)/len(v) for v in pairs.values()]
    summary['paired'][arm+'/'+split]={'paired_tasks':len(diffs),'paired_runs':sum(map(len,pairs.values())),'difference':statistics.mean(diffs) if diffs else None,'ci95':bootstrap(diffs)}
 if args.dev_details:summary['dev_runs']=[r for r in rows if r['split']=='dev']
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
