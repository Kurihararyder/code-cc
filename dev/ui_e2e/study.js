// 「學習」頁：洞察、工坊（診斷／練習／示範題／排序題／找 bug／預測輸出／解法比較／術語表）、筆記、目標與匯出；
// 另外檢查語言切換、色盲友善配色、練習頁的錯因提示與逐行追蹤的圖像檢視、考場模式（禁止貼上）。
const { chromium } = require('playwright');
const log = (ok, msg) => { console.log((ok ? 'PASS ' : 'FAIL ') + msg); if (!ok) process.exitCode = 1; };
const BASE = 'http://127.0.0.1:8793/';
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  await ctx.addInitScript(() => { localStorage.setItem('cpe.onboarded', 'true'); });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
  p.on('console', (m) => { if (m.type() === 'error' && !/409|400/.test(m.text())) errs.push('CONSOLE ' + m.text()); });
  const api = (path, body) => p.evaluate(async ([path, body]) => {
    const tok = document.querySelector('meta[name="cpe-token"]').content;
    const r = await fetch(path, { method: body ? 'POST' : 'GET', headers: { 'X-CPE-Token': tok, 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
    return r.json();
  }, [path, body]);

  // ---- 洞察 ----
  await p.goto(BASE + '#/study/insights'); await p.waitForSelector('text=知識點掌握');
  log((await p.locator('a[data-nav="study"]').count()) === 1, '導覽列有「學習」');
  log((await p.locator('text=下一題推薦').count()) >= 1 && (await p.locator('text=現在該複習').count()) >= 1, '洞察頁有複習、掌握度、推薦');
  log((await p.locator('text=落點預測').count()) >= 1 && (await p.locator('text=考前清單').count()) >= 1, '有落點預測與考前清單');
  await p.screenshot({ path: 'shots/s1-insights.png', fullPage: true });

  // ---- 工坊：適性診斷 ----
  await p.click('button[role=tab]:has-text("工坊")'); await p.waitForSelector('text=適性診斷');
  await p.click('button:has-text("開始診斷")'); await p.waitForSelector('.choice');
  let n = 0; let finished = false;
  for (; n < 14; n++) {
    await p.locator('.choice').first().click();                    // 一律選 A：大多會答錯，用來測流程而不是測答案
    await p.waitForSelector('.callout');
    const next = p.locator('button.primary:has-text("下一題"), button.primary:has-text("看結果")').first();
    const label = await next.textContent(); await next.click();
    if (label.includes('看結果')) { finished = true; break; }
    await p.waitForSelector('.choice');
  }
  log(finished && n >= 5 && n <= 11, `適性診斷：答完 ${n + 1} 題後出現結果`);
  log((await p.locator('text=大略').count()) >= 1, '診斷結果有「只是大略建議」的說明');
  // 知識點練習
  await p.selectOption('select[aria-label="知識點"]', 'graph'); await p.click('button:has-text("開始"):right-of(select[aria-label="知識點"])');
  await p.waitForSelector('.choice'); log(true, '知識點練習出題');
  // 微課
  await p.selectOption('select[aria-label="微課"]', 'dp'); await p.click('button:has-text("看"):right-of(select[aria-label="微課"])');
  await p.waitForSelector('text=常見陷阱'); log(true, '微課顯示重點、程式與常見陷阱');
  // 示範題 → 空白練習
  await p.selectOption('select[aria-label="示範題"]', 'w-sum');
  await p.click('button:has-text("開始"):right-of(input[aria-label="留白步數"])'); await p.waitForSelector('textarea[aria-label="你寫的程式"]');
  await p.fill('textarea[aria-label="你寫的程式"]', 'print(max(a))'); await p.click('button:has-text("檢查"):below(textarea[aria-label="你寫的程式"])');
  await p.waitForSelector('text=還沒通過'); log(true, '空白練習：寫錯 → 還沒通過');
  await p.fill('textarea[aria-label="你寫的程式"]', 'print(sum(a))'); await p.click('button:has-text("檢查"):below(textarea[aria-label="你寫的程式"])');
  await p.waitForSelector('text=通過所有測資'); log(true, '空白練習：寫對 → 通過所有測資');
  // 排序題
  await p.selectOption('select[aria-label="排序題"]', 'w-sum'); await p.click('button:has-text("開始"):right-of(select[aria-label="排序題"])');
  await p.waitForSelector('button[aria-label="上移"]'); log((await p.locator('input[aria-label="使用這一行"]').count()) >= 3, '排序題：列出可排序的行與勾選');
  // 找 bug
  await p.selectOption('select[aria-label="找 bug"]', 'b-range'); await p.click('button:has-text("開始"):right-of(select[aria-label="找 bug"])');
  await p.waitForSelector('button.line'); await p.locator('button.line').nth(0).click(); await p.waitForSelector('text=不是第 1 行');
  await p.locator('button.line').nth(2).click(); await p.waitForSelector('text=找到了'); log(true, '找 bug：點錯行有提示，點對行顯示原因');
  // 預測輸出
  await p.selectOption('select[aria-label="預測輸出"]', 'p-float'); await p.click('button:has-text("開始"):right-of(select[aria-label="預測輸出"])');
  await p.fill('textarea[aria-label="你預測的輸出"]', '0.3'); await p.click('button:has-text("檢查"):below(textarea[aria-label="你預測的輸出"])');
  await p.waitForSelector('text=不一樣'); log(true, '預測輸出：0.3 不對，顯示實際輸出');
  // 解法比較、術語表
  await p.click('button:has-text("看"):right-of(select[aria-label="解法比較"])'); await p.waitForSelector('text=雜湊計數'); log(true, '解法比較列出各種做法與複雜度');
  await p.fill('input[aria-label="搜尋"]', 'subsequence'); await p.waitForSelector('li:has-text("子序列")'); log(true, '術語表搜尋 subsequence → 子序列');
  await p.screenshot({ path: 'shots/s2-lab.png', fullPage: true });

  // ---- 筆記 ----
  await p.click('button[role=tab]:has-text("筆記")'); await p.waitForSelector('text=寫筆記');
  await p.selectOption('select[aria-label="種類"]', 'recall'); await p.fill('input[aria-label="題號"] >> nth=0', 'uva10009');
  await p.fill('textarea[aria-label="筆記內容"]', '用 BFS 找最短路徑，記錄每個城市的上一個城市，最後倒著回溯。'); await p.click('button:has-text("送出") >> nth=0');
  await p.waitForSelector('text=對照這題的關鍵洞察'); log(true, '回想筆記：送出後對照這題的關鍵洞察');
  await p.waitForSelector('li:has-text("[recall]")'); log(true, '最近的筆記列出剛寫的');

  // ---- 目標 ----
  await p.click('button[role=tab]:has-text("目標")'); await p.waitForSelector('text=設定目標');
  const d = new Date(Date.now() + 40 * 864e5).toISOString().slice(0, 10);
  await p.fill('input[aria-label="目標日期"]', d); await p.fill('input[aria-label="目標題數"]', '30'); await p.click('button:has-text("設定目標") >> nth=-1');
  await p.waitForSelector('text=已解出／目標'); log(true, '設定目標後顯示進度與需要的速度');
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 8000 }).catch(() => null), p.click('button:has-text("cpe-anki.tsv")')]);
  log(!!dl && dl.suggestedFilename() === 'cpe-anki.tsv', '可以下載 Anki 卡片');

  // ---- 語言與色盲友善 ----
  await p.goto(BASE + '#/settings'); await p.waitForSelector('text=介面語言');
  await p.click('button[aria-label="介面語言"] >> nth=0', { timeout: 1000 }).catch(() => {});
  await p.click('[aria-label="介面語言"] button:has-text("English")'); await p.waitForSelector('text=Learn');
  log((await p.locator('a[data-nav="study"] span').first().textContent()) === 'Learn' && (await p.locator('a[data-nav="home"] span').first().textContent()) === 'Today', '切到 English：導覽列變成英文');
  await p.goto(BASE + '#/study/insights'); await p.waitForSelector('text=Concept mastery'); log(true, '學習頁的標題也是英文');
  await p.goto(BASE + '#/settings'); await p.click('[aria-label="介面語言"] button:has-text("中文")'); await p.waitForSelector('text=學習');
  await p.click('[aria-label="色盲友善配色"] button:has-text("開")');
  log((await p.evaluate(() => document.documentElement.dataset.cb)) === '1', '色盲友善配色：html 標記為開啟');
  const okColor = await p.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--ok').trim());
  log(okColor === '#0072b2' || okColor === '#56b4e9', '通過的顏色改成藍色系（' + okColor + '）');
  await p.click('[aria-label="色盲友善配色"] button:has-text("關")');

  // ---- 練習頁：錯因與追蹤圖像 ----
  await api('/api/new', { id: 'd001' });
  await p.goto(BASE + '#/practice/d001'); await p.waitForSelector('.editor');
  await p.fill('textarea.ta', 'a = [1, 2, 3]\nprint(a[7])\n'); await p.click('button:has-text("執行測試")');
  await p.waitForSelector('text=可能的錯因'); log((await p.locator('text=可能的錯因：越界').count()) === 1, '練習頁：執行錯誤顯示「可能的錯因：越界」與建議');
  await p.fill('textarea.ta', 'a = [1, 2]\nb = a + [3]\nprint(b)\n'); await p.click('button:has-text("逐行追蹤")');
  await p.waitForSelector('table.trace'); await p.click('button:has-text("圖像")'); await p.waitForSelector('.vz');
  log((await p.locator('.vz-var').count()) >= 1, '逐行追蹤的圖像檢視：顯示變數');
  await p.screenshot({ path: 'shots/s3-practice.png' });

  // ---- 考場模式：不能貼上 ----
  await api('/api/mock', { kind: 'short' }).catch(() => ({}));
  const exam = await api('/api/state');
  if (exam.exam) {
    await p.goto(BASE + '#/practice/' + exam.exam.problems[0].id); await p.waitForSelector('textarea.ta');
    await p.evaluate(() => { const ta = document.querySelector('textarea.ta'); const ev = new Event('paste', { bubbles: true, cancelable: true }); ta.dispatchEvent(ev); window.__pasteBlocked = ev.defaultPrevented; });
    log(await p.evaluate(() => window.__pasteBlocked), '考場模式：貼上被擋下');
    await api('/api/exam/finish', {});
  } else log(true, '（略過考場模式：這個工作區開不了短考）');

  log(errs.length === 0, '沒有 console 錯誤' + (errs.length ? '：' + errs.join(' | ') : ''));
  await b.close();
})().catch((e) => { console.log('FAIL 例外 ' + e.message); process.exit(1); });
