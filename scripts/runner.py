#!/usr/bin/env python3
"""Interleaved, resumable private-bank evaluator. Public reports are aggregate only."""
import argparse, concurrent.futures, hashlib, json, os, random, selectors, shutil, sqlite3, subprocess, time
from pathlib import Path

def receive(proc, seconds=170):
 sel=selectors.DefaultSelector();sel.register(proc.stdout,selectors.EVENT_READ)
 try:
  if not sel.select(seconds):raise TimeoutError('actor response deadline')
  line=proc.stdout.readline()
  if not line:raise RuntimeError('actor exited before response')
  return json.loads(line)
 finally:sel.close()

def metrics(db,run):
 with sqlite3.connect(db) as c:
  r=c.execute('select count(*),coalesce(sum(input),0),coalesce(sum(output),0),coalesce(sum(case when state="done" then cost else reserve end),0) from calls where run=?',(run,)).fetchone()
 return dict(zip(['calls','input_tokens','output_tokens','cost_usd'],r))

def single(args,task,arm,rep):
 run=f'{args.sweep}-{task["id"]}-{arm}-{rep}'
 dest=args.state/'runs'/run
 if (dest/'result.json').exists():return json.loads((dest/'result.json').read_text())
 if dest.exists():
  dest.rename(dest.with_name(dest.name+'-interrupted-'+str(time.time_ns())))
 dest.mkdir(parents=True,exist_ok=True);work=dest/'workspace';home=dest/'home';work.mkdir(exist_ok=True);home.mkdir(exist_ok=True)
 for name,content in task['files'].items():
  p=work/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
 os.chown(work,1000,1000);os.chown(home,1000,1000)
 for p in work.rglob('*'):os.chown(p,1000,1000)
 profile=args.external_profile if arm=='external' else args.root/'profiles'/arm
 command=['docker','run','--rm','-i','--name',run,'--cpus','1.5','--memory','768m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only','--tmpfs','/tmp:rw,nosuid,size=128m','-v',f'{work}:/workspace','-v',f'{home}:/home/lab','-v',f'{profile}:/profile:ro','-e',f'LAB_ARM={arm}','-e',f'LAB_RUN_KEY={run}','-e','LAB_GATEWAY=http://172.17.0.1:18943/v1','dsh-opus:0.1.5rc1']
 start=time.time();events=[];error=None
 with (dest/'stderr.log').open('w') as err:
  proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
  try:
   for turn in task['turns']:
    if time.time()-start>task['budget']['seconds']:raise TimeoutError('run wall deadline')
    proc.stdin.write(json.dumps(turn)+'\n');proc.stdin.flush();reply=receive(proc);events.append(reply)
    if not reply['ok'] or reply.get('finish')=='error':raise RuntimeError(reply.get('error') or json.dumps(reply.get('events',[])[-1:]))
   proc.stdin.close();proc.wait(timeout=10)
  except Exception as e:error=str(e)
  finally:
   subprocess.run(['docker','rm','-f',run],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   if proc.poll() is None:proc.kill();proc.wait()
 (dest/'events.json').write_text(json.dumps(events,default=str))
 private=dest/'grading.json';private.write_text(json.dumps(task))
 gradecmd=['docker','run','--rm','--network','none','--cpus','1.5','--memory','768m','--pids-limit','64','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only','--tmpfs','/tmp:size=64m','--entrypoint','python','-v',f'{work}:/workspace:ro','-v',f'{private}:/grading.json:ro','-v',f'{args.bank.parent / "grader.py"}:/grader.py:ro','dsh-opus:0.1.5rc1','/grader.py','/grading.json','/workspace']
 try:
  grade=subprocess.run(gradecmd,capture_output=True,text=True,timeout=15);passed=json.loads(grade.stdout)['passed'] if grade.returncode==0 else False
 except Exception:passed=False
 m=metrics(args.state/'spend.sqlite',run)
 tag=None if passed else ('TIMEOUT' if error and 'deadline' in error else 'MAX_TURNS' if error and 'BUDGET_LIMIT' in error else 'INFRA' if error else 'REASONING')
 flat=[e for turn in events for e in turn.get('events',[])]
 tool_calls=[e for e in flat if e.get('type')=='tool/call']
 extra={'tool_calls':len(tool_calls),'steps':sum(e.get('type')=='step/start' for e in flat),'compactions':sum(e.get('type')=='compaction/summary' for e in flat),'tool_errors':sum('isError' in str(e) and "'isError': True" in str(e) for e in flat if e.get('type')=='tool/result')}
 result={'run':run,'task':task['id'],'family':task['family'],'split':task['split'],'arm':arm,'rep':rep,'passed':passed,'failure_tag':tag,'error':error,'seconds':time.time()-start,**m,**extra}
 text=json.dumps(result);temp=dest/'result.tmp';temp.write_text(text);temp.rename(dest/'result.json')
 # IDs are private logs; aggregate summarizer is the only proposer interface for hidden splits.
 print(json.dumps({'completed':run,'passed':passed,'cost':m['cost_usd'],'error':error and error[:200]}),flush=True)
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--bank',type=Path,required=True);ap.add_argument('--sweep',required=True);ap.add_argument('--arms',nargs='+',default=['sdk-minimal','standard','autonomy']);ap.add_argument('--split',nargs='+',default=['dev','held-out','transfer']);ap.add_argument('--k',type=int,default=5);ap.add_argument('--limit',type=int);ap.add_argument('--per-family',type=int);ap.add_argument('--workers',type=int,default=2);ap.add_argument('--external-profile',type=Path)
 args=ap.parse_args();args.root=Path(__file__).resolve().parent.parent;args.state=args.root/'.local';args.state.mkdir(exist_ok=True);args.bank=args.bank.resolve()
 bank=json.loads(args.bank.read_text());tasks=[t for t in bank if t['split'] in args.split]
 if args.per_family:
  counts={}
  tasks=[t for t in tasks if counts.setdefault(t['family'],0)<args.per_family and not counts.update({t['family']:counts[t['family']]+1})]
 if args.limit:tasks=tasks[:args.limit]
 if 'external' in args.arms and args.external_profile is None:ap.error('--external-profile is required')
 jobs=[];rng=random.Random(20260928)
 # Each task/repetition is a block. Arms randomized within blocks, in the same time window.
 for rep in range(args.k):
  order=list(tasks);rng.shuffle(order)
  for task in order:
   arms=list(args.arms);rng.shuffle(arms)
   jobs.extend((task,a,rep) for a in arms)
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
  pending=[]
  for task,arm,rep in jobs:
   with sqlite3.connect(args.state/'spend.sqlite') as c:
    spend=c.execute('select coalesce(sum(case when state="done" then cost else reserve end),0) from calls').fetchone()[0]
   if spend>=17.75:print('STOP: approaching budget cap',flush=True);break
   pending.append(pool.submit(single,args,task,arm,rep))
   if len(pending)>=args.workers:
    pending.pop(0).result()
  for future in pending:future.result()

if __name__=='__main__':main()
