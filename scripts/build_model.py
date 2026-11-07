"""Photo-referenced MLB Myeongdong study; authored dimensions from F&F sample C.
Blender Z-up metres -> glTF Y-up. No UI or external renderer is used.
"""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
random.seed(47)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
M={};G={}
def mat(name,color,metal=0,rough=.65,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
    if emission:b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emission
    M[name]=m
for args in [('plaster',(.68,.7,.7)),('floor',(.83,.825,.79)),('grid',(.38,.4,.4)),('concrete',(.24,.265,.27)),('silver',(.55,.59,.61),.72,.28),('blue',(.018,.052,.62),.23,.28),('navy',(.012,.019,.05)),('wood',(.34,.22,.12)),('woodlight',(.5,.35,.2)),('light',(.94,.96,1),0,.25,2.2),('warm',(.95,.86,.65),0,.3,1.5),('white',(.88,.87,.83)),('cream',(.64,.56,.39)),('black',(.018,.019,.024)),('teal',(.04,.37,.48)),('pink',(.6,.27,.34)),('burgundy',(.28,.028,.055)),('green',(.06,.22,.15)),('rubber',(.5,.52,.51)),('skin',(.72,.68,.61))]:mat(*args)
def mesh(m,verts,faces,group='store',smooth=False):
    key=(m,group)
    if key not in G:G[key]=[[],[],[]]
    v,f,sm=G[key];i=len(v);v.extend(verts);f.extend([tuple(i+a for a in face) for face in faces]);sm.extend([smooth]*len(faces))
def box(m,c,s,group='store',angle=0):
    x,y,z=c;a,b,d=[v/2 for v in s];co=math.cos(angle);si=math.sin(angle)
    vv=[(x+u*co-v*si,y+u*si+v*co,z+w) for u,v,w in [(-a,-b,-d),(a,-b,-d),(a,b,-d),(-a,b,-d),(-a,-b,d),(a,-b,d),(a,b,d),(-a,b,d)]]
    mesh(m,vv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],group)
def tube(m,a,b,r=.025,n=10,group='store'):
    a,b=Vector(a),Vector(b);v=(b-a).normalized();u=v.cross(Vector((0,0,1)))
    if u.length<.01:u=v.cross(Vector((0,1,0)))
    u.normalize();w=v.cross(u);vv=[]
    for p in [a,b]:
        vv += [tuple(p+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*w)) for i in range(n)]
    ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh(m,vv,ff,group)
def sphere(m,c,s,group='store',half=False):
    n=14;nr=7;vv=[]
    for j in range(nr+1):
        ph=j/nr*math.pi*(.5 if half else 1)
        for i in range(n):
            th=i/n*math.tau;vv.append((c[0]+s[0]*math.sin(ph)*math.cos(th),c[1]+s[1]*math.sin(ph)*math.sin(th),c[2]+s[2]*math.cos(ph)))
    mesh(m,vv,[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(nr) for i in range(n)],group,True)
def sign(text,c,size,m='white',rot=(math.pi/2,0,0),group='store'):
    cu=bpy.data.curves.new('lettering','FONT');cu.body=text;cu.size=size;cu.align_x='CENTER';cu.extrude=.001;cu.bevel_depth=.0005
    ob=bpy.data.objects.new('Sign '+text,cu);bpy.context.collection.objects.link(ob);ob.location=c;ob.rotation_euler=rot;cu.materials.append(M[m])
    ob['model_group']=group
def cap(x,y,z,color,rot=0,group='store'):
    sphere(color,(x,y,z+.095),(.125,.14,.11),group,True)
    dx=math.sin(rot)*.12;dy=-math.cos(rot)*.12
    sphere(color,(x+dx,y+dy,z+.009),(.135,.15,.012),group)
    sphere('white',(x,y,z+.207),(.014,.014,.008),group)
    # Two narrow embroidered strokes, viewed at the front.
    tube('white',(x-.025,y-.131,z+.11),(x+.02,y-.131,z+.17),.006,6,group)
    tube('white',(x-.025,y-.132,z+.17),(x+.02,y-.132,z+.11),.006,6,group)
def shoe(x,y,z,color='white',group='store',rot=0):
    sphere('white',(x,y,z+.045),(.12,.23,.045),group)
    sphere(color,(x,y+.03,z+.13),(.105,.19,.105),group)
    sphere('navy',(x,y+.13,z+.21),(.065,.063,.024),group)
    for j in range(4):tube('cream',(x-.06,y-.06+j*.028,z+.21),(x+.06,y-.045+j*.028,z+.215),.006,6,group)
