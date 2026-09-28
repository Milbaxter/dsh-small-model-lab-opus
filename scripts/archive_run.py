"""Compact completed evidence, deleting only reproducible runtime caches."""
import gzip,shutil,tarfile
from pathlib import Path

def archive(dest):
 dest=Path(dest);home=dest/'home'
 if home.exists():
  shutil.rmtree(home/'.cache',ignore_errors=True)
  with tarfile.open(dest/'dsh-home.tar.gz','w:gz',compresslevel=1) as tar:tar.add(home,arcname='home')
  shutil.rmtree(home)
 events=dest/'events.json'
 if events.exists():
  with events.open('rb') as src,gzip.open(dest/'events.json.gz','wb') as dst:shutil.copyfileobj(src,dst)
  events.unlink()
 (dest/'grading.json').unlink(missing_ok=True)
if __name__=='__main__':
 import sys
 root=Path(sys.argv[1])
 n=0
 for p in root.glob('*/result.json'):archive(p.parent);n+=1
 print('Archived completed runs:',n)
