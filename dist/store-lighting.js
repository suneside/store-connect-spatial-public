import * as THREE from 'three';
import {worldPoint} from './store-schema.js';

// A neutral display transform keeps retail colours stable under bright shop lights.
export function configureStoreLighting(scene,renderer,store){
  renderer.toneMapping=THREE.NeutralToneMapping;
  renderer.toneMappingExposure=.88;
  scene.environmentIntensity=.46;
  scene.background.set('#d8d7d3');
  scene.fog?.color.copy(scene.background);
  scene.traverse(o=>{
    if(o.isHemisphereLight){o.color.set('#fffaf4');o.groundColor.set('#8c8982');o.intensity=.44}
    if(o.isDirectionalLight){o.color.set('#fff9f1');o.intensity=1.55}
    if(o.isPointLight){o.color.set('#fffaf3');o.intensity=10;o.decay=2}
  });
  if(store){
    const c=worldPoint(store,store.widthMm/2,store.depthMm/2);let point=0;
    scene.traverse(o=>{if(o.isDirectionalLight){o.position.set(c.x-4,store.heightMm/1000+12,c.z+6);o.target.position.set(c.x,0,c.z)}if(o.isPointLight){const p=worldPoint(store,store.widthMm/2,store.depthMm*(++point)/5);o.position.set(p.x,store.heightMm/1000-.2,p.z)}});
  }
  // Track lights illuminate merchandise from above and the aisle, like the reference.
  for(const z of [-3.5,-9,-15.5,-20])for(const side of [-1,1]){
    const spot=new THREE.SpotLight('#fff5e8',30,9,.68,.65,2);
    spot.position.set(side*2.7,3.1,z);spot.target.position.set(side*4.25,1.1,z-.35);
    if(store){const p=worldPoint(store,store.widthMm*(side<0?.25:.75),store.depthMm*Math.abs(z)/24),t=worldPoint(store,store.widthMm*(side<0?.1:.9),store.depthMm*Math.abs(z)/24);spot.position.set(p.x,store.heightMm/1000-.2,p.z);spot.target.position.set(t.x,1.1,t.z)}
    spot.castShadow=z===-3.5;spot.shadow.mapSize.set(1024,1024);spot.shadow.normalBias=.003;spot.shadow.bias=-.00003;
    spot.shadow.camera.near=.15;spot.shadow.camera.far=9;scene.add(spot,spot.target);
  }
}
export function calibrateStoreMaterials(root){
  const seen=new Set();
  root.traverse(o=>{
    if(!o.isMesh)return;
    for(const m of (Array.isArray(o.material)?o.material:[o.material])){
      if(seen.has(m))continue;seen.add(m);
      const name=m.name.split('.')[0];
      m.envMapIntensity=o.userData.photo_generated?.6:.75;
      if(name==='blue'){m.color.set('#354f88');m.roughness=.42;m.metalness=.08}
      if(name==='floor'){m.color.set('#d0cfc7');m.roughness=.65;m.clearcoat=.03}
      if(name==='grid'){m.color.set('#7a7e79');m.roughness=.84}
      if(name==='white'){m.color.set('#d8d8d1');m.roughness=.76}
      if(name==='plaster'){m.color.set('#afb2ac');m.roughness=.92}
      if(name==='wood'||name==='woodlight'){m.color.set('#d2c7b6');m.roughness=.68}
      if(name==='silver'||name==='chrome'){m.roughness=.32;m.envMapIntensity=.6}
      if(name==='light'||name==='warm')m.emissiveIntensity=Math.min(m.emissiveIntensity,.9);
    }
  });
}
