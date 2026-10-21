// Drive a deployed (or local) explorer in headless Chrome over the DevTools protocol and check what a visitor sees.
//   node scripts/check_live_explorer.mjs <chrome-executable> <site-url> [<local site dir for the CSV reference>]
// Checks, at desktop and phone widths: national search, facility navigation, real assertion rows and filters, the
// evidence drawer (keyboard focus, trap, Escape, source links), both CSV buttons against the rows the site's own CSV
// module produces from the published data (scripts/verify_explorer_csv.py compares those with the database), the
// historical page, reduced motion, horizontal overflow, page exceptions and that every request stays on the site.
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const [chrome, base, siteDir = "site"] = process.argv.slice(2);
const origin = new URL(base).origin;
const profile = mkdtempSync(join(tmpdir(), "fineprint-cdp-"));
const port = 9300 + Math.floor(Math.random() * 500);
const proc = spawn(chrome, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`, "--disk-cache-size=1", "--window-size=1280,1000", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let page;
for (let i = 0; i < 60 && !page; i++) {
  await sleep(250);
  try { page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page"); } catch { /* starting */ }
}
const ws = new WebSocket(page.webSocketDebuggerUrl);
let msgId = 0;
const pending = new Map();
const events = [];
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else events.push(d);
};
await new Promise((r) => { ws.onopen = r; });
const send = (method, params = {}) => new Promise((r) => { const i = ++msgId; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const run = async (expression) => (await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;
const waitFor = async (expression, ms = 30000) => { for (let t = 0; t < ms; t += 150) { if (await run(expression)) return true; await sleep(150); } return false; };
const key = async (k, shift = false) => {
  const codes = { Tab: 9, Enter: 13, Escape: 27 };
  const base = { key: k, code: k, windowsVirtualKeyCode: codes[k], nativeVirtualKeyCode: codes[k], modifiers: shift ? 8 : 0 };
  await send("Input.dispatchKeyEvent", { type: "keyDown", ...base, ...(k === "Enter" ? { text: "\r" } : {}) });
  await send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
  await sleep(60);
};
const viewport = (width, height = 900) => send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
const go = async (hash, ready) => {
  await send("Page.navigate", { url: "about:blank" });
  await send("Page.navigate", { url: new URL(hash, base).href });
  return waitFor(ready);
};
const overflow = () => run("document.documentElement.scrollWidth - document.documentElement.clientWidth");
const type = async (text) => {
  await run(`{ const i = document.querySelector('#q'); i.focus(); i.value = ''; i.dispatchEvent(new Event('input')); } true`);
  await send("Input.insertText", { text });
  await sleep(250);
};
const captureCsv = (clickExpr) => run(`(async () => {
  const orig = URL.createObjectURL.bind(URL); let blob = null;
  URL.createObjectURL = (b) => { blob = b; return orig(b); };
  ${clickExpr}.click();
  URL.createObjectURL = orig;
  return blob ? await blob.text() : null; })()`);
const exportBtn = "[...document.querySelectorAll('#main button')].find((b) => b.textContent.startsWith('Export CSV'))";
const seg = (label) => `[...document.querySelectorAll('.seg button')].find((b) => b.textContent === ${JSON.stringify(label)}).click()`;
const rowsShown = "document.querySelectorAll('#main .data tbody tr, #main .cards > li').length";

// Reference rows: the site's own CSV module over the local copy of the published files.
const src = readFileSync(join(resolve(siteDir), "explorer-core.js"), "utf-8");
const core = await import("data:text/javascript;charset=utf-8," + encodeURIComponent(src));
const read = (p) => JSON.parse(readFileSync(join(resolve(siteDir), "data", p), "utf-8"));
const idxFile = read("current/facilities.json");
const index = core.facilityIndex(idxFile);
const RM = "093132819";
const rank = { DIRECT: 0, TENTATIVE: 1, UNKNOWN: 2 };
const rmAll = core.facilityRows(read(`current/examples/${RM}.json`), index.get(RM)).sort((x, y) => rank[x.confidence] - rank[y.confidence]
  || (x.product_ndc_5_4 || "~").localeCompare(y.product_ndc_5_4 || "~") || x.set_id.localeCompare(y.set_id) || x.evidence_id - y.evidence_id);
const rmMfg = rmAll.filter((r) => r.operation === "MANUFACTURE");
const csvOf = (rows) => core.toCSV(core.CURRENT_CSV_COLUMNS, rows.map(core.currentCsvRow));
const sameCsv = (got, want) => {
  if (!got) return false;
  const a = got.trimEnd().split("\r\n"), b = want.trimEnd().split("\r\n");
  return a[0] === b[0] && JSON.stringify(a.slice(1).sort()) === JSON.stringify(b.slice(1).sort());
};
const hist = read("historical/rocky_mount_2023.json");
const histCsv = core.toCSV(core.HISTORICAL_CSV_COLUMNS, core.historicalRows(hist));
const noMfg = [...index.values()].find((f) => !f.example && f.mfg_direct + f.mfg_tentative + f.mfg_unknown === 0);

await send("Runtime.enable");
await send("Page.enable");
await send("Network.enable");
const out = { site: base, checked_at: new Date().toISOString().slice(0, 19) + "Z", desktop: {}, phone: {}, keyboard: {}, history: {} };
const d = out.desktop, p = out.phone, k = out.keyboard;
await viewport(1280);

// Home and national search
d.home_loaded = await go("#/", "!!document.querySelector('#q') && !!document.querySelector('.stat-n')");
d.home_stats = await run("[...document.querySelectorAll('.stat-n')].map((e) => e.textContent)");
d.search_rocky_mount_first = (await type("Rocky Mount"), await run("document.querySelector('.results a.row-link')?.getAttribute('href')"));
d.search_rocky_mount_count = await run("document.querySelector('.results .count')?.textContent");
d.search_placeholder_query_first = (await type("Rocky Mount, NC"), await run("document.querySelector('.results a.row-link')?.getAttribute('href')"));
await type("FEI 1925262");
await key("Enter");
d.search_fei_enter_navigates_to = (await waitFor("location.hash === '#/facility/030606222' && !!document.querySelector('.fac-head h1')")) ? await run("location.hash") : await run("location.hash");
d.mcpherson_heading = await run("document.querySelector('.fac-head h1')?.textContent");
await go("#/", "!!document.querySelector('#q')");
await type("zzqx no such site");
await run("document.querySelector('form[role=search]').requestSubmit()");
await sleep(200);
d.search_empty_state = await run("document.querySelector('.results .status-note')?.textContent || null");

// Facility page: real rows, filters, CSV
d.facility_loaded = await go(`#/facility/${RM}`, `${rowsShown} >= 183`);
d.facility_heading = await run("document.querySelector('.fac-head h1').textContent");
d.facility_rows = await run(rowsShown);
d.facility_count_text = await run("document.querySelector('.count-line').textContent");
d.csv_all_equals_reference = sameCsv(await captureCsv(exportBtn), csvOf(rmMfg));
await run(seg("Unknown"));
await sleep(150);
d.filter_unknown_rows = await run(rowsShown);
d.csv_unknown_equals_reference = sameCsv(await captureCsv(exportBtn), csvOf(rmMfg.filter((r) => r.confidence === "UNKNOWN")));
await run(seg("Tentative"));
await sleep(150);
d.filter_tentative_empty_state = await run("document.querySelector('.empty')?.textContent || null");
await run(seg("All"));
await run("{ const s = document.querySelector('#op'); s.value = 'all'; s.dispatchEvent(new Event('change')); } true");
await sleep(300);
d.all_operations_rows_first_page = await run(rowsShown);
d.all_operations_count_text = await run("document.querySelector('.count-line').textContent");
await run("[...document.querySelectorAll('.more button')].forEach((b) => b.click()); true");
await sleep(300);
d.all_operations_rows_after_show_all = await run(rowsShown);
d.csv_all_operations_equals_reference = sameCsv(await captureCsv(exportBtn), csvOf(rmAll));
d.first_row_label_link = await run("document.querySelector('.data tbody tr td.ver a')?.href");
d.first_row_label_link_expected = core.links.label(rmAll[0].set_id);
d.nav_current = await run("[...document.querySelectorAll('[data-nav][aria-current]')].map((a) => a.dataset.nav + ':' + a.getAttribute('aria-current'))");

// Evidence drawer by keyboard
await go(`#/facility/${RM}`, `${rowsShown} >= 183`);
await run("document.querySelector('.data tbody tr .btn.ev').focus(); true");
await key("Enter");
k.drawer_opened_by_enter = await waitFor("!!document.querySelector('[role=dialog][aria-modal=true]')", 3000);
k.focus_on_close_button = await run("document.activeElement?.textContent === 'Close · Esc'");
k.drawer_title = await run("document.getElementById('ev-title')?.textContent");
k.drawer_shows_first_row_set_id = await run(`document.querySelector('[role=dialog]').textContent.includes(${JSON.stringify(rmMfg[0].set_id)})`);
k.drawer_shows_first_row_sha256 = await run(`document.querySelector('[role=dialog]').textContent.includes(${JSON.stringify(rmMfg[0].xml_sha256)})`);
k.drawer_shows_first_row_xml_location = await run(`document.querySelector('[role=dialog]').textContent.includes(${JSON.stringify(rmMfg[0].xml_location)})`);
k.drawer_links = await run("[...document.querySelectorAll('[role=dialog] a[href]')].map((a) => a.href)");
k.drawer_links_expected = [core.links.label(rmMfg[0].set_id), core.links.versionZip(rmMfg[0].set_id, rmMfg[0].version),
  core.links.fdaXml(rmMfg[0].document_id), core.links.history(rmMfg[0].set_id)];
k.background_inert = await run("document.getElementById('main').inert === true");
const focusables = await run("document.querySelectorAll('[role=dialog] a[href], [role=dialog] button').length");
let escaped = false;
for (let i = 0; i < focusables + 2; i++) { await key("Tab"); if (!(await run("!!document.activeElement.closest('[role=dialog]')"))) escaped = true; }
await key("Tab", true);
await key("Tab", true);
if (!(await run("!!document.activeElement.closest('[role=dialog]')"))) escaped = true;
k.focus_trapped_in_drawer = !escaped;
await key("Escape");
k.escape_closes_drawer = await run("!document.querySelector('[role=dialog]')");
k.focus_returned_to_trigger = await run("document.activeElement?.classList.contains('ev') && document.activeElement === document.querySelector('.data tbody tr .btn.ev')");
k.background_restored = await run("document.getElementById('main').inert === false && !document.body.classList.contains('lock')");
await run("document.querySelector('.data tbody tr .btn.ev').click(); true");
await sleep(150);
await run("document.querySelector('.dlg-overlay').click(); true");
k.overlay_click_closes = await run("!document.querySelector('[role=dialog]')");

// Skip link and page states
await go("#/", "!!document.querySelector('#q')");
await run("document.activeElement.blur(); true");
await key("Tab");
k.first_tab_is_skip_link = await run("document.activeElement?.classList.contains('skip')");
await key("Enter");
k.skip_link_moves_focus_to_h1 = await run("document.activeElement?.tagName === 'H1' && location.hash === '#/'");
d.unknown_duns_page = (await go("#/facility/000000000", "!!document.querySelector('.status-note')"), await run("document.querySelector('.status-note p').textContent"));
d.no_manufacture_page = (await go(`#/facility/${noMfg.duns}`, "!!document.querySelector('.fac-head h1')"),
await run("document.querySelector('.toolbar .status-note p')?.textContent || null"));
d.about_release_parts = (await go("#/about", "!!document.querySelector('.files')"), await run("document.querySelectorAll('.files tbody tr').length"));

// Historical page
out.history.loaded = await go("#/rocky-mount-2023", `!!document.querySelector('.case-title') && ${rowsShown} > 100`);
out.history.title = await run("document.querySelector('.case-title').textContent");
out.history.figures = await run("[...document.querySelectorAll('.figs .n')].map((e) => e.textContent)");
out.history.bar_widths = await run("[...document.querySelectorAll('.hbar i')].map((e) => e.style.width)");
out.history.recall_cells = await run("[...document.querySelectorAll('.cells')].map((c) => c.querySelectorAll('.hit').length + '/' + c.children.length)");
out.history.supplementary_rows = await run("[...document.querySelectorAll('.supp tbody tr')].map((r) => [...r.children].map((c) => c.textContent).join(' | '))");
await run("[...document.querySelectorAll('.more button')].forEach((b) => b.click()); true");
await sleep(400);
out.history.cohort_rows = await run(rowsShown);
out.history.csv_equals_reference = sameCsv(await captureCsv(exportBtn), histCsv);
out.history.csv_rows = histCsv.trimEnd().split("\r\n").length - 1;
out.history.strip = await run("document.querySelector('.strip.hist').textContent");

// Phone widths
await viewport(390, 844);
p.facility_cards_first_page_390 = (await go(`#/facility/${RM}`, "document.querySelectorAll('#main .cards > li').length >= 60"), await run("document.querySelectorAll('#main .cards > li').length"));
await run("[...document.querySelectorAll('.more button')].forEach((b) => b.click()); true");
await sleep(300);
p.facility_cards_390 = await run("document.querySelectorAll('#main .cards > li').length");
p.facility_has_no_table_390 = await run("!document.querySelector('#main .data')");
p.csv_390_equals_reference = sameCsv(await captureCsv(exportBtn), csvOf(rmMfg));
p.facility_overflow_390 = await overflow();
await run("document.querySelector('.cards .btn.ev').click(); true");
await sleep(300);
p.drawer_width_390 = await run("Math.round(document.querySelector('.dlg-panel').getBoundingClientRect().width)");
await key("Escape");
for (const w of [390, 320]) {
  await viewport(w, 800);
  p[`home_overflow_${w}`] = (await go("#/", "!!document.querySelector('.stat-n')"), await overflow());
  p[`facility_overflow_${w}`] = (await go(`#/facility/${RM}`, "document.querySelectorAll('#main .cards > li').length >= 60"), await overflow());
  p[`history_overflow_${w}`] = (await go("#/rocky-mount-2023", "!!document.querySelector('.case-title')"), await overflow());
  p[`about_overflow_${w}`] = (await go("#/about", "!!document.querySelector('.files')"), await overflow());
}

// Reduced motion
await viewport(1280);
await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await go(`#/facility/${RM}`, `${rowsShown} >= 183`);
await run("document.querySelector('.data tbody tr .btn.ev').click(); true");
await sleep(100);
out.reduced_motion_drawer_animation_s = await run("parseFloat(getComputedStyle(document.querySelector('.dlg-panel')).animationDuration)");
await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
out.normal_motion_drawer_animation_s = (await go(`#/facility/${RM}`, `${rowsShown} >= 183`),
await run("document.querySelector('.data tbody tr .btn.ev').click(); parseFloat(getComputedStyle(document.querySelector('.dlg-panel')).animationDuration)"));

const requests = events.filter((e) => e.method === "Network.requestWillBeSent").map((e) => e.params.request.url)
  .filter((u) => /^https?:/.test(u));
out.requests = requests.length;
out.third_party_requests = [...new Set(requests.filter((u) => new URL(u).origin !== origin))];
out.page_exceptions = events.filter((e) => e.method === "Runtime.exceptionThrown").map((e) => e.params.exceptionDetails.exception?.description || e.params.exceptionDetails.text);
out.console_errors = events.filter((e) => e.method === "Runtime.consoleAPICalled" && e.params.type === "error").map((e) => e.params.args.map((a) => a.value ?? a.description).join(" "));

const checks = {
  home: d.home_loaded && d.home_stats.join() === "55,064,4,314",
  search: d.search_rocky_mount_first === `#/facility/${RM}` && d.search_placeholder_query_first === `#/facility/${RM}`
    && d.search_fei_enter_navigates_to === "#/facility/030606222" && /^No establishment matches/.test(d.search_empty_state || ""),
  facility: d.facility_rows === 183 && d.facility_heading === "Rocky Mount, NC — Hospira, Inc." && d.filter_unknown_rows === 3
    && /measured result/.test(d.filter_tentative_empty_state || "") && d.all_operations_rows_after_show_all === rmAll.length
    && d.first_row_label_link === d.first_row_label_link_expected,
  csv: d.csv_all_equals_reference && d.csv_unknown_equals_reference && d.csv_all_operations_equals_reference && out.history.csv_equals_reference,
  drawer: k.drawer_opened_by_enter && k.focus_on_close_button && k.drawer_shows_first_row_set_id && k.drawer_shows_first_row_sha256
    && k.drawer_shows_first_row_xml_location && JSON.stringify(k.drawer_links) === JSON.stringify(k.drawer_links_expected)
    && k.background_inert && k.focus_trapped_in_drawer && k.escape_closes_drawer && k.focus_returned_to_trigger && k.background_restored
    && k.overlay_click_closes,
  keyboard: k.first_tab_is_skip_link && k.skip_link_moves_focus_to_h1,
  states: /names this DUNS/.test(d.unknown_duns_page || "") && /No MANUFACTURE assertion/.test(d.no_manufacture_page || "") && d.about_release_parts === 6,
  history: out.history.loaded && out.history.title.includes("46.1% shorter") && out.history.figures.join() === "480,−46.1%,63/65"
    && out.history.recall_cells.join() === "63/65,63/65" && out.history.cohort_rows === out.history.csv_rows,
  phone: p.facility_cards_first_page_390 === 60 && p.facility_cards_390 === 183 && p.facility_has_no_table_390
    && p.csv_390_equals_reference && p.drawer_width_390 === 390
    && [390, 320].every((w) => ["home", "facility", "history", "about"].every((v) => p[`${v}_overflow_${w}`] === 0)),
  reduced_motion: out.reduced_motion_drawer_animation_s < 0.001 && out.normal_motion_drawer_animation_s > 0.1,
  no_third_party_requests: out.third_party_requests.length === 0,
  no_page_errors: out.page_exceptions.length === 0 && out.console_errors.length === 0,
};
out.checks = checks;
out.ok = Object.values(checks).every(Boolean);
console.log(JSON.stringify(out, null, 1));
proc.kill();
await sleep(500);
try { rmSync(profile, { recursive: true, force: true }); } catch { /* Chrome may still hold files */ }
process.exit(out.ok ? 0 : 1);
