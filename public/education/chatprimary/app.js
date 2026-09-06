(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const STORE = 'chatprimary.lesson.v1';
  const subjectNames = {chinese:'语文',math:'数学',english:'英语'};
  const topics = {
    4:{chinese:['抓住关键词','把一件事写清楚','体会人物心情'],math:['小数的意义','运算律','三角形的内角和'],english:['介绍我的一天','描述教室物品','表达喜欢什么']},
    5:{chinese:['概括段落大意','体会说明方法','把人物写具体'],math:['小数乘除法','分数的意义','长方体的体积'],english:['描述正在做的事','介绍我的周末','比较人物和物品']},
    6:{chinese:['用文本支持观点','读懂描写的作用','写一段有理由的表达'],math:['百分数的意义','比和比例','圆的面积'],english:['讲述过去的经历','表达未来的计划','读短文找关键信息']}
  };
  const help = {hint:'我卡住了，请给我一点提示，先别直接说答案。',example:'这个例子我还不太懂，请换一个更具体的小例子。',challenge:'请换一道题，让我试试是不是真的懂了。',summary:'请根据我刚才实际的回答，帮我回看收获和还需要练的地方。'};
  const stages = ['diagnose','explore','explain','transfer','reflect'];
  let subject='math', key='', vendor='deepseek', course=null, messages=[], stage='diagnose',
    observation=null, pending=null, busy=false, controller=null, generation=0, requests=0;
  const welcome=$('messages').innerHTML;
  const alias={ds:'deepseek',deepseek:'deepseek',glm:'zhipu',zhipu:'zhipu',qwen:'qwen'};
  try {
    const oldVendor=alias[localStorage.getItem('sde_wds_vendor')||''];
    const oldKey=localStorage.getItem('sde_wds_key')||'';
    if(oldVendor&&oldKey.length>=8&&oldKey.length<=300&&!/\s/.test(oldKey)){vendor=oldVendor;key=oldKey;}
  } catch {}
  const credentialsReady=()=>key.length>=8;
  function connectLabel(){ $('open-settings').textContent=credentialsReady()?'模型已连接 · 家长设置':'家长／老师设置'; }
  function selectSubject(value){
    subject=value;
    document.querySelectorAll('[data-subject]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.subject===subject)));
    renderTopics();
  }
  function renderTopics(){
    const list=topics[$('grade').value][subject];$('topics').replaceChildren();
    list.forEach(t=>{const b=document.createElement('button');b.type='button';b.textContent=t;b.addEventListener('click',()=>{$('topic').value=t;$('topic').focus();});$('topics').append(b);});
    $('topic').value=list[0];
  }
  function getCourse(){return {grade:Number($('grade').value),subject,topic:$('topic').value.trim(),edition:$('edition').value.trim(),material:$('material').value.trim(),pace:$('pace').value,interest:$('interest').value};}
  function showCourse(){
    const active=!!course;$('course-controls').disabled=active;$('start').disabled=active;$('reset').hidden=!active;
    document.querySelector('.lesson-panel').classList.toggle('active',active);
    $('lesson-title').textContent=active?`${course.grade} 年级 · ${subjectNames[course.subject]} · ${course.topic}`:'准备好你的第一个想法';
    $('answer').placeholder=active?'说说你的想法，也可以写“我不会”。':'先选课题，开始自学。';
    updateControls();
  }
  function updateControls(){
    // Pending requests must be retried or discarded before another message can be sent.
    const blocked=busy||!course||!!pending||messages.length>=40;
    $('answer').disabled=blocked;$('send').disabled=blocked;
    document.querySelectorAll('[data-help]').forEach(b=>b.disabled=blocked);
    $('stop').hidden=!busy;$('send').hidden=busy;$('retry').disabled=busy;
    $('open-settings').disabled=busy;
  }
  function addMessage(role,text){
    $('messages').querySelector('.starter-note')?.remove();
    const article=document.createElement('article');article.className='message '+role;
    const speaker=document.createElement('span');speaker.className='speaker';speaker.textContent=role==='assistant'?'ChatPrimary':'我的想法';
    const bubble=document.createElement('div');bubble.className='bubble';bubble.textContent=text;
    article.append(speaker,bubble);$('messages').append(article);$('messages').scrollTop=$('messages').scrollHeight;
  }
  function showObservation(value){
    observation=value;if(value){stage=stages.includes(value.stage)?value.stage:'diagnose';$('evidence').textContent=value.evidence;$('next-step').textContent=value.next;}
    else{stage='diagnose';$('evidence').textContent='你的想法会成为下一步学习的起点。';$('next-step').textContent='选一个课题，从一个小问题开始。';}
    document.querySelectorAll('[data-stage]').forEach(el=>{if(el.dataset.stage===stage)el.setAttribute('aria-current','step');else el.removeAttribute('aria-current');});
  }
  function persist(){
    try{
      if($('remember').checked&&course&&messages.length>=2){
        // Explicit allowlist: never include keys, provider credentials or pending requests.
        localStorage.setItem(STORE,JSON.stringify({v:1,time:Date.now(),course,messages,observation}));
        $('storage-note').textContent='仅在这台设备保留 7 天；可随时清空。不要在共用设备上勾选。';
      }else{localStorage.removeItem(STORE);$('storage-note').textContent='未保留本次学习。离开页面就会清空；不要输入姓名、学校、电话等个人信息。';}
    }catch{$('remember').checked=false;$('storage-note').textContent='浏览器未允许保存；本次仍可继续学习，离开页面后不会保留。';}
  }
  function restore(){
    try{
      const s=JSON.parse(localStorage.getItem(STORE)||'null');if(!s)return;
      const c=s.course;
      if(s.v!==1||!Number.isFinite(s.time)||Date.now()-s.time>7*86400000||!c||![4,5,6].includes(c.grade)||!Object.hasOwn(subjectNames,c.subject)||typeof c.topic!=='string'||!c.topic.trim()||c.topic.length>120||!['gentle','steady','challenge'].includes(c.pace)||!['daily','nature','sport','space'].includes(c.interest)||!Array.isArray(s.messages)||s.messages.length<2||s.messages.length>40||s.messages.length%2!==0)throw new Error('invalid');
      if(!s.messages.every((m,i)=>m&&m.role===(i%2?'assistant':'user')&&typeof m.content==='string'&&m.content.length<=4000))throw new Error('invalid');
      course={grade:c.grade,subject:c.subject,topic:c.topic,edition:String(c.edition||'').slice(0,80),material:String(c.material||'').slice(0,2000),pace:c.pace,interest:c.interest};
      messages=s.messages.map(m=>({role:m.role,content:m.content}));$('grade').value=String(course.grade);selectSubject(course.subject);
      for(const id of ['topic','edition','material','pace','interest'])$(id).value=course[id];
      $('messages').replaceChildren();messages.forEach(m=>addMessage(m.role,m.content));
      if(s.observation&&stages.includes(s.observation.stage)&&typeof s.observation.evidence==='string'&&typeof s.observation.next==='string')showObservation({stage:s.observation.stage,evidence:s.observation.evidence.slice(0,300),next:s.observation.next.slice(0,300)});
      $('remember').checked=true;showCourse();persist();$('status').textContent='已恢复这台设备上的本次学习。';
    }catch{try{localStorage.removeItem(STORE);}catch{}}
  }
  function openSettings(){
    $('vendor').value=vendor;$('api-key').value='';$('api-key').placeholder=key?'已有本页连接；留空则继续使用':'粘贴所选模型的 API Key';
    $('settings-status').textContent=key?'已有连接。密钥不会显示在这里。':'请由家长或老师填写。';$('settings').showModal();
  }
  function showError(text){$('error-text').textContent=text;$('error-box').hidden=false;}
  async function runPending(){
    if(!pending||busy)return;
    if(!credentialsReady()){openSettings();return;}
    const task=pending;const ticket=++generation;
    busy=true;controller=new AbortController();const activeController=controller;$('error-box').hidden=true;updateControls();
    $('status').textContent='ChatPrimary 正在看你的想法……';
    const soft=setTimeout(()=>{if(ticket===generation)$('status').textContent='还在准备一个适合你的小问题，可以再等一会儿。';},12000);
    const timeout=setTimeout(()=>activeController.abort(),65000);
    try{
      const response=await fetch('/api/chatprimary',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({...course,vendor,key,action:task.action,stage,messages:[...messages,{role:'user',content:task.text}]}),signal:controller.signal,cache:'no-store'});
      let data;try{data=await response.json();}catch{throw new Error('这次连接没有完成，请重新发送。');}
      if(ticket!==generation)return;
      if(!response.ok||!data.ok){if(data.code==='need_key'||data.code==='key_rejected')key='';connectLabel();throw new Error(data.message||'这次没有收到回答，请重试。');}
      if(typeof data.reply!=='string'||!stages.includes(data.stage)||typeof data.evidence!=='string'||typeof data.next!=='string')throw new Error('这次回答不完整，请重新发送。');
      messages.push({role:'user',content:task.text},{role:'assistant',content:data.reply});
      pending=null;addMessage('assistant',data.reply);showObservation({stage:data.stage,evidence:data.evidence,next:data.next});
      requests++;persist();
      $('status').textContent=messages.length>=40?'这节课已经有 20 次互动。可以回看收获，再换一节课。':requests%8===0?'可以把眼睛从屏幕上移开，休息一下，再继续。':'';
    }catch(error){if(ticket!==generation)return;showError(error.name==='AbortError'?'已停止等待，你的话还在。可以重新发送，或换一节课。':error.message);$('status').textContent='';}
    finally{clearTimeout(soft);clearTimeout(timeout);if(ticket===generation){busy=false;controller=null;updateControls();if(!pending)$('answer').focus();}}
  }
  function send(text,action='answer'){
    if(busy||pending||!course||messages.length>=40||!text.trim())return;
    if(!credentialsReady()){openSettings();return;}
    pending={text:text.trim(),action};addMessage('user',pending.text);$('answer').value='';runPending();
  }
  function reset(){
    generation++;controller?.abort();controller=null;busy=false;course=null;messages=[];pending=null;requests=0;
    $('answer').value='';$('messages').innerHTML=welcome;$('status').textContent='';$('error-box').hidden=true;
    showObservation(null);$('remember').checked=false;persist();showCourse();$('topic').focus();
  }
  $('lesson-form').addEventListener('submit',event=>{
    event.preventDefault();if(busy||course)return;if(!credentialsReady()){openSettings();return;}
    const c=getCourse();if(!c.topic){$('topic').focus();return;}
    course=c;messages=[];pending=null;$('messages').replaceChildren();showCourse();
    send('我想学习“'+course.topic+'”。请先给我一个小尝试。','start');
    if(window.matchMedia('(max-width:760px)').matches)document.querySelector('.chat-panel').scrollIntoView({block:'start'});
  });
  $('chat-form').addEventListener('submit',event=>{event.preventDefault();send($('answer').value);});
  $('answer').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();send($('answer').value);}});
  document.querySelectorAll('[data-help]').forEach(b=>b.addEventListener('click',()=>send(help[b.dataset.help],b.dataset.help)));
  document.querySelectorAll('[data-subject]').forEach(b=>b.addEventListener('click',()=>{if(!course&&subject!==b.dataset.subject){selectSubject(b.dataset.subject);$('edition').value='';$('material').value='';}}));
  $('grade').addEventListener('change',()=>{renderTopics();$('edition').value='';$('material').value='';});
  $('open-settings').addEventListener('click',openSettings);$('close-settings').addEventListener('click',()=>$('settings').close());
  $('vendor').addEventListener('change',()=>{$('api-key').value='';$('settings-status').textContent='切换模型时，请填写对应厂商的密钥。';});
  $('settings-form').addEventListener('submit',event=>{
    event.preventDefault();const value=$('api-key').value.trim();const nextVendor=$('vendor').value;
    if(!value&&(!key||nextVendor!==vendor)){$('settings-status').textContent='请填写所选厂商的 API Key。';return;}
    if(value&&(value.length<8||value.length>300||/\s/.test(value))){$('settings-status').textContent='密钥格式不完整或含有空格，请检查后再保存。';return;}
    if(value)key=value;vendor=nextVendor;$('api-key').value='';$('settings').close();connectLabel();
    $('status').textContent=pending?'连接设置已保存。点击“重新发送”继续。':'连接设置已保存，可以开始学习。';
  });
  $('settings').addEventListener('close',()=>{$('api-key').value='';});
  $('forget-key').addEventListener('click',()=>{key='';$('api-key').value='';$('settings-status').textContent='已断开本页连接；本站其他页面已有设置未改动。';connectLabel();});
  $('remember').addEventListener('change',persist);$('retry').addEventListener('click',runPending);
  $('stop').addEventListener('click',()=>controller?.abort());
  for(const id of ['reset','clear'])$(id).addEventListener('click',()=>{if(course||messages.length||pending)$('reset-dialog').showModal();else reset();});
  $('cancel-reset').addEventListener('click',()=>$('reset-dialog').close());
  $('confirm-reset').addEventListener('click',()=>{$('reset-dialog').close();reset();});
  selectSubject(subject);connectLabel();restore();updateControls();
})();
