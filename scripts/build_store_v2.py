"""Detailed photo-referenced retail model. Shared high-poly product meshes, PBR materials.
Run with Blender --background --factory-startup --python scripts/build_store_v2.py.
"""
import bpy, math, json, random, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
source=(ROOT/'scripts'/'build_model.py').read_text(encoding='utf-8')
exec(compile(source.split('# Architecture.')[0],str(ROOT/'scripts'/'build_model.py'),'exec'))
from detail_apparel import build_cap, build_jacket
from detail_accessories import build_sneaker, build_bag
PBR=ROOT/'assets'/'pbr'

def pbrmat(name,color,rough=.65,metal=0,texture=None,color_map=True,normal_strength=.22):
    mat(name,color,metal,rough);m=M[name];b=m.node_tree.nodes.get('Principled BSDF');nodes=m.node_tree.nodes;links=m.node_tree.links
    if texture:
        for suffix,socket in [('color','Base Color'),('roughness','Roughness'),('normal','Normal')]:
            f=PBR/f'{texture}_{suffix}.jpg'
            if not f.exists() or (suffix=='color' and not color_map):continue
            n=nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(f),check_existing=True)
            if suffix!='color':n.image.colorspace_settings.name='Non-Color'
            if suffix=='normal':
                normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=normal_strength;links.new(n.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],b.inputs[socket])
            else:links.new(n.outputs['Color'],b.inputs[socket])
    return m

pbrmat('wood',(.65,.46,.26),.45,texture='oak_veneer_01',normal_strength=.25)
pbrmat('woodlight',(.65,.46,.26),.45,texture='oak_veneer_01',normal_strength=.2)
pbrmat('concrete',(.115,.13,.14),.85,texture='concrete_floor',color_map=False,normal_strength=.15)
pbrmat('plaster',(.57,.59,.58),.86,texture='concrete_floor',color_map=False,normal_strength=.07)
pbrmat('grid',(.26,.275,.28),.53,texture='concrete_floor',color_map=False,normal_strength=.12)
pbrmat('silver',(.68,.72,.75),.25,.92)
pbrmat('chrome',(.82,.85,.86),.18,.97)
pbrmat('blue',(.008,.025,.32),.24,.2)
pbrmat('wool_navy',(.012,.022,.047),.93,texture='denim_fabric',color_map=False,normal_strength=.25)
pbrmat('leather_cream',(.71,.65,.5),.5,texture='leather_white',color_map=False,normal_strength=.25)
pbrmat('thread_ivory',(.79,.76,.66),.95)
pbrmat('rib_knit',(.022,.028,.04),.96,texture='denim_fabric',color_map=False,normal_strength=.3)
pbrmat('shoe_leather',(.83,.82,.77),.42,texture='leather_white',color_map=False,normal_strength=.25)
pbrmat('shoe_suede',(.39,.35,.28),.92,texture='denim_fabric',color_map=False,normal_strength=.15)
pbrmat('rubber',(.65,.64,.6),.73)
pbrmat('mesh_fabric',(.29,.31,.3),.94,texture='denim_fabric',color_map=False,normal_strength=.4)
pbrmat('bag_leather',(.14,.085,.045),.5,texture='leather_white',color_map=False,normal_strength=.28)
pbrmat('gold',(.63,.42,.14),.24,.88)
pbrmat('mirror',(.75,.8,.83),.075,1)
pbrmat('glass',(.7,.82,.84),.12,.1)
glass=M['glass'].node_tree.nodes.get('Principled BSDF');glass.inputs['Transmission Weight'].default_value=.85;glass.inputs['IOR'].default_value=1.45

