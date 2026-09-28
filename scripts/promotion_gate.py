"""Explicit all-or-nothing promotion; unavailable evidence never counts as passing."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);args=p.parse_args();e=json.loads(args.evidence.read_text())
def positive_ci(item):
 # Repeated binary trials have much coarser resolution; floating-point dust is not uplift.
 return item is not None and item.get('complete_k5',False) and item.get('ci95') is not None and item['ci95'][0]>1e-12
checks={
 'dev_improves':positive_ci(e.get('dev')),
 'heldout_ci_above_zero':positive_ci(e.get('heldout')),
 'transfer_no_regression':bool(e.get('transfer',{}).get('complete_k5') and e['transfer'].get('difference',-1)>=0),
 'second_model_no_regression':bool(e.get('second_model',{}).get('complete_k5') and e['second_model'].get('difference',-1)>=0),
 'matched_budget_control':positive_ci(e.get('matched_control')) and e['matched_control'].get('control_complete') is True,
 'tokens_per_solve_limit':isinstance(e.get('tokens_per_solve_ratio'),(int,float)) and e['tokens_per_solve_ratio']<=1.25,
 'leakage_check':e.get('leakage_passed') is True,
 'terminal_bench_no_regression':bool(e.get('terminal_bench',{}).get('complete_k5') and e['terminal_bench'].get('difference',-1)>=0),
}
print(json.dumps({'promote':all(checks.values()),'gates':checks,'decision':'promote' if all(checks.values()) else 'reject or insufficient evidence'},indent=2))
