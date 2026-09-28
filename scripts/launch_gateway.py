import os,subprocess
from pathlib import Path
base=Path(__file__).resolve().parent.parent
os.chdir(base)
for l in (base/'.env').read_text().splitlines():
 if l.startswith('OPENROUTER_API_KEY='):os.environ['OPENROUTER_API_KEY']=l.split('=',1)[1].strip().strip('\"\'')
os.environ['GATEWAY_BIND']='172.17.0.1'
with (base/'gateway.log').open('ab') as log:
 p=subprocess.Popen(['python3',str(base/'scripts/gateway.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
(base/'.local/gateway.pid').write_text(str(p.pid))
print('Gateway PID:',p.pid)
