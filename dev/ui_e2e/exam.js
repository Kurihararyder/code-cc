// 考試頁、整場歷屆模擬、計分板、單字本、今日計畫、校準、工程任務、備份下載。
const { chromium, devices } = require('playwright');
const log = (ok, msg) => { console.log((ok ? 'PASS ' : 'FAIL ') + msg); if (!ok) process.exitCode = 1; };
const BASE = 'http://127.0.0.1:8793/';
const MAN = Array.from({ length: 7 }, (_, i) => `2023-01-10,${i + 1},${20001 + i},Problem ${i + 1},${(50 / (i + 1)).toFixed(2)}`).join('\n') + '\n# 2023-01-10 avg=1.4';
const STMT = (n) => `Problem ${n}\n\nRead one integer from the standard input and print the value of that integer multiplied by ${n} on a single line. The input contains exactly one integer and nothing else, so you do not need to worry about blank lines.\n\nSample Input\n3\n\nSample Output\n${3 * n}\n`;
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  await ctx.addInitScript(() => { localStorage.setItem('cpe.onboarded', 'true'); });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !/409|400/.test(m.text())) errs.push('CONSOLE ' + m.text()); });

  // ---- 今日計畫 ----
  await p.goto(BASE + '#/home'); await p.waitForSelector('.plan');
  log((await p.locator('.plan li').count()) >= 1, '首頁有「今日計畫」，列出項目');
  const before = await p.locator('.plan li').count();
  await p.click('button:has-text("15 分")'); await p.waitForTimeout(400);
  log((await p.locator('.plan li').count()) <= before && (await p.locator('button[aria-pressed="true"]:has-text("15 分")').count()) === 1, '切換到 15 分鐘，項目不會變多');
  await p.screenshot({ path: 'shots/e1-plan.png' });

  // ---- 考試頁：內建資料 ----
  await p.click('a[data-nav="exam"]'); await p.waitForSelector('text=2020-10-20 場');
  log((await p.locator('section:has-text("2020-10-20 場") tbody tr').count()) === 7, '內建 2020-10-20 場有 7 題');
  log((await p.locator('text=無 UVA 題號').count()) === 2, '報告沒給 UVA 題號的 2 題如實標示，不亂補');
  log((await p.locator('section:has-text("2020-10-20 場") >> text=開始整場').count()) === 0, '沒有測資 → 不能開始整場');
  await p.screenshot({ path: 'shots/e2-exam-page.png', fullPage: true });

  // ---- 匯入清單 ----
  await p.click('button:has-text("匯入歷屆清單")'); await p.fill('.modal textarea', 'garbage');
  await p.click('.modal button:has-text("匯入")'); await p.waitForSelector('.modal .bad');
  log(true, '匯入錯誤格式 → 顯示說明，不關閉對話框');
  await p.fill('.modal textarea', MAN); await p.click('.modal button:has-text("匯入")');
  await p.waitForSelector('text=2023-01-10 場'); log(true, '匯入 7 題清單 → 出現新場次');
  log((await p.locator('section:has-text("2023-01-10 場") .stars').first().textContent()).includes('★'), '星等依答對率換算');
  log((await p.locator('section:has-text("2023-01-10 場") >> text=平均答對 1.4 題').count()) === 1, '平均答對題數有匯入');

  // ---- 貼上 7 題題目 ----
  for (let n = 1; n <= 7; n++) {
    await p.locator('section:has-text("2023-01-10 場") tbody tr').nth(n - 1).locator('button:has-text("貼上題目")').click();
    await p.fill('.modal textarea', STMT(n)); await p.click('.modal button:has-text("儲存")');
    await p.waitForSelector('.modal', { state: 'detached' });
  }
  await p.waitForSelector('section:has-text("2023-01-10 場") >> text=開始整場');
  log(true, '7 題都有題目與範例測資 → 可以開始整場');

  // ---- 開始整場 ----
  await p.click('section:has-text("2023-01-10 場") >> text=開始整場'); await p.click('.modal button:has-text("開始")');
  await p.waitForSelector('.scoreboard'); log((await p.locator('.scoreboard tbody tr').count()) === 7, '考試中：計分板 7 列');
  log((await p.textContent('.examcard')).includes('歷屆整場進行中'), '標題顯示歷屆整場');
  await p.screenshot({ path: 'shots/e3-scoreboard.png' });

  // ---- 作答第 1 題 ----
  await p.click('.scoreboard tbody tr:nth-child(1) .linkish'); await p.waitForSelector('#p2');
  if (await p.locator('#p2 >> text=用 Python 開始').count()) await p.click('#p2 >> text=用 Python 開始');
  await p.waitForSelector('.editor');
  log((await p.locator('.stmt').textContent()).includes('Read one integer'), '英文題目文字顯示在題目面板');
  // 英文單字：雙擊 → 查字典／加入單字本（考試中仍可用，AI 鎖定）
  await p.dblclick('.stmt >> text=integer >> nth=0'); await p.waitForSelector('.pop');
  log((await p.locator('.pop .opt:has-text("查字典")').count()) === 1, '雙擊英文單字 → 有「查字典」');
  log(await p.locator('.pop .opt:has-text("查字典")').isEnabled(), '考試中字典仍可用');
  log(await p.locator('.pop .opt:has-text("這是什麼意思")').isDisabled(), '考試中 AI 選項鎖定');
  await p.click('.pop .opt:has-text("加入單字本")'); await p.waitForSelector('.toast:has-text("已加入單字本")'); log(true, '加入單字本');
  const added = ((await p.textContent('.toast:has-text("已加入單字本")')).match(/：(\S+)/) || [])[1];
  await p.click('.ta'); await p.keyboard.press('Control+a'); await p.keyboard.type('print(int(input()) * 1)\n');
  await p.click('text=執行測試'); await p.waitForFunction(() => document.querySelector('.verdict .badge.AC'));
  log(true, '第 1 題通過');
  await p.click('a[data-nav="exam"]'); await p.waitForSelector('.scoreboard .sb.ac');
  log((await p.locator('.scoreboard tfoot').textContent()).includes('1/7'), '計分板更新為 1/7');
  // 第 2 題故意答錯 → 罰時
  await p.click('.scoreboard tbody tr:nth-child(2) .linkish'); await p.waitForSelector('#p2');
  if (await p.locator('#p2 >> text=用 Python 開始').count()) await p.click('#p2 >> text=用 Python 開始');
  await p.waitForSelector('.editor'); await p.click('.ta'); await p.keyboard.press('Control+a'); await p.keyboard.type('print(0)\n');
  await p.click('text=執行測試'); await p.waitForFunction(() => (document.querySelector('.verdict')?.textContent || '').includes('WA'));
  await p.click('a[data-nav="exam"]'); await p.waitForSelector('.scoreboard .sb.wrong');
  log((await p.locator('.scoreboard .sb.wrong').textContent()).includes('✗1'), '答錯 → 計分板顯示 ✗1');

  // ---- 交卷 ----
  await p.click('.examcard button:has-text("交卷")'); await p.click('.modal button:has-text("交卷")');
  await p.waitForSelector('.modal:has-text("交卷完成")');
  log((await p.textContent('.modal')).includes('超過了約'), '交卷後顯示歷年考生百分位');
  await p.screenshot({ path: 'shots/e4-finish.png' });
  await p.click('.modal button:has-text("回到今日")');

  // ---- 單字本 ----
  await p.click('a[data-nav="exam"]'); await p.waitForSelector('h3:has-text("單字本")');
  log((await p.locator('section:has-text("單字本") .mono', { hasText: added }).count()) >= 1, `單字本有剛加入的字（${added}）`);
  log((await p.locator('section:has-text("單字本") a[href*="dictionary.cambridge.org"]').count()) >= 1, '單字附字典連結');

  // ---- 校準 ----
  await p.click('a[data-nav="stats"]'); await p.waitForSelector('text=難度校準');
  log((await p.locator('section:has-text("難度校準") tbody tr').count()) >= 1, '統計頁：校準表有資料（剛解出的題）');
  log((await p.textContent('section:has-text("考試紀錄")')).includes('超過約'), '考試紀錄顯示百分位');

  // ---- 工程任務 ----
  await p.goto(BASE + '#/course/eng'); await p.waitForSelector('text=工程能力');
  log((await p.locator('section:has-text("用 pytest 為 3 個舊題目寫測試")').count()) === 1, '工程任務頁列出任務');
  const t3 = p.locator('section:has-text("用 pytest 為 3 個舊題目寫測試")');
  await t3.locator('button:has-text("建立範本")').click(); await p.waitForSelector('.toast:has-text("已建立")'); log(true, '建立範本');
  await t3.locator('button:has-text("驗收")').click(); await p.waitForSelector('.modal:has-text("還沒過")', { timeout: 60000 });
  log((await p.locator('.modal li.bad').count()) >= 1, '範本還沒寫 → 驗收失敗並說明哪裡不過');
  await p.click('.modal button:has-text("關閉")');
  const t2 = p.locator('section:has-text("學會開 PR")');
  await t2.locator('button:has-text("驗收")').click(); await p.fill('.modal input', 'https://example.com/x'); await p.click('.modal button:has-text("驗收")');
  await p.waitForSelector('.modal:has-text("還沒過")'); log(true, '手動任務：不合格的證據網址被拒絕');
  await p.click('.modal button:has-text("關閉")');
  await p.screenshot({ path: 'shots/e5-eng.png', fullPage: true });

  // ---- 單元抽屜的歷屆題庫 ----
  await p.goto(BASE + '#/course/15'); await p.waitForSelector('.drawer');
  log((await p.locator('.drawer h4:has-text("歷屆題庫")').count()) === 1, '單元 15 顯示歷屆題庫區塊');
  await p.keyboard.press('Escape');

  // ---- 備份下載 ----
  await p.goto(BASE + '#/settings'); await p.waitForSelector('text=備份與搬家');
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('button:has-text("下載備份")')]);
  const path = await dl.path(); const size = require('fs').statSync(path).size;
  log(dl.suggestedFilename().endsWith('.zip') && size > 500, `下載備份 zip（${size} bytes）`);

  // ---- 版本與更新（只檢查，不更新）----
  await p.goto(BASE + '#/settings'); await p.waitForSelector('h3:has-text("版本與更新")');
  log(/\d+\.\d+\.\d+/.test(await p.textContent('section:has-text("版本與更新") .mono')), '設定頁顯示目前版本');
  await p.click('button:has-text("檢查更新")');
  await p.waitForFunction(() => { const t = document.querySelector('#updResult')?.textContent || ''; return t && !t.includes('檢查中'); }, null, { timeout: 60000 });
  log((await p.textContent('#updResult')).length > 3, '檢查更新有回應（最新／有新版本／或說明為何無法檢查）：' + (await p.textContent('#updResult')).slice(0, 40));

  // ---- 手機：6 個導覽項目不溢出 ----
  const m = await b.newContext({ ...devices['iPhone 13'] });
  await m.addInitScript(() => { localStorage.setItem('cpe.onboarded', 'true'); });
  const q = await m.newPage(); await q.goto(BASE + '#/exam'); await q.waitForSelector('text=2020-10-20 場');
  const sw = await q.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
  log(sw[0] <= sw[1] + 1, `手機：考試頁無橫向捲動（${sw[0]} ≤ ${sw[1]}）`);
  const navs = await q.locator('.rail .navbtn').evaluateAll(els => els.map(e => { const r = e.getBoundingClientRect(); return [r.left, r.right]; }));
  log(navs.length === 7 && navs.every(([l, r]) => l >= 0 && r <= 391), '手機：底部 7 個導覽項目都在畫面內');
  await q.screenshot({ path: 'shots/e6-mobile-exam.png' });
  await q.goto(BASE + '#/home'); await q.waitForSelector('.plan');
  const sw2 = await q.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
  log(sw2[0] <= sw2[1] + 1, '手機：首頁（含今日計畫）無橫向捲動');

  log(errs.length === 0, '沒有 JS 錯誤' + (errs.length ? '：' + errs.slice(0, 3).join(' | ') : ''));
  await b.close();
})();
