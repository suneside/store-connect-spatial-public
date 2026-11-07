"""Refine the home architecture without rebuilding or replacing the source scene.

Adds furniture construction details and per-vertex ambient occlusion. Uses Blender
in background mode only; retains all fixture IDs and the authored footprint.
"""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/MLB_Myeongdong_Architecture.blend'))
random.seed(73)
def material(name,color,metal=0,rough=.6):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m
metal=material('V4_brushed_hardware',(.22,.25,.27),.88,.3)
oak=material('V4_hanger_oak',(.22,.12,.055),0,.7)
dark=material('V4_groove',(.012,.014,.016),0,.8)
labelmat=material('V4_label',(.62,.60,.52),0,.8)
def tube(a,b,r,mat,group):
    d=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=d.length,location=(Vector(a)+Vector(b))/2)
    ob=bpy.context.object;ob.rotation_euler=d.to_track_quat('Z','Y').to_euler();ob.data.materials.append(mat)
    ob['model_group']=group;ob.name='V4_hardware';return ob
def box(loc,size,mat,group,bevel=.003):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(mat)
    ob['model_group']=group;ob.name='V4_joinery'
    if bevel:
        mod=ob.modifiers.new('edge_radius','BEVEL');mod.width=bevel;mod.segments=3
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob
placements=json.loads((ROOT/'dist/assets/placements-v3.json').read_text())
for p in placements:
    x,z,ny=p['position'];y=-ny;s=p['scale'];group=p['fixture'];angle=p['rotation']
    if p['kind']=='jacket' and group!='C-M01':
        # Shoulder support and bent hook meet the existing garment rail.
        h=z+.76*s;ux,uy=math.cos(angle),math.sin(angle)
        for side in [-1,1]:tube((x,y,h+.035),(x+side*.17*s*ux,y+side*.17*s*uy,h-.045),.011,oak,group)
        tube((x-.17*s*ux,y-.17*s*uy,h-.045),(x+.17*s*ux,y+.17*s*uy,h-.045),.007,oak,group)
        points=[(x+.026*math.cos(a)*ux,y+.026*math.cos(a)*uy,h+.05+.026*math.sin(a)) for a in [i/12*math.pi*1.7 for i in range(13)]]
        for a,b in zip(points,points[1:]):tube(a,b,.0035,metal,group)
    elif p['kind'] in ['shoe','bag']:
        # Small shelf label holders; deliberately no invented prices/SKU labels.
        box((x,y-.14,z+.006),(.085,.038,.012),labelmat,group,.002)
# Detailed construction of timber cabinetry: shadow gaps and skirting.
for x,ya,yb,group in [(-4.4,1.2,6,'C-C01'),(-4.4,6.5,11.5,'C-W02'),(-4.4,12.5,19,'C-W01'),(4.25,6.5,10.3,'C-B01')]:
    inward=1 if x<0 else -1
    box((x+inward*.275,(ya+yb)/2,.085),(.018,yb-ya,.018),dark,group,.001)
    bays=max(1,round((yb-ya)/1.2))
    for j in range(1,bays):
        yy=ya+(yb-ya)*j/bays
        box((x+inward*.277,yy,.23),(.012,.007,.28),dark,group,.001)
    for level in [.57,1.02,1.47,1.92]:
        if group not in ['C-C01','C-B01']:continue
        for j in range(bays+1):
            yy=ya+(yb-ya)*j/bays
            tube((x-inward*.17,yy,level-.13),(x+inward*.21,yy,level-.025),.009,metal,group)
# Visible joints on the curved stadium shelves.
for h in [.43+i*.39 for i in range(6)]:
    for a in [.12,.85,1.57,2.3,3.02]:
        x,y=math.cos(a)*1.75,19.35+math.sin(a)*1.75
        tube((x,y,h-.035),(x,y,h+.035),.03,metal,'C-S01')

# Apply modifiers before baking contact shading into COLOR_0; no lightmap seams.
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for ob in meshes:
    bpy.context.view_layer.objects.active=ob
    for mod in list(ob.modifiers):
        try:bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError:pass
# BVH excludes light panels and glass. It is only used for short-range occlusion.
verts=[];faces=[]
for ob in meshes:
    if ob.get('model_group') in ['ceiling','facade'] or 'glass' in ob.name:continue
    offset=len(verts);verts.extend(ob.matrix_world@v.co for v in ob.data.vertices)
    faces.extend(tuple(offset+i for i in f.vertices) for f in ob.data.polygons)
bvh=BVHTree.FromPolygons(verts,faces)
for index,ob in enumerate(meshes):
    if ob.get('model_group') in ['ceiling','facade'] or any(k in ob.name for k in ['light','warm','glass']):continue
    me=ob.data;attr=me.color_attributes.new(name='ContactOcclusion',type='FLOAT_COLOR',domain='CORNER')
    me.color_attributes.active_color=attr
    normalmat=ob.matrix_world.to_3x3().inverted().transposed();cache={}
    for face in me.polygons:
        normal=(normalmat@face.normal).normalized()
        tangent=normal.cross(Vector((0,0,1)))
        if tangent.length<.05:tangent=normal.cross(Vector((0,1,0)))
        tangent.normalize();bitangent=normal.cross(tangent)
        for li in face.loop_indices:
            vi=me.loops[li].vertex_index;key=(vi,tuple(round(c,2) for c in normal))
            if key not in cache:
                pos=ob.matrix_world@me.vertices[vi].co+normal*.006;occlusion=0
                for k in range(12):
                    phi=k*2.399963;z=(k+.5)/12;r=math.sqrt(1-z*z)
                    direction=normal*z+(tangent*math.cos(phi)+bitangent*math.sin(phi))*r
                    hit=bvh.ray_cast(pos,direction,.45)
                    if hit[0] is not None:occlusion+=max(0,1-hit[3]/.45)
                cache[key]=max(.57,1-occlusion/12*.58)
            v=cache[key];attr.data[li].color=(v,v,v,1)
    if index%20==0:print('AO',index,len(meshes),flush=True)
# Join newly authored details by material/fixture to keep draw calls modest.
groups={}
for ob in list(bpy.context.scene.objects):
    if ob.type=='MESH' and ob.name.startswith('V4_'):
        groups.setdefault((ob.get('model_group'),ob.data.materials[0].name),[]).append(ob)
for (group,name),objects in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name=f'{group}__{name}'
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath:image.pack()
bpy.context.scene['quality_revision']='V4 joinery, hanger hardware, shelf brackets, baked short-range ambient occlusion'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/MLB_Myeongdong_Refined.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'dist/assets/store-refined.glb'),export_format='GLB',export_extras=True,export_apply=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_texcoord_quantization=14,export_all_vertex_colors=True)
print('REFINED_ARCHITECTURE_COMPLETE',flush=True)
