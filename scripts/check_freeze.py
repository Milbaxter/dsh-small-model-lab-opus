"""Verify private task-bank content matches its public commit/hash lock."""
import hashlib,json,subprocess,sys
from pathlib import Path
bank=Path(sys.argv[1]).resolve();lock=json.loads(Path(sys.argv[2]).read_text())
commit=subprocess.check_output(['git','-C',str(bank),'rev-parse','HEAD'],text=True).strip()
assert commit==lock['task_bank_commit'],'Task bank commit changed'
for name,digest in lock['files'].items():
 assert hashlib.sha256((bank/name).read_bytes()).hexdigest()==digest,f'Frozen file changed: {name}'
print('Frozen task-bank commit and file hashes verified.')
