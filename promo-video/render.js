// 逐格算圖：node render.js <輸出資料夾> [fps] [只輸出這些秒數的預覽, 逗號分隔]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const out = process.argv[2];
  const fps = +(process.argv[3] || 30);
  const preview = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.fonts.ready);
  const times = preview || Array.from({ length: 30 * fps }, (_, i) => i / fps);
  for (let i = 0; i < times.length; i++) {
    await page.evaluate(t => window.render(t), times[i]);
    const name = preview ? `p_${times[i]}.jpg` : `f_${String(i).padStart(4, '0')}.jpg`;
    await page.screenshot({ path: path.join(out, name), type: 'jpeg', quality: preview ? 70 : 95 });
  }
  await browser.close();
})();
