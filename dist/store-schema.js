// Shared browser/server validation. Dimensions are always millimetres, never NTS pixels.
export const DEFAULT_STORE='myeongdong';
export const fixtureTypes=['wall','cap_wall','cap_island','shoe_wall','bag_wall','table','mannequin'];
const idPattern=/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/;
const fail=m=>{throw Object.assign(new Error(m),{status:400})};
const number=(n,min,max,label)=>{if(!Number.isFinite(n)||n<min||n>max)fail(label+' 범위를 확인하세요.');return n};
const text=(s,max,label)=>{if(typeof s!=='string'||!s.trim()||s.length>max)fail(label+'을 확인하세요.');return s.trim()};
export const validStoreId=id=>typeof id==='string'&&idPattern.test(id);
export function validateStore(raw){
  if(!raw||!validStoreId(raw.id)||raw.id===DEFAULT_STORE)fail('매장 ID를 확인하세요.');
  const widthMm=number(raw.widthMm,2000,100000,'매장 폭'),depthMm=number(raw.depthMm,2000,100000,'매장 깊이');
  const heightMm=number(raw.heightMm,2000,10000,'층 높이');
  const originMm=raw.originMm??[widthMm/2,0];if(!Array.isArray(originMm)||originMm.length!==2)fail('원점 좌표를 확인하세요.');
  originMm.forEach(v=>number(v,-100000,100000,'원점'));
  const rotationDeg=number(raw.rotationDeg??0,-360,360,'도면 회전');
  for(const key of ['assortment','display','keepClearMm'])if(raw[key]!==undefined&&!Array.isArray(raw[key]))fail(key+' 목록 형식을 확인하세요.');
  let outlineMm=raw.outlineMm??[[0,0],[widthMm,0],[widthMm,depthMm],[0,depthMm]];
  if(!Array.isArray(outlineMm)||outlineMm.length<3||outlineMm.length>40)fail('외곽 점은 3~40개로 입력하세요.');
  outlineMm=outlineMm.map(p=>{if(!Array.isArray(p)||p.length!==2)fail('외곽 좌표 오류');return[number(p[0],0,widthMm,'외곽 X'),number(p[1],0,depthMm,'외곽 Y')]});
  if(Math.abs(outlineMm.reduce((area,p,i)=>{const q=outlineMm[(i+1)%outlineMm.length];return area+p[0]*q[1]-q[0]*p[1]},0))<1000000)fail('유효한 매장 외곽 면적이 필요합니다.');
  if(!Array.isArray(raw.fixtures)||raw.fixtures.length<1||raw.fixtures.length>60)fail('집기는 1~60개 등록하세요.');
  const ids=new Set();
  const fixtures=raw.fixtures.map(f=>{
    if(!validStoreId(f.id)||ids.has(f.id))fail('집기 ID는 중복 없이 입력하세요.');ids.add(f.id);
    if(!fixtureTypes.includes(f.type))fail('집기 종류를 확인하세요.');
    const w=number(f.widthMm,200,widthMm,'집기 폭'),d=number(f.depthMm,150,depthMm,'집기 깊이');
    const x=number(f.xMm,0,widthMm-w,'집기 X'),y=number(f.yMm,0,depthMm-d,'집기 Y');
    return{id:f.id,label:text(f.label,60,'집기 이름'),type:f.type,xMm:x,yMm:y,widthMm:w,depthMm:d,heightMm:number(f.heightMm??1800,200,heightMm,'집기 높이'),rotationDeg:number(f.rotationDeg??0,-360,360,'집기 회전'),fixed:f.fixed!==false,capacity:number(f.capacity??24,1,500,'진열 한도')};
  });
  let planImage=raw.planImage||'';
  if(planImage&&(!/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/]+=*$/.test(planImage)||planImage.length>1500000))fail('도면은 1MB 이하 PNG·JPG·WebP로 올리세요.');
  const assortment=(raw.assortment??[]).map(r=>({productId:text(r.productId,64,'상품 ID'),onHandQty:number(r.onHandQty,0,99999,'재고'),reservedQty:number(r.reservedQty??0,0,99999,'예약'),unsellableQty:number(r.unsellableQty??0,0,99999,'판매 불가')}));
  if(assortment.length>300||new Set(assortment.map(r=>r.productId)).size!==assortment.length)fail('상품 ID가 중복되거나 300종을 넘었습니다.');
  const display=(raw.display??[]).map(r=>{if(!ids.has(r.fixture)||!assortment.some(p=>p.productId===r.productId))fail('진열에 없는 집기·상품 ID가 있습니다.');return{fixture:r.fixture,productId:r.productId,quantity:number(r.quantity,1,500,'진열 수량')}});
  if(display.length>1000||new Set(display.map(r=>r.fixture+'|'+r.productId)).size!==display.length)fail('동일 집기·상품의 진열 수량은 한 줄로 합쳐 주세요.');
  const keepClearMm=(raw.keepClearMm??[]).map(r=>{if(!Array.isArray(r)||r.length!==4)fail('통로 좌표 오류');return[number(r[0],0,widthMm,'통로 X'),number(r[1],0,depthMm,'통로 Y'),number(r[2],0,widthMm,'통로 폭'),number(r[3],0,depthMm,'통로 깊이')]});
  return{id:raw.id,name:text(raw.name,80,'매장 이름'),floorLabel:text(raw.floorLabel||'1F',20,'층 이름'),widthMm,depthMm,heightMm,originMm,rotationDeg,outlineMm,keepClearMm,planImage,fixtures,assortment,display};
}
export function worldPoint(store,x,y){
  const a=store.rotationDeg*Math.PI/180,px=(x-store.originMm[0])/1000,py=(y-store.originMm[1])/1000;
  return{x:px*Math.cos(a)-py*Math.sin(a),z:-(px*Math.sin(a)+py*Math.cos(a))};
}
export function insidePolygon(x,y,points){let inside=false;for(let i=0,j=points.length-1;i<points.length;j=i++){const a=points[i],b=points[j];if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])inside=!inside}return inside;}
export function planPoint(store,x,z){const a=-store.rotationDeg*Math.PI/180;return{x:(x*Math.cos(a)+z*Math.sin(a))*1000+store.originMm[0],y:(x*Math.sin(a)-z*Math.cos(a))*1000+store.originMm[1]};}
export function fixtureContains(store,f,x,z,margin=0){const p=planPoint(store,x,z),cx=f.xMm+f.widthMm/2,cy=f.yMm+f.depthMm/2,a=-f.rotationDeg*Math.PI/180;const dx=p.x-cx,dy=p.y-cy;return Math.abs(dx*Math.cos(a)-dy*Math.sin(a))<f.widthMm/2+margin*1000&&Math.abs(dx*Math.sin(a)+dy*Math.cos(a))<f.depthMm/2+margin*1000;}
