// Capture explorer pages at fixed viewport widths in headless Chrome over the DevTools protocol.
//   node scripts/screenshot_explorer.mjs <chrome-executable> <out-dir> <spec.json>
// spec.json: [{ "name": "home", "url": "http://.../#/", "widths": [1440, 768, 390, 320],
//               "ready": "<JS expression, truthy when the page is ready>",
//               "action": "<optional JS run before capture>", "viewportOnly": false,
//               "reducedMotion": false, "maxHeight": 6000, "format": "png" | "jpeg",
//               "report": "<optional JS whose value is printed with the capture>",
//               "fromSelector": "<optional CSS selector: start the capture just above this element>" }]
// Widths are set with device-metrics emulation, so narrow phones work even where the OS enforces a
// minimum window width. Writes <out-dir>/<name>-<width>.png and prints what it captured as JSON.
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [chrome, outDir, specPath] = process.argv.slice(2);
const spec = JSON.parse(readFileSync(specPath, "utf-8"));
mkdirSync(outDir, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "fineprint-shots-"));
const port = 9300 + Math.floor(Math.random() * 500);
const proc = spawn(chrome, ["--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "--disk-cache-size=1", "about:blank"],
{ stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let page;
for (let i = 0; i < 60 && !page; i++) {
  await sleep(250);
  try { page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page"); } catch { /* starting */ }
}
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
const exceptions = [];
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  else if (d.method === "Runtime.exceptionThrown") exceptions.push(d.params.exceptionDetails.text);
};
await new Promise((r) => { ws.onopen = r; });
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const run = async (expression) => (await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;
const waitFor = async (expression, ms = 30000) => { for (let t = 0; t < ms; t += 200) { if (await run(expression)) return true; await sleep(200); } return false; };
await send("Runtime.enable");
await send("Page.enable");

const done = [];
for (const s of spec) {
  for (const width of s.widths) {
    const height = s.height || 900;
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
    await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: s.reducedMotion ? "reduce" : "no-preference" }] });
    await send("Page.navigate", { url: "about:blank" });
    await sleep(100);
    await send("Page.navigate", { url: s.url });
    const ready = await waitFor(s.ready || "document.readyState === 'complete'");
    await run("document.fonts ? document.fonts.ready.then(() => true) : true");
    if (s.action) { await run(s.action); await sleep(s.settle ?? 600); }
    await sleep(300);
    const m = await send("Page.getLayoutMetrics");
    const full = Math.ceil(m.result.cssContentSize?.height || m.result.contentSize.height);
    // Long tables make pages tens of thousands of pixels tall; cap the capture (Chrome stalls on huge surfaces).
    const y = s.fromSelector ? Math.max(0, Math.floor(await run(`document.querySelector(${JSON.stringify(s.fromSelector)}).getBoundingClientRect().top + window.scrollY - 24`))) : 0;
    const tall = Math.min(full - y, s.maxHeight || 6000);
    const clip = s.viewportOnly ? { x: 0, y: 0, width, height, scale: 1 } : { x: 0, y, width, height: tall, scale: 1 };
    const fmtOut = s.format || "png";
    const shot = await send("Page.captureScreenshot", { format: fmtOut, ...(fmtOut === "jpeg" ? { quality: s.quality || 82 } : {}),
      captureBeyondViewport: !s.viewportOnly, clip });
    const file = join(outDir, `${s.name}-${width}.${fmtOut === "jpeg" ? "jpg" : "png"}`);
    writeFileSync(file, Buffer.from(shot.result.data, "base64"));
    const overflow = await run("document.documentElement.scrollWidth - document.documentElement.clientWidth");
    done.push({ name: s.name, width, file, ready, page_height: full, captured_height: s.viewportOnly ? height : tall,
      horizontal_overflow_px: overflow, ...(s.report ? { report: await run(s.report) } : {}) });
  }
}
await send("Emulation.clearDeviceMetricsOverride");
console.log(JSON.stringify({ captured: done, page_exceptions: exceptions }, null, 1));
proc.kill();
await sleep(500);
try { rmSync(profile, { recursive: true, force: true }); } catch { /* Chrome may still hold files */ }
