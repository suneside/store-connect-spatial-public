"""Detailed, reusable retail accessory meshes for Blender 5.2.

All dimensions are metres; Z is up, front is -Y. Functions return newly
created MESH objects and never clear or render the caller's scene.
No external assets or dependencies are required.
"""
import bpy
import math
from mathutils import Vector

TAU = math.tau

def _material(materials, key, color, rough=.6, metal=0):
    if key in materials:
        return materials[key]
    name = 'detail_' + key
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    return mat

def _mesh(name, vertices, faces, material, smooth=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.materials.append(material)
    data.update()
    # Metre-scale box projection supports tiling PBR leather/fabric maps.
    uv = data.uv_layers.new(name='UVMap')
    for polygon in data.polygons:
        dominant=max(range(3),key=lambda i:abs(polygon.normal[i]))
        axes=(1,2) if dominant==0 else (0,2) if dominant==1 else (0,1)
        for loop_index in polygon.loop_indices:
            co=data.vertices[data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv=(co[axes[0]],co[axes[1]])
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    for polygon in data.polygons:
        polygon.use_smooth = smooth
    return obj

def _box(name, center, size, mat, bevel=.002, segments=3):
    x, y, z = center
    a, b, c = [v/2 for v in size]
    vertices = [(x+sx*a,y+sy*b,z+sz*c) for sx,sy,sz in
                [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                 (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    ob = _mesh(name, vertices, [(0,3,2,1),(4,5,6,7),(0,1,5,4),
                (1,2,6,5),(2,3,7,6),(3,0,4,7)], mat, False)
    if bevel:
        modifier=ob.modifiers.new('Tailored edge radius','BEVEL')
        modifier.width=bevel;modifier.segments=segments
    return ob

def _catmull(points, steps=8, closed=False):
    pts=[Vector(p) for p in points]
    n=len(pts);out=[]
    span=n if closed else n-1
    for i in range(span):
        p0=pts[(i-1)%n] if closed or i else pts[0]
        p1=pts[i];p2=pts[(i+1)%n]
        p3=pts[(i+2)%n] if closed or i+2<n else pts[-1]
        for j in range(steps):
            t=j/steps
            out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    if not closed:out.append(pts[-1])
    return out

def _path(name, points, radius, mat, sides=8, smooth=True, closed=False):
    pts=[Vector(p) for p in points];vertices=[]
    for i,p in enumerate(pts):
        prev=pts[i-1] if i else (pts[-1] if closed else pts[0])
        nxt=pts[(i+1)%len(pts)] if i+1<len(pts) or closed else pts[-1]
        tangent=(nxt-prev).normalized()
        u=tangent.cross(Vector((0,0,1)))
        if u.length < .001:u=tangent.cross(Vector((0,1,0)))
        u.normalize();v=tangent.cross(u)
        for j in range(sides):vertices.append(tuple(p+radius*(u*math.cos(TAU*j/sides)+v*math.sin(TAU*j/sides))))
    faces=[]
    for i in range(len(pts) if closed else len(pts)-1):
        ni=(i+1)%len(pts)
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,ni*sides+(j+1)%sides,ni*sides+j))
    if not closed:faces.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))])
    return _mesh(name,vertices,faces,mat,smooth)

def _ellipse(name, center, radii, tube_radius, mat, plane='xy', n=64, sides=8):
    x,y,z=center;a,b=radii
    if plane=='xy':pts=[(x+a*math.cos(TAU*i/n),y+b*math.sin(TAU*i/n),z) for i in range(n)]
    elif plane=='xz':pts=[(x+a*math.cos(TAU*i/n),y,z+b*math.sin(TAU*i/n)) for i in range(n)]
    else:pts=[(x,y+a*math.cos(TAU*i/n),z+b*math.sin(TAU*i/n)) for i in range(n)]
    return _path(name,pts,tube_radius,mat,sides,True,True)