# Bake a procedural terrazzo material into a repeatable color map. This is shader
# authoring, with physical material scale, so no stock photo is repainted.
def terrazzo():
    bpy.ops.mesh.primitive_plane_add(size=2);plane=bpy.context.object;plane.name='bake_terrazzo'
    m=bpy.data.materials.new('TerrazzoBake');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    tex=n.new('ShaderNodeTexCoord');v=n.new('ShaderNodeTexVoronoi');v.inputs['Scale'].default_value=125;v.distance='EUCLIDEAN';l.new(tex.outputs['UV'],v.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1]);ramp.color_ramp.elements[0].position=.0;ramp.color_ramp.elements[0].color=(.1,.11,.12,1)
    for pos,color in [(.11,(.25,.27,.27,1)),(.18,(.51,.49,.44,1)),(.24,(.73,.73,.69,1)),(.3,(.82,.82,.78,1))]:ramp.color_ramp.elements.new(pos).color=color
    ramp.color_ramp.interpolation='CONSTANT';l.new(v.outputs['Distance'],ramp.inputs[0]);em=n.new('ShaderNodeEmission');l.new(ramp.outputs['Color'],em.inputs[0]);out=n.new('ShaderNodeOutputMaterial');l.new(em.outputs[0],out.inputs['Surface'])
    image=bpy.data.images.new('Fine white terrazzo',width=1024,height=1024);dest=n.new('ShaderNodeTexImage');dest.image=image;n.active=dest;plane.data.materials.append(m)
    bpy.context.scene.render.engine='CYCLES';bpy.context.scene.cycles.samples=1;bpy.ops.object.bake(type='EMIT')
    image.filepath_raw=str(PBR/'terrazzo_baked.png');image.file_format='PNG';image.save();bpy.data.objects.remove(plane,do_unlink=True)
    pbrmat('floor',(.8,.79,.74),.36);floor=M['floor'];base=floor.node_tree.nodes.get('Principled BSDF');im=floor.node_tree.nodes.new('ShaderNodeTexImage');im.image=image;floor.node_tree.links.new(im.outputs['Color'],base.inputs['Base Color'])
    base.inputs['Coat Weight'].default_value=.12;base.inputs['Coat Roughness'].default_value=.32
terrazzo()

def add_uv(ob):
    if ob.type!='MESH':return
    me=ob.data;uv=me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        normal=p.normal;axis=max(range(3),key=lambda i:abs(normal[i]));m=me.materials[p.material_index] if me.materials else None
        name=m.name if m else '';factor=3 if any(a in name for a in ['wool','leather','fabric','knit']) else .55 if 'wood' in name else 1
        axes=(1,2) if axis==0 else (0,2) if axis==1 else (0,1)
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]*factor,co[axes[1]]*factor)

TEMPLATES={};VARIANTS={};MESH_VARIANTS={};instances=[]
for kind,builder in [('cap',build_cap),('jacket',build_jacket),('shoe',build_sneaker),('bag',build_bag)]:
    obs=builder(M);bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);bpy.ops.object.join()
    master=bpy.context.object;master.name='Master_'+kind;add_uv(master)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='MATERIAL');bpy.ops.object.mode_set(mode='OBJECT')
    parts=list(bpy.context.selected_objects)
    for i,ob in enumerate(parts):ob.name=f'{kind}_part_{i}';ob['asset_type']=kind
    TEMPLATES[kind]=parts
    print('ASSET',kind,'triangles',sum(len(p.vertices)-2 for o in parts for p in o.data.polygons),flush=True)

COLORS={'navy':(.012,.022,.047),'white':(.77,.76,.68),'cream':(.46,.34,.2),'pink':(.36,.12,.16),'black':(.014,.016,.018),'teal':(.015,.12,.2),'green':(.04,.1,.065),'burgundy':(.18,.014,.035)}
def variant(m,color):
    if color=='navy' or m.name not in ['wool_navy','bag_leather','shoe_leather']:return m
    key=(m.name,color)
    if key not in VARIANTS:
        dup=m.copy();dup.name=m.name+'_'+color;dup.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*COLORS.get(color,COLORS['navy']),1);VARIANTS[key]=dup
    return VARIANTS[key]
