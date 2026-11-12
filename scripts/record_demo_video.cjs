/* Discover, rehearse and record actual PPO application states. No fabricated gameplay. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const {chromium}=require('playwright');

(async()=>{
  const root=path.resolve(process.argv[2]),output=path.resolve(process.argv[3]);
  const base=process.env.REL301M_DEMO_URL||'http://127.0.0.1:18772';
  const ffmpeg=process.env.FFMPEG_PATH;if(!ffmpeg)throw Error('Set FFMPEG_PATH');
  fs.mkdirSync(output,{recursive:true});const frames=path.join(output,'frames');
  if(fs.existsSync(frames))throw Error('Frames directory already exists. Use a new versioned output.');
  fs.mkdirSync(frames);
  const plan=JSON.parse(fs.readFileSync(path.join(root,'docs/course/video/storyboard.json'),'utf8'));
  const paragraphs=fs.readFileSync(path.join(root,'docs/course/video/SCRIPT_EN.md'),'utf8').split(/\r?\n\s*\r?\n/).map(p=>p.trim()).filter(p=>p&&!p.startsWith('#')&&!p.startsWith('Target:'));
  const spoken=paragraphs.join('\n\n'),wordCues=[];let timelineTime=0;
  for(const scene of plan.scenes){
    scene.start=timelineTime;
    for(const paragraph of scene.paragraphs){
      for(const word of paragraphs[paragraph].split(/\s+/)){
        wordCues.push({word,start:timelineTime,end:timelineTime+60/plan.reading_wpm,scene:scene.id});
        timelineTime+=60/plan.reading_wpm+(/[.!?]$/.test(word)?plan.sentence_pause_seconds:0);
      }
      timelineTime+=plan.paragraph_pause_seconds;
    }
    scene.seconds=Math.max(scene.minimum_seconds,timelineTime-scene.start+2);
    timelineTime=scene.start+scene.seconds;
  }
  const logo=fs.readFileSync(path.join(root,'paper/REL301m/Figures/0. General/fpt_logo_red_small.png')).toString('base64');
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,acceptDownloads:true,bypassCSP:true});
  const page=await context.newPage(),errors=[],actions=[],shots=[];
  page.on('pageerror',e=>errors.push(String(e)));let session,capturing=false,index=0,clock=0;
  const wait=ms=>page.waitForTimeout(ms);
  const state=()=>page.evaluate(()=>fetch('/api/state').then(r=>r.json()));
  async function click(selector){
    const target=page.locator(selector);await target.waitFor({state:'visible'});
    await page.waitForFunction(s=>{const el=document.querySelector(s);return el&&!el.disabled;},selector,{timeout:20000});
    assert.ok(await target.isEnabled(),`Enabled: ${selector}`);
    await target.scrollIntoViewIfNeeded();const b=await target.boundingBox();assert.ok(b);
    await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:18});await wait(300);await target.click();await wait(350);
    actions.push({at:(Date.now()-clock)/1000,selector});
  }
  async function pauseIfRunning(){
    if((await page.locator('#pause').innerText()).includes('Pause')&&await page.locator('#pause').isEnabled())await click('#pause');
  }
  async function slider(value){
    const input=page.locator('#weight-0'),b=await input.boundingBox();assert.ok(b);
    const current=Number(await input.inputValue())/100;
    await page.mouse.move(b.x+8+(b.width-16)*current,b.y+b.height/2,{steps:15});await page.mouse.down();
    await page.mouse.move(b.x+8+(b.width-16)*value,b.y+b.height/2,{steps:30});await page.mouse.up();await wait(400);
    actions.push({at:(Date.now()-clock)/1000,slider:Number(await input.inputValue())});
  }
  async function scene(id,work){
    const spec=plan.scenes.find(s=>s.id===id),start=Date.now();
    await page.evaluate(t=>{document.querySelector('#record-caption').textContent=t;},spec.caption);
    await boundaryFrame();
    if(work)await work();
    const used=Date.now()-start;if(used<spec.seconds*1000)await wait(spec.seconds*1000-used);
    await boundaryFrame();
    const s=await state();shots.push({id,at:(start-clock)/1000,duration:(Date.now()-start)/1000,
      environment:s.environment,steps:s.panels.map(p=>p.steps),raw_returns:s.panels.map(p=>p.raw_return),training_updates:s.training_updates});
    assert.equal(s.training_updates,0);
  }
  async function phrase(text){
    const terms=text.split(/\s+/),index=wordCues.findIndex((_,i)=>terms.every((term,j)=>wordCues[i+j]?.word===term));
    assert.ok(index>=0,`Narration phrase exists: ${text}`);
    const delay=wordCues[index].start*1000-(Date.now()-clock);
    if(delay>0)await wait(delay);
  }
  async function boundaryFrame(){
    if(!capturing)return;
    const bytes=await page.screenshot({type:'jpeg',quality:95});
    const file=`frame-${String(index++).padStart(6,'0')}.jpg`;
    fs.writeFileSync(path.join(frames,file),bytes);
    shots.frames.push({file,time:Date.now()/1000});
  }
  try{
    await page.goto(base,{waitUntil:'networkidle'});
    await page.waitForFunction(()=>document.querySelector('#led').classList.contains('ready'));
    const discovery=await page.locator('button,input,select').evaluateAll(els=>els.map(e=>({id:e.id,tag:e.tagName,text:e.textContent.trim().slice(0,90)})));
    for(const selector of ['#run','#step','#pause','#weight-0','#skin','#mine','#live','#trace'])assert.equal(await page.locator(selector).count(),1);
    // Rehearse the essential transition/reset without capture.
    await click('#step');assert.equal((await state()).panels[0].steps,1);
    await page.reload({waitUntil:'networkidle'});await page.waitForFunction(()=>document.querySelector('#led').classList.contains('ready'));
    await page.evaluate(logo=>{
      const style=document.createElement('style');style.textContent='#record-cursor{position:fixed;z-index:999999;pointer-events:none;width:25px;height:31px;left:40px;top:40px;filter:drop-shadow(1px 2px 2px #0008)}#record-caption{position:fixed;bottom:0;left:0;right:0;padding:15px 30px;background:#071b18f0;color:#fff;font:25px/1.3 Segoe UI;text-align:center;z-index:999995;pointer-events:none}#record-card{position:fixed;inset:0;z-index:999997;background:#f7f4ee;color:#14201b;padding:11vh 12vw;display:flex;flex-direction:column;justify-content:center;font:30px/1.6 Segoe UI}#record-card h1{font:64px/1.15 Georgia;margin:25px 0;color:#14201b}#record-card p{max-width:1300px}#record-card img{width:180px;align-self:flex-start}';document.head.append(style);
      const cursor=document.createElement('div');cursor.id='record-cursor';cursor.innerHTML='<svg viewBox="0 0 25 31"><path d="M2 1L22 18L13 19L9 29Z" fill="white" stroke="#14201b" stroke-width="2"/></svg>';document.body.append(cursor);
      document.addEventListener('mousemove',e=>{cursor.style.left=e.clientX+'px';cursor.style.top=e.clientY+'px';});
      const caption=document.createElement('div');caption.id='record-caption';document.body.append(caption);
      const card=document.createElement('div');card.id='record-card';card.innerHTML=`<img src="data:image/png;base64,${logo}" alt="FPT University"><p>REL301m · Project demonstration</p><h1>One policy.<br>Different priorities.</h1><p>Preference-conditioned multi-objective reinforcement learning<br>Minecart and LunarLander · Frozen PPO inference</p><p>Captioned demo master · Record your own narration in the Recording Desk.</p>`;document.body.append(card);
    },logo);
    session=await context.newCDPSession(page);clock=Date.now();actions.length=0;
    session.on('Page.screencastFrame',async event=>{
      try{if(capturing){const file=`frame-${String(index++).padStart(6,'0')}.jpg`;fs.writeFileSync(path.join(frames,file),Buffer.from(event.data,'base64'));shots.frames.push({file,time:event.metadata.timestamp});}}
      finally{await session.send('Page.screencastFrameAck',{sessionId:event.sessionId}).catch(()=>{});}
    });
    shots.frames=[];capturing=true;await session.send('Page.startScreencast',{format:'jpeg',quality:95,maxWidth:1920,maxHeight:1080,everyNthFrame:1});
    await scene('intro');await page.locator('#record-card').evaluate(e=>e.remove());
    await scene('lunar',async()=>{await phrase('Single step');for(let i=0;i<3;i++){await click('#step');await wait(700);}await phrase('Run comparison');await click('#run');await wait(6500);await pauseIfRunning();});
    await scene('preferences',async()=>{await slider(.42);assert.match(await page.locator('#preference-state').innerText(),/Not applied/);await phrase('Normally the change');await click('#run');await wait(3500);await pauseIfRunning();await phrase('The native renderer');const before=(await state()).panels[0].steps;await page.locator('#skin').selectOption('native');await wait(3500);assert.equal((await state()).panels[0].steps,before);await page.locator('#skin').selectOption('styled');});
    await scene('minecart',async()=>{await click('#mine');await wait(1500);await click('#run');await wait(9000);await pauseIfRunning();await slider(.8);await click('#run');await wait(8500);await pauseIfRunning();});
    await scene('live',async()=>{await click('#lunar');await click('#mine');for(let i=0;i<3;i++)await click('#step');await click('#live');await slider(.35);await click('#step');assert.ok((await state()).history_dependent);await click('details.model summary');const download=page.waitForEvent('download');await click('#trace');await (await download).saveAs(path.join(output,'demonstration-trace.json'));});
    await page.evaluate(()=>{const card=document.createElement('div');card.id='record-card';card.innerHTML='<p>What the evidence supports</p><h1>Task competence first.<br>Claims bounded by evidence.</h1><p>Minecart: three confirmation training seeds.<br>Lunar: two prospective confirmation seeds, separate from the displayed pilot.</p><p>No guarantee at every preference or shifted dynamics.<br>Adaptive-allocation superiority remains unestablished.<br>Inference only. Original final-test gate remains locked.</p>';document.body.append(card);});
    await scene('limits');capturing=false;await session.send('Page.stopScreencast');assert.deepEqual(errors,[]);
    assert.ok(shots.frames.length>100,'Continuous frame capture');
    shots.frames.sort((a,b)=>a.time-b.time);
    const list=shots.frames.map((f,i)=>`file '${path.join(frames,f.file).replaceAll('\\','/')}'\nduration ${i+1<shots.frames.length?Math.max(.001,shots.frames[i+1].time-f.time):.05}`).join('\n')+`\nfile '${path.join(frames,shots.frames.at(-1).file).replaceAll('\\','/')}'\n`;
    fs.writeFileSync(path.join(output,'frames.ffconcat'),list);
    const result=spawnSync(ffmpeg,['-nostdin','-hide_banner','-f','concat','-safe','0','-i',path.join(output,'frames.ffconcat'),'-vf','scale=1920:1080,setsar=1','-r','30','-fps_mode','cfr','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',path.join(output,'demo.mp4')],{encoding:'utf8',maxBuffer:20*1024*1024});
    fs.writeFileSync(path.join(output,'encode.log'),result.stderr||'');assert.equal(result.status,0,result.stderr?.slice(-2000));
    const frameCount=shots.frames.length,mediaOffset=shots.frames[0].time-clock/1000;delete shots.frames;
    const adjusted=wordCues.map(cue=>{const scene=plan.scenes.find(s=>s.id===cue.scene),actual=shots.find(s=>s.id===cue.scene);const shift=actual.at-scene.start-mediaOffset;return {...cue,start:Math.max(0,cue.start+shift),end:Math.max(0,cue.end+shift)};});
    fs.writeFileSync(path.join(output,'narration-timeline.json'),JSON.stringify({version:1,reading_wpm:plan.reading_wpm,script:spoken,words:adjusted,scenes:shots.map(s=>({id:s.id,start:Math.max(0,s.at-mediaOffset),end:s.at+s.duration-mediaOffset})),scope:'Word times follow the captured scene clock, not speech recognition'},null,2));
    fs.writeFileSync(path.join(output,'capture-receipt.json'),JSON.stringify({status:'pass',scope:'Real browser presentation recording; not independent research validation',width:1920,height:1080,fps:30,frame_count:frameCount,reading_wpm:plan.reading_wpm,discovery,actions,scenes:shots,training_updates:0,final_test_steps:0,page_errors:errors,narration:'No human voice yet'},null,2));
    console.log(`PASS: ${frameCount} real frames encoded to ${path.join(output,'demo.mp4')}`);
  }finally{capturing=false;await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
