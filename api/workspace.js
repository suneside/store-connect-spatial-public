import {timingSafeEqual} from 'node:crypto';
import {DEFAULT_STORE,validStoreId,validateStore} from '../dist/store-schema.js';

const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const fixtures=new Set(['C-W01','C-W02','C-C01','C-C02','C-S01','C-B01','C-T01','C-M01']);
const allowed={draft:['requested'],requested:['completed'],completed:['reviewed','requested'],reviewed:['requested']};
function equal(a,b){const x=Buffer.from(a||''),y=Buffer.from(b||'');return x.length===y.length&&x.length>0&&timingSafeEqual(x,y)}
function fail(message,status=400){throw Object.assign(new Error(message),{status})}
function text(value,max,required=true){if(typeof value!=='string'||value.length>max||(required&&!value.trim()))fail('입력 내용을 확인해 주세요.');return value.trim()}
export function validateTask(input,storeFixtures=fixtures){
  if(!input||!uuid.test(input.id)||!storeFixtures.has(input.fixture))fail('유효하지 않은 집기 또는 작업입니다.');
  return {id:input.id,fixture:input.fixture,title:text(input.title,140),owner:text(input.owner,80),body:text(input.body,5000),type:input.type==='plan'?'plan':'verify',status:'requested',created:new Date().toISOString(),report:'',evidence:null,history:[{status:'requested',at:new Date().toISOString(),note:'VMD 확인 요청'}]};
}
export function transition(current,input){
  if(!allowed[current.status]?.includes(input.status))fail('허용되지 않은 상태 변경입니다.',409);
  const note=text(input.note??'',2000,input.status==='completed');
  let evidence=current.evidence??null;
  if(input.evidence){if(typeof input.evidence!=='string'||input.evidence.length>700000||!/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+=*$/.test(input.evidence))fail('사진은 500KB 이하 JPG·PNG·WebP만 가능합니다.');evidence=input.evidence}
  return {...current,status:input.status,report:input.status==='completed'?note:current.report,evidence,history:[...(current.history||[]),{status:input.status,at:new Date().toISOString(),note}].slice(-50)};
}
export default async function handler(req,res){
  res.setHeader('Cache-Control','no-store');
  const send=(status,data)=>res.status(status).json(data);
  try{
    const {SUPABASE_URL:url,SUPABASE_SERVICE_ROLE_KEY:key,SPATIAL_WORKSPACE_ID:workspace,SPATIAL_DEMO_INVITE:invite}=process.env;
    const publicDemo=process.env.SPATIAL_PUBLIC_DEMO==='true';
    const configured=Boolean(url&&key&&uuid.test(workspace||'')&&(publicDemo||invite?.length>=32));
    const action=req.query?.action??'tasks';
    const cookie=(req.headers.cookie||'').split(';').map(v=>v.trim()).find(v=>v.startsWith('spatial_demo='))?.slice(13);
    const authorized=configured&&(publicDemo||equal(cookie,invite));
    if(req.method==='GET'&&action==='status')return send(200,{configured,authorized,publicDemo,storage:configured?'supabase':'local',mode:publicDemo?'public-demo':'hackathon-demo'});
    if(!configured)return send(503,{error:'공유 시연 환경이 아직 연결되지 않았습니다.'});
    if(!['GET','POST','PATCH'].includes(req.method)){res.setHeader('Allow','GET, POST, PATCH');return send(405,{error:'Method not allowed'})}
    if(req.method!=='GET'){
      const origin=req.headers.origin;
      if(origin&&new URL(origin).host!==req.headers.host)return send(403,{error:'Origin rejected'});
      if(!req.headers['content-type']?.includes('application/json'))return send(415,{error:'JSON required'});
    }
    const body=typeof req.body==='string'?JSON.parse(req.body):req.body;
    if(req.method==='POST'&&action==='join'){
      if(!equal(body?.invite,invite))return send(403,{error:'시연 초대 링크를 확인해 주세요.'});
      res.setHeader('Set-Cookie',`spatial_demo=${invite}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=604800`);
      return send(200,{ok:true});
    }
    if(!authorized)return send(401,{error:'시연 초대 링크로 접속해 주세요.'});
    async function db(path,options={},table='spatial_demo_tasks'){
      const response=await fetch(`${url}/rest/v1/${table}${path}`,{...options,headers:{apikey:key,Authorization:`Bearer ${key}`,'Content-Type':'application/json',Prefer:'return=representation',...options.headers},signal:AbortSignal.timeout(15000)});
      if(!response.ok){if(response.status===409)fail('이미 공유된 작업입니다. 새로고침해 주세요.',409);fail('공유 저장에 실패했습니다. 잠시 후 다시 시도해 주세요.',502)}
      return response.status===204?[]:response.json();
    }
    const workspaceScope=`workspace_id=eq.${encodeURIComponent(workspace)}`;
    const storeId=req.query?.store??DEFAULT_STORE;
    if(!validStoreId(storeId))fail('매장 ID를 확인해 주세요.');
    if(action==='stores'){
      if(req.method==='GET')return send(200,{stores:(await db(`?${workspaceScope}&order=updated_at.desc&limit=30`,{},'spatial_demo_stores')).map(r=>({...r.payload,revision:r.revision}))});
      if(req.method!=='POST')return send(405,{error:'GET 또는 POST를 사용하세요.'});
      const config=validateStore(body);if(config.id!==storeId)fail('매장 ID가 일치하지 않습니다.');
      const query=`?${workspaceScope}&id=eq.${encodeURIComponent(storeId)}`;
      const existing=await db(query,{},'spatial_demo_stores');let rows;
      if(existing.length){if(body.revision!==existing[0].revision)fail('다른 담당자가 매장 설정을 변경했습니다. 변경 내용을 내보낸 뒤 새로고침하세요.',409);
        rows=await db(`${query}&revision=eq.${body.revision}`,{method:'PATCH',body:JSON.stringify({payload:config,revision:body.revision+1,updated_at:new Date().toISOString()})},'spatial_demo_stores');
        if(!rows.length)fail('매장 설정이 변경됐습니다. 새로고침해 주세요.',409);
      }else{if(body.revision!==0)fail('매장 버전을 확인하세요.',409);rows=await db('',{method:'POST',body:JSON.stringify({workspace_id:workspace,id:storeId,payload:config})},'spatial_demo_stores')}
      return send(200,{store:{...rows[0].payload,revision:rows[0].revision}});
    }
    if(action!=='tasks')fail('알 수 없는 요청입니다.');
    const scope=`${workspaceScope}&store_id=eq.${encodeURIComponent(storeId)}`;
    if(req.method==='GET')return send(200,{tasks:(await db(`?${scope}&order=created_at.desc&limit=100`)).map(row=>({...row.payload,revision:row.revision}))});
    if(req.method==='POST'){
      let storeFixtures=fixtures;
      if(storeId!==DEFAULT_STORE){const stores=await db(`?${workspaceScope}&id=eq.${encodeURIComponent(storeId)}`,{},'spatial_demo_stores');if(!stores.length)fail('매장 관리에서 설정을 먼저 공유하세요.');storeFixtures=new Set(stores[0].payload.fixtures.map(f=>f.id))}
      const task={...validateTask(body,storeFixtures),storeId};
      const rows=await db('',{method:'POST',body:JSON.stringify({id:task.id,workspace_id:workspace,store_id:storeId,payload:task})});
      return send(201,{task:{...rows[0].payload,revision:rows[0].revision}});
    }
    if(!uuid.test(body?.id||'')||!Number.isInteger(body?.revision))fail('작업 버전을 확인해 주세요.');
    const query=`?${scope}&id=eq.${body.id}`;const existing=await db(query);
    if(!existing.length)fail('작업을 찾을 수 없습니다.',404);
    if(existing[0].revision!==body.revision)fail('다른 화면에서 변경됐습니다. 최신 상태로 새로고침해 주세요.',409);
    const payload=transition(existing[0].payload,body);
    const rows=await db(`${query}&revision=eq.${body.revision}`,{method:'PATCH',body:JSON.stringify({payload,revision:body.revision+1,updated_at:new Date().toISOString()})});
    if(!rows.length)fail('다른 화면에서 변경됐습니다. 새로고침해 주세요.',409);
    return send(200,{task:{...rows[0].payload,revision:rows[0].revision}});
  }catch(error){return send(error.status||500,{error:error.status?error.message:'요청 처리 중 오류가 발생했습니다.'})}
}
