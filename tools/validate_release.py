from pathlib import Path
import hashlib,json,sys,subprocess
root=Path(__file__).resolve().parents[1];m=json.loads((root/'manifest.json').read_text(encoding='utf-8'));errors=[]
for row in m['files']:
 p=root/row['path']
 if not p.is_file():errors.append('Missing: '+row['path']);continue
 b=p.read_bytes()
 if len(b)!=row['size']or hashlib.sha512(b).hexdigest()!=row['sha512']:errors.append('Stale checksum: '+row['path'])
lock=json.loads((root/'mods-lock.json').read_text(encoding='utf-8'));indexed={row['file']['filename']:row for row in lock.values()}
for mod in m['mods']:
 f=indexed.get(mod['filename'],{}).get('file',{})
 if f.get('hashes',{}).get('sha512')!=mod['sha512']or f.get('size')!=mod['size']:errors.append('Inconsistent mod lock: '+mod['filename'])
info=json.loads((root/'pack-info.json').read_text(encoding='utf-8'))
if info['packVersion']!=m['packVersion']:errors.append('Pack version mismatch')
if (root/'.git').exists():
 tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0'))
 for row in m['files']:
  if row['path']not in tracked:errors.append('Manifest file is not tracked in Git: '+row['path'])
if errors:print('\n'.join(errors));sys.exit(1)
print('PASS release '+m['packVersion']+': '+str(len(m['files']))+' file checksums and '+str(len(m['mods']))+' locked mods')
