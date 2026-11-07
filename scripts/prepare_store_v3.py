"""Separate authored architecture from photo-generated product assets."""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/MLB_Myeongdong_Detailed.blend'))
placements={}
for ob in list(bpy.context.scene.objects):
    if not ob.get('instanced_asset'):continue
    kind=ob['asset_type'];group=ob['model_group'];loc=list(ob.location);rotation=ob.rotation_euler.z;scale=list(ob.scale)
    key=(kind,group,*[round(v,5) for v in loc],round(rotation,5),*[round(v,5) for v in scale])
    display_color=next((c for c in ['navy','white','cream','pink','black','teal','green','burgundy'] if ob.data.name.endswith('_'+c)),'white')
    placements[key]={'kind':kind,'fixture':group,'position':[loc[0],loc[2],-loc[1]],'rotation':rotation,'scale':scale[0],'display_color':display_color}
    bpy.data.objects.remove(ob,do_unlink=True)
out=ROOT/'dist/assets'
(out/'placements-v3.json').write_text(json.dumps(list(placements.values()),indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/MLB_Myeongdong_Architecture.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'store-architecture.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_apply=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_texcoord_quantization=14)
print('ARCHITECTURE_READY',len(placements),'product positions')
