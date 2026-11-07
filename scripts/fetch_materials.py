import urllib.request, json, concurrent.futures, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'assets'/'pbr';target.mkdir(exist_ok=True)
sources=[]
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'StoreConnectPrototype/1.0'}),timeout=40).read()
jobs=[]
for asset in ['terrazzo_tiles','fine_grained_wood','leather_white','denim_fabric','concrete_floor','oak_veneer_01']:
    d=json.loads(get('https://api.polyhaven.com/files/'+asset))
    for key,label in [('Diffuse','color'),('nor_gl','normal'),('Rough','roughness')]:
        info=d.get(key,{}).get('1k',{}).get('jpg')
        if info:jobs.append((info['url'],target/f'{asset}_{label}.jpg'))
    sources.append({'asset':asset,'url':'https://polyhaven.com/a/'+asset,'license':'CC0'})
def download(job):
    url,path=job
    if not path.exists():path.write_bytes(get(url))
    return path.name,path.stat().st_size
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    for result in pool.map(download,jobs):print(result)
(target/'sources.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
# Copy just the transitive imports required by the web rendering pipeline.
src=Path('C:/ILuvCodex/mini4-garage/node_modules/three/examples/jsm');dst=ROOT/'dist'/'vendor'/'three'/'examples'/'jsm'
seen=set()
def copy(rel):
    path=(src/rel).resolve()
    if path in seen:return
    seen.add(path);code=path.read_text(encoding='utf-8')
    dest=dst/path.relative_to(src);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(code,encoding='utf-8')
    for dep in re.findall(r"from\s+['\"]([^'\"]+)['\"]",code):
        if dep.startswith('.'):copy((path.parent/dep).resolve().relative_to(src))
for name in ['EffectComposer','RenderPass','GTAOPass','UnrealBloomPass','OutputPass']:
    copy(Path('postprocessing')/(name+'.js'))
print('Rendering modules',len(seen))

