"""Aggregate ledger and wire-metadata audit; never publish prompts or task IDs."""
import argparse,collections,datetime,json,sqlite3,time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--state',type=Path,default=Path('.local'));p.add_argument('--workflow-start',type=float);args=p.parse_args()
mapping={}
for f in (args.state/'runs').glob('*/result.json'):
 r=json.loads(f.read_text());run=r['run'];suffix='-'+r['task']+'-'+r['arm']+'-'+run.rsplit('-',1)[-1]
 if run.endswith(suffix):mapping[run]=run[:-len(suffix)]
for job in (args.state/'harbor-jobs').glob('*'):
 for f in job.glob('*/result.json'):
  r=json.loads(f.read_text());meta=(r.get('agent_result') or {}).get('metadata') or {}
  if meta.get('gateway_run'):mapping[meta['gateway_run']]='terminal-bench/'+job.name
groups=collections.defaultdict(lambda:{'calls':0,'confirmed_usd':0,'unresolved_reserve_usd':0,'input_tokens':0,'output_tokens':0,'states':collections.Counter()})
with sqlite3.connect(args.state/'spend.sqlite') as c:
 for run,state,reserve,cost,inp,out in c.execute('select run,state,reserve,cost,input,output from calls'):
  label=mapping.get(run,'terminal-bench/unmapped' if run.startswith('tb-') else 'setup-or-unfinished')
  g=groups[label];g['calls']+=1;g['confirmed_usd']+=cost or 0;g['unresolved_reserve_usd']+=reserve if state!='done' else 0;g['input_tokens']+=inp or 0;g['output_tokens']+=out or 0;g['states'][state]+=1
 for g in groups.values():g['conservative_usd']=g['confirmed_usd']+g['unresolved_reserve_usd']
audit={'recorded_requests':0,'request_pin_violations':0,'successful_response_models':collections.Counter(),'successful_response_providers':collections.Counter(),'http_statuses':collections.Counter()}
for f in (args.state/'wire').glob('*/*.json'):
 d=json.loads(f.read_text());q=d['request'];r=d['response'];status=d['status'];audit['recorded_requests']+=1;audit['http_statuses'][status]+=1
 valid=q.get('model')=='qwen/qwen3-8b' and q.get('provider')=={'only':['alibaba'],'allow_fallbacks':False} and q.get('temperature')==.6 and q.get('top_p')==.95 and q.get('reasoning')=={'enabled':False} and q.get('max_tokens',99999)<=2048
 audit['request_pin_violations']+=not valid
 if status==200:
  audit['successful_response_models'][r.get('model','unreported')]+=1
  audit['successful_response_providers'][r.get('provider','unreported')]+=1
direct=0.000028886 # Native tool-calling preflight, outside the accounting gateway.
confirmed=sum(g['confirmed_usd'] for g in groups.values())+direct
conservative=sum(g['conservative_usd'] for g in groups.values())+direct
now=time.time()
result={'generated_at_utc':datetime.datetime.fromtimestamp(now,datetime.timezone.utc).isoformat(),'direct_preflight_usd':direct,'confirmed_total_usd':confirmed,'conservative_total_usd':conservative,'sweeps':dict(sorted(groups.items())),'wire_audit':audit}
if args.workflow_start:result.update(workflow_start_utc=datetime.datetime.fromtimestamp(args.workflow_start,datetime.timezone.utc).isoformat(),wall_clock_seconds=now-args.workflow_start)
print(json.dumps(result,indent=2))
