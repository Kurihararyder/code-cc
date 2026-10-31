// 考試頁的「CPE 原題」卡片：看到三個題單、按「從 GitHub 匯入」（測試用假 GitHub）、匯入後可以練、課程單元出現題單。
const { chromium } = require('playwright');
const log = (ok, msg) => { console.log((ok ? 'PASS ' : 'FAIL ') + msg); if (!ok) process.exitCode = 1; };
const BASE = 'http://127.0.0.1:8793/';
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 } });
  await ctx.addInitScript(() => { localStorage.setItem('cpe.onboarded', 'true'); });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !/409|400/.test(m.text())) errs.push('CONSOLE ' + m.text()); });

  await p.goto(BASE + '#/exam'); await p.waitForSelector('#cpeSets');
  log((await p.textContent('#cpeSets')).includes('可練 0/91'), 'CPE 原題卡：一開始 0/91 題可練（題單共 91 題）');
  await p.locator('#cpeSets summary').first().click();
  log((await p.locator('#cpeSets details').first().locator('li').count()) === 49, '一星題 49 題都列出');
  log((await p.locator('#cpeSets button.li[disabled]').count()) > 0, '還沒匯入的題不能點進去練');
  await p.screenshot({ path: 'shots/c1-cpe-before.png', fullPage: true });

  await p.click('#cpeSets button:has-text("從 GitHub 匯入")');
  await p.waitForSelector('#cpeSets .pill.ok', { timeout: 60000 });
  log((await p.textContent('#cpeSets')).includes('可練 5/91'), '按下匯入 → 可練 5/91（假 GitHub 只有 5 份 PDF）');
  await p.screenshot({ path: 'shots/c2-cpe-after.png', fullPage: true });

  await p.locator('#cpeSets details').first().locator('button.li:not([disabled])').first().click();
  await p.waitForSelector('.stmt');
  log((await p.locator('.stmt').textContent()).includes('Read two integers'), '點進去：題目文字顯示出來');
  log((await p.locator('.stmt').textContent()).includes('Sample Input'), '範例輸入輸出在題目裡');

  // 搜尋與篩選
  await p.goto(BASE + '#/exam'); await p.waitForSelector('#cpeSets');
  await p.fill('#cpeSets input[type=search]', 'bfs');
  log((await p.locator('#cpeSets li').count()) >= 3 && (await p.locator('#cpeSets li').count()) < 20, '搜尋「bfs」→ 依類型標籤找到少數幾題');
  await p.fill('#cpeSets input[type=search]', '');
  await p.selectOption('#cpeSets select', 'ready');
  const nready = await p.locator('#cpeSets li').count();
  log(nready === 5, '篩選「已匯入、還沒通過」→ 5 題（' + nready + '）');
  await p.selectOption('#cpeSets select', 'missing');
  log((await p.locator('#cpeSets li').count()) === 90, '篩選「尚未匯入」→ 90 列（三個題單共 95 列，有 4 題重複列在兩個題單）');
  await p.selectOption('#cpeSets select', 'all');
  // 練習頁有原 PDF 按鈕
  await p.goto(BASE + '#/practice/uva10008'); await p.waitForSelector('.stmt');
  log((await p.locator('.stmt button:has-text("開啟原 PDF 對照")').count()) === 1, '練習頁有「開啟原 PDF 對照」');
  const [pop] = await Promise.all([ctx.waitForEvent('page', { timeout: 8000 }).catch(() => null), p.click('.stmt button:has-text("開啟原 PDF 對照")')]);
  log(!!pop, '按下去在新分頁開出 PDF');
  if (pop) await pop.close();
  await p.goto(BASE + '#/course/15'); await p.waitForSelector('.drawer'); await p.waitForSelector('text=CPE 一星題選集');
  log((await p.locator('text=CPE 一星題選集').count()) >= 1, '單元 15 出現「CPE 一星題選集」題單');
  await p.screenshot({ path: 'shots/c3-unit15.png', fullPage: true });
  const m = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
  await m.addInitScript(() => { localStorage.setItem('cpe.onboarded', 'true'); });
  const mp = await m.newPage();
  await mp.goto(BASE + '#/exam'); await mp.waitForSelector('#cpeSets');
  const over = await mp.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  log(over <= 1, '手機寬度：CPE 原題卡沒有橫向捲動（溢出 ' + over + 'px）');
  await mp.locator('#cpeSets').screenshot({ path: 'shots/c4-cpe-mobile.png' });
  log(errs.length === 0, '沒有 console 錯誤' + (errs.length ? '：' + errs.join(' | ') : ''));
  await b.close();
})().catch(e => { console.log('FAIL 例外 ' + e.message); process.exit(1); });
