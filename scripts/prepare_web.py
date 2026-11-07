import json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
src=Path('C:/ILuvCodex/mini4-garage/node_modules/three')
for rel in ['build/three.module.js','build/three.core.js','examples/jsm/loaders/GLTFLoader.js','examples/jsm/utils/BufferGeometryUtils.js','examples/jsm/utils/SkeletonUtils.js','examples/jsm/controls/OrbitControls.js']:
    dest=DIST/'vendor'/'three'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/rel,dest)
shutil.copy2(src/'LICENSE',DIST/'vendor'/'three'/'LICENSE')
d=json.loads((ROOT/'assets'/'brief-data.json').read_text(encoding='utf-8'))
out={}
for k in ['stores','fixtures','inventory','current_display','work_records','field_notes','sales_summary','inbound']:
    out[k]=[r for r in d[k] if r.get('store_id')=='C']
out['products']=d['products'];out['snapshot']=d['snapshot'];out['source_url']='https://app.notion.com/p/hashed/F-F-4103f43d95de81808acde9fa2a026005'
for p in out['products']:p['image']='assets/products/'+Path(p['image']).name
(DIST/'assets'/'data.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
ref=DIST/'assets'/'references';ref.mkdir(exist_ok=True)
for n in ['tenant_2024_9.jpg','wokard_1.jpg','wokard_0.jpg']:
    shutil.copy2(ROOT/'reference_research'/n,ref/n)
print('Web assets prepared')
