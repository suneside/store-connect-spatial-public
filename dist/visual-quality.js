import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export const productTemplates = new Map();
export function instanceProducts(root) {
  root.updateMatrixWorld(true);
  const batches = new Map(), firstPositions = new Map();
  root.traverse(o => {
    if (!o.isMesh || !o.userData.instanced_asset) return;
    const kind=o.userData.asset_type, pos=new THREE.Vector3().setFromMatrixPosition(o.matrixWorld);
    if (!firstPositions.has(kind)) firstPositions.set(kind,pos);
    if (pos.distanceTo(firstPositions.get(kind))<.001) {
      if (!productTemplates.has(kind)) productTemplates.set(kind,[]);
      const part=new THREE.Mesh(o.geometry,o.material);part.quaternion.copy(o.quaternion);
      part.scale.copy(o.scale);productTemplates.get(kind).push(part);
    }
    const key=o.geometry.uuid+'|'+o.material.uuid+'|'+o.userData.model_group;
    if(!batches.has(key))batches.set(key,[]);batches.get(key).push(o);
  });
  for(const parts of batches.values()) {
    const first=parts[0],batch=new THREE.InstancedMesh(first.geometry,first.material,parts.length);
    batch.name='Products_'+first.userData.model_group;batch.userData={...first.userData};
    batch.castShadow=true;batch.receiveShadow=true;
    parts.forEach((part,i)=>batch.setMatrixAt(i,part.matrixWorld));
    batch.instanceMatrix.needsUpdate=true;batch.computeBoundingSphere();
    parts.forEach(p=>p.removeFromParent());root.add(batch);
  }
  return {batches:batches.size,parts:[...batches.values()].reduce((s,p)=>s+p.length,0)};
}

export function createFinish(renderer,scene,camera,w,h) {
  const target=new THREE.WebGLRenderTarget(w,h,{type:THREE.HalfFloatType,samples:4});
  const composer=new EffectComposer(renderer,target);composer.addPass(new RenderPass(scene,camera));
  const ao=new GTAOPass(scene,camera,w,h);
  ao.updateGtaoMaterial({radius:.18,thickness:.12,distanceExponent:2,distanceFallOff:1,scale:1,samples:24});
  ao.blendIntensity=.55;
  ao.updatePdMaterial({radius:6,rings:3,samples:24});composer.addPass(ao);
  const bloom=new UnrealBloomPass(new THREE.Vector2(w,h),.012,.2,4);composer.addPass(bloom);
  composer.addPass(new OutputPass());
  renderer.info.autoReset=false;
  return {ao,bloom,render:()=>{renderer.info.reset();composer.render()},resize:(w,h)=>composer.setSize(w,h),quality:high=>{ao.enabled=high;bloom.enabled=high}};
}

const descriptions={
  cap:['6패널 베이스볼 캡','입체 패널 · 곡선형 챙 · 봉제선 · 통풍구 · 자수 로고',18090],
  jacket:['바시티 재킷','드레이프 · 가죽 소매 · 시보리 · 단추 · 입체 포켓',26308],
  shoe:['청키 스니커즈','다층 아웃솔 · 트레드 · 가죽 패널 · 신발끈 · 통풍구',27568],
  bag:['모노그램 숄더백','곡면 바디 · 파이핑 · 스트랩 · 금속 링 · 지퍼',23038]
};
export function openProductStudy(modal,environment) {
  modal('가까이 보는 상품 디테일',`<div class="study-tabs">${Object.entries(descriptions).map(([key,d])=>`<button data-study="${key}">${d[0]}</button>`).join('')}</div><div id="product-study"></div><div class="study-caption"><strong id="study-title"></strong><p id="study-description"></p><small id="study-stats"></small></div><p class="record-note">드래그로 회전 · 휠로 확대. 품목을 표현한 직접 제작 모델이며, 개별 SKU를 스캔한 복제품은 아닙니다.</p>`,'MATERIAL & FORM / DETAIL STUDY');
  const host=document.querySelector('#product-study'),scene=new THREE.Scene();scene.background=new THREE.Color('#e9e8e4');scene.environment=environment;scene.environmentIntensity=1.2;
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(host.clientWidth,380);renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;host.append(renderer.domElement);
  const camera=new THREE.PerspectiveCamera(34,host.clientWidth/380,.001,20),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;
  scene.add(new THREE.HemisphereLight('#ffffff','#64717c',2));const key=new THREE.DirectionalLight('#fff4e3',3);key.position.set(2,3,4);scene.add(key);
  let model;
  function show(kind){if(model)scene.remove(model);model=new THREE.Group();for(const p of productTemplates.get(kind)||[])model.add(p.clone());scene.add(model);
    if(kind==='bag')model.rotation.y=Math.PI;
    const box=new THREE.Box3().setFromObject(model),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());model.position.sub(center);const d=Math.max(size.x,size.y,size.z);camera.position.set(d*1.1,d*.5,d*1.8);controls.target.set(0,0,0);controls.minDistance=d*.7;controls.maxDistance=d*4;controls.update();
    const detail=descriptions[kind];document.querySelector('#study-title').textContent=detail[0];document.querySelector('#study-description').textContent=detail[1];document.querySelector('#study-stats').textContent=detail[2].toLocaleString()+' TRIANGLES · PBR MATERIALS';document.querySelectorAll('[data-study]').forEach(b=>b.classList.toggle('active',b.dataset.study===kind));
  }
  document.querySelectorAll('[data-study]').forEach(b=>b.onclick=()=>show(b.dataset.study));show('cap');
  let frame;function draw(){if(!host.isConnected||!document.querySelector('#dialog').open){cancelAnimationFrame(frame);controls.dispose();renderer.dispose();renderer.forceContextLoss();return}frame=requestAnimationFrame(draw);controls.update();renderer.render(scene,camera)}draw();
}
