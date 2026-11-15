import sys,json,pathlib,uuid,hashlib,urllib.request,time,hmac,secrets,os,platform
import minecraft_launcher_lib
root=pathlib.Path(__file__).resolve().parent.parent
FORBIDDEN_JVM_PREFIXES=(
 '-javaagent','-agentlib','-agentpath','-xbootclasspath',
 '-xx:-disableattachmechanism','-xx:+startattachlistener',
 '-xx:onerror','-xx:onoutofmemoryerror','-djdk.instrument','-djava.security'
)
def emit(kind,**values):print(json.dumps({'type':kind,**values},ensure_ascii=False),flush=True)
def compute_hwid():
 raw='|'.join([
  platform.node() or '',
  platform.machine() or '',
  platform.processor() or '',
  os.environ.get('PROCESSOR_IDENTIFIER',''),
  os.environ.get('USERNAME',''),
  str(uuid.getnode())
 ])
 return hashlib.sha256(('eldoria-hwid-v1:'+raw).encode('utf-8')).hexdigest()[:24]
def load_allowed_mod_filenames(entries):
 allowed={'eldoria-skin-auth-2.0.0-neoforge-1.21.1.jar','eldoria-client-ui-1.0.1-neoforge-1.21.1.jar'}
 for r in entries:
  if r.get('side')!='server' and 'file' in r and 'filename' in r['file']:
   allowed.add(r['file']['filename'])
 manifest_file=root/'manifest.json'
 if manifest_file.is_file():
  try:
   m=json.loads(manifest_file.read_text(encoding='utf-8'))
   for f in m.get('files',[]):
    p=str(f.get('path',''))
    if p.startswith('mods/') and '/' not in p[5:]:
     allowed.add(p[5:])
   for mod in m.get('mods',[]):
    if mod.get('side')!='server' and mod.get('filename'):
     allowed.add(mod['filename'])
  except Exception:
   pass
 return allowed
def load_mod_entries():
 lock_file=root/'mods-lock.json'
 if lock_file.is_file():
  return list(json.loads(lock_file.read_text(encoding='utf-8')).values())
 manifest_file=root/'manifest.json'
 if manifest_file.is_file():
  manifest=json.loads(manifest_file.read_text(encoding='utf-8'))
  if isinstance(manifest.get('mods'),list):
   return [{'name':m['name'],'side':m.get('side','both'),'file':{'filename':m['filename'],'url':m['url'],'hashes':{'sha512':m['sha512']}}}for m in manifest['mods']]
 raise FileNotFoundError('Не найден mods-lock.json или manifest.json')
try:
 settings=json.load(sys.stdin);full=sys.argv[1]=='verify'
 entries=load_mod_entries()
 mods_dir=root/'mods'
 mods_dir.mkdir(parents=True,exist_ok=True)
 allowed_filenames=load_allowed_mod_filenames(entries)
 emit('status',text='Проверка защиты Eldoria Guard и модов…')
 for r in entries:
  if r['side']=='server':continue
  f=r['file'];fname=f['filename'];allowed_filenames.add(fname)
  dest=mods_dir/fname;valid=dest.is_file()
  expected_sha512=(f.get('hashes')or{}).get('sha512','')
  if valid and full and expected_sha512:
   digest=hashlib.sha512()
   with dest.open('rb')as stream:
    for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
   valid=digest.hexdigest()==expected_sha512
  if not valid:
   emit('status',text='Загрузка: '+r['name'])
   with urllib.request.urlopen(urllib.request.Request(f['url'],headers={'User-Agent':'EldoriaClient/1.0'}),timeout=90)as response:data=response.read()
   if expected_sha512 and hashlib.sha512(data).hexdigest()!=expected_sha512:raise RuntimeError('Неверная контрольная сумма '+fname)
   dest.write_bytes(data)
 # Eldoria Guard: Удаление любых посторонних .jar / .zip / .dll из папки mods перед запуском
 removed_foreign=[]
 for item in mods_dir.iterdir():
  if item.is_file() and item.name not in allowed_filenames:
   try:
    item.unlink()
    removed_foreign.append(item.name)
   except Exception:
    raise RuntimeError('Обнаружен посторонний файл в папке mods: '+item.name)
 if full:
  emit('result',value={'ok':True,'missing':[],'removedForeign':removed_foreign,'mods':len(list(mods_dir.glob('*.jar'))),'scope':'Проверены файлы клиента Eldoria-Client, защита Eldoria Guard и контрольные суммы модов TechnoMagic.'})
 else:
  nick=settings['nickname'];digest=bytearray(hashlib.md5(('OfflinePlayer:'+nick).encode()).digest());digest[6]=(digest[6]&15)|48;digest[8]=(digest[8]&63)|128
  hwid=compute_hwid()
  import ctypes
  shell=ctypes.WinDLL('shell32',use_last_error=True);kernel=ctypes.WinDLL('kernel32');shell.CommandLineToArgvW.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];shell.CommandLineToArgvW.restype=ctypes.POINTER(ctypes.c_wchar_p);kernel.LocalFree.argtypes=[ctypes.c_void_p]
  n=ctypes.c_int();argv=shell.CommandLineToArgvW('java '+settings.get('jvmArgs',''),ctypes.byref(n))
  if not argv:raise ctypes.WinError(ctypes.get_last_error())
  try:
   raw_custom=[argv[i]for i in range(1,n.value)]
  finally:
   kernel.LocalFree(argv)
  custom=[a for a in raw_custom if not a.lower().startswith(FORBIDDEN_JVM_PREFIXES)]
  options={
   'username':nick,
   'uuid':str(uuid.UUID(bytes=bytes(digest))),
   'token':'0',
   'executablePath':settings.get('javaPath')or str(root/'runtime/bin/java.exe'),
   'jvmArguments':[
    '-XX:+DisableAttachMechanism',
    '-Xms1024M',
    '-Xmx'+str(settings['ram'])+'M',
    '-XX:+UseG1GC',
    '-XX:+ParallelRefProcEnabled',
    '-Dfile.encoding=UTF-8',
    '-Deldoria.hwid='+hwid,
    '-Deldoria.site.url=http://127.0.0.1:8778'
   ]+custom,
   'gameDirectory':str(root),
   'launcherName':'Eldoria TechnoMagic',
   'launcherVersion':'2.0.0',
   'customResolution':True,
   'resolutionWidth':str(settings['width']),
   'resolutionHeight':str(settings['height'])
  }
  version=json.loads((root/'pack-info.json').read_text())['version']
  args=minecraft_launcher_lib.command.get_minecraft_command(version,str(root),options)
  if settings.get('gameFullscreen'):args.append('--fullscreen')
  emit('result',value={'args':args})
except Exception as e:emit('error',text=str(e));sys.exit(1)
