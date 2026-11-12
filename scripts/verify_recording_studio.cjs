/* Actual browser capture/export integration using synthetic test audio only. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
(async()=>{
  const output=path.resolve(process.argv[2]),wav=path.resolve(process.argv[3]);fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({channel:'msedge',headless:true,args:['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--autoplay-policy=no-user-gesture-required']});
  const page=await browser.newPage({viewport:{width:1500,height:1100}});const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));page.on('dialog',d=>d.accept());
  try{
    await page.goto('http://127.0.0.1:18780',{waitUntil:'networkidle'});
    await page.locator('#record').waitFor({state:'visible'});await page.waitForFunction(()=>!document.querySelector('#record').disabled);
    assert.equal(await page.locator('html').getAttribute('lang'),'en');
    await page.evaluate(()=>{window.micRequests=0;const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);navigator.mediaDevices.getUserMedia=(...args)=>{window.micRequests++;return original(...args);};});
    assert.equal(await page.evaluate(()=>window.micRequests),0,'No automatic mic access');
    await page.locator('#record').click();await page.waitForFunction(()=>document.querySelector('#state').textContent==='Recording');
    await page.waitForTimeout(1300);await page.locator('#pause').click();const position=await page.locator('#source').evaluate(v=>v.currentTime);
    await page.waitForTimeout(700);assert.ok(Math.abs((await page.locator('#source').evaluate(v=>v.currentTime))-position)<.12,'Paused take freezes video');
    await page.locator('#pause').click();await page.waitForTimeout(1200);await page.locator('#stop').click();
    await page.waitForFunction(()=>document.querySelector('#state').textContent==='Take ready');
    assert.equal(await page.evaluate(()=>window.micRequests),1);
    assert.ok((await page.locator('#raw').getAttribute('href')).startsWith('blob:'));
    // Importing a known voice fixture exercises the non-microphone source too.
    await page.locator('#voice-file').setInputFiles(wav);await page.locator('details summary').click();await page.locator('#music').check();
    await page.locator('#record').click();await page.waitForFunction(()=>document.querySelector('#state').textContent==='Recording');
    await page.waitForTimeout(2200);await page.locator('#stop').click();await page.waitForFunction(()=>document.querySelector('#state').textContent==='Take ready');
    assert.equal(await page.evaluate(()=>window.micRequests),1,'Imported narration does not open mic');
    const raw=await page.locator('#raw').getAttribute('href');
    await page.route('**/api/export',r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Synthetic export failure'})}));
    await page.locator('#export').click();await page.waitForFunction(()=>document.querySelector('#export-status').textContent.includes('Export failed'));
    assert.equal(await page.locator('#raw').getAttribute('href'),raw,'Original kept after export failure');
    await page.unroute('**/api/export');await page.locator('#export').click();await page.locator('#download').waitFor({state:'visible',timeout:120000});
    const url=await page.locator('#download').getAttribute('href'),response=await page.request.get('http://127.0.0.1:18780'+url);
    assert.equal(response.status(),200);fs.writeFileSync(path.join(output,'synthetic-narrated-test.mp4'),await response.body());
    await page.screenshot({path:path.join(output,'recording-desk.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.body.scrollWidth<=innerWidth));
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify({status:'pass',scope:'Synthetic audio/fixture video; no real microphone-quality claim',no_auto_mic:true,microphone_request_on_record:true,pause_resume:true,imported_audio:true,music_mix:true,original_take_survives_failed_export:true,local_mp4_export:true,mobile_no_overflow:true,page_errors:errors},null,2));
    console.log('PASS: real browser recording desk, fake mic, imported voice, pause, recovery and MP4 export');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
