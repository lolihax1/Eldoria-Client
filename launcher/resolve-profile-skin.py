import pathlib,json,zipfile,base64,sys,re
root=pathlib.Path('D:/Users/NeKinder/Games/Eldoria-TechnoMagic')
name=sys.argv[1] if len(sys.argv)>1 else ''
if re.fullmatch(r'[A-Za-z0-9_]{3,16}',name):
 custom_skin=root/'launcher'/'skins'/(name+'.png')
 if custom_skin.is_file():
  print(json.dumps({'dataUrl':'data:image/png;base64,'+base64.b64encode(custom_skin.read_bytes()).decode(),'source':'Скин аккаунта Eldoria (64×64)'},ensure_ascii=False))
  sys.exit(0)
steve_asset='D:/Users/NeKinder/Desktop/Eldoria_Full_Site/dist/assets/steve.png'
if pathlib.Path(steve_asset).is_file():
 data=pathlib.Path(steve_asset).read_bytes()
else:
 with zipfile.ZipFile(root/'versions/1.21.1/1.21.1.jar')as z:data=z.read('assets/minecraft/textures/entity/player/wide/steve.png')
print(json.dumps({'dataUrl':'data:image/png;base64,'+base64.b64encode(data).decode(),'source':'Стандартный скин: Steve (64×64)'},ensure_ascii=False))
