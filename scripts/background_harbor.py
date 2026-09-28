import json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
config=Path(sys.argv[1]).resolve();name=json.loads(config.read_text())['job_name']
with (root/'.local'/f'{name}.log').open('ab') as log:
 p=subprocess.Popen([str(root/'venv/bin/harbor'),'run','-c',str(config)],cwd=root,env={**os.environ,'PYTHONPATH':str(root)},stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
(root/'.local'/f'{name}.pid').write_text(str(p.pid));print('Started Harbor job',name,'PID',p.pid)