def place(kind,loc,group,color='navy',scale=1,angle=0):
    for part in TEMPLATES[kind]:
        ob=part.copy();ob.data=part.data;bpy.context.collection.objects.link(ob);ob.name=kind+'_'+group
        ob.location=loc;ob.rotation_euler=(0,0,angle);ob.scale=(scale,scale,scale);ob['model_group']=group;ob['asset_type']=kind;ob['instanced_asset']=True
        variant_key=(part.data.name,color)
        if variant_key not in MESH_VARIANTS:
            data=part.data.copy();data.name=part.data.name+'_'+color
            for i,original in enumerate(data.materials):data.materials[i]=variant(original,color) if original else M['black']
            MESH_VARIANTS[variant_key]=data
        ob.data=MESH_VARIANTS[variant_key]
        instances.append(ob)
def cap(x,y,z,color,rot=0,group='store'):
    if group=='C-C01':rot=math.pi/2
    place('cap',(x,y,z),group,color,1.05,rot)
def jacket(x,y,z,color='navy',group='store',scale=1):
    angle=math.pi/2 if group in ['C-W01','C-W02'] else 0
    place('jacket',(x,y,z-.30*scale),group,color,scale,angle)
def shoe(x,y,z,color='white',group='store',rot=0):
    if group=='C-S01':rot=math.atan2(y-19.35,x)-math.pi/2
    place('shoe',(x,y,z),group,color,1.06,rot)
def bag(x,y,z,color='cream',group='store'):
    place('bag',(x,y,z),group,color,1.0,-math.pi/2 if group=='C-B01' else 0)

# Higher resolution hardware and anatomical mannequin parts.
old_sphere=sphere
def sphere(m,c,s,group='store',half=False):
    n=40;nr=20;vv=[]
    for j in range(nr+1):
        ph=j/nr*math.pi*(.5 if half else 1)
        for i in range(n):
            th=i/n*math.tau;vv.append((c[0]+s[0]*math.sin(ph)*math.cos(th),c[1]+s[1]*math.sin(ph)*math.sin(th),c[2]+s[2]*math.cos(ph)))
    mesh(m,vv,[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(nr) for i in range(n)],group,True)
old_tube=tube
def tube(m,a,b,r=.025,n=10,group='store'):old_tube(m,a,b,r,max(16,n),group)
def arc_band(m,c,r,w,z,thickness,group,start=.12,end=math.pi-.12,segments=96):
    vv=[]
    for h in [z-thickness/2,z+thickness/2]:
        for rr in [r-w/2,r+w/2]:
            vv += [(c[0]+rr*math.cos(start+(end-start)*i/segments),c[1]+rr*math.sin(start+(end-start)*i/segments),h) for i in range(segments+1)]
    n=segments+1;ff=[]
    for i in range(segments):ff += [(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)]
    ff += [(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)];mesh(m,vv,ff,group)

