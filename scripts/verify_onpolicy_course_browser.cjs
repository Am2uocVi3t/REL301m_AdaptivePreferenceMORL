/* Real Edge/Playwright checks against the independently installed demo. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

(async () => {
  const root = process.cwd();
  const output = path.resolve(process.argv[2] || path.join(root, 'artifacts/presentation-verification/2026-11-01'));
  fs.mkdirSync(output, {recursive:true});
  const errors = [];
  const context = await chromium.launchPersistentContext(path.join(output, 'edge-profile'), {
    executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless:true, viewport:{width:1440,height:1000},
    args:['--no-first-run','--disable-default-apps',`--disk-cache-dir=${path.join(output,'edge-cache')}`]
  });
  try {
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(String(error)));
    await page.goto('http://127.0.0.1:18766', {waitUntil:'networkidle'});
    await page.waitForFunction(() => document.querySelector('#led').classList.contains('ready'));
    const state = () => page.evaluate(() => fetch('/api/state').then(response=>response.json()));
    let before = await state();
    assert.equal(before.environment,'lunar');
    assert.deepEqual(before.panels[0].observation,before.panels[1].observation);
    await page.locator('#step').click();
    await page.waitForFunction(() => document.querySelector('#left-step').textContent==='0001');
    before = await state();
    assert.deepEqual(before.panels[0].raw_return,before.panels[1].raw_return);
    await page.locator('#weight-0').evaluate(element => {
      element.value='100';element.dispatchEvent(new Event('input',{bubbles:true}));
    });
    assert.equal((await state()).panels[1].steps,1);
    await page.locator('#live').check();
    await page.locator('#step').click();
    await page.waitForFunction(() => document.querySelector('#right-step').textContent==='0002');
    const changed = await state();
    assert.equal(changed.panels[1].weights[0],1);
    assert.equal(changed.history_dependent,true);
    await page.screenshot({path:path.join(output,'lunar-browser.png'),fullPage:true});
    await page.locator('#skin').selectOption('native');
    await page.waitForFunction(() => document.querySelector('#left-native').naturalWidth>0);
    assert.equal((await state()).panels[0].steps,2);
    await page.locator('#skin').selectOption('styled');
    await page.locator('#mine').click();
    await page.waitForFunction(() => document.querySelector('#sliders').children.length===3);
    assert.match(await page.locator('#notice').textContent(),/PPO/);
    assert.match(await page.locator('#model-info').textContent(),/20264311/);
    await page.locator('#step').click();
    await page.waitForFunction(() => document.querySelector('#left-step').textContent==='0001');
    assert.equal((await state()).environment,'mine');
    await page.screenshot({path:path.join(output,'minecart-browser.png'),fullPage:true});
    for (const endpoint of ['/docs/report.pdf','/docs/guide.pdf']) {
      const response=await page.request.get('http://127.0.0.1:18766'+endpoint);
      assert.equal(response.status(),200);assert.match(response.headers()['content-type'],/pdf/);
    }
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(output,'mobile-browser.png'),fullPage:true});
    const dimensions=await page.evaluate(()=>({body:document.body.scrollWidth,viewport:window.innerWidth}));
    assert.deepEqual(errors,[]);
    const result={status:'PASS',browser:'Microsoft Edge headless',
      independently_launched_package:true, minecart_ppo_verified:true,matched_reset:true,single_step:true,
      pending_slider_no_steps:true,live_preference_without_reset:true,
      native_render_no_steps:true,both_environments:true,pdf_links:true,page_errors:errors,
      mobile_dimensions:dimensions,mobile_horizontal_overflow:dimensions.body>dimensions.viewport};
    fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(result,null,2));
    process.stdout.write(JSON.stringify(result,null,2)+'\n');
  } finally {await context.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
