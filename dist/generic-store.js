import * as T from 'three';
import {worldPoint} from './store-schema.js';
const colours={navy:'navy',black:'black',cream:'cream',white:'white',beige:'cream',pink:'pink',blue:'teal',green:'green',brown:'cream'};
function rounded(w,h,d,r=.014){r=Math.min(r,w/4,h/4,d/4);const s=new T.Shape(),x=-w/2,y=-d/2;s.moveTo(x+r,y);s.lineTo(x+w-r,y);s.quadraticCurveTo(x+w,y,x+w,y+r);s.lineTo(x+w,y+d-r);s.quadraticCurveTo(x+w,y+d,x+w-r,y+d);s.lineTo(x+r,y+d);s.quadraticCurveTo(x,y+d,x,y+d-r);s.lineTo(x,y+r);s.quadraticCurveTo(x,y,x+r,y);const g=new T.ExtrudeGeometry(s,{depth:Math.max(.001,h-2*r),bevelEnabled:true,bevelThickness:r,bevelSize:r/2,bevelSegments:3,steps:1,curveSegments:5});g.rotateX(-Math.PI/2);g.translate(0,-h/2+r,0);return g}
export function buildGenericStore(store,products){
  const root=new T.Group(),placements=[],walls=[];
  const mats={wood:new T.MeshStandardMaterial({color:'#967754',roughness:.68}),shelf:new T.MeshStandardMaterial({color:'#c7c5ba',roughness:.64}),steel:new T.MeshStandardMaterial({color:'#939c9e',metalness:.85,roughness:.3}),wall:new T.MeshStandardMaterial({color:'#bdbeb7',roughness:.92}),floor:new T.MeshStandardMaterial({color:'#bab8ae',roughness:.72}),dark:new T.MeshStandardMaterial({color:'#323c42',roughness:.68})};
  const textureLoader=new T.TextureLoader();for(const [key,file]of [['wood','oak.jpg'],['floor','terrazzo.png']]){const texture=textureLoader.load('./assets/materials/'+file);texture.colorSpace=T.SRGBColorSpace;texture.wrapS=texture.wrapT=T.RepeatWrapping;texture.anisotropy=4;mats[key].map=texture}
  const box=(group,w,h,d,x,y,z,material)=>{const mesh=new T.Mesh(rounded(w,h,d),material);mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData.model_group=group.userData.model_group;group.add(mesh);return mesh};
  const points=store.outlineMm.map(p=>worldPoint(store,...p)),shape=new T.Shape(points.map(p=>new T.Vector2(p.x,-p.z)));
  const floor=new T.Mesh(new T.ExtrudeGeometry(shape,{depth:.08,bevelEnabled:false}),mats.floor);floor.geometry.rotateX(-Math.PI/2);floor.position.y=-.08;floor.receiveShadow=true;root.add(floor);
  for(let i=0;i<points.length;i++){const a=points[i],b=points[(i+1)%points.length],length=Math.hypot(a.x-b.x,a.z-b.z);if(i===0)continue;const wall=box(root,length,store.heightMm/1000,.08,(a.x+b.x)/2,store.heightMm/2000,(a.z+b.z)/2,mats.wall);wall.rotation.y=-Math.atan2(b.z-a.z,b.x-a.x);wall.name='store__plaster';walls.push(wall)}
  for(const f of store.fixtures){
    const g=new T.Group(),c=worldPoint(store,f.xMm+f.widthMm/2,f.yMm+f.depthMm/2),w=f.widthMm/1000,d=f.depthMm/1000,h=f.heightMm/1000;
    g.userData.model_group=f.id;g.position.set(c.x,0,c.z);g.rotation.y=(f.rotationDeg+store.rotationDeg)*Math.PI/180;root.add(g);
    const garment=f.type==='wall',table=f.type==='table'||f.type==='mannequin';
    box(g,w,.10,d,0,.05,0,mats.dark);box(g,w,.28,d,0,.24,0,mats.wood);
    const heights=table?[Math.min(h,.86)]:garment?[h-.12]:Array.from({length:Math.max(2,Math.min(5,Math.floor(h/.4)))},(_,i)=>.52+i*.38);
    if(!table){for(const x of [-w/2+.035,w/2-.035])box(g,.035,h,.035,x,h/2,-d/2+.035,mats.steel);if(garment){box(g,w,.035,.035,0,h-.1,0,mats.steel)}else{box(g,w,h-.36,.035,0,(h+.36)/2,-d/2+.025,mats.wall)}}
    for(const y of heights)if(!garment)box(g,w+.02,.035,d+.02,0,y,0,mats.shelf);
    box(g,w-.02,.012,.012,0,.11,d/2+.002,mats.dark);
    for(const y of heights)if(!garment)for(const x of [-w*.4,w*.4]){box(g,.018,.018,d*.8,x,y-.028,0,mats.steel);box(g,.018,.12,.018,x,y-.08,-d*.35,mats.steel)}
    const rows=store.display.filter(r=>r.fixture===f.id);let placed=0;
    for(const row of rows){const product=products.find(p=>p.product_id===row.productId),kind=product?.category==='cap'?'cap':product?.category==='shoes'?'shoe':product?.category==='bag'?'bag':'jacket';const count=Math.min(row.quantity,12,Math.max(0,24-placed));
      for(let i=0;i<count;i++,placed++){
        const perRow=Math.max(1,Math.floor(w/(kind==='jacket'?.45:.36))),level=garment?0:Math.floor(placed/perRow)%heights.length;
        const x=-w/2+w/(perRow*2)+(placed%perRow)*w/perRow,z=0,y=garment?h-.87:heights[level]+.025;
        const pos=new T.Vector3(x,y,z).applyAxisAngle(new T.Vector3(0,1,0),g.rotation.y).add(g.position);
        placements.push({kind,fixture:f.id,position:pos.toArray(),rotation:g.rotation.y,scale:1,display_color:colours[product?.color_family]||'white'});
      }
    }
  }
  return{root,placements,walls};
}
