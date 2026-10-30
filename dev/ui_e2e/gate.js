const { chromium } = require('playwright');
const log = (ok, msg) => console.log((ok ? 'PASS ' : 'FAIL ') + msg);
const REF = {
  d001: 'print(f"Hello, {input().strip()}!")\n',
  d002: 'import sys\nfor l in sys.stdin:\n    p=l.split()\n    if p: print(int(p[0])+int(p[1]))\n',
  d003: 'w,h=map(int,input().split())\nprint(w*h,2*(w+h))\n',
  d004: 'import sys\nfor l in sys.stdin:\n    if l.strip(): print(f"{int(l)*9/5+32:.1f}")\n',
};
let PAGE;
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => localStorage.setItem('cpe.onboarded', 'true'));
  const p = await ctx.newPage(); PAGE = p; const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + e.message)); p.on('console', m => { if (m.type() === 'error' && !/409|400/.test(m.text())) errs.push('CONSOLE ' + m.text()); });
  await p.goto('http://127.0.0.1:8793/#/home'); await p.waitForTimeout(800);
  const api = (path, body) => p.evaluate(async ([path, body]) => {
    const tok = document.querySelector('meta[name="cpe-token"]').content;
    const r = await fetch(path, { method: 'POST', headers: { 'X-CPE-Token': tok, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); return r.json();
  }, [path, body]);
  for (const id of ['d001', 'd002', 'd003']) { await api('/api/new', { id }); const r = await api('/api/test', { id, code: REF[id] }); if (r.verdict !== 'AC') log(false, id + ' ' + r.verdict); }
  await p.reload(); await p.waitForSelector('text=開始單元檢核'); log(true, '三題必做完成 → 首頁出現「開始單元檢核」');
  await p.screenshot({ path: 'shots/g1-home.png' });
  await p.click('text=開始單元檢核'); await p.waitForSelector('.modal'); log((await p.textContent('.modal')).includes('AI 詢問與提示全部鎖定'), '檢核前顯示規則確認');
  await p.click('.modal-f .primary'); await p.waitForSelector('.examcard'); log(true, '檢核開始 → 首頁出現考試面板（倒數計時）');
  log(await p.locator('#examChip').count() === 1, '頂列出現考試倒數');
  await p.screenshot({ path: 'shots/g2-exam.png' });
  await p.click('.examcard .scoreboard .linkish >> nth=0'); await p.waitForSelector('.editor'); await p.waitForTimeout(300);
  const id0 = await p.evaluate(() => location.hash.split('/').pop()); log(['d004', 'd002'].includes(id0), '從考試面板開啟題目 ' + id0);
  log((await p.locator('.pill.bad', { hasText: '考試中' }).count()) === 1, '題目頁標示「考試中」');
  // 考試中 AI 鎖定
  await p.fill('.ta', REF[id0]); await p.dblclick('.ta', { position: { x: 40, y: 16 } });
  await p.waitForSelector('.pop'); log((await p.locator('.pop .opt:disabled').count()) === 3, '考試中：三種問法全部鎖定');
  await p.keyboard.press('Escape');
  await p.click('text=執行測試'); await p.waitForSelector('.verdict .badge.AC'); log(true, id0 + ' 在考試中通過');
  const other = id0 === 'd004' ? 'd002' : 'd004';
  await p.goto('http://127.0.0.1:8793/#/practice/' + other); await p.waitForSelector(`.pchip.cur:has-text("${other}")`); await p.waitForSelector('.editor'); await p.fill('.ta', REF[other]);
  await p.click('text=執行測試'); await p.waitForSelector('.verdict .badge.AC'); log(true, other + ' 在考試中通過');
  await p.goto('http://127.0.0.1:8793/#/home'); await p.waitForSelector('.examcard');
  await p.click('.examcard >> text=交卷'); await p.waitForSelector('.modal'); await p.click('.modal-f .primary');
  await p.waitForSelector('.modal >> text=答對題數'); const txt = await p.textContent('.modal'); log(txt.includes('檢核通過'), '交卷結果：' + txt.replace(/\s+/g, ' ').slice(0, 90));
  await p.screenshot({ path: 'shots/g3-finish.png' });
  await p.click('.modal-f .primary'); await p.waitForTimeout(900);
  log((await p.textContent('.topbar')).includes('單元 2/52'), '通過後自動進入單元 2：' + (await p.textContent('.crumb')).slice(0, 30));
  log(await p.locator('.examcard').count() === 0, '考試面板消失');
  log(errs.length === 0, '沒有 JS／CSP 錯誤' + (errs.length ? '：' + errs.slice(0, 3).join(' | ') : ''));
  await b.close();
})().catch(async e => { console.log('FAIL 例外：' + e.message.split('\n')[0]); await PAGE.screenshot({ path: 'shots/gfail.png' }); console.log(await PAGE.evaluate(() => document.querySelector('#view').innerText.slice(0,400).replace(/\n/g,'|'))); process.exit(1); });
