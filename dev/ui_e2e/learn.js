// 弱點診斷、題目語言切換、真實考場英文模式、對拍補測資、單元 49 的弱點區塊。
const { chromium } = require('playwright');
const log = (ok, msg) => { console.log((ok ? 'PASS ' : 'FAIL ') + msg); if (!ok) process.exitCode = 1; };
const BASE = 'http://127.0.0.1:8793/';
const BUGGY = 'n = int(input())\na = input().split()\nprint(1 + sum(1 for i in range(1, n) if a[i] != a[i-1]))\n';
const BRUTE = 'n = int(input())\na = input().split()\nr = []\nfor x in a:\n    if x not in r:\n        r.append(x)\nprint(len(r))\n';
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => localStorage.setItem('cpe.onboarded', 'true'));
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !/409|400/.test(m.text())) errs.push('CONSOLE ' + m.text()); });
  await p.goto(BASE); const token = await p.evaluate(() => document.querySelector('meta[name=cpe-token]').content);
  const api = (path, body) => p.evaluate(async ([path, body, token]) => {
    const r = await fetch(path, { method: body === undefined ? 'GET' : 'POST', headers: { 'X-CPE-Token': token, 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
    return r.json();
  }, [path, body, token]);

  // ---- 弱點：做三題動態規劃都失敗 ----
  await api('/api/course/goto', { n: 34 });
  const u31 = await api('/api/unit?n=31'), u32 = await api('/api/unit?n=32');
  const dp = [...u31.drills, ...u32.drills].map(d => d.id).slice(0, 3);
  for (const id of dp) { await api('/api/new', { id }); await api('/api/save', { id, code: 'print(0)\n' }); await api('/api/test', { id }); await api('/api/test', { id }); }
  await p.goto(BASE + '#/stats'); await p.waitForSelector('h3:has-text("主題弱點")');
  log((await p.locator('.weakrow', { hasText: '動態規劃' }).count()) === 1, '統計頁：主題弱點列出「動態規劃」');
  log((await p.locator('.weakrow:has-text("動態規劃") .pill.bad').count()) === 1, '動態規劃標示為弱點');
  log((await p.locator('section:has-text("主題弱點") h4:has-text("建議加練")').count()) === 1, '有建議加練的題');
  await p.locator('section:has(h3:has-text("主題弱點"))').screenshot({ path: 'shots/l1-weak-card.png' });
  await p.goto(BASE + '#/home'); await p.waitForSelector('.plan');
  await p.click('button:has-text("90 分")'); await p.waitForTimeout(500);
  log((await p.locator('.plan .pill:has-text("弱點")').count()) >= 1, '今日計畫排進「弱點」加練');
  await p.goto(BASE + '#/course/49'); await p.waitForSelector('.drawer');
  log((await p.locator('.drawer h4:has-text("依你的紀錄診斷出的弱點")').count()) === 1, '單元 49 的抽屜顯示依紀錄診斷的弱點');
  await p.keyboard.press('Escape');

  // ---- 題目語言 ----
  await p.goto(BASE + '#/practice/d031'); await p.waitForSelector('.stmt');
  log((await p.textContent('.stmt')).includes('中文對照'), '階段 1 的題：自動＝中英對照');
  log((await p.locator('.stmt hr').count()) === 1, '分隔線有畫出來');
  await p.click('.langseg button:has-text("EN")'); await p.waitForFunction(() => !document.querySelector('.stmt').textContent.includes('中文對照'));
  log((await p.textContent('.stmt')).includes('Sample Input') && (await p.locator('.stmt h2:has-text("輸入")').count()) === 0, '切到 EN：只剩英文題目');
  await p.screenshot({ path: 'shots/l2-en.png' });
  await p.click('.langseg button:has-text("中")'); await p.waitForFunction(() => document.querySelector('.stmt').textContent.includes('這題在練什麼'));
  log(true, '切到中文');
  await p.click('.langseg button:has-text("自動")'); await p.waitForFunction(() => document.querySelector('.stmt').textContent.includes('中文對照'));
  log(true, '切回自動');
  await p.goto(BASE + '#/settings'); await p.waitForSelector('select[aria-label="內建練習題的題目語言"]');
  log((await p.inputValue('select[aria-label="內建練習題的題目語言"]')) === 'auto', '設定頁可選題目語言');

  // ---- 真實考場模式：內建題也一律英文 ----
  const ex = await api('/api/mock', { kind: 'short', real: true });
  log(!ex.error, '比照考場的短測驗可以開始（內建題有英文版）' + (ex.error ? '：' + ex.error : ''));
  const st = await api('/api/state'); const pid = st.exam.problems[0].id;
  await p.goto(BASE + '#/practice/' + pid); await p.waitForSelector('.stmt h1');
  const txt = await p.textContent('.stmt');
  log(/Input/.test(txt) && !/[\u4e00-\u9fff]{4}/.test(txt.replace(/考試中/g, '')), `考試中 ${pid}：題目全英文`);
  log((await p.locator('.langseg').count()) === 0, '考試中不能切換語言');
  await api('/api/exam/finish', {});

  // ---- 對拍補測資 ----
  await api('/api/past/statement', { id: 'fz9', text: 'Count the distinct numbers among n integers given on one line. '.repeat(3) + '\n\nSample Input\n3\n1 1 2\n\nSample Output\n2\n' });
  await api('/api/new', { id: 'fz9' }); await api('/api/save', { id: 'fz9', code: BUGGY });
  const t0 = await api('/api/test', { id: 'fz9' });
  log(t0.verdict === 'AC', '壞解答先通過範例（排序好的範例藏得住 bug）');
  await p.goto(BASE + '#/practice/fz9'); await p.waitForSelector('.editor');
  await p.click('button:has-text("對拍補測資")'); await p.waitForSelector('.modal textarea');
  await p.fill('.modal textarea', BRUTE); await p.click('.modal button:has-text("開始對拍")');
  await p.waitForSelector('.modal .callout.warn', { timeout: 90000 });
  log((await p.textContent('.modal')).includes('差異 1'), '對拍找到差異並顯示輸入、暴力解與你的輸出');
  await p.waitForSelector('.modal .callout.ok:has-text("已存成")'); log(true, '差異已存成測資');
  await p.screenshot({ path: 'shots/l3-fuzz.png' });
  await p.click('.modal button:has-text("關閉")');
  await p.click('text=執行測試'); await p.waitForFunction(() => (document.querySelector('.verdict')?.textContent || '').includes('WA'));
  log(true, '存下的測資讓壞解答現形（WA）');

  log(errs.length === 0, '沒有 JS 錯誤' + (errs.length ? '：' + errs.slice(0, 3).join(' | ') : ''));
  await b.close();
})();
