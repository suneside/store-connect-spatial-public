import test from 'node:test';
import assert from 'node:assert/strict';
import handler,{validateTask,transition} from '../api/workspace.js';
const draft={id:'12345678-1234-4123-8123-123456789abc',fixture:'C-S01',title:'슈즈장 확인',owner:'매장 담당자',body:'가려진 하단을 확인해주세요.',status:'reviewed'};
test('requests reject unknown fixtures and cannot inject a reviewed status',()=>{assert.equal(validateTask(draft).status,'requested');assert.throws(()=>validateTask({...draft,fixture:'another-store'}))});
test('completion requires a report; review follows completion; unsafe images rejected',()=>{const initial=validateTask(draft);assert.throws(()=>transition(initial,{status:'reviewed',note:'skip'}));assert.throws(()=>transition(initial,{status:'completed',note:''}));assert.throws(()=>transition(initial,{status:'completed',note:'checked',evidence:'data:image/svg+xml;base64,AAAA'}));const completed=transition(initial,{status:'completed',note:'하단 재진열 완료'});assert.equal(transition(completed,{status:'reviewed',note:'재확인'}).history.length,3);assert.equal(transition(completed,{status:'requested',note:'측면 추가 확인'}).status,'requested')});
function response(){return{headers:{},setHeader(k,v){this.headers[k]=v},status(v){this.code=v;return this},json(v){this.body=v;return this}}}
test('public demo allows anonymous shared workflow without exposing credentials; still rejects foreign origins',async()=>{
  const before={...process.env};const original=globalThis.fetch;const calls=[];
  Object.assign(process.env,{SUPABASE_URL:'https://example.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'test-only-secret',SPATIAL_WORKSPACE_ID:draft.id,SPATIAL_PUBLIC_DEMO:'true'});delete process.env.SPATIAL_DEMO_INVITE;
  globalThis.fetch=async(url,options)=>{calls.push({url,options});return{ok:true,status:200,json:async()=>options.method==='POST'?[{payload:JSON.parse(options.body).payload,revision:1}]:[]}};
  const headers={host:'demo.test','content-type':'application/json'};
  try{
    let r=response();await handler({method:'GET',query:{action:'status'},headers},r);assert.equal(r.body.authorized,true);assert.equal(r.body.publicDemo,true);assert.equal(JSON.stringify(r.body).includes('secret'),false);
    r=response();await handler({method:'GET',query:{action:'tasks'},headers},r);assert.equal(r.code,200);
    r=response();await handler({method:'POST',query:{action:'tasks'},headers,body:draft},r);assert.equal(r.code,201);assert.match(calls.at(-1).url,/spatial_demo_tasks/);
    r=response();await handler({method:'POST',query:{action:'tasks'},headers:{...headers,origin:'https://bad.test'},body:draft},r);assert.equal(r.code,403);
  }finally{globalThis.fetch=original;for(const k of Object.keys(process.env))if(!(k in before))delete process.env[k];Object.assign(process.env,before)}
});
test('shared task reads and writes are scoped to the selected store and validate its registered fixtures',async()=>{
  Object.assign(process.env,{SUPABASE_URL:'https://example.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'test-only',SPATIAL_WORKSPACE_ID:draft.id,SPATIAL_DEMO_INVITE:'a'.repeat(40)});
  const original=globalThis.fetch;const calls=[];
  globalThis.fetch=async(url,options)=>{calls.push({url,options});const isConfig=url.includes('spatial_demo_stores');return{ok:true,status:200,json:async()=>isConfig?[{payload:{fixtures:[{id:'F01'}]}}]:options.method==='POST'?[{payload:JSON.parse(options.body).payload,revision:1}]:[]}};
  const headers={host:'demo.test','content-type':'application/json',cookie:'spatial_demo='+'a'.repeat(40)};
  try{let r=response();await handler({method:'GET',query:{action:'tasks',store:'gangnam'},headers},r);assert.equal(r.code,200);assert.match(calls.at(-1).url,/store_id=eq.gangnam/);
    r=response();await handler({method:'POST',query:{action:'tasks',store:'gangnam'},headers,body:draft},r);assert.equal(r.code,400);
    r=response();await handler({method:'POST',query:{action:'tasks',store:'gangnam'},headers,body:{...draft,fixture:'F01'}},r);assert.equal(r.code,201);assert.equal(JSON.parse(calls.at(-1).options.body).store_id,'gangnam');
    r=response();await handler({method:'PATCH',query:{action:'tasks',store:'other-store'},headers,body:{id:draft.id,revision:1,status:'completed',note:'wrong store'}},r);assert.equal(r.code,404);assert.match(calls.at(-1).url,/store_id=eq.other-store/);
  }finally{globalThis.fetch=original}
});
test('API refuses unauthenticated writes and cross-origin joins without accessing database',async()=>{Object.assign(process.env,{SUPABASE_URL:'https://example.supabase.co',SUPABASE_SERVICE_ROLE_KEY:'test-only',SPATIAL_WORKSPACE_ID:draft.id,SPATIAL_DEMO_INVITE:'a'.repeat(40)});let r=response();await handler({method:'POST',query:{},headers:{host:'demo.test','content-type':'application/json'},body:draft},r);assert.equal(r.code,401);r=response();await handler({method:'POST',query:{action:'join'},headers:{host:'demo.test',origin:'https://bad.test','content-type':'application/json'},body:{invite:'a'.repeat(40)}},r);assert.equal(r.code,403);r=response();await handler({method:'POST',query:{action:'join'},headers:{host:'demo.test','content-type':'application/json'},body:{invite:'a'.repeat(40)}},r);assert.equal(r.code,200);assert.match(r.headers['Set-Cookie'],/HttpOnly; Secure; SameSite=Lax/)});
