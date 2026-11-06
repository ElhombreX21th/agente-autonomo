// Requires Playwright and Chromium. Run against an isolated, empty demo database.
const { chromium } = require('playwright');
const fs = require('node:fs');
const base = process.env.AGENT_TEST_URL || 'http://127.0.0.1:8787';
(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium', args:['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1100}});
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    // Route through Node's local HTTP client: browser enterprise navigation policy
    // can otherwise block a loopback URL in this managed cloud environment.
    await page.route(base+'/**',async route=>{
      const req=route.request();
      const response=await fetch(req.url(),{method:req.method(),headers:req.headers(),body:req.postData() || undefined});
      await route.fulfill({status:response.status,headers:Object.fromEntries(response.headers),body:Buffer.from(await response.arrayBuffer())});
    });
    await page.goto(base);
    await page.getByRole('button',{name:'Create a support task'}).click();
    await page.getByLabel('Fictional request').fill('Synthetic urgent export failure at Demo Site A');
    await page.getByRole('button',{name:'Create reviewable plan'}).click();
    await page.waitForFunction(()=>document.querySelector('#task-state').textContent==='approval_required');
    await page.getByRole('button',{name:'Approve local execution',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#task-state').textContent==='completed');
    if(!await page.locator('#result').innerText().then(t=>t.includes('urgent')))throw Error('Expected urgent classification');
    await page.screenshot({path:process.env.AGENT_SCREENSHOT || '/tmp/agent-workspace.png'});
    const download=page.waitForEvent('download');
    await page.getByRole('button',{name:'Export task JSON'}).click();
    const file=await download;
    const data=JSON.parse(fs.readFileSync(await file.path(),'utf8'));
    if(data.status!=='completed'||data.events.length!==5)throw Error('Incorrect export');
    await page.reload();
    await page.getByRole('button',{name:'Activity & history',exact:true}).click();
    await page.getByLabel('Search loaded tasks by request or status').fill('Synthetic urgent export failure');
    await page.getByRole('button',{name:'Inspect',exact:true}).first().click();
    await page.waitForFunction(()=>document.querySelector('#task-state').textContent==='completed');
    await page.getByLabel('Fictional request').fill('Synthetic nonurgent checklist review');
    await page.getByLabel('Permitted local tool').selectOption('checklist');
    await page.getByRole('button',{name:'Create reviewable plan'}).click();
    await page.waitForFunction(()=>document.querySelector('#task-state').textContent==='approval_required');
    await page.getByRole('button',{name:'Cancel pending task'}).click();
    await page.waitForFunction(()=>document.querySelector('#task-state').textContent==='cancelled');
    await page.setViewportSize({width:390,height:844});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile horizontal overflow');
    if(errors.length)throw Error(errors.join('\n'));
    console.log('Browser: create → approve → result → export → reload → history; cancellation and mobile layout OK');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