def jacket(x,y,z,color='teal',group='store',scale=1):
    # Rounded garment volume, collar, sleeves, pockets, ribbed hem, hanger.
    sphere(color,(x,y,z),(.24*scale,.11*scale,.32*scale),group)
    for a in [-1,1]:
        tube(color,(x+a*.2*scale,y,z+.22*scale),(x+a*.32*scale,y,z-.19*scale),.085*scale,10,group)
        tube('white',(x+a*.32*scale,y,z-.17*scale),(x+a*.33*scale,y,z-.23*scale),.075*scale,10,group)
        box('white',(x+a*.11*scale,y-.106*scale,z-.1*scale),(.07*scale,.015,.025*scale),group,angle=-a*.3)
    box('white',(x,y-.005,z-.28*scale),(.37*scale,.16*scale,.035),group)
    tube('white',(x,y-.11*scale,z-.25*scale),(x,y-.11*scale,z+.23*scale),.009,6,group)
    tube('silver',(x-.2*scale,y,z+.31*scale),(x,y,z+.43*scale),.009,6,group)
    tube('silver',(x+.2*scale,y,z+.31*scale),(x,y,z+.43*scale),.009,6,group)
    for j in range(5):sphere('silver',(x,y-.12,z-.17+j*.075),(.012,.007,.012),group)
    box('white',(x-.11*scale,y-.108,z+.12*scale),(.07,.012,.08),group)
def bag(x,y,z,color='cream',group='store'):
    sphere(color,(x,y,z+.18),(.16,.08,.16),group)
    for a in [-1,1]:tube(color,(x+a*.12,y,z+.25),(x+a*.09,y,z+.43),.015,8,group)
    tube(color,(x-.09,y,z+.43),(x+.09,y,z+.43),.015,8,group)
    box('silver',(x,y-.08,z+.19),(.035,.012,.025),group)
def shelf_unit(x,y,w,kind,group,face=1):
    # Unit faces +X if on the left and -X if on the right. Local shelves follow Y.
    box('wood',(x,y,.17),(.5,w,.34),group)
    box('plaster',(x-face*.21,y,1.6),(.07,w,2.7),group)
    for sy in [-w/2,w/2]:tube('silver',(x+face*.2,y+sy,.2),(x+face*.2,y+sy,2.8),.025,10,group)
    levels=5 if kind in ['cap','shoe','bag'] else 2
    for k in range(levels):
        h=.52+k*.43;box('blue' if kind=='bag' else 'white',(x,y,h),(.54,w,.035),group)
        box('warm',(x+face*.24,y,h-.026),(.018,w,.015),group)
        count=max(2,int(w/.36))
        for j in range(count):
            yy=y-w/2+(j+.5)*w/count;col=['navy','white','cream','pink','black','teal'][int(j+k*2)%6]
            if kind=='cap':cap(x+face*.04,yy,h+.02,col,group=group)
            elif kind=='shoe':shoe(x,yy,h+.02,col,group)
            elif kind=='bag':bag(x+face*.03,yy,h+.03,col,group)
    if kind=='clothes':
        tube('silver',(x+face*.12,y-w/2,1.94),(x+face*.12,y+w/2,1.94),.018,10,group)
        for j in range(max(3,int(w/.45))):
            yy=y-w/2+.25+j*.45
            # Flat garments face toward the entry, interspersed along rail.
            jacket(x+face*.15,yy,1.38,['navy','cream','teal','white','burgundy'][j%5],group,.85)
    for j in range(max(1,int(w/1.3))):box('silver',(x-face*.2,y-w/2+j*1.3,1.5),(.03,.035,2.8),group)

# Architecture. Sample footprint 10 m wide by 22 m deep, height is an explicit visual assumption.
box('floor',(0,11,-.08),(10,22,.16));box('concrete',(0,11,3.8),(10,22,.16),'ceiling')
box('plaster',(-5.07,11,1.85),(.14,22,3.7));box('plaster',(5.07,11,1.85),(.14,22,3.7));box('plaster',(0,22.04,1.85),(10,.12,3.7))
for y in [i*2.2 for i in range(11)]:box('grid',(0,y,.006),(10,.21,.01))
for x in [-4.9,-2.45,0,2.45,4.9]:box('grid',(x,11,.007),(.20,22,.012))
# Terrazzo aggregate, small geometry adds grain without external texture assets.
for i in range(6500):
    x=random.uniform(-4.95,4.95);y=random.uniform(0,22);s=random.uniform(.008,.024)
    box(random.choice(['grid','woodlight','white']),(x,y,.013),(s,s*.7,.003))
