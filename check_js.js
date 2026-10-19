const fs = require('fs');
const html = fs.readFileSync('C:\\Users\\MR.SHI\\WorkBuddy\\2026-09-18-21-33-18\\token-dashboard.html', 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
console.log('script blocks:', scripts.length);
scripts.forEach((s, i) => {
  try { new Function(s); console.log('block', i, 'OK len', s.length); }
  catch (e) {
    console.log('block', i, 'SYNTAX ERROR:', e.message);
    const m = e.stack.match(/<anonymous>:(\d+)/);
    if (m) {
      const lines = s.split('\n');
      const n = +m[1];
      console.log('near line', n, ':', (lines[n - 1] || '').slice(0, 200));
    }
  }
});
