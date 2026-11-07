"""Reusable detailed retail apparel for Blender 5.2.

Functions return newly linked objects, centred on X/Y, Z-up, front towards -Y.
build_cap: approximately 0.23 W x 0.31 D x 0.16 H, sole at Z=0.
build_jacket: approximately 0.69 W x 0.19 D x 0.76 H, hem at Z=0.
All generated geometry is original; no external textures or downloads are used.
"""
import bpy
import math
from mathutils import Vector

TAU=math.tau

def _mat(materials,key,color,rough=.7,metal=0):
    if key in materials:return materials[key]
    m=bpy.data.materials.get('Apparel_'+key)
    if not m:
        m=bpy.data.materials.new('Apparel_'+key);m.use_nodes=True
        p=m.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value=(*color,1)
        p.inputs['Roughness'].default_value=rough
        p.inputs['Metallic'].default_value=metal
        m.diffuse_color=(*color,1)
    return m

def _mesh(name,verts,faces,mat,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    if mat:me.materials.append(mat)
    for f in me.polygons:f.use_smooth=smooth
    return ob

def _path(name,points,radius,mat,sides=6,closed=False):
    """A mesh tube following a polyline; lightweight seams can share one object."""
    vv=[];ff=[];n=len(points)
    pts=[Vector(p) for p in points]
    for i,p in enumerate(pts):
        if closed:t=(pts[(i+1)%n]-pts[(i-1)%n]).normalized()
        elif i==0:t=(pts[1]-p).normalized()
        elif i==n-1:t=(p-pts[i-1]).normalized()
        else:t=(pts[i+1]-pts[i-1]).normalized()
        a=t.cross(Vector((0,1,0)))
        if a.length<.01:a=t.cross(Vector((1,0,0)))
        a.normalize();b=t.cross(a)
        vv.extend(tuple(p+radius*(a*math.cos(j*TAU/sides)+b*math.sin(j*TAU/sides))) for j in range(sides))
    for i in range(n if closed else n-1):
        j=(i+1)%n
        ff.extend((i*sides+k,i*sides+(k+1)%sides,j*sides+(k+1)%sides,j*sides+k) for k in range(sides))
    if not closed:ff += [tuple(reversed(range(sides))),tuple((n-1)*sides+k for k in range(sides))]
    return _mesh(name,vv,ff,mat)

def _ellipsoid(name,center,scale,mat,segments=24,rings=12):
    vv=[];ff=[]
    for j in range(rings+1):
        p=math.pi*j/rings
        for i in range(segments):
            t=TAU*i/segments;vv.append((center[0]+scale[0]*math.sin(p)*math.cos(t),center[1]+scale[1]*math.sin(p)*math.sin(t),center[2]+scale[2]*math.cos(p)))
    for j in range(rings):
        for i in range(segments):ff.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
    return _mesh(name,vv,[tuple(reversed(f)) for f in ff],mat)

def _stitches(name,paths,mat,r=.00042,step=3):
    # Consolidate many discrete dashes into one mesh, avoiding hundreds of objects.
    vv=[];ff=[]
    for points in paths:
        for i in range(0,len(points)-1,step):
            a=Vector(points[i]);b=Vector(points[min(i+1,len(points)-1)])
            tangent=(b-a).normalized();u=tangent.cross(Vector((0,1,0)))
            if u.length<.01:u=tangent.cross(Vector((1,0,0)))
            u.normalize();w=tangent.cross(u);base=len(vv)
            for p in [a,b]:vv.extend(tuple(p+r*(u*math.cos(k*TAU/4)+w*math.sin(k*TAU/4))) for k in range(4))
            ff.extend((base+k,base+(k+1)%4,base+(k+1)%4+4,base+k+4) for k in range(4))
    return _mesh(name,vv,ff,mat)

def _letter(name,text,location,size,mat,extrude=.0006):
    cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER'
    cu.extrude=extrude;cu.bevel_depth=.00028;cu.bevel_resolution=2;cu.resolution_u=5
    ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob)
    ob.location=location;ob.rotation_euler=(math.pi/2,0,0);cu.materials.append(mat)
    return ob

