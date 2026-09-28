"""Start a resumable sweep with detached logs; invoke runner arguments after --."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
args=sys.argv[1:];name=args[args.index('--sweep')+1]
state=root/'.local';state.mkdir(exist_ok=True)
pidfile=state/(name+'.pid')
try:
 old=int(pidfile.read_text());command=Path(f'/proc/{old}/cmdline').read_bytes().split(b'\0')
 if str(root/'scripts/runner.py').encode() in command and b'--sweep' in command and command[command.index(b'--sweep')+1]==name.encode():
  print('Already running',name,'PID',old);raise SystemExit(0)
except (OSError,ValueError,IndexError):pass
with (state/(name+'.log')).open('ab') as log:
 p=subprocess.Popen(['python3',str(root/'scripts/runner.py'),*args],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
pidfile.write_text(str(p.pid));print('Started',name,'PID',p.pid)
