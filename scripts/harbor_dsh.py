"""Harbor adapter that runs the same DSH SDK/profile in official task containers."""
import hashlib,json,os,shlex,sqlite3,tempfile
from pathlib import Path
from harbor.agents.base import BaseAgent
from harbor.models.agent.context import AgentContext
ROOT=Path(__file__).resolve().parent.parent

class DSHAgent(BaseAgent):
 def __init__(self,*args,arm='standard',rep=0,**kwargs):
  super().__init__(*args,**kwargs);self.arm=arm;self.rep=int(rep)
 @staticmethod
 def name():return 'dsh-small-model-lab'
 def version(self):return '0.1.5rc1'
 async def setup(self,environment):
  result=await environment.exec('python3 -m venv /opt/dsh-lab-venv || (apt-get update -qq && apt-get install -y -qq python3 python3-venv && python3 -m venv /opt/dsh-lab-venv); /opt/dsh-lab-venv/bin/pip install --disable-pip-version-check -q deepseek-harness-sdk==0.1.5rc1',timeout_sec=300)
  if result.return_code:raise RuntimeError('DSH setup failed: '+(result.stderr or '')[-1000:])
  await environment.upload_file(ROOT/'scripts/actor.py','/opt/dsh-lab-actor.py')
  await environment.upload_dir(ROOT/'profiles'/self.arm,'/profile')
 async def run(self,instruction,environment,context:AgentContext):
  rid='tb-'+self.arm+'-'+hashlib.sha256(str(self.logs_dir).encode()).hexdigest()[:16]+'-'+str(self.rep)
  pwd=await environment.exec('pwd',timeout_sec=10)
  with tempfile.TemporaryDirectory() as d:
   payload=Path(d)/'request.json';payload.write_text(json.dumps({'prompt':instruction,'session':'benchmark'})+'\n')
   await environment.upload_file(payload,'/opt/dsh-lab-request.json')
  result=await environment.exec('/opt/dsh-lab-venv/bin/python -u /opt/dsh-lab-actor.py < /opt/dsh-lab-request.json > /tmp/dsh-agent-result.json',env={'LAB_ARM':self.arm,'LAB_RUN_KEY':rid,'LAB_GATEWAY':'http://172.17.0.1:18943/v1','LAB_HOME':'/tmp/dsh-lab-home','LAB_WORKSPACE':pwd.stdout.strip(),'DSH_TELEMETRY_DISABLED':'1'},timeout_sec=450)
  await environment.download_file('/tmp/dsh-agent-result.json',self.logs_dir/'dsh-result.json')
  with sqlite3.connect(ROOT/'.local/spend.sqlite') as c:
   row=c.execute('select coalesce(sum(input),0),coalesce(sum(output),0),coalesce(sum(case when state="done" then cost else reserve end),0) from calls where run=?',(rid,)).fetchone()
  context.n_input_tokens=row[0];context.n_output_tokens=row[1];context.cost_usd=row[2]
  context.metadata={'profile':self.arm,'rep':self.rep,'gateway_run':rid,'exit_code':result.return_code}
