import bpy,sys,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from detail_apparel import build_cap,build_jacket
from detail_accessories import build_sneaker,build_bag
for kind,builder in [('cap',build_cap),('shoe',build_sneaker),('jacket',build_jacket),('bag',build_bag)]:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 builder({})
 path=root/'dist/assets/photo-products'/f'{kind}-shop.glb'
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_apply=True,export_yup=True)
 for level in ['compact','detail']:shutil.copy2(path,path.with_name(f'{kind}-{level}.glb'))
 print('PUBLIC_MODEL',kind,path.stat().st_size,flush=True)
