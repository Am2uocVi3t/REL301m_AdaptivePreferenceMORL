/* Real-browser English UI checks and real-policy screenshots. No training. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

(async () => {
  const base = process.env.REL301M_DEMO_URL || 'http://127.0.0.1:18769';
  const output = path.resolve(process.argv[2]);
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({channel:'msedge', headless:true});
  const page = await browser.newPage({viewport:{width:1600,height:1100}});
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  const state = () => page.evaluate(() => fetch('/api/state').then(r=>r.json()));
  try {
    await page.goto(base, {waitUntil:'networkidle'});
    await page.waitForFunction(() => document.querySelector('#led').classList.contains('ready'));
    assert.equal(await page.locator('html').getAttribute('lang'), 'en');
    assert.match(await page.locator('h1').innerText(), /One policy/);
    const specs=await page.evaluate(()=>fetch('/api/config').then(r=>r.json()).then(c=>c.environments));
    const records=[];
    for (const name of ['lunar','mine']) {
      if (name==='mine') await page.locator('#mine').click();
      await page.waitForFunction(n => document.querySelector('#sliders').children.length === n, name==='mine'?3:4);
      const initial=await state();
      assert.deepEqual(initial.panels[0].observation,initial.panels[1].observation);
      // Fixed presentation horizon: no selection based on success or reward.
      for (let i=0; i<(name==='lunar'?80:120); i++) {
        const before=await state();
        if(before.all_done) break;
        await page.locator('#step').click();
        await page.waitForFunction(t => document.querySelector('#left-step').textContent !== t,
          String(before.panels[0].steps).padStart(4,'0'));
      }
      const final=await state();
      assert.equal(final.training_updates,0);
      const body=await page.locator('body').innerText();
      assert.ok(!/[\u0102-\u01b0\u1ea0-\u1ef9]/u.test(body),'English visible UI');
      await page.screenshot({path:path.join(output,`${name}-english.png`),fullPage:true});
      await page.locator('#skin').selectOption('native');
      await page.waitForFunction(() => document.querySelector('#left-native').naturalWidth>0);
      assert.equal((await state()).panels[0].steps,final.panels[0].steps);
      await page.screenshot({path:path.join(output,`${name}-native.png`),fullPage:true});
      await page.locator('#skin').selectOption('styled');
      records.push({environment:name,environment_seed:specs[name].seed,training_seed:specs[name].training_seed,
        checkpoint_sha256:specs[name].weights_sha256,steps:final.panels.map(p=>p.steps),
        raw_returns:final.panels.map(p=>p.raw_return),training_updates:0});
    }
    await page.reload({waitUntil:'networkidle'});
    await page.waitForFunction(() => document.querySelector('#led').classList.contains('ready'));
    await page.locator('#weight-0').evaluate(el=>{el.value='100';el.dispatchEvent(new Event('input',{bubbles:true}));});
    assert.match(await page.locator('#preference-state').innerText(),/Not applied/);
    const beforeLive=await state();
    await page.locator('#live').check(); await page.locator('#step').click();
    await page.waitForFunction(() => document.querySelector('#comparison').textContent.includes('histories'));
    const afterLive=await state();
    assert.equal(afterLive.generation,beforeLive.generation);
    assert.equal(afterLive.panels[1].weights[0],1);
    const guide=await page.request.get(base+'/guide.html'); assert.equal(guide.status(),200);
    const report=await page.request.get(base+'/docs/report.pdf');
    assert.equal(report.status(),200);assert.match(report.headers()['content-type'],/pdf/);
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(output,'mobile-english.png'),fullPage:true});
    assert.ok(await page.evaluate(()=>document.body.scrollWidth<=innerWidth),'mobile has no horizontal overflow');
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(output,'browser-receipt.json'),JSON.stringify({status:'pass',
      scope:'English UI and fixed-horizon presentation diagnostics, not task-performance evidence',
      records,live_preference:true,native_renderer:true,mobile:true,page_errors:errors},null,2));
    console.log('PASS: English UI, real-policy steps, native renderer, live preferences and mobile');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