def _stitches(name, points, material, length=.0025, radius=.00035, every=2):
    """One joined mesh for all short stitches along a seam."""
    points=[Vector(p) for p in points];verts=[];faces=[]
    for i in range(0,len(points)-1,every):
        delta=points[i+1]-points[i]
        if delta.length<.00001:continue
        direction=delta.normalized();a=points[i];b=a+direction*min(length,delta.length*.8)
        u=direction.cross(Vector((0,0,1)))
        if u.length<.001:u=direction.cross(Vector((0,1,0)))
        u.normalize();v=direction.cross(u)
        base=len(verts)
        for p in [a,b]:
            for j in range(4):verts.append(tuple(p+radius*(u*math.cos(TAU*j/4)+v*math.sin(TAU*j/4))))
        for j in range(4):faces.append((base+j,base+(j+1)%4,base+4+(j+1)%4,base+4+j))
    return _mesh(name,verts,faces,material,True)

def _ribbon(name, points, width, thick, mat, axis='x'):
    pts=[Vector(p) for p in points];vertices=[]
    for i,p in enumerate(pts):
        t=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]
        t.normalize()
        u=Vector((1,0,0)) if axis=='x' else Vector((0,1,0))
        u=(u-t*u.dot(t)).normalized();v=t.cross(u).normalized()
        vertices.extend([tuple(p+u*width/2+v*thick/2),tuple(p-u*width/2+v*thick/2),tuple(p-u*width/2-v*thick/2),tuple(p+u*width/2-v*thick/2)])
    faces=[]
    for i in range(len(pts)-1):
        for j in range(4):faces.append((4*i+j,4*i+(j+1)%4,4*i+4+(j+1)%4,4*i+4+j))
    faces.extend([(3,2,1,0),tuple(range(len(vertices)-4,len(vertices)))])
    return _mesh(name,vertices,faces,mat,True)

def _freeze(objects):
    """Apply edge modifiers and return mesh-only objects. No selection changes."""
    depsgraph=bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.modifiers:
            evaluated=obj.evaluated_get(depsgraph)
            data=bpy.data.meshes.new_from_object(evaluated,depsgraph=depsgraph)
            obj.modifiers.clear();old=obj.data;obj.data=data
            if old.users==0:bpy.data.meshes.remove(old)
    return objects

