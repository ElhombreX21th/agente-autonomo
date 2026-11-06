const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

async function main() {
  const requestPath = process.argv[2];
  const outputDir = process.argv[3];
  if (!requestPath || !outputDir) throw new Error('usage: browser_worker.cjs REQUEST OUTPUT_DIR');
  const workflow = JSON.parse(fs.readFileSync(requestPath, 'utf8'));
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined),
    headless: process.env.BROWSER_HEADED !== '1',
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const extracted = {};
  try {
    for (let index = 0; index < workflow.steps.length; index += 1) {
      const step = workflow.steps[index];
      if (step.action === 'goto') {
        await page.goto(step.value, { waitUntil: 'domcontentloaded', timeout: 30000 });
      } else if (step.action === 'fill') {
        const value = step.secret_env ? process.env[step.secret_env] : step.value;
        if (value === undefined) throw new Error(`missing secret environment variable: ${step.secret_env}`);
        await page.locator(step.selector).fill(value);
      } else if (step.action === 'select') {
        const value = step.secret_env ? process.env[step.secret_env] : step.value;
        if (value === undefined) throw new Error(`missing value: ${step.secret_env}`);
        await page.locator(step.selector).selectOption(value);
      } else if (step.action === 'click' || step.action === 'logout') {
        await page.locator(step.selector).click();
      } else if (step.action === 'check') {
        await page.locator(step.selector).check();
      } else if (step.action === 'wait_for') {
        await page.locator(step.selector).waitFor({ state: 'visible', timeout: 30000 });
      } else if (step.action === 'extract') {
        extracted[step.label || `step_${index + 1}`] = await page.locator(step.selector).innerText();
      } else if (step.action === 'screenshot') {
        const destination = path.resolve(outputDir, step.value);
        const root = path.resolve(outputDir) + path.sep;
        if (!destination.startsWith(root)) throw new Error('screenshot escaped output directory');
        fs.mkdirSync(path.dirname(destination), { recursive: true });
        await page.screenshot({ path: destination, fullPage: true });
      } else if (step.action === 'human_challenge') {
        const challenge = await page.locator('iframe[src*="captcha"], [class*="captcha" i], [id*="captcha" i]').count();
        if (challenge || process.env.BROWSER_HEADED !== '1') {
          fs.writeFileSync(path.join(outputDir, 'human-action-required.json'), JSON.stringify({
            status: 'human_action_required',
            instruction: step.value || 'Complete the visible human-verification challenge, then resume.',
            url: page.url(),
          }, null, 2));
          process.exitCode = 20;
          return;
        }
      }
    }
    fs.writeFileSync(path.join(outputDir, 'result.json'), JSON.stringify({ status: 'completed', extracted, url: page.url() }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
