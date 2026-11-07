import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export const catalog={
  cap:{label:'샘플 캡',sku:'HAT-001',image:'assets/products/cap.svg',description:'코드 생성 샘플 · 패널 · 곡선 챙'},
  shoe:{label:'레더 스니커즈',sku:'SHO-003',image:'assets/products/shoe.svg',description:'가죽 어퍼 · 스웨이드 토캡 · 검솔'},
  jacket:{label:'후드 경량 패딩',sku:'OUT-004',image:'assets/products/jacket.svg',description:'입체 퀼팅 · 허리 라인 · 후드와 지퍼'},
  bag:{label:'샘플 가방',sku:'BAG-001',image:'assets/products/bag.svg',description:'다이아 퀼팅 · 패브릭 핸들 · 샘플 자수'}
};
const loader=new GLTFLoader().setDRACOLoader(new DRACOLoader().setDecoderPath('./vendor/draco/').setWorkerLimit(2));
export const photoTemplates=new Map(), detailCache=new Map();
// Display colourways are illustrative; the detail viewer preserves the source photo.
const displayColours={navy:'#34465c',white:'#ffffff',cream:'#d3c5ab',pink:'#b58386',black:'#36393d',teal:'#426f7e',green:'#62725b',burgundy:'#81535a'};
export async function loadPhotoProducts(root,onProgress=()=>{},providedPlacements) {
  const placements=providedPlacements??await fetch('./assets/placements-v3.json').then(r=>r.json());
  let complete=0,batchCount=0;const lodBatches=[];
  await Promise.all(Object.keys(catalog).map(async kind=>{
    const [gltf,compact]=await Promise.all(['shop','compact'].map(lod=>loader.loadAsync('./assets/photo-products/'+kind+'-'+lod+'.glb')));
    const compactParts=[];compact.scene.traverse(p=>{if(p.isMesh)compactParts.push(p)});let partIndex=0;
    gltf.scene.updateMatrixWorld(true);photoTemplates.set(kind,gltf.scene);
    const positions=placements.filter(p=>p.kind===kind),groups=new Map();
    for(const p of positions){const key=p.fixture+':'+Math.floor(p.position[0]/4)+':'+Math.floor(p.position[2]/4);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(p)}
    gltf.scene.traverse(part=>{
      if(!part.isMesh)return;
      const low=compactParts[partIndex++]?.geometry??part.geometry;
      part.material.envMapIntensity=.75;
      for(const rows of groups.values()){
        const fixture=rows[0].fixture;
        const batch=new THREE.InstancedMesh(part.geometry,part.material,rows.length),dummy=new THREE.Object3D();
        batch.name=kind+'_'+fixture;batch.userData={model_group:fixture,asset_type:kind,reference_sku:catalog[kind].sku,photo_generated:true};batch.castShadow=true;batch.receiveShadow=true;
        rows.forEach((p,i)=>{dummy.position.set(...p.position);dummy.rotation.set(0,p.rotation,0);dummy.scale.setScalar(p.scale);dummy.updateMatrix();batch.setMatrixAt(i,dummy.matrix.clone().multiply(part.matrixWorld));if(kind==='jacket'||kind==='cap')batch.setColorAt(i,new THREE.Color(displayColours[p.display_color]||'#ffffff'))});
        if(batch.instanceColor)batch.instanceColor.needsUpdate=true;
        batch.instanceMatrix.needsUpdate=true;batch.computeBoundingSphere();root.add(batch);batchCount++;lodBatches.push({batch,near:part.geometry,far:low,center:batch.boundingSphere.center.clone(),high:true});
      }
    });onProgress(++complete,4);
  }));
  return {batches:batchCount,products:placements.length,source:'Original procedural geometry / public source samples',updateLod(position){let changed=false;for(const item of lodBatches){const high=position.distanceTo(item.center)<(item.high?9:7.5);if(high!==item.high){item.high=high;item.batch.geometry=high?item.near:item.far;changed=true}}return changed}};
}
export async function loadProductDetail(kind){
  if(!detailCache.has(kind))detailCache.set(kind,loader.loadAsync('./assets/photo-products/'+kind+'-detail.glb').then(g=>g.scene));
  return (await detailCache.get(kind)).clone(true);
}
export function openPhotoStudy(modal,environment){
  modal('공개 샘플 상품 디테일',`<div class="study-tabs">${Object.entries(catalog).map(([key,p])=>`<button data-study="${key}">${p.label}</button>`).join('')}</div><div class="photo-study-layout"><div id="product-study"></div><aside class="photo-reference"><img id="study-reference" alt="직접 작성한 품목 아이콘"><strong id="study-title"></strong><p id="study-description"></p><small>코드로 생성한 샘플 모델</small></aside></div><p class="record-note">드래그로 회전 · 휠로 확대. 공개 소스에는 직접 생성한 샘플 모델을 사용합니다. 실제 배포의 사진 기반 애셋은 별도입니다.</p>`,'PRODUCT / PHOTO TO 3D');
  const host=document.querySelector('#product-study'),scene=new THREE.Scene();scene.background=new THREE.Color('#e8e8e2');scene.environment=environment;scene.environmentIntensity=.7;
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(host.clientWidth,380);renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.8;host.append(renderer.domElement);
  const camera=new THREE.PerspectiveCamera(34,host.clientWidth/380,.001,20),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;
  scene.add(new THREE.HemisphereLight('#ffffff','#64717c',1));const key=new THREE.DirectionalLight('#fff4e3',1.5);key.position.set(2,3,4);scene.add(key);
  let model,version=0,disposed=false;
  async function show(kind){const v=++version;document.querySelectorAll('[data-study]').forEach(b=>b.classList.toggle('active',b.dataset.study===kind));const p=catalog[kind];document.querySelector('#study-title').textContent=p.label;document.querySelector('#study-description').textContent='모델 불러오는 중…';document.querySelector('#study-reference').src=p.image;
    try{const next=await loadProductDetail(kind);if(v!==version||disposed)return;if(model)scene.remove(model);model=next;scene.add(model);const box=new THREE.Box3().setFromObject(model),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());model.position.sub(center);const d=Math.max(size.x,size.y,size.z);camera.position.set(d*.8,d*.4,d*1.8);controls.target.set(0,0,0);controls.minDistance=d*.7;controls.maxDistance=d*4;controls.update();document.querySelector('#study-description').textContent=p.description;}catch{if(v===version&&!disposed)document.querySelector('#study-description').textContent='모델을 불러오지 못했습니다. 다른 상품을 선택하거나 다시 열어주세요.'}}
  document.querySelectorAll('[data-study]').forEach(b=>b.onclick=()=>show(b.dataset.study));show('cap');
  let frame;function draw(){if(!host.isConnected||!document.querySelector('#dialog').open){disposed=true;cancelAnimationFrame(frame);controls.dispose();renderer.dispose();renderer.forceContextLoss();return}frame=requestAnimationFrame(draw);controls.update();renderer.render(scene,camera)}draw();
}
