// 管理後台與登入閘門的瀏覽器測試（對假 Supabase）。用法見 run_admin.sh
const { chromium } = require('playwright');
const base = process.argv[2];
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1360, height: 860 } });
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.goto(base); await p.waitForSelector('.gate-card');
  await p.fill('input[aria-label=學號]', 's001'); await p.fill('input[aria-label=密碼]', 'bad'); await p.click('button[type=submit]'); await p.waitForTimeout(600);
  ok((await p.textContent('.gate-msg')).includes('錯誤'), 'wrong password shows an error');
  await p.fill('input[aria-label=密碼]', 'init1234'); await p.click('button[type=submit]'); await p.waitForSelector('#userBtn');
  await p.keyboard.press('Escape');
  await p.goto(base + '#/admin/users'); await p.waitForTimeout(500);
  ok(await p.isVisible('text=只有管理員可以使用'), 'student cannot open the admin page');
  await p.click('#userBtn'); await p.click('text=回報題目問題'); await p.fill('textarea[aria-label=說明]', '範例輸出和說明不一致'); await p.fill('input[aria-label=題號]', 'd019'); await p.click('.modal-f >> text=送出'); await p.waitForTimeout(500);
  ok(await p.isVisible('text=已送出'), 'student can report a problem');
  await p.click('#userBtn'); await p.click('text=登出'); await p.waitForSelector('.gate-card');
  await p.fill('input[aria-label=學號]', 'admin'); await p.fill('input[aria-label=密碼]', 'admin1234'); await p.click('button[type=submit]'); await p.waitForSelector('#userBtn');
  await p.keyboard.press('Escape');
  for (const t of ['overview', 'users', 'insights', 'network', 'ai', 'release', 'reports', 'audit']) {
    await p.goto(base + '#/admin/' + t); await p.waitForTimeout(700);
    ok(await p.isVisible('.admin-tabs button[aria-selected=true]'), 'tab ' + t + ' renders');
  }
  await p.goto(base + '#/admin/overview'); await p.waitForTimeout(600);
  ok(await p.isVisible('text=不同 IP 登入') && await p.isVisible('text=1 則題目回報還沒處理'), 'overview shows anomalies and open reports');
  await p.goto(base + '#/admin/reports'); await p.waitForTimeout(600);
  ok(await p.isVisible('text=範例輸出和說明不一致'), 'reports tab lists the report');
  await p.click('text=標記已處理'); await p.waitForTimeout(400);
  ok(await p.isVisible('text=沒有待處理的回報'), 'resolving removes it from the queue');
  await p.goto(base + '#/admin/users'); await p.waitForTimeout(500);
  await p.click('text=批次新增'); await p.fill('textarea[aria-label=名單]', 'n001, 甲\nn002, 乙\ns001, 重複'); await p.click('.modal-f >> text=建立'); await p.waitForSelector('.modal-h >> text=已建立');
  const mt = await p.locator('.modal').last().textContent(); const mt2 = await p.textContent('.modal-h >> text=已建立'); void mt2; if (!(mt.includes('pw-n001') && mt.includes('學號已存在'))) console.log('MODAL:', mt.slice(0, 300)); ok(mt.includes('pw-n001') && mt.includes('學號已存在'), 'bulk create shows passwords and duplicates');
  await p.click('.modal-f >> text=完成'); await p.waitForTimeout(500);
  await p.check('thead input[type=checkbox]'); ok(await p.isVisible('text=已選 3 位'), 'select all shows the bulk bar');
  await p.click('.bulkbar >> text=停用'); await p.click('.modal-f >> text=執行'); await p.waitForTimeout(600);
  ok((await p.locator('tbody .pill', { hasText: '待開通' }).count()) === 3, 'bulk disable applied to 3 students');
  await p.check('thead input[type=checkbox]'); await p.click('.bulkbar >> text=封存'); await p.click('.modal-f >> text=封存'); await p.waitForTimeout(600);
  ok(await p.isVisible('text=沒有符合的學員'), 'archived students are hidden');
  await p.selectOption('select[aria-label=狀態]', 'archived'); await p.waitForTimeout(300);
  ok((await p.locator('tbody tr').count()) === 3, 'archived filter shows them');
  ok(errs.length === 0, 'no page errors ' + errs.join('|'));
  await b.close(); process.exit(fails ? 1 : 0);
})();
