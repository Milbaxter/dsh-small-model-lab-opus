"""Package the gate-selected profile without embedding provider credentials or tasks."""
import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--decision',required=True);p.add_argument('--output',type=Path);args=p.parse_args()
root=Path(__file__).resolve().parent.parent;source=root/'profiles'/args.profile;dest=args.output or root/'champion'
assert source.is_dir();dest.mkdir(exist_ok=True)
for f in source.iterdir():
 if f.is_file():shutil.copy2(f,dest/f.name)
patch=json.loads((source/'patch.json').read_text())
# Direct-run form mounts /profile. Installable form resolves local bundle paths.
package_name='@milbaxter/dsh-small-model-lab-champion'
installed=json.loads(json.dumps(patch).replace('file:///profile/',package_name+'/'))
(dest/'index.mjs').write_text('export const name = \'lab-champion-bundle\';\nexport function apply() {}\n')
exports={'.':'./index.mjs',**{'./'+f.name:'./'+f.name for f in source.glob('*.mjs')}}
(dest/'cordis.patch.yml').write_text(json.dumps(installed,indent=2)+'\n')
(dest/'package.json').write_text(json.dumps({'name':'@milbaxter/dsh-small-model-lab-champion','version':'0.1.0','type':'module','license':'MIT','main':'./index.mjs','exports':exports,'dsh':{'bundle':{'patch':'./cordis.patch.yml'}},'files':['*.json','*.mjs','*.yml','README.md','LICENSE']},indent=2)+'\n')
shutil.copy2(root/'LICENSE',dest/'LICENSE')
(dest/'selection.json').write_text(json.dumps({'profile':args.profile,'decision':args.decision,'runtime':'0.1.5rc1','model':'qwen/qwen3-8b'},indent=2)+'\n')
(dest/'README.md').write_text('# DSH champion profile\n\nSelected profile: `'+args.profile+'`. Decision: '+args.decision+'.\n\nInstall into an isolated, configured DSH SDK home:\n\n```sh\ndsh plugin --profile sdk add -w file:/absolute/path/champion\n```\n\nOr use the accompanying repository one-command runner:\n\n```sh\nscripts/run-champion.sh /absolute/workspace "Your task instruction"\n```\n\nThe run script needs the prepared Docker image and budget gateway described in the repository README. For cross-evaluation, mount this directory at `/profile` and apply `patch.json` after the standard SDK profile. The bundle does not change model, provider, sampling, permissions, or task instructions. See RESULTS.md for evidence and limitations.\n')
print(dest)