# Exposed roof beams, tracks, ducts, giant diffuse grid panels.
for y in [1,4,7,10,13,16,19,21.5]:
    box('concrete',(0,y,3.55),(10,.18,.3),'ceiling')
    for x in [-3.8,3.8]:
        box('silver',(x,y,3.3),(.06,2.7,.06),'ceiling')
        for dy in [-.8,0,.8]:
            tube('silver',(x,y+dy,3.31),(x,y+dy,3.05),.07,10,'ceiling')
            tube('light',(x,y+dy,3.04),(x,y+dy,3.015),.055,10,'ceiling')
for x in [-4.2,4.2]:tube('concrete',(x,0,3.55),(x,22,3.55),.15,18,'ceiling')
for y in [2,6.8,11.6,16.4,20.2]:
    box('silver',(0,y,3.4),(3.8,3.15,.07),'ceiling');box('light',(0,y,3.35),(3.73,3.08,.035),'ceiling')
    for dx in [-.63,.63]:box('silver',(dx,y,3.322),(.025,3.1,.016),'ceiling')
    box('silver',(0,y,3.32),(3.8,.025,.016),'ceiling')
# Storefront with black MLB fascia and vertical brushed-silver fins.
box('navy',(0,-.09,3.6),(10.3,.5,.8),'facade');sign('MLB',(0,-.36,3.37),.68,'white',group='facade')
box('silver',(0,.05,6),(10.3,.35,4),'facade')
for x in [i*.27-5 for i in range(38)]:box('plaster',(x,-.18,6),(.035,.10,4),'facade')
for x in [-5,5]:box('silver',(x,0,1.6),(.15,.3,3.2),'facade')
box('grid',(0,-1.2,-.05),(12,2.4,.1),'facade')
# Reconstructed sample fixture anchors; models styled to the reference photography.
D=json.loads((ROOT/'assets'/'brief-data.json').read_text(encoding='utf-8'))
fixtures=[f for f in D['fixtures'] if f['store_id']=='C']
anchors=[]
for f in fixtures:
    xx,yy,w,d=[a/1000 for a in f['rect_mm']];x=yy+d/2-5;y=xx+w/2;fid=f['fixture_id'];kind=f['type']
    anchors.append(dict(id=fid,x=x,z=-y,y=1.5,label=f['label'],rect=[yy-5,xx,d,w]))
    if kind in ['wall','cap_wall','bag_wall']:
        shelf_unit(x,y,w,{'wall':'clothes','cap_wall':'cap','bag_wall':'bag'}[kind],fid,1 if x<0 else -1)
    elif kind=='shoe_wall':
        # Iconic royal-blue stadium-like curved shoe display, based on wide-angle store references.
        cx=0;cy=19.35
        for j in range(6):
            z=.45+j*.38;rr=1.75
            for a in range(18):
                th=.15+a/17*2.85;px=cx+math.cos(th)*rr;py=cy+math.sin(th)*rr
                box('blue',(px,py,z),(.42,.46,.035),fid,th)
                if j<5 and a%2==0:shoe(px,py,z+.03,['white','cream','navy'][a%3],fid)
            for th in [.15,1.57,3]:tube('silver',(cx+math.cos(th)*rr,cy+math.sin(th)*rr,.1),(cx+math.cos(th)*rr,cy+math.sin(th)*rr,2.7),.025,10,fid)
        box('blue',(0,20,.25),(1.5,.65,.45),fid)
        anchors[-1]['x']=0;anchors[-1]['z']=-19.35;anchors[-1]['rect']=[-2,19,4,2.2]
        sign('FOOTWEAR',(0,21.96,2.85),.24,'navy')
    elif kind=='cap_island':
        box('silver',(x,y,.45),(d,w,.9),fid)
        for k in range(3):
            h=.95+k*.38;box('blue',(x,y,h),(d+.12,w+.08,.045),fid)
            for j in range(5):cap(x,y-w/2+.2+j*.34,h+.03,['navy','cream','white','green','black'][j],group=fid)
        for sy in [-w/2,w/2]:tube('silver',(x,y+sy,.9),(x,y+sy,1.85),.025,10,fid)
    elif kind=='table':
        box('wood',(x,y,.4),(d,w,.8),fid);box('blue',(x,y,.83),(d+.05,w+.05,.05),fid)
        for j in range(3):bag(x-.2,y-.6+j*.55,.86,['navy','cream','white'][j],fid)
        for k in range(4):box('white',(x+.2,y,.88+k*.055),(.35,.45,.05),fid)
    elif kind=='mannequin':
        tube('silver',(x,y,.02),(x,y,.14),.42,32,fid)
        for s in [-1,1]:tube('cream',(x+s*.12,y,.2),(x+s*.09,y,.95),.075,12,fid);shoe(x+s*.12,y-.08,.13,'white',fid)
        jacket(x,y,1.31,'teal',fid,1.05);tube('skin',(x,y,1.6),(x,y,1.72),.07,12,fid)
        sphere('skin',(x,y,1.83),(.1,.09,.14),fid);cap(x,y,1.88,'navy',group=fid)
