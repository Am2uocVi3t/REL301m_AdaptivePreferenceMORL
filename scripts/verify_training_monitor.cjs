/* Exercise the actual local monitor and store browser receipts on D:. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(path.resolve(path.dirname(process.execPath), '../node_modules/playwright'));

(async () => {
  const output = path.resolve('artifacts/training-monitor/verification');
  fs.mkdirSync(output, {recursive:true});
  const context = await chromium.launchPersistentContext(path.join(output, 'edge-profile'), {
    executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless:true,
    viewport:{width:1440,height:1080},
    args:['--no-first-run','--disable-default-apps',`--disk-cache-dir=${path.join(output,'edge-cache')}`]
  });
  const errors = [];
  try {
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(String(error)));
    page.on('console', event => {if (event.type() === 'error') errors.push(event.text());});
    await page.goto('http://127.0.0.1:8770/', {waitUntil:'networkidle'});
    await page.waitForFunction(() => document.getElementById('connection').textContent === 'CONNECTED');
    const state = await page.evaluate(() => fetch('/api/state').then(r=>r.json()));
    assert.equal(await page.locator('#jobs tr').count(),12);
    assert.equal(await page.locator('#done').textContent(),String(state.counts.complete));
    await page.selectOption('#filter','failed');
    assert.equal(await page.locator('#jobs button').count(),state.counts.failed + state.counts.interrupted);
    await page.selectOption('#filter','all');
    await page.locator('#jobs button').first().click();
    await page.waitForFunction(() => document.getElementById('selected-name').textContent.includes('ARM A'));
    await page.waitForFunction(() => document.querySelector('#loss-plot svg'));
    await page.click('#tab-stdout');
    await page.waitForFunction(() => document.getElementById('log-name').textContent.endsWith('.stdout.log'));
    await page.click('#pause');
    assert.equal(await page.locator('#pause').textContent(),'Resume view');
    assert.match(await page.locator('#refresh-label').textContent(),/TRAINING UNAFFECTED/);
    await page.click('#pause');
    await page.click('#refresh');
    await page.waitForTimeout(800);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth),false);
    await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth),false);
    await page.route('**/api/state', route=>route.abort());
    await page.click('#refresh');
    await page.waitForFunction(()=>document.getElementById('connection').textContent === 'DISCONNECTED');
    assert.match(await page.locator('#offline').textContent(),/does not mean training stopped/);
    await page.unroute('**/api/state');
    await page.click('#refresh');
    await page.waitForFunction(()=>document.getElementById('connection').textContent === 'CONNECTED');
    const unexpected = errors.filter(message=>!message.includes('ERR_FAILED'));
    assert.deepEqual(unexpected,[]);
    fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify({
      status:'pass',observed:new Date().toISOString(),counts:state.counts,steps:state.total_steps,
      checks:['real data rendered','worker filters','selection and recorded loss plot','log tabs','pause and refresh',
        'desktop/mobile no body overflow','disconnect warning and reconnection','no unexpected browser errors'],
      desktop:path.join(output,'desktop.png'),mobile:path.join(output,'mobile.png')
    },null,2));
    console.log(JSON.stringify({status:'pass',counts:state.counts,steps:state.total_steps}));
  } finally {await context.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