def _patch(name,c,w,h,mat,r=.009):
    # Capsule-like rounded embroidered patch with a true closed perimeter.
    x,y,z=c;points=[]
    for cx,cz,start in [(x+w/2-r,z+h/2-r,0),(x-w/2+r,z+h/2-r,90),(x-w/2+r,z-h/2+r,180),(x+w/2-r,z-h/2+r,270)]:
        for k in range(9):
            a=math.radians(start+k*90/8);points.append((cx+r*math.cos(a),y,cz+r*math.sin(a)))
    vv=points+[(p[0],p[1]+.002,p[2]) for p in points];n=len(points)
    ff=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    ff.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return _mesh(name,vv,ff,mat,False)

def build_cap(materials):
    """Six-panel cotton cap with thickness, curved bill and embroidered monogram."""
    cloth=_mat(materials,'wool_navy',(.012,.023,.055),.88)
    dark=_mat(materials,'black',(.012,.015,.018),.9)
    thread=_mat(materials,'thread_ivory',(.85,.83,.73),.93)
    chrome=_mat(materials,'chrome',(.35,.38,.41),.3,.8)
    objects=[];segments=72;rings=26
    def crown(theta,phi,offset=0):
        # The six panels have a subtle fullness between stitched radial seams.
        fullness=1+.016*math.sin(3*(theta+math.pi/3))**2*math.sin(phi)**2
        xx=(.111+offset)*math.sin(phi)*math.cos(theta)*fullness
        yy=(.104+offset)*math.sin(phi)*math.sin(theta)*fullness
        zz=.019+(.131+offset)*math.cos(phi)
        # Firmer and taller front buckram; small back crown fabric ripples.
        front=max(0,-math.sin(theta))
        zz+=.007*front*math.sin(phi)**2
        yy+=.0018*math.sin(theta*12)*math.sin(phi)**4*(1-front)
        return (xx,yy,zz)
    vv=[];ff=[]
    for j in range(rings+1):
        phi=.014+(math.pi/2-.014)*j/rings
        vv += [crown(i*TAU/segments,phi) for i in range(segments)]
    for j in range(rings):
        for i in range(segments):ff.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
    ff.append(tuple(reversed(range(segments))))
    objects.append(_mesh('Cap_six_panel_crown',vv,[tuple(reversed(f)) for f in ff],cloth))
    # Interior sweatband ring is visible when viewed from underneath.
    bottom=[crown(i*TAU/72,math.pi/2,-.003) for i in range(72)]
    objects.append(_path('Cap_lower_seam',bottom,.0014,cloth,8,True))
    inner=[(p[0]*.97,p[1]*.97,p[2]-.009) for p in bottom]
    objects.append(_path('Cap_sweatband',inner,.006,dark,8,True))
    # Bill: 2D sheet with front contour, lateral bend and 2mm edge thickness.
    def brim(u,t):
        w=.086+.027*math.sin(t*math.pi*.73)
        x=u*w
        y=-.065-.145*t+.027*u*u*t
        z=.024-.012*t-.019*u*u*(.45+.55*t)+.004*math.sin(math.pi*t)
        return (x,y,z)
    nu=36;nt=18;verts=[]
    for lower in [False,True]:
        for j in range(nt+1):
            for i in range(nu+1):
                p=brim(-1+2*i/nu,j/nt);verts.append((p[0],p[1],p[2]-(.0025 if lower else 0)))
    count=(nu+1)*(nt+1);faces=[]
    for j in range(nt):
        for i in range(nu):
            a=j*(nu+1)+i;faces.extend([(a,a+nu+1,a+nu+2,a+1),(count+a,count+a+1,count+a+nu+2,count+a+nu+1)])
    boundary=list(range(nu+1))+[j*(nu+1)+nu for j in range(1,nt+1)]+[nt*(nu+1)+i for i in reversed(range(nu))]+[j*(nu+1) for j in reversed(range(1,nt))]
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):faces.append((a,b,b+count,a+count))
    objects.append(_mesh('Cap_curved_bill',verts,faces,cloth))
    objects.append(_path('Cap_bill_bound_edge',[brim(-1+2*i/nu,1) for i in range(nu+1)],.0012,cloth,6))
    stitchpaths=[]
    for t in [.48,.59,.70,.81,.92]:
        stitchpaths.append([(x,y,z+.0012) for x,y,z in [brim(-.97+1.94*i/80,t) for i in range(81)]])
    seams=[]
    for k in range(6):
        th=-math.pi/2-math.pi/6+k*TAU/6
        points=[crown(th,.07+(math.pi/2-.09)*j/45,.0006) for j in range(46)]
        objects.append(_path('Cap_panel_seam_%02d'%k,points,.00075,cloth,6))
        for offset in [-.012,.012]:stitchpaths.append([crown(th+offset,.10+(math.pi/2-.14)*j/74,.0010) for j in range(75)])
        # Ventilation eyelets sit on the actual crown tangent plane.
        theta=th+math.pi/6;phi=.98;c=Vector(crown(theta,phi,.0008));normal=Vector((c.x/.111,c.y/.104,(c.z-.019)/.131)).normalized()
        tang=Vector((-math.sin(theta),math.cos(theta),0));cross=normal.cross(tang).normalized()
        points=[tuple(c+.0024*(tang*math.cos(a*TAU/16)+cross*math.sin(a*TAU/16))) for a in range(16)]
        objects.append(_path('Cap_embroidered_eyelet_%02d'%k,points,.00065,cloth,6,True))
    objects.append(_stitches('Cap_precision_topstitch',stitchpaths,thread,.00027,3))
    objects.append(_ellipsoid('Cap_top_button',(0,0,.152),(.007,.007,.004),cloth,24,8))
    # Individual overlapping letters read as embroidered NY rather than an X.
    objects.append(_letter('Cap_N_embroidery','N',(-.003,-.099,.087),.042,thread,.0006))
    objects.append(_letter('Cap_Y_embroidery','Y',(.004,-.100,.087),.048,thread,.0007))
    # Rear adjustable cotton strap and brushed metal buckle.
    strap=[(-.032,.102,.032),(-.015,.108,.031),(.016,.108,.031),(.035,.102,.032)]
    objects.append(_path('Cap_adjustable_rear_strap',strap,.005,cloth,8))
    buckle=[(.01,.11,.023),(.03,.109,.023),(.03,.109,.041),(.01,.11,.041)]
    objects.append(_path('Cap_buckle',buckle,.0012,chrome,8,True))
    for o in objects:
        o['asset_type']='detailed_baseball_cap'
        o.location.z+=.010
    return objects

