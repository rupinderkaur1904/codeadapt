const { chromium } = require("playwright"); const fs = require("fs"); const path=require("path");
(async () => {
  const dir = process.argv[2], out = process.argv[3]; fs.mkdirSync(out, { recursive: true });
  const br = await chromium.launch(); const p = await (await br.newContext({ deviceScaleFactor: 2, viewport: { width: 1800, height: 1400 } })).newPage();
  p.on("pageerror", e => console.log("ERR", e.message)); p.on("console", m => console.log("console", m.text()));
  await p.goto("file://" + path.resolve("render.html"));
  for (let i = 0; i < 10; i++) {
    const xml = fs.readFileSync(`${dir}/${i}.xml`, "utf8");
    const [w, h] = await p.evaluate(x => renderPage(x), xml);
    await p.setViewportSize({ width: Math.max(w, 400), height: Math.max(h, 300) });
    await p.waitForTimeout(200);
    await p.locator("#g").screenshot({ path: `${out}/${i}.png` });
    console.log(i, w, h);
  }
  await br.close();
})();
