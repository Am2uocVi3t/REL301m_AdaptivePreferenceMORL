/* Unit tests with a fake DOM/canvas/transport. Not browser-rendering evidence. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const directory=process.argv[2]||'outputs/REL301m_Interactive_Demo';
const config=JSON.parse(fs.readFileSync(path.join(directory,'config.json'),'utf8')).environments;
const elements=new Map();
class Element{
  constructor(){this._id='';this.events={};this.children=[];this.value='';this.textContent='';this.hidden=false;this.disabled=false;this.checked=false;this.style={};this.width=800;this.height=500;this.classes=new Set();this.classList={add:v=>this.classes.add(v),remove:v=>this.classes.delete(v),toggle:(v,on)=>on?this.classes.add(v):this.classes.delete(v)};}
  set id(v){this._id=v;elements.set(v,this);}get id(){return this._id;}
  setAttribute(k,v){this[k]=v;}
  addEventListener(k,v){this.events[k]=v;}
  append(...values){this.children.push(...values);}
  replaceChildren(){this.children=[];}
  click(){return this.events.click?.();}
  getContext(){return canvasContext;}
}
let draws=0;
const canvasContext=new Proxy({createLinearGradient:()=>({addColorStop(){}}),createRadialGradient:()=>({addColorStop(){}})}, {
  get(target,key){if(key in target)return target[key];return (...args)=>{for(const arg of args)if(typeof arg==='number')assert.ok(Number.isFinite(arg),`finite canvas ${key}`);draws++;};},set(t,k,v){t[k]=v;return true;}
});
const document={getElementById:id=>{if(!elements.has(id)){const e=new Element();e.id=id;}return elements.get(id);},createElement:()=>new Element(),fullscreenElement:null,documentElement:{requestFullscreen:async()=>{}},exitFullscreen:async()=>{}};
document.getElementById('speed').value='1';document.getElementById('skin').value='styled';
let backend={generation:0,tick_id:0,environment:null,panels:[],all_done:false},lastRequest=null,pendingFailure=false;
let posts=[];let networkFailure=false;
const sceneFor=name=>name==='mine'?{kind:'minecart',position:[0,0],angle:45,speed:0,cargo:[0,0],capacity:1,mines:[[.16,.84],[.5,.84]]}:{kind:'lunar',lander:{position:[10,10],angle:.1,fixtures:[[[-.5,-.3],[.5,-.3],[0,.5]]]},legs:[],terrain:[[0,4],[10,3],[20,4]],pad:[8,12,3],contact:[false,false]};
const panel=(weights,name)=>({weights:weights.slice(),steps:0,action:null,scene:sceneFor(name),raw_return:weights.map(()=>0),done:false,terminated:false,truncated:false,switches:[]});
async function fetchMock(url,options){
  if(networkFailure)throw Error('Synthetic network failure');
  let value;if(url==='/api/config')value={environments:config,token:'test-only',state:structuredClone(backend)};
  else if(url.startsWith('/api/state'))value=structuredClone(backend);
  else if(url==='/api/trace')value={state:structuredClone(backend)};
  else if(url==='/api/reset'){
    const request=JSON.parse(options.body);posts.push({url,request});assert.equal(request.generation,backend.generation);
    backend={generation:backend.generation+1,tick_id:0,environment:request.environment,panels:[panel(config[request.environment].default_weights,request.environment),panel(request.weights,request.environment)],history_dependent:false,all_done:false};value=structuredClone(backend);
  }else if(url==='/api/tick'){
    const request=JSON.parse(options.body);lastRequest=request;posts.push({url,request});assert.equal(request.generation,backend.generation);assert.equal(request.tick_id,backend.tick_id+1);
    if(request.weights){backend.panels[1].weights=request.weights.slice();backend.history_dependent=true;}
    for(const p of backend.panels){p.steps+=request.steps;p.action=0;p.raw_return=p.raw_return.map((v,i)=>v+request.steps*(i+1));}
    backend.tick_id=request.tick_id;value=structuredClone(backend);
  }else throw Error(`unexpected request ${url}`);
  if(url.includes('native=1')||lastRequest?.native){value.panels?.forEach(p=>p.native_frame='test-jpeg');}
  return {ok:true,json:async()=>value};
}
const timers=new Map();let timerId=0;
const context={document,window:{},SceneRenderer:null,fetch:fetchMock,AbortController,performance:{now:()=>0},setTimeout:cb=>{timers.set(++timerId,cb);return timerId;},clearTimeout:id=>timers.delete(id),Blob,URL:{createObjectURL:()=>'',revokeObjectURL(){}},console};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(directory,'website/renderer.js'),'utf8'),context);context.SceneRenderer=context.window.SceneRenderer;
vm.runInContext(fs.readFileSync(path.join(directory,'website/app.js'),'utf8'),context);
const settle=async()=>{for(let i=0;i<20;i++)await Promise.resolve();};
const event=async(id,type)=>{await document.getElementById(id).events[type]();await settle();};
let checks=0;const check=(condition,label)=>{assert.ok(condition,label);checks++;};
(async()=>{
  await settle();check(backend.generation===1&&backend.panels[0].steps===0,'boot paused');
  const math=context.window.DemoMath;
  for(const dimension of [3,4]){for(let i=0;i<dimension;i++)for(const value of [0,.17,.5,1]){const weights=math.redistribute(Array(dimension).fill(1/dimension),i,value);check(Math.abs(weights.reduce((a,b)=>a+b,0)-1)<1e-9,'simplex sum');check(weights.every(v=>v>=0&&v<=1),'simplex bounds');}const weights=math.redistribute([1,...Array(dimension-1).fill(0)],0,.4);check(Math.abs(weights.reduce((a,b)=>a+b,0)-1)<1e-9,'redistribute zero others');}
  const frozen=JSON.stringify(backend);document.getElementById('weight-0').value='100';await event('weight-0','input');
  check(JSON.stringify(backend)===frozen,'slider pending sends no inference');check(document.getElementById('preference-state').textContent.includes('Chưa áp dụng'),'pending disclosed');
  await event('step','click');check(!('weights'in lastRequest),'normal single step does not apply pending weights');check(backend.panels[1].steps===1,'one real API tick');
  document.getElementById('live').checked=true;await event('live','change');await event('step','click');
  check(lastRequest.weights[0]===1&&backend.generation===1&&backend.panels[1].steps===2,'live weights without reset');check(document.getElementById('comparison').textContent.includes('lịch sử'),'history caveat');
  await event('run','click');await settle();check(backend.generation===2,'run resets same engine');check(document.getElementById('pause').textContent.includes('Tạm dừng'),'running pause control');
  await event('pause','click');const paused=JSON.stringify(backend);await settle();check(JSON.stringify(backend)===paused,'pause no physics');
  const beforeSkin=JSON.stringify(backend);document.getElementById('skin').value='native';await event('skin','change');check(JSON.stringify(backend)===beforeSkin,'skin no tick');check(document.getElementById('left').hidden,'native mode hides cosmetic canvas');
  document.getElementById('skin').value='styled';await event('skin','change');await event('mine','click');check(backend.environment==='mine'&&backend.panels[0].steps===0,'Minecart selected/reset paused');check(document.getElementById('sliders').children.length===3,'three Minecart sliders');
  await event('step','click');check(backend.panels[0].steps===1,'Minecart tick');check(document.getElementById('notice').textContent.includes('chưa đạt'),'Minecart failure visible');
  const renderer=new context.window.SceneRenderer(new Element(),'#70e4c4');const input=panel([.3,.3,.4],'mine');const original=JSON.stringify(input);renderer.draw(input);check(JSON.stringify(input)===original,'renderer never changes state');renderer.draw(input);check(renderer.trail.length===1,'paused render does not duplicate trail');check(draws>0,'both sprite render paths executed');
  networkFailure=true;const count=posts.length;await event('step','click');check(!document.getElementById('error').hidden,'error visible');check(document.getElementById('step').disabled&&document.getElementById('pause').disabled,'fault halts controls');check(posts.length===count,'failed call not retried');
  console.log(JSON.stringify({status:'PASS',assertions:checks,scope:'Fake DOM/canvas/transport unit tests only, not browser rendering',draw_calls:draws}));
})().catch(error=>{console.error(error);process.exitCode=1;});
