// Produce the explorer's CSV downloads outside the browser, with the same code the site runs.
//   node scripts/explorer_csv.mjs <site-dir>            -> JSON {"current": {duns: csv}, "historical": csv}
// Current CSVs: MANUFACTURE rows for every establishment DUNS; all operations for the example facilities.
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const site = resolve(process.argv[2] || "site");
// A data: URL is always loaded as an ES module, whatever the Node version's .js detection rules.
const src = readFileSync(join(site, "explorer-core.js"), "utf-8");
const core = await import("data:text/javascript;charset=utf-8," + encodeURIComponent(src));
const read = (p) => JSON.parse(readFileSync(join(site, "data", p), "utf-8"));

const index = read("current/facilities.json");
const facilities = core.facilityIndex(index);
const shards = new Map();
const out = { current: {}, historical: null };
for (const f of facilities.values()) {
  let bundle;
  if (f.example) bundle = read(`current/examples/${f.duns}.json`);
  else {
    const s = core.shardOf(f.duns);
    if (!shards.has(s)) {
      try { shards.set(s, read(`current/manufacture/${s}.json`)); } catch { shards.set(s, null); }
    }
    bundle = shards.get(s);
  }
  const rows = bundle ? core.facilityRows(bundle, f) : [];
  out.current[f.duns] = core.toCSV(core.CURRENT_CSV_COLUMNS, rows.map(core.currentCsvRow));
}
out.historical = core.toCSV(core.HISTORICAL_CSV_COLUMNS, core.historicalRows(read("historical/rocky_mount_2023.json")));
process.stdout.write(JSON.stringify(out));