def build_jacket(materials):
    """Hanging varsity jacket with shaped raglan sleeves and constructed trims."""
    wool=_mat(materials,'wool_navy',(.018,.032,.062),.9)
    leather=_mat(materials,'leather_cream',(.67,.61,.48),.44)
    thread=_mat(materials,'thread_ivory',(.85,.83,.73),.94)
    rib=_mat(materials,'rib_knit',(.022,.035,.057),.94)
    chrome=_mat(materials,'chrome',(.36,.4,.43),.26,.85)
    dark=_mat(materials,'black',(.01,.014,.017),.8)
    objects=[];n=64;nr=30
    def profile(t):
        # Taper at hem; chest volume and shoulders; upper opening tapers to neck.
        if t<.14:return .177+t*.10,.071+t*.045
        if t<.74:return .191+(t-.14)*.035,.080+(t-.14)*.014
        if t<.88:return .212-(t-.74)*.26,.089-(t-.74)*.035
        return .175-(t-.88)*.85,.084-(t-.88)*.18
    def torso(theta,t,offset=0):
        w,d=profile(t);a=math.cos(theta);b=math.sin(theta)
        x=(w+offset)*math.copysign(abs(a)**.82,a)
        y=(d+offset)*math.copysign(abs(b)**.72,b)
        z=.065+t*.61
        # Several diagonal folds plus smaller broad wrinkles toward lower torso.
        front=max(0,-b);back=max(0,b)
        wrinkle=.004*math.sin(theta*7+t*17)*(1-t)**1.4+.002*math.sin(theta*15-t*20)*math.sin(t*math.pi)
        y+=math.copysign(wrinkle,b)
        z+=.007*math.cos(theta*4+.6)*math.sin(t*math.pi)*front
        return (x,y,z)
    vv=[];ff=[]
    for j in range(nr+1):vv.extend(torso(i*TAU/n,j/nr) for i in range(n))
    for j in range(nr):
        for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    objects.append(_mesh('Jacket_shaped_wool_body',vv,ff,wool))
    # Soft ribbed waistband with true micro ribs and contrasting knitted stripes.
    def ellipse_band(name,zmin,zmax,w,d,material,ribbing=True):
        count=96;rings=7;v=[];f=[]
        for j in range(rings+1):
            z=zmin+(zmax-zmin)*j/rings
            for i in range(count):
                t=i*TAU/count;rr=(.0012*math.cos(t*48) if ribbing else 0)
                v.append(((w+rr)*math.cos(t),(d+rr)*math.sin(t),z+.0015*math.sin(t*5)))
        for j in range(rings):
            for i in range(count):f.append((j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i))
        return _mesh(name,v,f,material)
    objects.append(ellipse_band('Jacket_ribbed_hem',.012,.077,.179,.073,rib))
    for z in [.031,.050]:objects.append(ellipse_band('Jacket_hem_ivory_stripe',z,z+.006,.181,.075,thread,False))
    # Raised centre placket, fasteners, and twin stitch tracks.
    placket=[(0,-profile(t)[1]-.004,.065+t*.61) for t in [i/38 for i in range(39)]]
    objects.append(_path('Jacket_front_placket',placket,.009,wool,10))
    stitchpaths=[]
    for x in [-.011,.011]:stitchpaths.append([(x,y-.003,z) for _,y,z in placket])
    for z in [.105,.185,.265,.345,.425,.505,.585]:
        t=(z-.065)/.61;y=-profile(t)[1]-.013
        objects.append(_ellipsoid('Jacket_press_stud',(0,y,z),(.0053,.0026,.0053),chrome,16,8))
        objects.append(_ellipsoid('Jacket_stud_inner',(0,y-.0025,z),(.0027,.0009,.0027),dark,12,6))
    # Open rib collar surrounding visible dark neck hole.
    collar=[]
    for i in range(65):
        t=TAU*i/64;collar.append((.065*math.cos(t),.061*math.sin(t),.680+.014*math.sin(t)))
    objects.append(_path('Jacket_stand_collar',collar,.014,rib,12,True))
    objects.append(_path('Jacket_collar_knit_stripe',[(x*1.05,y*1.05,z+.006) for x,y,z in collar],.003,thread,8,True))
    # Curved tapered sleeves sweep down from rounded shoulder to angled cuffs.
    for side in [-1,1]:
        def sleeve_center(t):return Vector((side*(.18+.16*t-.012*t*t),.006+.012*math.sin(t*math.pi),.596-.405*t))
        sv=[];sf=[];sn=40;sr=25
        for j in range(sr+1):
            t=j/sr;c=sleeve_center(t)
            tangent=(sleeve_center(min(1,t+.01))-sleeve_center(max(0,t-.01))).normalized()
            u=Vector((0,1,0));v=tangent.cross(u).normalized()
            radius=.075*(1-t)+.042*t
            for i in range(sn):
                a=i*TAU/sn
                # Restrained elbow and underarm folds, not an inflated cylinder.
                fold=(.0035*math.sin(t*32+a*2)+.002*math.cos(t*52-a*3))*math.sin(math.pi*t)**1.5
                sv.append(tuple(c+(radius+fold)*(u*math.cos(a)*.88+v*math.sin(a))))
        for j in range(sr):
            for i in range(sn):sf.append((j*sn+i,j*sn+(i+1)%sn,(j+1)*sn+(i+1)%sn,(j+1)*sn+i))
        objects.append(_mesh('Jacket_leather_sleeve_'+str(side),sv,sf,leather))
        seam=[tuple(sleeve_center(t)+Vector((0,-(.075*(1-t)+.042*t)*.88-.001,0))) for t in [i/60 for i in range(61)]]
        stitchpaths.extend([[(x+side*.006,y,z) for x,y,z in seam],[(x-side*.006,y,z) for x,y,z in seam]])
        objects.append(_path('Jacket_sleeve_seam_'+str(side),seam,.0012,thread,6))
        # Sleeve cuff rings follow the sloping forearm, with recessed dark sleeve mouth.
        end=sleeve_center(1);axis=(sleeve_center(1)-sleeve_center(.99)).normalized();u=Vector((0,1,0));v=axis.cross(u).normalized()
        for length,rad,material,name in [(.046,.044,rib,'ribbed_cuff'),(.007,.045,thread,'cuff_stripe')]:
            center=end+axis*(.020 if name=='ribbed_cuff' else .027);verts=[];faces=[];cn=64;cr=6
            for j in range(cr+1):
                c=center+axis*(length*(j/cr-.5))
                for i in range(cn):
                    a=i*TAU/cn;rr=rad+(.0008*math.cos(a*32) if material==rib else 0)
                    verts.append(tuple(c+rr*(u*math.cos(a)+v*math.sin(a))))
            for j in range(cr):
                for i in range(cn):faces.append((j*cn+i,j*cn+(i+1)%cn,(j+1)*cn+(i+1)%cn,(j+1)*cn+i))
            objects.append(_mesh('Jacket_'+name+str(side),verts,faces,material))
        # Welt pocket: angled leather lips and a visible dark recessed slit.
        x=side*.117
        pocket=[(x-side*.023,-.087,.235),(x+side*.025,-.089,.319)]
        objects.append(_path('Jacket_welt_pocket_shadow_'+str(side),pocket,.009,dark,8))
        objects.append(_path('Jacket_leather_welt_'+str(side),[(px-side*.008,py-.004,pz) for px,py,pz in pocket],.0045,leather,8))
        objects.append(_path('Jacket_pocket_lower_piping_'+str(side),[(px+side*.008,py-.004,pz) for px,py,pz in pocket],.0025,thread,6))
    objects.append(_stitches('Jacket_double_needle_stitching',stitchpaths,thread,.00065,2))
    # Chest chenille emblem and woven hem label; all geometry, usable in glTF.
    objects.append(_patch('Jacket_chest_patch',(-.105,-.091,.495),.074,.091,leather,.009))
    objects.append(_letter('Jacket_chest_N','N',(-.11,-.095,.499),.055,wool,.001))
    objects.append(_letter('Jacket_chest_Y','Y',(-.101,-.097,.499),.059,wool,.001))
    objects.append(_patch('Jacket_woven_hem_label',(.108,-.077,.055),.038,.018,thread,.002))
    objects.append(_letter('Jacket_label_wordmark','MLB',(.108,-.080,.055),.011,wool,.0002))
    # Sculpted hardwood hanger: triangular shoulder rails plus metal hook.
    hanger=[(-.198,.016,.601),(-.102,.016,.694),(0,.016,.724),(.102,.016,.694),(.198,.016,.601)]
    objects.append(_path('Jacket_hanger_shoulders',hanger,.008,leather,10))
    objects.append(_path('Jacket_hanger_crossbar',[(-.19,.016,.603),(.19,.016,.603)],.005,leather,10))
    hook=[(.022*math.cos(a),.016,.748+.022*math.sin(a)) for a in [math.pi*.08+i*math.pi*1.6/28 for i in range(29)]]
    hook += [(0,.016,.724)]
    objects.append(_path('Jacket_hanger_hook',hook,.0025,chrome,8))
    for o in objects:o['asset_type']='detailed_varsity_jacket'
    return objects
