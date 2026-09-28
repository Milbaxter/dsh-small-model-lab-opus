"""Start a resumable sweep with detached logs; invoke runner arguments after --."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
args=sys.argv[1:];name=args[args.index('--sweep')+1]
state=root/'.local';state.mkdir(exist_ok=True)
with (state/(name+'.log')).open('ab') as log:
 p=subprocess.Popen(['python3',str(root/'scripts/runner.py'),*args],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
(state/(name+'.pid')).write_text(str(p.pid));print('Started',name,'PID',p.pid)