def build_sneaker(materials):
    """Chunky panelled leather sneaker, toe -Y; 0.126 x 0.318 x 0.15 m."""
    before=set(bpy.data.objects)
    leather=_material(materials,'shoe_leather',(.72,.70,.64),.42)
    rubber=_material(materials,'rubber',(.61,.60,.55),.77)
    meshmat=_material(materials,'mesh_fabric',(.34,.36,.36),.92)
    ivory=_material(materials,'thread_ivory',(.86,.84,.76),.77)
    chrome=_material(materials,'chrome',(.44,.46,.48),.25,.85)
    black=_material(materials,'black',(.014,.018,.022),.65)
    shadow=_material(materials,'shoe_suede',(.34,.32,.27),.94)
    # Foot-shaped multi-level sole. Width and sculpted sidewall vary around outline.
    outline=_catmull([(0,-.158,0),(.032,-.15,0),(.054,-.12,0),(.062,-.066,0),(.057,-.014,0),(.043,.043,0),(.043,.111,0),(.031,.147,0),(0,.157,0),(-.031,.149,0),(-.045,.118,0),(-.044,.055,0),(-.052,.002,0),(-.06,-.063,0),(-.054,-.119,0),(-.03,-.149,0)],6,True)
    n=len(outline)
    def sole(name,levels,mat):
        verts=[]
        for z,scale in levels:
            for p in outline:verts.append((p.x*scale,p.y*scale,z+.003*math.cos(p.y*16)))
        faces=[tuple(reversed(range(n)))]
        for j in range(len(levels)-1):faces += [(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for i in range(n)]
        faces.append(tuple((len(levels)-1)*n+i for i in range(n)))
        return _mesh(name,verts,faces,mat,True)
    sole('Sneaker / sculpted outsole',[(.004,.86),(.007,.96),(.011,1.0),(.02,1.0),(.024,.985)],rubber)
    sole('Sneaker / midsole heel cushion',[(.022,.97),(.026,1),(.034,.98),(.041,.91)],ivory)
    sole('Sneaker / welt leather rim',[(.038,.91),(.042,.92),(.045,.88)],leather)
    # Actual tread lugs and engraved-looking side segmentation.
    for j in range(13):
        y=-.135+j*.022
        width=.10 if y<0 else .073
        _box('Outsole tread / cross lug %02d'%j,(0,y,.0045),(width,.01,.006),rubber,.0015,2)
        for side in [-1,1]:
            _box('Outsole sidewall notch',(side*(width/2+.006),y,.016),(.007,.009,.012),shadow,.001,2)
    # Longitudinal sections of upper: heel collar is open, not a solid ellipsoid.
    profile=[(-.15,.004,.043,.052),(-.137,.031,.04,.064),(-.11,.048,.04,.076),(-.075,.054,.041,.084),(-.035,.051,.041,.092),(0,.045,.043,.111),(.04,.041,.045,.132),(.08,.039,.043,.142),(.12,.035,.04,.136),(.145,.014,.038,.106),(.15,.002,.04,.083)]
    points=_catmull(profile,5,False);rings=48;verts=[]
    for p in points:
        y,w,bottom,top=p;mid=(bottom+top)/2;rh=(top-bottom)/2
        for j in range(rings):
            th=TAU*j/rings
            # Soft panel creasing at lateral flex line.
            crease=1-.018*math.sin(y*240)*math.exp(-((y+.045)/.022)**2)
            verts.append((w*math.sin(th)*crease,y,mid+rh*math.cos(th)))
    faces=[]
    for i in range(len(points)-1):
        y=(points[i][0]+points[i+1][0])/2
        for j in range(rings):
            th=TAU*(j+.5)/rings
            if .025<y<.135 and math.cos(th)>.38:continue
            faces.append((i*rings+j,i*rings+(j+1)%rings,(i+1)*rings+(j+1)%rings,(i+1)*rings+j))
    _mesh('Sneaker / lasted leather upper',verts,faces,leather)
    # Dark sock cavity and inner side lining.
    _ellipse('Sneaker / padded collar binding',(0,.082,.126),(.033,.054),.0085,leather,n=64,sides=12)
    _ellipse('Sneaker / dark interior collar',(0,.082,.119),(.026,.047),.006,meshmat,n=64,sides=8)
    _mesh('Sneaker / deep sockliner',[(0,.08,.079)]+[(.026*math.cos(TAU*j/64),.082+.047*math.sin(TAU*j/64),.081) for j in range(64)],[(0,j+1,(j+1)%64+1) for j in range(64)],black)
    # Flexible mesh tongue underneath laces, with radiused stitched label.
    tongue=_catmull([(0,-.063,.084),(0,-.03,.098),(0,.006,.118),(0,.035,.141),(0,.055,.146)],8)
    _ribbon('Sneaker / padded tongue',tongue,.051,.008,meshmat)
    _box('Sneaker / tongue patch',(0,.042,.147),(.035,.024,.002),leather,.002,3)
    # Toe perforations follow the surface and are tiny dark discs.
    for row in range(4):
        yy=-.125+row*.011
        for col in range(-2,3):
            xx=col*.011;zz=.070+(yy+.125)*.26-abs(xx)*.16
            _ellipse('Toe perforation',(xx,yy,zz),(.00065,.00065),.00025,shadow,n=10,sides=4)
    # Side leather overlays and parallel stitches.
    for side in [-1,1]:
        toe=_catmull([(side*.019,-.146,.055),(side*.044,-.122,.064),(side*.052,-.085,.067),(side*.05,-.05,.061)],12)
        _path('Sneaker / toe bumper panel',toe,.005,shadow,10)
        _stitches('Toe bumper double stitch',[(p.x+side*.001,p.y,p.z+.003) for p in toe],ivory,every=2)
        overlay=_catmull([(side*.049,-.07,.063),(side*.045,-.02,.076),(side*.035,.045,.095),(side*.035,.11,.102),(side*.023,.14,.091)],12)
        _path('Sneaker / sculpted quarter overlay',overlay,.0045,leather,10)
        _stitches('Quarter edge stitches',[(p.x+side*.001,p.y,p.z+.003) for p in overlay],ivory,every=2)
        heel=_catmull([(side*.035,.075,.057),(side*.037,.11,.067),(side*.028,.143,.08),(0,.151,.09)],10)
        _path('Sneaker / heel stabilizer',heel,.005,shadow,10)
        # Vertical NY-inspired side monogram, laid onto side leather, genuinely raised.
        mx=side*.047
        for line in [[(mx,-.005,.061),(mx,-.005,.092),(mx,.024,.061),(mx,.024,.092)],[(mx,.005,.089),(mx,.016,.076),(mx,.03,.09)],[(mx,.016,.076),(mx,.016,.059)]]:
            _path('Sneaker / raised side monogram',line,.0016,black,8)
    # Eyelet stays and six real zigzag laces, each with round eyelet hardware.
    for side in [-1,1]:
        rail=_catmull([(side*.023,-.057,.088),(side*.024,-.018,.107),(side*.024,.025,.131)],8)
        _path('Sneaker / leather eyelet stay',rail,.0053,leather,10)
    for j in range(6):
        y=-.052+j*.0148;z=.091+j*.0082
        for side in [-1,1]:_ellipse('Sneaker / metal eyelet',(side*.024,y,z),(.0026,.0026),.00075,chrome,n=16,sides=6)
        yy=y+.014 if j<5 else y+.006;zz=z+.008
        lace=_catmull([(-.024,y,z+.001),(-.012,y+.003,z+.004),(.006,yy-.003,zz+.003),(.024,yy,zz)],4)
        _path('Sneaker / crossing cotton lace A',lace,.00135,ivory,8)
        lace2=_catmull([(.024,y,z+.002),(.012,y+.003,z+.005),(-.006,yy-.003,zz+.004),(-.024,yy,zz+.001)],4)
        _path('Sneaker / crossing cotton lace B',lace2,.00135,ivory,8)
    for side in [-1,1]:
        bow=_catmull([(0,.027,.141),(side*.016,.014,.145),(side*.032,.026,.143),(side*.013,.035,.144),(0,.027,.141)],7)
        _path('Sneaker / bow loop',bow,.0013,ivory,8)
    pull=_catmull([(0,.133,.107),(0,.15,.135),(0,.145,.155),(0,.128,.144)],8)
    _ribbon('Sneaker / woven heel pull tab',pull,.013,.002,black)
    return _freeze([o for o in bpy.data.objects if o not in before])

def build_bag(materials):
    """Structured leather hobo bag; detailed gussets, piping, strap and hardware."""
    before=set(bpy.data.objects)
    leather=_material(materials,'bag_leather',(.20,.105,.055),.38)
    ivory=_material(materials,'thread_ivory',(.75,.62,.42),.8)
    metal=_material(materials,'gold',(.67,.43,.16),.23,.85)
    black=_material(materials,'black',(.018,.014,.012),.8)
    # A rounded rectangular cross section whose top dips at the opening.
    n=72;levels=24;verts=[]
    for j in range(levels+1):
        t=j/levels;z=.014+t*.199
        wx=.117+.022*math.sin(math.pi*t*.88)-.014*t*t
        dy=.037+.012*math.sin(math.pi*t)-.004*t
        for k in range(n):
            a=TAU*k/n
            sx=math.copysign(abs(math.cos(a))**.56,math.cos(a));sy=math.copysign(abs(math.sin(a))**.56,math.sin(a))
            x=wx*sx;y=dy*sy
            # Sculpted leather folds at side-gusset junctions.
            y += math.copysign(.0018*math.sin(t*math.pi*3)*abs(sx)**8,y)
            top_dip=.024*(1-abs(sx)**2)*t**7
            verts.append((x,y,z-top_dip))
    faces=[tuple(reversed(range(n)))]
    for j in range(levels):faces += [(j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k) for k in range(n)]
    _mesh('Bag / tailored leather shell',verts,faces,leather)
    # A visible inner rim and a dark recessed interior, not a flat solid cap.
    top=[Vector(verts[levels*n+k]) for k in range(n)]
    _path('Bag / rolled opening edge',top,.0025,leather,10,True,True)
    inset=[(p.x*.96,p.y*.88,p.z-.009) for p in top]
    _mesh('Bag / suede interior liner',[(0,0,.145)]+inset,[(0,k+1,(k+1)%n+1) for k in range(n)],black)
    # Front and rear panel perimeter seams, laid onto the gently bulged body.
    for side in [-1,1]:
        y=side*.047
        seam=_catmull([(-.105,y*.73,.034),(-.121,y*.9,.058),(-.124,y,.13),(-.109,y*.78,.195),(0,y*.78,.181),(.109,y*.78,.195),(.124,y,.13),(.121,y*.9,.058),(.105,y*.73,.034),(0,y*.84,.025)],7,True)
        # Project the piping onto the same curved shell rather than a flat plane.
        for p in seam:
            t=max(0,min(1,(p.z-.014)/.199))
            wx=.117+.022*math.sin(math.pi*t*.88)-.014*t*t
            dy=.037+.012*math.sin(math.pi*t)-.004*t
            sx=min(.995,abs(p.x/wx));cosine=sx**(1/.56)
            surface=dy*max(0,1-cosine*cosine)**.28+.0018*math.sin(t*math.pi*3)*sx**8
            p.y=side*(surface+.0006)
        _path('Bag / panel piping',seam,.0015,leather,8,True,True)
        _stitches('Bag / saddle stitch',[(p.x*.975,p.y*1.012,p.z+.002) for p in seam],ivory,length=.0022,every=1)
    # Rolled shoulder strap and two substantial metal rings.
    for side in [-1,1]:
        _ellipse('Bag / cast brass strap ring',(side*.108,0,.218),(.011,.016),.0023,metal,'xz',40,10)
        tab=_catmull([(side*.109,-.015,.173),(side*.113,-.012,.205),(side*.109,0,.229),(side*.109,.013,.205),(side*.109,.017,.178)],5)
        _ribbon('Bag / folded strap attachment',tab,.016,.003,leather)
        _box('Bag / brass rivet',(side*.109,-.017,.19),(.004,.002,.004),metal,.001,3)
    strap=_catmull([(-.108,0,.232),(-.103,.003,.30),(-.071,.006,.377),(0,.009,.405),(.071,.006,.377),(.103,.003,.30),(.108,0,.232)],9)
    _ribbon('Bag / shaped leather shoulder strap',strap,.021,.005,leather,axis='y')
    for side in [-1,1]:_stitches('Bag / strap stitching',[(p.x,p.y+side*.008,p.z+.003) for p in strap],ivory,length=.0025,every=1)
    # Zipper across the recessed opening, with individually formed teeth.
    for row in [-1,1]:
        _path('Bag / zipper tape',[(-.089,row*.003,.189),(.089,row*.003,.189)],.0017,black,6)
        for j in range(42):_box('Bag / zipper tooth',(-.086+j*.0042,row*.002,.19),(.0018,.0028,.0018),metal,.00035,2)
    _box('Bag / zipper slider',(.083,0,.194),(.012,.008,.004),metal,.0015,3)
    _ellipse('Bag / zipper pull',(.091,-.003,.198),(.006,.013),.0015,metal,'xy',24,8)
    # Raised front monogram in brass, contrasting subtly with grained leather.
    y=-.050
    for pts in [[(-.024,y,.106),(-.024,y,.143),(.004,y,.106),(.004,y,.143)],
                [(-.008,y,.143),(.006,y,.124),(.022,y,.143)],[(.006,y,.124),(.006,y,.103)]]:
        _path('Bag / raised brass monogram',pts,.0017,metal,10)
    for side in [-1,1]:
        for front in [-1,1]:_box('Bag / base protection foot',(side*.087,front*.025,.009),(.009,.009,.007),metal,.0025,4)
    return _freeze([o for o in bpy.data.objects if o not in before])

def asset_stats(objects):
    vertices=triangles=0
    for obj in objects:
        if obj.type!='MESH':continue
        vertices+=len(obj.data.vertices)
        triangles+=sum(max(0,len(p.vertices)-2) for p in obj.data.polygons)
    return {'objects':len(objects),'vertices':vertices,'triangles':triangles}

if __name__=='__main__':
    # Optional geometry-only validation. This never renders or opens a UI.
    import json
    sneaker=build_sneaker({});bag=build_bag({})
    print('ACCESSORY_STATS',json.dumps({'sneaker':asset_stats(sneaker),'bag':asset_stats(bag)}))
