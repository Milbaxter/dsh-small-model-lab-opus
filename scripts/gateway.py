#!/usr/bin/env python3
"""Credential boundary, fixed sampling, per-run budgets and durable cost accounting."""
import hashlib, re, http.server, json, os, sqlite3, threading, time, urllib.request, urllib.error
from pathlib import Path
BASE=Path(os.environ.get('LAB_STATE','.local')); BASE.mkdir(parents=True,exist_ok=True)
DB=BASE/'spend.sqlite'; LOCK=threading.Lock()
CAP=18.0 # Stop well before the user's $20 cap, including preflight and uncertainty.
MODEL='qwen/qwen3-8b'

def connection():
 c=sqlite3.connect(DB);c.execute('create table if not exists calls (id integer primary key, run text, started real, state text, reserve real, cost real, input int, output int, response_id text)');return c

def reserve(run):
 with LOCK, connection() as c:
  total=c.execute("select coalesce(sum(case when state='done' then cost else reserve end),0) from calls").fetchone()[0]
  count,tokens=c.execute('select count(*),coalesce(sum(input+output),0) from calls where run=?',(run,)).fetchone()
  if total+.04>CAP or count>=20 or tokens>=100000:raise ValueError('BUDGET_LIMIT')
  return c.execute('insert into calls(run,started,state,reserve) values(?,?,?,?)',(run,time.time(),'pending',.04)).lastrowid

class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,status,data):
  b=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_POST(self):
  run=self.headers.get('Authorization','').removeprefix('Bearer ')
  if not re.fullmatch(r'[a-zA-Z0-9_-]{1,150}',run):return self.send(401,{'error':{'message':'missing run token'}})
  try:
   body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
   if body.get('model')!=MODEL:raise ValueError('MODEL_NOT_ALLOWED')
   body.update(provider={'only':['alibaba'],'allow_fallbacks':False},temperature=.6,top_p=.95,reasoning={'enabled':False},stream=False,max_tokens=min(body.get('max_tokens',2048),2048))
   body.pop('stream_options',None);body.pop('max_completion_tokens',None)
   body['seed']=928000+(int(run.rsplit('-',1)[-1]) if run.rsplit('-',1)[-1].isdigit() else 0)
   # Per-request worst-case reservation exceeds this request's upper cost bound.
   if len(json.dumps(body))>220000:raise ValueError('CONTEXT_BUDGET')
   ident=reserve(run)
   req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY'],'Content-Type':'application/json'})
   try:
    with urllib.request.urlopen(req,timeout=100) as r:result=json.load(r);status=r.status
   except urllib.error.HTTPError as e:result=json.loads(e.read());status=e.code
   usage=result.get('usage',{});cost=usage.get('cost')
   with LOCK,connection() as c:
    c.execute('update calls set state=?,cost=?,input=?,output=?,response_id=? where id=?',('done' if cost is not None else 'unknown',cost,usage.get('prompt_tokens',0),usage.get('completion_tokens',0),result.get('id'),ident))
   trace=BASE/'wire'/run;trace.mkdir(parents=True,exist_ok=True)
   (trace/f'{ident}.json').write_text(json.dumps({'request':body,'response':result,'status':status}))
   if body.get('stream') is False and self.headers.get('x-unused') is None:
    # DSH requests streaming: synthesize the standard SSE wire from the completed response.
    if status!=200:return self.send(status,result)
    self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
    msg=result['choices'][0]['message'];delta={k:v for k,v in msg.items() if k in ('role','content','reasoning_content','tool_calls')}
    for i,t in enumerate(delta.get('tool_calls',[])):t['index']=i
    chunk={'id':result['id'],'object':'chat.completion.chunk','created':result.get('created',int(time.time())),'model':MODEL,'choices':[{'index':0,'delta':delta,'finish_reason':None}]}
    self.wfile.write(('data: '+json.dumps(chunk)+'\n\n').encode())
    chunk['choices']=[{'index':0,'delta':{},'finish_reason':result['choices'][0].get('finish_reason','stop')}];chunk['usage']=usage
    self.wfile.write(('data: '+json.dumps(chunk)+'\n\ndata: [DONE]\n\n').encode());self.wfile.flush()
  except Exception as e:
   self.send(429 if str(e)=='BUDGET_LIMIT' else 502,{'error':{'message':str(e),'type':'lab_gateway'}})

if __name__=='__main__':
 connection().close();http.server.ThreadingHTTPServer((os.environ.get('GATEWAY_BIND','127.0.0.1'),int(os.environ.get('GATEWAY_PORT','18943'))),Handler).serve_forever()
