"""Display a one-command result and return nonzero for SDK/budget errors."""
import json,sys

seen=False
for line in sys.stdin:
 if not line.strip():continue
 seen=True
 result=json.loads(line)
 if result.get('final'):print(result['final'])
 if not result.get('ok') or result.get('finish')=='error':
  errors=[e.get('data',{}).get('reason',{}).get('error',{}).get('message') for e in result.get('events',[]) if e.get('type')=='turn/end']
  print(result.get('error') or next((e for e in errors if e),'DSH stopped with an error.'),file=sys.stderr)
  raise SystemExit(1)
if not seen:
 print('DSH returned no result.',file=sys.stderr)
 raise SystemExit(1)
