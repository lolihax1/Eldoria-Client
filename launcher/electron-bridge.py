import sys,json,pathlib,uuid,hashlib,urllib.request,time,hmac,secrets
import minecraft_launcher_lib
root=pathlib.Path(__file__).resolve().parent.parent
LAUNCHER_HMAC_SECRET=b'eldoria-tm-official-launcher-2026-hmac-v1-9f4b2c8e7a1d6f3b5e0c9a8d7f6e5b4c'
def emit(kind,**values):print(json.dumps({'type':kind,**values},ensure_ascii=False),flush=True)
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
def make_launch_ticket(nick):
 clean=str(nick or '').strip()
 nick_lower=clean.lower()
 issued_at=int(time.time()*1000)
 nonce=secrets.token_hex(16)
 payload=f'eldoria-ticket-v1:{nick_lower}:{issued_at}:{nonce}'
 sig=hmac.new(LAUNCHER_HMAC_SECRET,payload.encode('utf-8'),hashlib.sha256).hexdigest()
 ticket_obj={'nick':clean,'nickLower':nick_lower,'issuedAt':issued_at,'nonce':nonce,'ticketSig':sig}
 try:
  ticket_path=root/'launcher'/'.eldoria-launch-ticket'
  ticket_path.parent.mkdir(parents=True,exist_ok=True)
  ticket_path.write_text(json.dumps(ticket_obj,ensure_ascii=False,indent=2),encoding='utf-8')
 except Exception:
  pass
 return f'{nick_lower}:{issued_at}:{nonce}:{sig}'
try:
 settings=json.load(sys.stdin);full=sys.argv[1]=='verify'
 entries=load_mod_entries()
 (root/'mods').mkdir(parents=True,exist_ok=True)
 emit('status',text='Проверка модов Eldoria TechnoMagic…')
 for r in entries:
  if r['side']=='server':continue
  f=r['file'];dest=root/'mods'/f['filename'];valid=dest.is_file()
  expected_sha512=(f.get('hashes')or{}).get('sha512','')
  if valid and full and expected_sha512:
   digest=hashlib.sha512()
   with dest.open('rb')as stream:
    for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
   valid=digest.hexdigest()==expected_sha512
  if not valid:
   emit('status',text='Загрузка: '+r['name'])
   with urllib.request.urlopen(urllib.request.Request(f['url'],headers={'User-Agent':'EldoriaClient/1.0'}),timeout=90)as response:data=response.read()
   if expected_sha512 and hashlib.sha512(data).hexdigest()!=expected_sha512:raise RuntimeError('Неверная контрольная сумма '+f['filename'])
   dest.write_bytes(data)
 if full:
  emit('result',value={'ok':True,'missing':[],'mods':len(list((root/'mods').glob('*.jar'))),'scope':'Проверены файлы клиента Eldoria-Client и контрольные суммы модов TechnoMagic.'})
 else:
  nick=settings['nickname'];digest=bytearray(hashlib.md5(('OfflinePlayer:'+nick).encode()).digest());digest[6]=(digest[6]&15)|48;digest[8]=(digest[8]&63)|128
  ticket_str=make_launch_ticket(nick)
  import ctypes
  shell=ctypes.WinDLL('shell32',use_last_error=True);kernel=ctypes.WinDLL('kernel32');shell.CommandLineToArgvW.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];shell.CommandLineToArgvW.restype=ctypes.POINTER(ctypes.c_wchar_p);kernel.LocalFree.argtypes=[ctypes.c_void_p]
  n=ctypes.c_int();argv=shell.CommandLineToArgvW('java '+settings.get('jvmArgs',''),ctypes.byref(n))
  if not argv:raise ctypes.WinError(ctypes.get_last_error())
  try:custom=[argv[i]for i in range(1,n.value)]
  finally:kernel.LocalFree(argv)
  options={'username':nick,'uuid':str(uuid.UUID(bytes=bytes(digest))),'token':'0','executablePath':settings.get('javaPath')or str(root/'runtime/bin/java.exe'),'jvmArguments':['-Xms1024M','-Xmx'+str(settings['ram'])+'M','-XX:+UseG1GC','-XX:+ParallelRefProcEnabled','-Dfile.encoding=UTF-8','-Deldoria.launcher.ticket='+ticket_str,'-Deldoria.site.url=http://127.0.0.1:8778']+custom,'gameDirectory':str(root),'launcherName':'Eldoria TechnoMagic','launcherVersion':'2.0.0','customResolution':True,'resolutionWidth':str(settings['width']),'resolutionHeight':str(settings['height'])}
  version=json.loads((root/'pack-info.json').read_text())['version']
  args=minecraft_launcher_lib.command.get_minecraft_command(version,str(root),options)
  if settings.get('gameFullscreen'):args.append('--fullscreen')
  emit('result',value={'args':args})
except Exception as e:emit('error',text=str(e));sys.exit(1)