# Blue promotional pedestal / illuminated tiled front, octagonal oak table.
for x in [-1.1,1.1]:
    box('light',(x,3,.46),(1.18,1.1,.92),'promo');box('blue',(x,3,.94),(1.25,1.18,.05),'promo')
    for j in range(5):box('grid',(x-.59+j*.295,2.442,.46),(.009,.008,.92),'promo')
    for h in [.2,.4,.6,.8]:box('grid',(x,2.441,h),(1.18,.008,.009),'promo')
    for k in range(2):shoe(x-.25+k*.4,2.9,.97,'white','promo')
tube('wood',(0,2,.03),(0,2,.56),.72,8,'promo');tube('white',(0,2,.56),(0,2,.62),.75,8,'promo');shoe(0,1.9,.65,'cream','promo')
sign('MLB',(0,2.02,1.08),.28,'blue',group='promo')
# Free-standing garment racks extend the dense visual rhythm of the photographed store.
for yi in [7.8,11.3,14.8]:
    for x in [-2.5,2.4]:
        group='racks';box('wood',(x,yi,.035),(1.6,1.5,.07),group)
        for side in [-.63,.63]:tube('silver',(x+side,yi,.08),(x+side,yi,1.8),.024,10,group)
        tube('silver',(x-.63,yi,1.8),(x+.63,yi,1.8),.024,10,group)
        for j in range(4):jacket(x-.48+j*.32,yi,1.25,['cream','teal','navy','white'][(j+int(yi))%4],group,.8)
# Front right stair: visible reference feature, bounded at upper landing in the prototype.
for j in range(14):box('floor',(3.3,.9+j*.24,(j+1)*.105),(1.65,.26,(j+1)*.21),'stairs')
for x in [2.46,4.14]:
    for j in range(0,14,3):tube('silver',(x,.9+j*.24,(j+1)*.21),(x,.9+j*.24,(j+1)*.21+1),.018,8,'stairs')
    tube('silver',(x,.9,1.21),(x,4.04,3.94),.025,10,'stairs')
sign('2F  /  KIDS',(4.99,1.1,2.3),.18,'white',(math.pi/2,0,math.pi/2),'stairs')
# Rear service block and a counter with monitor.
box('plaster',(4.1,18.8,1.6),(1.7,6.4,3.2),'service');box('navy',(3.23,20.4,1.1),(.03,1.2,2.2),'service')
box('wood',(3.48,13.4,.52),(.8,3.2,1.04),'counter');box('white',(3.48,13.4,1.07),(.9,3.3,.06),'counter')
box('black',(3.48,13.4,1.35),(.06,.44,.35),'counter');sign('FITTING',(0,21.94,2.45),.17,'white')
# Final grouped meshes; material batching makes the web model inexpensive to draw.
for (m,group),(vv,ff,sm) in G.items():
    me=bpy.data.meshes.new(group+'_'+m);me.from_pydata(vv,[],ff);me.materials.append(M[m]);me.update()
    ob=bpy.data.objects.new(group+'__'+m,me);bpy.context.collection.objects.link(ob);ob['model_group']=group
    for polygon in me.polygons:polygon.use_smooth=sm[polygon.index]
    # Flat geometry is intentional for shelves, faceted curves remain sufficiently dense.
scene=bpy.context.scene;scene.world.color=(.4,.4,.4)
scene['reference_note']='Public MLB Myeongdong photos (2024 renovation; latest capture date not verified). Sample C footprint, inferred heights and arrangement. No as-built accuracy claim.'
out=ROOT/'dist'/'assets';out.mkdir(parents=True,exist_ok=True)
(out/'anchors.json').write_text(json.dumps(anchors,ensure_ascii=False),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets'/'MLB_Myeongdong_Study.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'store.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_apply=True)
print('MODEL_COMPLETE',len(G),'groups',sum(len(g[1]) for g in G.values()),'faces')
