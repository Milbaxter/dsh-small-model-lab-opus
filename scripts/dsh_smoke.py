import json, os
from pathlib import Path
from deepseek_harness import DeepSeekHarness
base=Path('/opt/dsh-small-model-lab-opus')
work=base/'smoke-work';work.mkdir(exist_ok=True)
patch=[{'id':'session-log-deepseek','config':{'enabled':False}}, {'insert':[{'id':'llm-pi-ai','name':'@deepseek-ai/dsh-llm-pi-ai','config':{'providers':{'lab-openrouter':{'api':'openai-completions','apiKeyEnv':'LAB_RUN_KEY','baseURL':'http://127.0.0.1:18943/v1','compat':{'supportsDeveloperRole':False,'maxTokensField':'max_tokens'},'models':[{'id':'qwen/qwen3-8b','contextWindow':32768,'maxTokens':2048}],'retryPolicy':{'mode':'normal','maxRetries':0}}}}}]}]
p=base/'smoke-patch.json';p.write_text(json.dumps(patch))
with DeepSeekHarness(provider='lab-openrouter',model='qwen/qwen3-8b',max_tokens=1024,cwd=str(work),dsh_home=str(base/'smoke-home'),profile='sdk-minimal',patches=(str(p),),env={'LAB_RUN_KEY':'p0-smoke','DSH_TELEMETRY_DISABLED':'1'},request_timeout_seconds=120) as h:
 r=h.run('Use bash to write the text dsh-tool-ok to probe.txt, then read it back. /no_think',session_id='p0-tool')
 print(r.final_response);print('finish_reason:',r.finish_reason)
 print('artifact verified:',(work/'probe.txt').exists() and (work/'probe.txt').read_text().strip()=='dsh-tool-ok')
