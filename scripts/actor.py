"""Generic SDK driver; receives only the current visible user message via stdin."""
import json, os, sys, traceback
from pathlib import Path
from deepseek_harness import DeepSeekHarness
arm=os.environ.get('LAB_ARM','standard')
home=Path(os.environ.get('LAB_HOME','/home/lab'));home.mkdir(parents=True,exist_ok=True)
workspace=os.environ.get('LAB_WORKSPACE','/workspace')
provider={'api':'openai-completions','apiKeyEnv':'LAB_RUN_KEY','baseURL':os.environ['LAB_GATEWAY'],'compat':{'supportsDeveloperRole':False,'maxTokensField':'max_tokens'},'models':[{'id':'qwen/qwen3-8b','contextWindow':32768,'maxTokens':2048}],'retryPolicy':{'mode':'normal','maxRetries':0}}
llm={'id':'llm-pi-ai','name':'@deepseek-ai/dsh-llm-pi-ai','config':{'providers':{'lab-openrouter':provider}}}
patch=[{'id':'session-log-deepseek','config':{'enabled':False}}]
if arm=='sdk-minimal':patch.append({'insert':[llm]})
else:
 patch += [llm]
p=home/'provider.json';p.write_text(json.dumps(patch))
patches=[str(p)]
if Path('/profile/patch.json').exists():patches.append('/profile/patch.json')
try:
 with DeepSeekHarness(provider='lab-openrouter',model='qwen/qwen3-8b',max_tokens=2048,cwd=workspace,dsh_home=str(home/'dsh'),profile='sdk-minimal' if arm=='sdk-minimal' else 'sdk',patches=tuple(patches),env={'DSH_TELEMETRY_DISABLED':'1','DSH_PERMISSION_MODE':'danger-full-access'},initialize_timeout_seconds=60,request_timeout_seconds=150) as harness:
  for line in sys.stdin:
   request=json.loads(line)
   try:
    result=harness.run(request['prompt'],session_id=request['session'])
    print(json.dumps({'ok':True,'final':result.final_response,'finish':result.finish_reason,'events':result.events},default=str),flush=True)
   except Exception as e:
    print(json.dumps({'ok':False,'error':str(e)}),flush=True)
except Exception as e:
 print(json.dumps({'ok':False,'error':str(e)}),flush=True)
