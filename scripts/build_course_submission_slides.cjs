/* Preserve the team's fixed 16:9 visual system; export a bounded English edition. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
  const root=path.resolve(process.argv[2]),output=path.resolve(process.argv[3]);fs.mkdirSync(output,{recursive:true});
  const folder=path.join(root,'docs/course/presentation');
  const data=JSON.parse(fs.readFileSync(path.join(folder,'submission-en.json'),'utf8'));
  const source=fs.readFileSync(path.join(folder,'index.html'),'utf8');
  const base=source.match(/<style>([\s\S]*?)<\/style>/)[1];
  const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
  const diagrams={formulation:['STATE s','PREFERENCE w','POLICY pi(a | s, w)','VECTOR REWARD r','WEIGHTED UTILITY w^T G'],architecture:['OBSERVATION + PREFERENCE','CONDITIONED FEATURES','CATEGORICAL ACTOR','VECTOR CRITIC + NORMALIZATION','ENVIRONMENT STEP'],workflow:['DECLARED PROTOCOL','TRAINING / VALIDATION BUDGETS','TASK-COMPETENCE GATE','PAIRED COMPARATIVE STUDY','FINAL TEST: LOCKED'],references:['CONDITIONED POLICIES','VECTOR VALUE LEARNING','PPO AND NORMALIZATION','BENCHMARKS AND PROVENANCE','QUALIFIED EVIDENCE']};
  const sections=data.slides.map((s,i)=>`<section class="slide ${i===0?'active':''}" id="slide-${i+1}"><div class="top-rule"></div><div class="ghost-num">${String(i+1).padStart(2,'0')}</div><div class="s-head"><div><div class="kicker-row"><span class="sp-pill sp-hung">${escape(s.speaker)}</span><span class="kicker-hint">FPT University · Group 2</span></div><h2 class="s-title">${escape(s.title)}</h2></div><div class="head-meta"><span class="crumb">${escape(s.tag)}</span><span class="page-chip">${i+1} / 12</span></div></div><div class="s-body lay-50-50"><div class="stack">${s.items.map((item,j)=>`<div class="card c-${j===0?'o':j===1?'t':'i'}"><span class="no n-${j===0?'o':j===1?'t':'i'}">0${j+1}</span><div><h4>${escape(item[0])}</h4><p>${escape(item[1])}</p></div></div>`).join('')}</div>${s.image?`<div class="fig"><div class="img-wrap"><img src="${s.image}" alt="${escape(s.caption)}"></div><div class="cap">${escape(s.caption)}</div></div>`:`<div class="diagram">${diagrams[s.diagram].map((text,k)=>`<div class="diagram-box">${escape(text)}</div>${k<4?'<div class="diagram-arrow">↓</div>':''}`).join('')}<p>One model input can change; the scientific scope stays explicit.</p></div>`}</div><div class="s-foot"><span>REL301m · <b>Preference-Conditioned MORL</b></span><span>${i+1} / 12 · ${escape(s.tag)}</span></div></section>`).join('');
  const css=`${base}\n:root{--font-display:Georgia,serif;--font-body:'Segoe UI',sans-serif;--font-mono:Consolas,monospace}.rv{opacity:1!important;animation:none!important}.s-title{font-size:60px;max-width:1450px}.s-head{min-height:150px}.card h4{font-size:28px}.card p{font-size:25px;line-height:1.45}.stack{justify-content:center}.card{padding:27px 28px}.fig .img-wrap img{width:100%;height:100%;object-fit:contain}.diagram{align-self:center;position:relative;z-index:2;text-align:center;padding:24px 55px}.diagram-box{border:2px solid #c9c2b2;background:white;padding:24px;font:700 25px 'Segoe UI';border-left:8px solid #de5a26;border-radius:12px}.diagram-arrow{font-size:34px;color:#0c5a50}.diagram p{font-size:23px;color:#61706a;margin-top:24px}.slide{transition:none}.s-foot{font-size:20px}@media print{@page{size:20in 11.25in;margin:0}html,body{width:1920px;height:auto;overflow:visible!important;margin:0}.deck-viewport{position:static;display:block;background:none}.deck-stage{position:static!important;transform:none!important;overflow:visible;box-shadow:none;height:auto}.slide,.slide.active{position:relative;inset:auto;opacity:1;visibility:visible;transform:none;page-break-after:always;break-after:page;overflow:hidden}.slide:last-child{break-after:auto;page-break-after:auto}}`;
  const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><title>REL301m - Group 2 English Defense</title><style>${css}</style></head><body><div class="deck-viewport"><div class="deck-stage" id="deckStage">${sections}</div></div><script>let i=0;const slides=[...document.querySelectorAll('.slide')];function fit(){document.querySelector('#deckStage').style.transform='scale('+Math.min(innerWidth/1920,innerHeight/1080)+')'}addEventListener('resize',fit);addEventListener('keydown',e=>{if(e.key==='ArrowRight')i=Math.min(11,i+1);if(e.key==='ArrowLeft')i=Math.max(0,i-1);slides.forEach((s,n)=>s.classList.toggle('active',n===i))});fit();</script></body></html>`;
  fs.writeFileSync(path.join(folder,'submission-en.html'),html.split(/\r?\n/).map(line=>line.trimEnd()).join('\n')+'\n');
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1920,height:1080}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto('http://127.0.0.1:18782/docs/course/presentation/submission-en.html',{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
    assert.equal(await page.locator('.slide').count(),12);assert.ok(await page.locator('img').evaluateAll(images=>images.every(i=>i.complete&&i.naturalWidth>0)),'All slide images load');
    const overflow=[];
    for(let i=0;i<12;i++){
      await page.evaluate(i=>document.querySelectorAll('.slide').forEach((s,n)=>s.classList.toggle('active',n===i)),i);
      const problems=await page.locator('.slide.active').evaluate(slide=>[...slide.querySelectorAll('.card,.s-head,.fig,.diagram')].filter(e=>e.getBoundingClientRect().bottom>1005||e.scrollHeight>e.clientHeight+3).map(e=>e.className));
      if(problems.length)overflow.push({slide:i+1,problems});
      await page.screenshot({path:path.join(output,`slide-${String(i+1).padStart(2,'0')}.png`)});
    }
    assert.deepEqual(overflow,[],'No content overflow');assert.deepEqual(errors,[]);
    await page.pdf({path:path.join(output,'REL301m_Slides.pdf'),preferCSSPageSize:true,printBackground:true});
    fs.writeFileSync(path.join(output,'slides-verification.json'),JSON.stringify({status:'pass',slide_count:12,language:'en',original_source_preserved:true,images_loaded:true,overflow,page_errors:errors},null,2));
    console.log('PASS: 12 English slides, loaded images, no content overflow, PDF exported');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
