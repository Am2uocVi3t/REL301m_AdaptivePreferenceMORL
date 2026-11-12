/* Verify the real scene-linked master and reader against one media clock. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
(async()=>{
  const output=path.resolve(process.argv[2]);fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1500,height:1100}}),errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  try{
    await page.goto(process.env.REL301M_STUDIO_URL||'http://127.0.0.1:18781',{waitUntil:'networkidle'});
    await page.waitForFunction(()=>!document.querySelector('#record').disabled);
    const config=await (await page.request.get(new URL('/api/config',page.url()).href)).json();
    const timeline=config.timeline;assert.equal(timeline.reading_wpm,95);assert.equal(timeline.words.length,336);
    assert.equal(await page.locator('#speed').inputValue(),'95');
    assert.equal(await page.locator('#source').evaluate(v=>v.playbackRate),1);
    await page.locator('#preview').click();await page.waitForTimeout(1000);await page.locator('#preview').click();
    const frozen=await page.locator('#source').evaluate(v=>v.currentTime);
    await page.waitForTimeout(550);assert.equal(await page.locator('#source').evaluate(v=>v.currentTime),frozen);
    const checked=[];
    for(const scene of timeline.scenes){
      const time=Number((scene.start+Math.min(3,(scene.end-scene.start)/2)).toFixed(1));
      await page.locator('#position').fill(String(time));await page.locator('#position').dispatchEvent('input');
      await page.waitForFunction(t=>Math.abs(document.querySelector('#source').currentTime-t)<.1,time);
      const expected=timeline.words.filter(w=>w.start<=time).at(-1)||timeline.words[0];
      await page.waitForFunction(word=>document.querySelector('.current-word')?.textContent===word,expected.word);
      checked.push({scene:scene.id,time,highlight:expected.word});
    }
    await page.locator('#speed').fill('70');await page.locator('#speed').dispatchEvent('input');
    assert.ok(Math.abs((await page.locator('#source').evaluate(v=>v.playbackRate))-70/95)<.0001);
    await page.locator('#script-top').click();await page.locator('#preview').click();
    const before=await page.locator('#source').evaluate(v=>v.currentTime);await page.waitForTimeout(1200);
    const after=await page.locator('#source').evaluate(v=>v.currentTime);
    assert.ok(after-before>.55&&after-before<1.2,'Slower pace changes the video clock too');
    await page.locator('#preview').click();
    const time=await page.locator('#source').evaluate(v=>v.currentTime),expected=timeline.words.filter(w=>w.start<=time).at(-1)||timeline.words[0];
    assert.equal(await page.locator('.current-word').innerText(),expected.word);
    const lunar=timeline.scenes.find(s=>s.id==='lunar');
    await page.locator('#position').fill((lunar.start+30).toFixed(1));await page.locator('#position').dispatchEvent('input');
    await page.waitForTimeout(500);await page.screenshot({path:path.join(output,'slow-synchronized-desk.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(output,'sync.json'),JSON.stringify({status:'pass',default_wpm:95,master_word_count:336,scene_seek_checks:checked,preview_pause_freezes_video:true,pace_70_changes_video_rate:true,highlight_uses_media_time:true,page_errors:errors},null,2));
    console.log('PASS: six scene boundaries, 95/70 WPM linked video speed, pause, seeking and media-clock highlighting');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