def shelf_unit(x,y,w,kind,group,face=1):
    bays=max(1,round(w/1.2));bw=w/bays
    box('wood',(x,y,.22),(.52,w,.42),group);box('black',(x,y,.045),(.44,w-.06,.09),group)
    for j in range(bays):
        yy=y-w/2+(j+.5)*bw
        box('wood',(x+face*.269,yy,.22),(.015,bw-.015,.34),group)
        tube('silver',(x+face*.285,yy+.08,.36),(x+face*.285,yy+.24,.36),.007,16,group)
    box('blue' if kind=='bag' else 'mirror' if kind=='cap' else 'plaster',(x-face*.22,y,1.7),(.055,w,2.5),group)
    for sy in [-w/2+i*bw for i in range(bays+1)]:
        box('silver',(x+face*.22,y+sy,1.6),(.045,.035,2.8),group)
    if kind=='clothes':
        for j in range(bays):
            yy=y-w/2+(j+.5)*bw
            # Arched timber portal follows the actual renovated wall system.
            r=bw*.44
            for side in [-1,1]:box('wood',(x+face*.25,yy+side*r,1.42),(.07,.055,1.96),group)
            pts=[(x+face*.25,yy+r*math.cos(a*math.pi/64),2.4+r*.65*math.sin(a*math.pi/64)) for a in range(65)]
            for a,b in zip(pts,pts[1:]):tube('wood',a,b,.028,16,group)
            box('wood',(x,yy,2.12),(.48,bw-.09,.035),group)
            tube('silver',(x+face*.12,yy-r,1.87),(x+face*.12,yy+r,1.87),.018,24,group)
            for k in range(2):jacket(x+face*.10,yy+(-.26 if k==0 else .26),1.37,['navy','cream','teal','burgundy'][(j+k)%4],group,.83)
    else:
        levels=5 if kind=='cap' else 4
        for k in range(levels):
            h=.57+k*.45;box('blue' if kind=='bag' else 'white',(x,y,h),(.55,w,.026),group)
            box('silver',(x+face*.277,y,h),(.018,w,.032),group)
            box('warm',(x+face*.23,y,h-.027),(.018,w-.06,.012),group)
            count=max(2,int(w/(.39 if kind=='cap' else .46)))
            for j in range(count):
                yy=y-w/2+(j+.5)*w/count;col=['navy','cream','white','black','pink','green'][(j//3+k)%6]
                if kind=='cap':cap(x+face*.02,yy,h+.017,col,group=group)
                elif kind=='bag':bag(x+face*.02,yy,h+.02,col,group)
        if kind=='bag':
            for j in range(1,bays):box('blue',(x,y-w/2+j*bw,1.55),(.54,.035,2.25),group)
    # Backlit category header and a slim cap ledge.
    box('navy',(x,y,2.92),(.55,w,.26),group)
    label={'cap':'HEADWEAR','clothes':'NEW YORK / MLB','bag':'ACCESSORIES'}[kind]
    sign(label,(x+face*.29,y,2.87),.12,'white',(math.pi/2,0,math.pi/2 if face==1 else -math.pi/2),group)

geometry=source.split('# Architecture.')[1].split('# Final grouped meshes')[0]
geometry='# Architecture.'+geometry
geometry=geometry.replace('range(6500)','range(1700)')
geometry=geometry.replace("random.uniform(.008,.024)","random.uniform(.005,.012)")
start=geometry.index("    elif kind=='shoe_wall':")
end=geometry.index("    elif kind=='cap_island':",start)
geometry=geometry[:start]+'''    elif kind=='shoe_wall':
        cx=0;cy=19.35
        box('woodlight',(0,20.1,.019),(4.6,3.6,.035),fid)
        for j in range(6):
            z=.43+j*.39
            arc_band('blue',(cx,cy),1.75,.46,z,.034,fid)
            arc_band('silver',(cx,cy),1.99,.018,z,.038,fid)
            arc_band('light',(cx,cy),1.51,.012,z-.026,.012,fid)
            if j<5:
                for a in range(8):
                    th=.23+a/7*2.67;shoe(math.cos(th)*1.75,cy+math.sin(th)*1.75,z+.02,['white','cream','navy'][a%3],fid)
        for th in [.12,.85,1.57,2.3,3.02]:tube('chrome',(math.cos(th)*1.75,cy+math.sin(th)*1.75,.08),(math.cos(th)*1.75,cy+math.sin(th)*1.75,2.65),.018,32,fid)
        # Upholstered curved stadium bench.
        sphere('blue',(0,20,.35),(.80,.32,.25),fid)
        anchors[-1]['x']=0;anchors[-1]['z']=-19.35;anchors[-1]['rect']=[-2,19,4,2.2]
        sign('FOOTWEAR',(0,21.96,2.85),.24,'navy')
''' + geometry[end:]
exec(compile(geometry,'photo_referenced_architecture','exec'))

# Visually coherent metalwork and shopfitting details.
for x in [-4.98,4.98]:
    box('silver',(x,11,.12),(.03,22,.21),'store')
    box('silver',(x,11,3.25),(.06,22,.05),'ceiling')
for y in [4.5,11,17.5]:
    # HVAC cassette with dark recessed louvers and multiple internal slats.
    box('plaster',(-3.0,y,3.51),(1.0,1.0,.15),'ceiling');box('black',(-3.0,y,3.421),(.86,.86,.025),'ceiling')
    for i in range(13):box('silver',(-3.0,y-.39+i*.065,3.405),(.83,.025,.025),'ceiling')
# Thin frameless glass stair balustrade, segmented panels and polished clips.
for j in range(5):
    yy=1.1+j*.58;zz=.3+j*.5
    box('glass',(2.46,yy,zz+.58),(.012,.55,1.0),'stairs')
    for h in [.2,.88]:box('chrome',(2.455,yy-.19,zz+h),(.05,.035,.035),'stairs')
# Recessed fitting-room jamb, handle, and ceiling signage.
for yy in [19.8,21]:box('silver',(3.18,yy,1.14),(.045,.055,2.27),'service')
tube('chrome',(3.15,20.85,.8),(3.15,20.85,1.18),.012,24,'service')

# Assemble architecture batches with true bevels and physically sized UVs.
for (m,group),(vv,ff,sm) in G.items():
    me=bpy.data.meshes.new(group+'_'+m);me.from_pydata(vv,[],ff);me.materials.append(M[m]);me.update()
    ob=bpy.data.objects.new(group+'__'+m,me);bpy.context.collection.objects.link(ob);ob['model_group']=group
    for p in me.polygons:p.use_smooth=sm[p.index]
    add_uv(ob)
    if m not in ['floor','grid','light','warm'] and len(ff)<25000:
        bevel=ob.modifiers.new('Machined rounded edges','BEVEL');bevel.width=.003 if m in ['silver','chrome'] else .006;bevel.segments=3;bevel.limit_method='ANGLE'
        bevel.harden_normals=True
        weighted=ob.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');weighted.keep_sharp=True;weighted.weight=50

# Remove prototype masters; every placed object retains shared mesh data.
for parts in TEMPLATES.values():
    for ob in parts:bpy.data.objects.remove(ob,do_unlink=True)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath:image.pack()
scene=bpy.context.scene;scene['reference_note']='MLB Myeongdong photographic reference study; authored sample-C dimensions; inferred heights. Detailed original product meshes, not SKU scans.'
scene['quality_revision']='V2 detailed shared meshes, machined edges, PBR surfaces'
scene.world.color=(.08,.08,.08)
out=ROOT/'dist'/'assets';(out/'anchors.json').write_text(json.dumps(anchors,ensure_ascii=False),encoding='utf-8')
stats={'revision':2,'objects':len(scene.objects),'unique_meshes':len(set(o.data for o in scene.objects if o.type=='MESH')),'placed_product_parts':len(instances),'triangles':sum(len(p.vertices)-2 for ob in scene.objects if ob.type=='MESH' for p in ob.data.polygons)}
(out/'model-stats.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets'/'MLB_Myeongdong_Detailed.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'store-v2.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_apply=True,export_image_format='AUTO',export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_texcoord_quantization=14)
import struct
binary=(out/'store-v2.glb').read_bytes();gltf=json.loads(binary[20:20+struct.unpack_from('<I',binary,12)[0]])
stats['exported_triangles']=sum(sum(gltf['accessors'][p['indices']]['count']//3 for p in gltf['meshes'][n['mesh']]['primitives'] if p.get('mode',4)==4) for n in gltf['nodes'] if 'mesh' in n)
stats['compressed_bytes']=len(binary)
(out/'model-stats.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print('V2_COMPLETE',json.dumps(stats),flush=True)
