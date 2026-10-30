const { chromium } = require('playwright');
const log = (ok, msg) => console.log((ok ? 'PASS ' : 'FAIL ') + msg);
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => { if (!localStorage.getItem('cpe.keep')) { localStorage.setItem('cpe.onboarded', 'true'); } });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !/409|400/.test(m.text())) errs.push('CONSOLE ' + m.text()); });
  await p.goto('http://127.0.0.1:8793/#/practice/d001'); await p.waitForSelector('#p2 >> text=用 Python 開始');
  log(true, '練習頁載入，尚未建立解答檔 → 顯示「開始這題」');
  await p.click('#p2 >> text=用 Python 開始'); await p.waitForSelector('.editor');
  // 編輯器行為
  await p.click('.ta'); await p.keyboard.press('Control+a'); await p.keyboard.type('def f(x):'); await p.keyboard.press('Enter');
  let v = await p.inputValue('.ta'); log(v === 'def f(x):\n    ', '自動縮排：冒號後 Enter 縮 4 格');
  await p.keyboard.type('return x'); await p.keyboard.press('Shift+Tab'); v = await p.inputValue('.ta'); log(v === 'def f(x):\nreturn x', 'Shift+Tab 取消縮排');
  await p.keyboard.press('Control+z'); v = await p.inputValue('.ta'); log(v.includes('    return x'), 'Ctrl+Z 可復原（原生 undo 堆疊保留）');
  await p.keyboard.press('Control+a'); await p.keyboard.type('name = input()\nprint("Hello " + name + "!")\n');
  log((await p.locator('.hl .hl-kw, .hl .hl-bi').count()) >= 2, '語法上色出現');
  await p.selectOption('select[aria-label="先預測結果"]', 'AC');
  await p.keyboard.press('Control+Enter'); await p.waitForSelector('.verdict .badge');
  log((await p.textContent('.verdict')).includes('WA'), 'Ctrl+Enter 執行測試 → WA');
  log((await p.textContent('.verdict')).includes('你預測 AC'), '預測對照');
  log((await p.locator('.diff .dl-bad').count()) >= 2, '失敗測資差異行標紅');
  await p.screenshot({ path: 'shots/d1-result.png' });
  // 選取 → 彈出選單
  await p.dblclick('.ta', { position: { x: 70, y: 36 } });
  await p.waitForSelector('.pop'); log(true, '雙擊選字 → 跳出「要問這一段嗎？」');
  const popBox = await p.locator('.pop').boundingBox(); const taBox = await p.locator('.ta').boundingBox();
  log(popBox.y > taBox.y && popBox.y < taBox.y + 140, `選單貼近選取位置（y=${Math.round(popBox.y)}）`);
  log(await p.locator('.pop .opt').nth(1).isEnabled(), '「考我這一段」已解鎖（已跑過測試）');
  await p.fill('.pop input', '我猜少了逗號'); await p.waitForTimeout(400); await p.screenshot({ path: 'shots/d2-popup.png' });
  await p.click('.pop .opt >> nth=1'); await p.waitForSelector('.thread .chip');
  log((await p.locator('.thread .chip', { hasText: '第' }).count()) >= 1, 'AI 回覆含已驗證引用（顯示行號）');
  await p.click('.thread .chip'); await p.waitForTimeout(250);
  log((await p.locator('.hl .l.focus').count()) >= 1, '點引用 → 編輯器該行閃爍標示');
  await p.fill('.reply textarea', '我覺得是 Hello 後面少逗號'); await p.click('.reply button');
  await p.waitForFunction(() => document.querySelectorAll('.thread .msg.ai').length >= 2); log(true, '回覆追問 → 收到 feedback');
  await p.screenshot({ path: 'shots/d3-thread.png' });
  // 閘門
  await p.dblclick('.ta', { position: { x: 30, y: 16 } }); await p.waitForSelector('.pop');
  log(await p.locator('.pop .opt').nth(1).isDisabled(), '剛問過 → 「考我這一段」鎖定並說明原因');
  log((await p.locator('.pop .opt').nth(1).textContent()).includes('先改一版'), '鎖定原因文字：' + (await p.locator('.pop .opt').nth(1).textContent()).replace(/\s+/g,' ').slice(0,40));
  await p.keyboard.press('Escape'); log((await p.locator('.pop').count()) === 0, 'Esc 關閉選單');
  // 題目敘述選取 → explain
  await p.click('.stmt p >> nth=0', { clickCount: 3 }); await p.waitForSelector('.pop');
  await p.click('.pop .opt >> nth=0'); await p.waitForFunction(() => document.querySelectorAll('.thread').length >= 2); log(true, '題目敘述選取 → 解釋（不受閘門限制）');
  // 修好 → AC
  await p.click('.ta'); await p.keyboard.press('Control+a'); await p.keyboard.type('print(f"Hello, {input().strip()}!")\n');
  await p.click('text=執行測試'); await p.waitForFunction(() => document.querySelector('.verdict .badge.AC')); log(true, '修正後 AC');
  log((await p.textContent('.res')).includes('之後要'), 'AC 後說明「用過提示 → 要無提示重寫」');
  // 提示階梯
  await p.click('text=提示階梯'); await p.waitForSelector('.step');
  log((await p.locator('.step').count()) === 5, '提示階梯顯示 L0–L4');
  // 指令面板
  await p.keyboard.press('Escape'); await p.keyboard.press('Control+k'); await p.waitForSelector('.palette input');
  await p.keyboard.type('d003'); await p.waitForSelector('.palette .li >> text=d003'); await p.keyboard.press('Enter'); await p.waitForFunction(() => location.hash.includes('d003'));
  log(true, 'Ctrl+K 搜尋 d003 → 跳轉');
  // 首頁：重練與統計
  await p.goto('http://127.0.0.1:8793/#/home'); await p.waitForTimeout(900);
  log((await p.textContent('#view')).includes('已通過題數'), '首頁載入');
  await p.screenshot({ path: 'shots/d4-home.png' });
  await p.goto('http://127.0.0.1:8793/#/stats'); await p.waitForTimeout(700); await p.screenshot({ path: 'shots/d5-stats.png' });
  // 深色
  await p.click('button[aria-label="切換外觀"]'); await p.click('button[aria-label="切換外觀"]'); await p.waitForTimeout(200);
  log((await p.evaluate(() => document.documentElement.dataset.theme)) === 'dark', '外觀循環到深色');
  await p.goto('http://127.0.0.1:8793/#/practice/d001'); await p.waitForSelector('.editor'); await p.waitForTimeout(500); await p.screenshot({ path: 'shots/d6-dark.png' });
  log(errs.length === 0, '沒有 JS／CSP 錯誤' + (errs.length ? '：' + errs.slice(0, 3).join(' | ') : ''));
  await b.close();
})().catch(e => { console.log('FAIL 例外：' + e.message.split('\n')[0]); process.exit(1); });
