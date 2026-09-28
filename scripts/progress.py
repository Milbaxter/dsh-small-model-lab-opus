"""Progress without hidden-split scores or task identities."""
import argparse,json,sqlite3,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--sweep',required=True);args=p.parse_args()
root=Path(__file__).resolve().parent.parent;state=root/'.local'
rows=[json.loads(f.read_text()) for f in (state/'runs').glob(args.sweep+'-*/result.json')]
with sqlite3.connect(state/'spend.sqlite') as c:
 total=c.execute('select count(*),coalesce(sum(cost),0),coalesce(sum(case when state="done" then cost else reserve end),0) from calls').fetchone()
 started=c.execute('select min(started) from calls where run like ?',(args.sweep+'-%',)).fetchone()[0]
print(json.dumps({'sweep':args.sweep,'completed':len(rows),'completed_by_arm':{a:sum(r['arm']==a for r in rows) for a in sorted({r['arm'] for r in rows})},'sweep_cost_usd':sum(r['cost_usd'] for r in rows),'global_calls':total[0],'global_confirmed_usd':total[1],'global_conservative_usd':total[2],'elapsed_minutes':(time.time()-started)/60 if started else None,'infra_failures':sum(r['failure_tag']=='INFRA' for r in rows)},indent=2))
