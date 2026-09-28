"""Prepare a Harbor job from a frozen private selection; never print task content."""
import argparse,json,random,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--lock',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--name',required=True);p.add_argument('--arms',nargs='+',default=['standard','autonomy']);p.add_argument('--oracle',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parent.parent;lock=json.loads(args.lock.read_text())
commit=subprocess.check_output(['git','-C',str(args.dataset),'rev-parse','HEAD'],text=True).strip()
assert commit==lock['commit'],'Terminal-Bench revision differs from freeze'
agents=[{'name':'oracle'}] if args.oracle else [{'import_path':'scripts.harbor_dsh:DSHAgent','model_name':'openrouter/qwen/qwen3-8b','override_timeout_sec':450,'kwargs':{'arm':a,'rep':r}} for r in range(5) for a in args.arms]
random.Random(9282026).shuffle(agents)
config={'job_name':args.name,'jobs_dir':str(root/'.local/harbor-jobs'),'n_attempts':1,'n_concurrent_trials':1,'agents':agents,'datasets':[{'path':str(args.dataset.resolve()),'task_names':lock['tasks']}],'environment':{'type':'docker','delete':True},'retry':{'max_retries':0},'quiet':True}
out=root/'.local'/f'{args.name}.json';out.write_text(json.dumps(config,indent=2)+'\n');print(out)
