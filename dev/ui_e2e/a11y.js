const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript(() => localStorage.setItem('cpe.onboarded', 'true'));
  const p = await ctx.newPage(); let bad = 0;
  const scan = async (name) => {
    const issues = await p.evaluate(() => {
      const out = [];
      const nameOf = (el) => (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || '').trim() || (el.querySelector('svg use') && '') ;
      document.querySelectorAll('button,a[href],[role=button]').forEach((el) => { if (!el.offsetParent && getComputedStyle(el).position !== 'fixed') return; if (!(el.getAttribute('aria-label') || el.textContent.trim() || el.getAttribute('title'))) out.push('無名稱按鈕: ' + el.outerHTML.slice(0, 80)); });
      document.querySelectorAll('input,select,textarea').forEach((el) => { if (el.type === 'hidden') return; const l = el.getAttribute('aria-label') || el.closest('label') || (el.id && document.querySelector(`label[for="${el.id}"]`)); if (!l) out.push('無標籤欄位: ' + el.outerHTML.slice(0, 80)); });
      document.querySelectorAll('svg.ic').forEach((s) => { if (s.getAttribute('aria-hidden') !== 'true') out.push('svg 沒有 aria-hidden'); });
      if (!document.querySelector('main#view')) out.push('缺少 main 地標');
      if (document.querySelectorAll('h1').length !== 1) out.push('h1 數量 = ' + document.querySelectorAll('h1').length);
      document.querySelectorAll('img').forEach((i) => { if (!i.alt) out.push('img 缺 alt'); });
      return out;
    });
    console.log((issues.length ? 'FAIL ' : 'PASS ') + name + (issues.length ? '\n  ' + [...new Set(issues)].slice(0, 6).join('\n  ') : '')); bad += issues.length;
  };
  for (const [n, h] of [['首頁', '#/home'], ['練習', '#/practice/d001'], ['課程', '#/course'], ['考試', '#/exam'], ['工程任務', '#/course/eng'], ['統計', '#/stats'], ['學習：洞察', '#/study/insights'], ['學習：工坊', '#/study/lab'], ['學習：筆記', '#/study/notes'], ['學習：目標', '#/study/goal'], ['設定', '#/settings']]) {
    await p.goto('http://127.0.0.1:8793/' + h); await p.waitForTimeout(900); await scan(n);
  }
  // 鍵盤：Tab 的第一個焦點應是「跳到主要內容」
  await p.goto('http://127.0.0.1:8793/#/home'); await p.waitForTimeout(700); await p.keyboard.press('Tab');
  const first = await p.evaluate(() => document.activeElement.textContent); console.log((first.includes('跳到主要內容') ? 'PASS' : 'FAIL') + ' 第一個 Tab 焦點：' + first);
  await p.keyboard.press('Enter'); const f2 = await p.evaluate(() => document.activeElement.id); console.log((f2 === 'view' ? 'PASS' : 'FAIL') + ' 跳到主要內容後焦點在 #view（' + f2 + '）');
  // 焦點可見
  await p.keyboard.press('Tab'); const ring = await p.evaluate(() => { const e = document.activeElement; return getComputedStyle(e).boxShadow; }); console.log((ring && ring !== 'none' ? 'PASS' : 'WARN') + ' 焦點框：' + ring.slice(0, 40));
  // 指令面板 Esc 後焦點回到觸發處
  await p.focus('.searchbtn'); await p.keyboard.press('Enter'); await p.waitForSelector('.palette'); await p.keyboard.press('Escape'); await p.waitForTimeout(150);
  const back = await p.evaluate(() => document.activeElement.className); console.log((back.includes('searchbtn') ? 'PASS' : 'FAIL') + ' 關閉面板後焦點回到按鈕（' + back + '）');
  await b.close(); process.exit(bad ? 1 : 0);
})();
