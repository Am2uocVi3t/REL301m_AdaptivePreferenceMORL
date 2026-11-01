/* Exercise real UI controls through complete episodes; compare with fixed diagnostic traces. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

(async () => {
  const root = process.cwd();
  const output = path.join(root, 'artifacts/demo-behavior-audit-v1/browser');
  fs.mkdirSync(output, {recursive: true});
  const diagnostic = JSON.parse(fs.readFileSync(path.join(root, 'artifacts/demo-behavior-audit-v1/results.json'), 'utf8'));
  const context = await chromium.launchPersistentContext(path.join(output, 'edge-profile'), {
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true, viewport: {width: 1440, height: 1000},
    args: ['--no-first-run', '--disable-default-apps', `--disk-cache-dir=${path.join(output, 'edge-cache')}`]
  });
  const errors = [];
  const receipts = [];
  try {
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(String(error)));
    await page.goto('http://127.0.0.1:18767/', {waitUntil: 'networkidle'});
    await page.waitForFunction(() => document.querySelector('#led').classList.contains('ready'));
    const state = () => page.evaluate(() => fetch('/api/state').then(response => response.json()));
    const stepsBeforeRenderer = (await state()).presentation_steps_total;
    await page.locator('#skin').selectOption('native');
    await page.waitForFunction(() => document.querySelector('#right-native').naturalWidth > 0);
    const rendererVisibility = await page.evaluate(() => ['left', 'right'].map(side => ({
      side, canvasDisplay: getComputedStyle(document.getElementById(side)).display,
      imageDisplay: getComputedStyle(document.getElementById(side + '-native')).display,
      imageTop: document.getElementById(side + '-native').getBoundingClientRect().top,
      viewportTop: document.getElementById(side).parentElement.getBoundingClientRect().top
    })));
    const visibilityPass = rendererVisibility.every(panel => panel.canvasDisplay === 'none');
    fs.writeFileSync(path.join(output, visibilityPass ? 'native-visibility-pass.json' : 'native-visibility-fail.json'), JSON.stringify(rendererVisibility, null, 2));
    for (const panel of rendererVisibility) {
      assert.equal(panel.canvasDisplay, 'none', 'Native renderer must hide the styled canvas');
      assert.notEqual(panel.imageDisplay, 'none');
      assert(Math.abs(panel.imageTop - panel.viewportTop) < 2, 'Native image must be inside the visible viewport');
    }
    assert.equal((await state()).presentation_steps_total, stepsBeforeRenderer);
    await page.locator('#skin').selectOption('styled');
    await page.locator('#speed').selectOption('4');
    const cases = [
      {environment: 'lunar', label: 'balanced'},
      {environment: 'lunar', label: 'landing_heavy', index: 0, value: 70},
      {environment: 'mine', label: 'ore1_only', index: 0, value: 100},
      {environment: 'mine', label: 'ore2_only', index: 1, value: 100}
    ];
    for (const item of cases) {
      if ((await state()).environment !== item.environment) {
        await page.locator(`#${item.environment}`).click();
        await page.waitForFunction(count => document.querySelector('#sliders').children.length === count, item.environment === 'lunar' ? 4 : 3);
      }
      await page.locator('#skin').selectOption('styled');
      await page.locator('#balanced').click();
      if (item.index !== undefined) {
        await page.locator(`#weight-${item.index}`).evaluate((element, value) => {
          element.value = String(value);
          element.dispatchEvent(new Event('input', {bubbles: true}));
        }, item.value);
      }
      await page.locator('#run').click();
      await page.waitForFunction(() => !document.querySelector('#pause').disabled);
      await page.waitForFunction(() => document.querySelector('#pause').disabled && document.querySelector('#left-step').textContent === '1000', null, {timeout: 45000, polling: 100});
      const result = await state();
      assert.equal(result.all_done, true);
      const expected = diagnostic.episodes.find(row => row.environment === item.environment && row.case === item.label && row.seed === (item.environment === 'lunar' ? 20000 : 670000));
      assert(expected);
      assert.equal(result.panels[1].steps, expected.steps);
      result.panels[1].weights.forEach((value, index) => assert(Math.abs(value - expected.weights[index]) < 1e-6));
      result.panels[1].raw_return.forEach((value, index) => assert(Math.abs(value - expected.raw_return[index]) < 1e-4));
      assert.equal(result.training_updates, 0);
      assert.equal(result.history_dependent, false);
      await page.locator('#skin').selectOption('native');
      await page.waitForFunction(() => !document.querySelector('#skin').disabled &&
        getComputedStyle(document.querySelector('#right')).display === 'none' &&
        document.querySelector('#right-native').complete && document.querySelector('#right-native').naturalWidth > 0);
      await page.screenshot({path: path.join(output, `${item.environment}_${item.label}.png`), fullPage: true});
      receipts.push({environment: item.environment, preference: item.label, state: result, agrees_with_direct_diagnostic: true});
      process.stdout.write(`${item.environment} ${item.label}: UI/engine episode matches, steps=${expected.steps}\n`);
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({status: 'PASS', page_errors: errors, cases: receipts}, null, 2));
  } finally {
    await context.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
