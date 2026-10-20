// Drive a deployed (or local) explorer in headless Chrome over the DevTools protocol and check what a visitor sees.
//   node scripts/check_live_explorer.mjs <chrome-executable> <site-url> [<local site dir for the CSV reference>]
// Checks: search finds both example facilities, the Rocky Mount page lists its 183 MANUFACTURE assertions, the
// "Download CSV" button produces exactly the rows the site's own CSV module produces from the published data
// (which scripts/verify_explorer_csv.py compares with the database), and the page throws no exceptions.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const [chrome, base, siteDir = "site"] = process.argv.slice(2);
const profile = mkdtempSync(join(tmpdir(), "fineprint-cdp-"));
const port = 9300 + Math.floor(Math.random() * 500);
const proc = spawn(chrome, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`, "--disk-cache-size=1", "--window-size=1280,1000", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function connect(url) {
  const ws = new WebSocket(url);
  let id = 0;
  const pending = new Map();
  const events = [];
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else events.push(d);
  };
  return {
    events, ws, ready: new Promise((r) => { ws.onopen = r; }),
    send: (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); }),
  };
}

let page;
for (let i = 0; i < 60 && !page; i++) {
  await sleep(250);
  try { page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page"); } catch { /* starting */ }
}
const pg = connect(page.webSocketDebuggerUrl);
await pg.ready;
await pg.send("Runtime.enable");
await pg.send("Page.enable");
const run = async (expression) => (await pg.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;
const waitFor = async (expression, ms = 30000) => { for (let t = 0; t < ms; t += 250) { if (await run(expression)) return true; await sleep(250); } return false; };
const firstCells = "[...document.querySelectorAll('#main table tbody tr')].map((r) => r.cells[0].innerText.trim())";
const search = async (text) => {
  await run(`{ const i = document.querySelector('#q'); i.value = ${JSON.stringify(text)}; i.dispatchEvent(new Event('input')); } true`);
  await sleep(300);
  return run(firstCells);
};

const out = { site: base, checked_at: new Date().toISOString().slice(0, 19) + "Z" };
await pg.send("Page.navigate", { url: new URL("#/", base).href });
out.home_loaded = await waitFor("!!document.querySelector('#q')");
out.search_rocky_mount_first_hit = (await search("Rocky Mount"))[0];
out.search_fei_1925262 = await search("FEI 1925262");
await pg.send("Page.navigate", { url: new URL("#/facility/093132819", base).href });
out.rocky_mount_rows = (await waitFor("document.querySelectorAll('#main table tbody tr').length >= 183"))
  ? await run("document.querySelectorAll('#main table tbody tr').length") : 0;
out.rocky_mount_count_text = await run("document.querySelector('.count').innerText");
const csv = await run(`(async () => {
  const orig = URL.createObjectURL.bind(URL); let blob = null;
  URL.createObjectURL = (b) => { blob = b; return orig(b); };
  [...document.querySelectorAll('button')].find((b) => b.textContent.includes('CSV')).click();
  URL.createObjectURL = orig;
  return blob ? await blob.text() : null; })()`);
await pg.send("Page.navigate", { url: new URL("#/rocky-mount-2023", base).href });
out.case_study_loaded = await waitFor("document.body.innerText.includes('46.1%') && document.querySelectorAll('#main table').length >= 2");
out.page_exceptions = pg.events.filter((e) => e.method === "Runtime.exceptionThrown").map((e) => e.params.exceptionDetails.text);

// Reference: the same module over the published files, MANUFACTURE rows for Rocky Mount.
const src = readFileSync(join(resolve(siteDir), "explorer-core.js"), "utf-8");
const core = await import("data:text/javascript;charset=utf-8," + encodeURIComponent(src));
const read = (p) => JSON.parse(readFileSync(join(resolve(siteDir), "data", p), "utf-8"));
const fac = core.facilityIndex(read("current/facilities.json")).get("093132819");
const ref = core.facilityRows(read("current/examples/093132819.json"), fac).filter((r) => r.operation === "MANUFACTURE");
const refLines = core.toCSV(core.CURRENT_CSV_COLUMNS, ref.map(core.currentCsvRow)).trimEnd().split("\r\n");
const btnLines = (csv || "").trimEnd().split("\r\n");
out.csv_button_rows = btnLines.length - 1;
out.csv_button_equals_reference = !!csv && btnLines[0] === refLines[0]
  && JSON.stringify(btnLines.slice(1).sort()) === JSON.stringify(refLines.slice(1).sort());
out.ok = out.home_loaded && out.search_rocky_mount_first_hit === "093132819"
  && out.search_fei_1925262.length === 1 && out.search_fei_1925262[0] === "030606222"
  && out.rocky_mount_rows === 183 && out.csv_button_equals_reference && out.case_study_loaded
  && out.page_exceptions.length === 0;
console.log(JSON.stringify(out, null, 1));
proc.kill();
await sleep(500);
try { rmSync(profile, { recursive: true, force: true }); } catch { /* Chrome may still hold files */ }
process.exit(out.ok ? 0 : 1);
