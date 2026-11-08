(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const renderers=[new SceneRenderer($('left'),'#bca9ff'),new SceneRenderer($('right'),'#70e4c4')];
  let config,token,spec,environment='lunar',pending=[],state={generation:0,tick_id:0,panels:[]};
  let running=false,busy=false,timer=null,resetting=false,halted=false;
  const clamp=v=>Math.max(0,Math.min(1,v));
  function redistribute(weights,index,value){
    const result=weights.slice(),remaining=1-clamp(value),old=weights.reduce((sum,v,i)=>sum+(i===index?0:v),0);
    result[index]=clamp(value);result.forEach((_,i)=>{if(i!==index)result[i]=old>1e-9?weights[i]/old*remaining:remaining/(weights.length-1);});return result;
  }
  function changed(){return !state.panels[1]||pending.some((v,i)=>Math.abs(v-state.panels[1].weights[i])>1e-5);}
  function showError(error){running=false;halted=true;clearTimeout(timer);$('error').hidden=false;$('error').textContent=`Đã dừng: ${error.message}. Không tự gửi lại bước. Bấm Chạy so sánh để reset; nếu nhiều tab cùng mở, hãy tải lại trang.`;$('connection').textContent='Đã dừng / cần kiểm tra';$('led').classList.remove('ready');buttons();}
  async function api(path,body){
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);
    try{const response=await fetch(path,body===undefined?{signal:controller.signal}:{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Token':token},body:JSON.stringify(body),signal:controller.signal});const data=await response.json();if(!response.ok)throw Error(data.error||`HTTP ${response.status}`);return data;}finally{clearTimeout(timeout);}
  }
  function buttons(){
    $('run').disabled=busy||!config;$('pause').disabled=halted||resetting||!state.panels.length||state.all_done;
    $('pause').textContent=running?'Ⅱ Tạm dừng':'▶ Tiếp tục';$('step').disabled=halted||busy||running||!state.panels.length||state.all_done;
    $('skin').disabled=busy||!config;$('trace').disabled=busy||!config;
    ['lunar','mine','default','balanced'].forEach(id=>$(id).disabled=busy||!config);
  }
  function updateSliders(){
    pending.forEach((value,i)=>{$(`weight-${i}`).value=String(value*100);$(`weight-label-${i}`).textContent=`${(value*100).toFixed(1)}%`;});
    $('total').textContent=`${(pending.reduce((a,b)=>a+b,0)*100).toFixed(0)}%`;
    const isChanged=changed();$('preference-state').classList.toggle('applied',!isChanged);
    $('preference-state').textContent=isChanged?($('live').checked?'Chờ bước inference tiếp theo; lịch sử không reset.':'Chưa áp dụng · bấm Chạy so sánh để reset cùng seed.'):'Đang dùng đúng preference hiển thị.';
  }
  function setupEnvironment(){
    spec=config[environment];pending=spec.default_weights.slice();$('seed').textContent=`SEED ${spec.seed} / CÙNG CHECKPOINT`;
    ['lunar','mine'].forEach(id=>$(id).classList.toggle('selected',id===environment));
    $('sliders').replaceChildren();spec.objectives.forEach((name,i)=>{
      const row=document.createElement('div');row.className='slider-row';
      const label=document.createElement('label');label.className='slider-heading';label.htmlFor=`weight-${i}`;
      const text=document.createElement('span');text.textContent=name;const output=document.createElement('output');output.id=`weight-label-${i}`;output.htmlFor=`weight-${i}`;label.append(text,output);
      const input=document.createElement('input');input.type='range';input.min='0';input.max='100';input.step='0.1';input.id=`weight-${i}`;input.setAttribute('aria-label',`Trọng số ${name}`);
      input.addEventListener('input',()=>{pending=redistribute(pending,i,Number(input.value)/100);updateSliders();});row.append(label,input);$('sliders').append(row);
    });
    $('rewards').replaceChildren();spec.objectives.forEach((name,i)=>{
      const row=document.createElement('div');row.className='reward-row';const label=document.createElement('span');label.textContent=name;row.append(label);
      for(let panel=0;panel<2;panel++){const cell=document.createElement('div');cell.className='reward-value';const meter=document.createElement('span');meter.className='meter';const bar=document.createElement('i');bar.id=`bar-${panel}-${i}`;meter.append(bar);const number=document.createElement('b');number.id=`reward-${panel}-${i}`;number.textContent='0.00';cell.append(meter,number);row.append(cell);}$('rewards').append(row);
    });
    $('model-info').textContent=`${spec.algorithm} · seed train ${spec.training_seed} · ${spec.training_step.toLocaleString()} interactions đã train. SHA256 ${spec.weights_sha256}`;
    $('notice').textContent=spec.caveat;renderers.forEach(r=>r.reset());updateSliders();
  }
  function draw(next){
    state=next;next.panels.forEach((panel,index)=>{
      const side=index?'right':'left';renderers[index].draw(panel);$(side+'-step').textContent=String(panel.steps).padStart(4,'0');$(side+'-action').textContent=panel.action===null?'Chờ hành động':spec.actions[panel.action];
      $(side+'-weights').textContent='w = ['+panel.weights.map(v=>v.toFixed(3)).join(', ')+']';
      $(side+'-status').textContent=panel.done?(panel.truncated||panel.presentation_cap?'TIME LIMIT / DỪNG':environment==='lunar'?(panel.raw_return[0]>0?'KẾT THÚC / LANDING +100':'KẾT THÚC / LANDING -100'):'EPISODE KẾT THÚC'):(running?'ĐANG INFERENCE':'TẠM DỪNG');
      const native=$('skin').value==='native';$(side).hidden=native;$(side+'-native').hidden=!native;
      if(panel.native_frame)$(side+'-native').src='data:image/jpeg;base64,'+panel.native_frame;
      panel.raw_return.forEach((value,i)=>{const max=Math.max(1,...next.panels.map(p=>Math.abs(p.raw_return[i])));$(`reward-${index}-${i}`).textContent=value.toFixed(2);$(`bar-${index}-${i}`).style.width=`${Math.abs(value)/max*100}%`;});
    });
    $('comparison').classList.toggle('warn',next.history_dependent);
    $('comparison').textContent=next.history_dependent?'Đã đổi w giữa episode: hai bên có lịch sử khác nhau. Reset để so sánh từ cùng trạng thái.':'Cùng checkpoint, cùng seed khởi tạo. Khác biệt nếu có đến từ preference; đây không phải so sánh thuật toán.';
    if(!halted){$('connection').textContent=running?'CPU / inference đang chạy':'CPU / model đã nạp';$('led').classList.add('ready');}updateSliders();buttons();
  }
  async function tick(single=false){
    if(halted||busy||(!running&&!single)||state.all_done)return;busy=true;buttons();
    const request={generation:state.generation,tick_id:state.tick_id+1,steps:single?1:Number($('speed').value),native:$('skin').value==='native'};
    if($('live').checked&&!state.panels[1].done)request.weights=pending.slice();
    const start=performance.now();
    try{const next=await api('/api/tick',request);if(next.all_done)running=false;draw(next);}catch(error){showError(error);try{const recovered=await api('/api/state');if(recovered.environment===environment)draw(recovered);}catch(_){/* Explicit reset/reload required, no mutation retry. */}}
    finally{busy=false;buttons();if(running)timer=setTimeout(()=>tick(),Math.max(0,33-(performance.now()-start)));}
  }
  async function reset(andRun){
    if(busy||resetting)return;resetting=true;running=false;clearTimeout(timer);busy=true;buttons();$('error').hidden=true;
    try{const next=await api('/api/reset',{environment,weights:pending,generation:state.generation});renderers.forEach(r=>r.reset());halted=false;running=andRun;draw(next);}
    catch(error){showError(error);try{const recovered=await api('/api/state');if(recovered.environment&&config[recovered.environment]){environment=recovered.environment;setupEnvironment();draw(recovered);}else state=recovered;}catch(_){/* Do not retry reset. */}}
    finally{busy=false;resetting=false;buttons();if(running)tick();}
  }
  $('run').addEventListener('click',()=>reset(true));
  $('pause').addEventListener('click',()=>{running=!running;clearTimeout(timer);draw(state);if(running)tick();});
  $('step').addEventListener('click',()=>tick(true));
  $('live').addEventListener('change',updateSliders);
  $('default').addEventListener('click',()=>{pending=spec.default_weights.slice();updateSliders();});
  $('balanced').addEventListener('click',()=>{pending=pending.map(()=>1/pending.length);updateSliders();});
  ['lunar','mine'].forEach(id=>$(id).addEventListener('click',async()=>{if(id===environment||busy)return;environment=id;setupEnvironment();await reset(false);}));
  $('skin').addEventListener('change',async()=>{if(busy)return;busy=true;clearTimeout(timer);buttons();try{if($('skin').value==='native'){const next=await api('/api/state?native=1');draw(next);}else draw(state);}catch(error){showError(error);}finally{busy=false;buttons();if(running)tick();}});
  $('fullscreen').addEventListener('click',()=>{const operation=document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();operation.catch(error=>showError(error));});
  $('trace').addEventListener('click',async()=>{try{const data=await api('/api/trace');const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=`morl-${environment}-g${state.generation}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){showError(error);}});
  async function boot(){try{const data=await api('/api/config');config=data.environments;token=data.token;state=data.state;setupEnvironment();await reset(false);}catch(error){showError(error);}}
  window.DemoMath={redistribute};boot();
})();
