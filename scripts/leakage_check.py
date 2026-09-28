"""Check candidate text against dev-only task-specific paths and answer strings.

This tool never reads held-out or transfer task records. Bank exports supplied here
must already contain dev records only. Report only overlaps, never expected answers.
"""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('profile',type=Path);p.add_argument('dev_export',type=Path);args=p.parse_args()
tasks=json.loads(args.dev_export.read_text());assert all(t['split']=='dev' for t in tasks)
text='\n'.join(p.read_text() for p in args.profile.rglob('*') if p.is_file())
violations=[]
for t in tasks:
 strings=set(t['files'])
 strings.update(re.findall(r'\b[a-z2-9]{12}\b',' '.join(x['prompt'] for x in t['turns'])))
 for s in strings:
  if len(s)>=5 and s in text:violations.append({'task':t['id'],'kind':'task-specific path or identifier overlap'})
print(json.dumps({'passed':not violations,'violations':violations,'note':'Automatic string screen plus a separate semantic review is required.'},indent=2))
raise SystemExit(bool(violations))
