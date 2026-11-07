const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={requested:'현장 요청',completed:'완료 보고',reviewed:'VMD 재확인'};
export async function initCollaboration({modal,toast,getDrafts,focus,storeId='myeongdong',storeName='MLB 명동'}){
  let configured=false,authorized=false,publicDemo=false,remote=[],role='vmd',busy=false,active=false,dirty=false;
  const button=document.createElement('button');button.id='shared-nav';button.textContent='현장 연결';document.querySelector('.main-nav').append(button);
  const request=async(action,method='GET',body)=>{const r=await fetch(`/api/workspace?action=${action}&store=${encodeURIComponent(storeId)}`,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const result=await r.json();if(!r.ok)throw Error(result.error||'연결을 확인해 주세요.');return result};
  const refresh=async()=>{if(authorized){const result=await request('tasks');remote=result.tasks;button.textContent=`현장 연결 · ${remote.filter(t=>t.status!=='reviewed').length}`}};
  const show=()=>{
    active=true;dirty=false;
    if(!configured){modal('현장 공유 연결 준비', '<p class="dialog-description">현재는 이 브라우저의 작업 초안을 저장합니다. 공유 시연 환경이 연결되면 요청·완료 보고·VMD 재확인을 다른 컴퓨터에서 이어갈 수 있습니다.</p>','STORE CONNECT SPATIAL');return}
    if(!authorized){modal('시연 워크스페이스에 참여', '<p class="dialog-description">전달받은 시연 초대 링크로 접속해 주세요. 3D 탐색과 로컬 초안은 계속 사용할 수 있습니다.</p>','HACKATHON DEMO');return}
    const drafts=getDrafts().filter(t=>!remote.some(r=>r.id===t.id));
    modal('같은 공간, 이어지는 업무',`<div class="shared-head"><div class="study-tabs"><button data-role="vmd" class="${role==='vmd'?'active':''}">VMD 리브</button><button data-role="field" class="${role==='field'?'active':''}">현장 담당자</button></div><button id="refresh-shared" class="secondary-btn">새로고침 ↻</button></div><p class="dialog-description">Supabase 공유 저장 · 시연용 역할 전환 · ${esc(storeName)}<br>요청 → 현장 완료 보고 → VMD 재확인. ${publicDemo?'로그인 없이 누구나 요청·보고를 작성하는 공개 시연 공간입니다. 실제 개인정보와 비공개 자료는 입력하지 마세요.':'이 초대 링크를 받은 참여자가 함께 사용하는 시연 공간입니다.'}</p><div class="workflow-stats">${Object.entries(labels).map(([k,l])=>`<span>${l}<strong>${remote.filter(t=>t.status===k).length}</strong></span>`).join('')}</div>${role==='vmd'&&drafts.length?`<div class="draft-share"><strong>이 브라우저의 요청 초안</strong>${drafts.map(t=>`<div><span>${esc(t.title)}</span><button data-share="${esc(t.id)}" class="secondary-btn">현장에 요청 ↗</button></div>`).join('')}</div>`:''}<div id="shared-tasks">${remote.map(t=>`<article class="task-card" data-shared-id="${esc(t.id)}"><div class="task-title"><strong>${esc(t.title)}</strong><span class="pill">${labels[t.status]}</span></div><small>${esc(t.fixture)} · ${esc(t.owner)}</small><p>${esc(t.body)}</p>${t.report?`<div class="field-report"><strong>현장 완료 보고</strong><p>${esc(t.report)}</p>${t.evidence?`<img alt="현장 담당자가 첨부한 완료 보고 사진" src="${esc(t.evidence)}">`:''}</div>`:''}<ol class="shared-history">${(t.history||[]).map(h=>`<li>${labels[h.status]} · ${new Date(h.at).toLocaleString('ko-KR')}${h.note?`<span>${esc(h.note)}</span>`:''}</li>`).join('')}</ol><div class="dialog-actions"><button data-focus-shared="${esc(t.fixture)}">공간에서 확인 ⌖</button>${role==='field'&&t.status==='requested'?`<button class="primary-btn" data-complete="${esc(t.id)}">완료 보고 작성</button>`:''}${role==='vmd'&&t.status==='completed'?`<button data-recheck="${esc(t.id)}">다시 요청</button><button class="primary-btn" data-approve="${esc(t.id)}">재확인 완료 ✓</button>`:''}</div></article>`).join('')||'<div class="empty">집기를 선택해 확인 요청 초안을 만든 뒤<br>이 화면에서 현장에 요청해 보세요.</div>'}</div>`,'VMD ↔ FIELD / SHARED WORKSPACE');
    document.querySelectorAll('[data-role]').forEach(b=>b.onclick=()=>{role=b.dataset.role;show()});
    document.querySelector('#refresh-shared').onclick=async()=>{try{await refresh();show()}catch(e){toast(e.message)}};
    document.querySelectorAll('[data-focus-shared]').forEach(b=>b.onclick=()=>{document.querySelector('#dialog').close();focus(b.dataset.focusShared)});
    document.querySelectorAll('[data-share]').forEach(b=>b.onclick=()=>mutate(()=>request('tasks','POST',getDrafts().find(t=>t.id===b.dataset.share))));
    document.querySelectorAll('[data-approve]').forEach(b=>b.onclick=()=>update(b.dataset.approve,'reviewed','VMD가 공간과 현장 완료 보고를 재확인했습니다.'));
    document.querySelectorAll('[data-recheck]').forEach(b=>b.onclick=()=>reportForm(b.dataset.recheck,false));
    document.querySelectorAll('[data-complete]').forEach(b=>b.onclick=()=>reportForm(b.dataset.complete,true));
  };
  async function mutate(fn){if(busy)return;busy=true;document.querySelectorAll('#dialog button').forEach(b=>b.disabled=true);try{await fn();await refresh();show();toast('공유 워크스페이스에 저장했습니다.')}catch(e){toast(e.message)}finally{busy=false;document.querySelectorAll('#dialog button').forEach(b=>b.disabled=false)}}
  function update(id,status,note,evidence){const task=remote.find(t=>t.id===id);return mutate(()=>request('tasks','PATCH',{id,revision:task.revision,status,note,evidence}))}
  function reportForm(id,completed){
    dirty=true;const task=remote.find(t=>t.id===id);
    modal(completed?'현장 완료 보고':'현장에 다시 확인 요청',`<p class="dialog-description">${esc(task.title)} · ${esc(task.fixture)}</p><form id="field-form"><div class="form-field"><label for="field-note">${completed?'변경한 내용과 확인 결과':'다시 확인할 내용'}</label><textarea id="field-note" maxlength="2000" required></textarea></div>${completed?'<div class="form-field"><label for="field-photo">현장 사진 (선택 · JPG, PNG, WebP · 500KB 이하)</label><input id="field-photo" type="file" accept="image/jpeg,image/png,image/webp"></div>':''}<div class="dialog-actions"><button type="button" id="back-shared">돌아가기</button><button class="primary-btn" type="submit">${completed?'완료 보고 저장':'다시 요청'}</button></div></form>`,'FIELD RECORD');
    document.querySelector('#back-shared').onclick=show;
    document.querySelector('#field-form').onsubmit=async e=>{e.preventDefault();const note=document.querySelector('#field-note').value.trim(),file=document.querySelector('#field-photo')?.files[0];let evidence;
      if(file){if(file.size>500000||!['image/jpeg','image/png','image/webp'].includes(file.type)){toast('500KB 이하의 JPG·PNG·WebP 사진을 선택해 주세요.');return}evidence=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file)})}
      await update(id,completed?'completed':'requested',note,evidence);
    };
  }
  button.onclick=async()=>{try{await refresh();show()}catch(e){toast(e.message)}};
  document.querySelector('#dialog').addEventListener('close',()=>{active=false;dirty=false});
  try{
    const status=await request('status');configured=status.configured;authorized=status.authorized;publicDemo=status.publicDemo===true;
    const fragment=new URLSearchParams(location.hash.slice(1));const invite=fragment.get('invite');
    if(invite&&configured){await request('join','POST',{invite});authorized=true;fragment.delete('invite');history.replaceState(null,'',location.pathname+location.search+(fragment.size?'#'+fragment.toString():''));toast('공유 시연 워크스페이스에 연결했습니다.');}
    if(authorized){await refresh();document.querySelector('#saved-indicator').textContent='초안은 이 브라우저 · 현장 연결에서 공유 요청';}
  }catch(e){if(location.hash.includes('invite='))toast(e.message)}
  // A user may open the invite in a tab that already shows the public 3D store.
  // Fragment-only navigation does not reload modules, so join explicitly as well.
  window.addEventListener('hashchange',async()=>{
    const fragment=new URLSearchParams(location.hash.slice(1)),invite=fragment.get('invite');if(!invite)return;
    try{const status=await request('status');configured=status.configured;if(!configured)return;await request('join','POST',{invite});authorized=true;fragment.delete('invite');history.replaceState(null,'',location.pathname+location.search+(fragment.size?'#'+fragment.toString():''));await refresh();document.querySelector('#saved-indicator').textContent='초안은 이 브라우저 · 현장 연결에서 공유 요청';if(active)show();toast('공유 시연 워크스페이스에 연결했습니다.')}catch(e){toast(e.message)}
  });
  setInterval(async()=>{if(!authorized||busy||dirty)return;try{const before=JSON.stringify(remote);await refresh();if(active&&document.querySelector('#shared-tasks')&&before!==JSON.stringify(remote))show()}catch{}},5000);
  return {getState:()=>({configured,authorized,tasks:remote.length})};
}
