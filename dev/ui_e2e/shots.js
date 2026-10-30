// 產生 README 用的截圖（docs/screens/home.png、exam.png）。先 ./fresh.sh，再在 /tmp/cpe-e2e 底下執行。
const { chromium } = require('playwright');
const OUT = process.env.OUT || '/home/user/code-cc/docs/screens';
const BASE = 'http://127.0.0.1:8793/';
const MAN = Array.from({ length: 7 }, (_, i) => `2023-01-10,${i + 1},${20001 + i},Problem ${i + 1},${(50 / (i + 1)).toFixed(2)}`).join('\n');
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  await ctx.addInitScript(() => localStorage.setItem('cpe.onboarded', 'true'));
  const p = await ctx.newPage();
  await p.goto(BASE); const token = await p.evaluate(() => document.querySelector('meta[name=cpe-token]').content);
  const post = (path, body) => p.evaluate(async ([path, body, token]) => (await fetch(path, { method: 'POST', headers: { 'X-CPE-Token': token, 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json(), [path, body, token]);
  await post('/api/past/import', { text: MAN });
  for (let n = 1; n <= 7; n++) await post('/api/past/statement', { id: `uva${20000 + n}`, text: `Read one integer and print it multiplied by ${n}. `.repeat(4) + `\n\nSample Input\n3\n\nSample Output\n${3 * n}\n` });
  await post('/api/new', { id: 'd001' });
  await p.goto(BASE + '#/home'); await p.waitForSelector('.plan'); await p.waitForTimeout(500);
  await p.screenshot({ path: OUT + '/home.png' });
  await post('/api/past/start', { date: '2023-01-10' });
  await post('/api/save', { id: 'uva20001', code: 'print(int(input()) * 1)\n' }); await post('/api/test', { id: 'uva20001' });
  await post('/api/save', { id: 'uva20002', code: 'print(0)\n' }); await post('/api/test', { id: 'uva20002' });
  await p.goto(BASE + '#/exam'); await p.waitForSelector('.scoreboard .sb.ac'); await p.waitForTimeout(400);
  await p.screenshot({ path: OUT + '/exam.png' });
  await b.close();
})();
