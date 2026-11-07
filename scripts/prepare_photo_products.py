"""Preserve photo-generated originals and export metre-scale web LODs."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/assets/photo-products';OUT.mkdir(parents=True,exist_ok=True)
specs={'cap':('Y',.31),'shoe':('Y',.29),'jacket':('Z',.76),'bag':('Z',.36)}
stats={}
for kind,(axis,size) in specs.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'.local/ai-models'/f'{kind}.glb'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bpy.ops.object.join();ob=bpy.context.object
    if kind in ('jacket','bag'):
        ob.rotation_euler.z=-math.pi/2
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
    bounds=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    mn=Vector([min(c[i] for c in bounds) for i in range(3)])
    mx=Vector([max(c[i] for c in bounds) for i in range(3)])
    scale=size/(mx-mn)['XYZ'.index(axis)]
    center=Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z))
    for v in ob.data.vertices:v.co=(v.co-center)*scale
    ob.name='Photo_'+kind;ob['reference_sku']={'cap':'HAT-001','shoe':'SHO-003','jacket':'OUT-004','bag':'BAG-001'}[kind]
    for p in ob.data.polygons:p.use_smooth=True
    original=len(ob.data.polygons)
    stats[kind]={'input_polygons':original,'dimensions_m':[round(v*scale,3) for v in mx-mn]}
    for lod,target in [('detail',45000),('shop',18000),('compact',6500)]:
        # Close shelves retain silhouette details; distant shelves use compact LOD.
        if lod in ('shop','compact'):
            limit=2048 if lod=='shop' else 1024
            for im in bpy.data.images:
                if im.size[0]>limit:
                    ratio=limit/im.size[0];im.scale(limit,max(1,int(im.size[1]*ratio)))
        dec=ob.modifiers.new('web_'+lod,'DECIMATE');dec.ratio=min(1,target/original)
        bpy.ops.export_scene.gltf(filepath=str(OUT/f'{kind}-{lod}.glb'),export_format='GLB',export_apply=True,export_extras=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=14,export_draco_texcoord_quantization=12)
        ob.modifiers.remove(dec)
    print('PHOTO_ASSET',kind,stats[kind],flush=True)
(OUT/'provenance.json').write_text(json.dumps({'source':'Higgsfield / Tripo H3.1','method':'image to 3D; approximate single-view reconstruction','models':stats},indent=2),encoding='utf-8')
