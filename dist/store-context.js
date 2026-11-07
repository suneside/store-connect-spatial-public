import {DEFAULT_STORE,validateStore,worldPoint} from './store-schema.js';
export {DEFAULT_STORE};
const database=new Promise((resolve,reject)=>{const r=indexedDB.open('store-connect-spatial',1);r.onupgradeneeded=()=>r.result.createObjectStore('stores',{keyPath:'id'});r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});
async function db(mode,run){const d=await database;return new Promise((resolve,reject)=>{const tx=d.transaction('stores',mode),r=run(tx.objectStore('stores'));tx.oncomplete=()=>resolve(r.result);tx.onerror=()=>reject(tx.error)})}
export const savedStores=()=>db('readonly',s=>s.getAll());
export const saveStore=s=>db('readwrite',table=>table.put(s));
export async function storeApi(action,method='GET',body,store=DEFAULT_STORE){const response=await fetch(`/api/workspace?action=${action}&store=${encodeURIComponent(store)}`,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const result=await response.json();if(!response.ok)throw Error(result.error||'공유 연결을 확인하세요.');return result}
export const cloud={configured:false,authorized:false,error:''};
export async function syncStoreLibrary(){
  try{Object.assign(cloud,await storeApi('status'));const fragment=new URLSearchParams(location.hash.slice(1));if(fragment.has('invite')&&cloud.configured){await storeApi('join','POST',{invite:fragment.get('invite')});cloud.authorized=true;fragment.delete('invite');history.replaceState(null,'',location.pathname+location.search+(fragment.size?'#'+fragment:''))}
    if(cloud.authorized){const {stores}=await storeApi('stores');const local=await savedStores();for(const remote of stores){if(!local.find(s=>s.id===remote.id)?.dirty)await saveStore({...validateStore(remote),revision:remote.revision,dirty:false})}}
  }catch(e){cloud.error=e.message}
}
export async function shareStore(store){const {store:result}=await storeApi('stores','POST',{...store,revision:store.revision??0},store.id);await saveStore({...result,dirty:false});return result}
export async function loadStoreContext(baseData,baseAnchors){
  await syncStoreLibrary();
  const id=new URLSearchParams(location.search).get('store')||DEFAULT_STORE;
  if(id===DEFAULT_STORE){const config=validateStore(await fetch('./assets/public-store.json').then(r=>r.json()));return{id,name:config.name,floorLabel:config.floorLabel,data:baseData,anchors:baseAnchors,config};}
  const saved=(await savedStores()).find(s=>s.id===id);
  if(!saved)throw Error('이 매장 설정이 없습니다. 초대 링크로 참여하거나 매장 설정 JSON을 가져와 주세요.');
  const config=validateStore(saved),products=baseData.products;
  const data={...baseData,fixtures:config.fixtures.map(f=>({fixture_id:f.id,label:f.label,type:f.type,store_id:id,rect_mm:[f.xMm,f.yMm,f.widthMm,f.depthMm],fixed:f.fixed,capacity:f.capacity})),inventory:config.assortment.map(p=>({store_id:id,product_id:p.productId,carried:true,on_hand_qty:p.onHandQty,customer_reserved_qty:p.reservedQty,unsellable_qty:p.unsellableQty})),current_display:config.display.map(p=>({store_id:id,fixture_id:p.fixture,product_id:p.productId,quantity:p.quantity,display_mode:'shelf'})),work_records:[],field_notes:[],sales_summary:[],inbound:[],products};
  for(const row of config.assortment)if(!products.some(p=>p.product_id===row.productId))throw Error('등록되지 않은 상품 ID: '+row.productId);
  const anchors=config.fixtures.map(f=>{const point=worldPoint(config,f.xMm+f.widthMm/2,f.yMm+f.depthMm/2);return{id:f.id,label:f.label,x:point.x,z:point.z,y:f.heightMm/1000,rect:[(f.xMm-config.originMm[0])/1000,f.yMm/1000,f.widthMm/1000,f.depthMm/1000]}});
  return{id,name:config.name,floorLabel:config.floorLabel,data,anchors,config};
}
export function switchStore(id){const url=new URL(location.href);id===DEFAULT_STORE?url.searchParams.delete('store'):url.searchParams.set('store',id);location.assign(url)}
