// Facility Evidence Explorer: a static view of exported fineprint graph records. All text from source
// records is inserted with textContent (never parsed as HTML). CSV rows come from explorer-core.js, the
// same module scripts/verify_explorer_csv.py checks against the database.
import {
  CONFIDENCE, CURRENT_CSV_COLUMNS, HISTORICAL_CSV_COLUMNS, REASONS, STATUS, currentCsvRow, facilityIndex,
  facilityRows, historicalRows, links, matches, shardOf, toCSV,
} from "./explorer-core.js";

const REPO = "https://github.com/s2002kumar/fineprint";
const ROCKY_MOUNT = "093132819";
const EXAMPLES = [ROCKY_MOUNT, "030606222"];
const PROMPTS = ["Rocky Mount", "093132819", "FEI 1021343", "McPherson"];
const main = document.getElementById("main");
const wide = window.matchMedia("(min-width: 640px)");
const pageSize = () => (wide.matches ? 500 : 60); // rows rendered before "Show all"; CSV exports always hold every row
const cache = new Map();
let cleanups = [];
let closeDrawer = null;
let firstRoute = true;
let lastQuery = "";

const CONF_LABEL = { DIRECT: "Direct", TENTATIVE: "Tentative", UNKNOWN: "Unknown" };
const STATUS_SHORT = {
  CURRENT_REGISTERED: "Currently registered", CURRENT_REGISTERED_NO_FEI: "Registered without an FEI",
  CURRENT_EXCLUDED: "Excluded registration", STALE_REGISTERED: "Older registration file only",
  AMBIGUOUS_MULTIPLE_FEI: "More than one FEI", NOT_FOUND: "No FDA registration found",
};
const CLASSES = {
  DIRECT: "The pre-cutoff label lists MANUFACTURE at Rocky Mount for this product. Flagged.",
  OTHER_SITE: "MANUFACTURE is listed only at other sites.",
  RM_SECONDARY_ONLY: "Rocky Mount appears only for packing, labeling or testing.",
  UNKNOWN_NO_ESTABLISHMENT: "The label has no establishment section.",
  UNKNOWN_NO_MANUFACTURE_OP: "The label lists establishments but no MANUFACTURE operation for this product.",
  NOT_IN_COHORT: "On Pfizer's list, but no admissible pre-cutoff label was found.",
};

function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat(Infinity)) {
    if (k == null || k === false) continue;
    el.append(k instanceof Node ? k : document.createTextNode(String(k)));
  }
  return el;
}
const ext = (href, text, cls = "link") => h("a", { href, class: cls, rel: "noopener", target: "_blank" }, text,
  h("span", { class: "sr-only" }, " (opens in new tab)"), h("span", { "aria-hidden": "true" }, " ↗"));
const arrow = (ch = "→") => h("span", { class: "arrow", "aria-hidden": "true" }, ch);
const fmt = (n) => Number(n).toLocaleString("en-US");
const plural = (n, word) => `${fmt(n)} ${word}${n === 1 ? "" : "s"}`;
const dot = (c) => h("span", { class: `dot ${c.toLowerCase()}`, "aria-hidden": "true" });
const show = (...nodes) => main.replaceChildren(...nodes.flat(Infinity).filter((x) => x != null && x !== false));
const mfgTotal = (f) => f.mfg_direct + f.mfg_tentative + f.mfg_unknown;

async function load(path) {
  if (!cache.has(path)) {
    cache.set(path, fetch(`data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
      return r.json();
    }).catch((err) => { cache.delete(path); throw err; }));
  }
  return cache.get(path);
}

function download(name, text) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  const link = h("a", { href: url, download: name });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function setTitle(t) {
  document.title = t ? `${t} · fineprint explorer` : "fineprint · Facility Evidence Explorer";
}

// FDA registration addresses end "City, State (XX) zip, United States (USA)" for US sites, which gives a reliable
// "City, ST". Elsewhere the fields before the country vary too much to pick out a city, so only the country is used.
function placeOf(addr) {
  const parts = (addr || "").split(/,\s*/).map((s) => s.trim()).filter(Boolean);
  const cm = parts.length >= 2 ? /^(.*?)\s*\(([A-Z]{3})\)$/.exec(parts[parts.length - 1]) : null;
  if (!cm) return null;
  let n = parts.length - 1;
  let country = cm[1];
  if (/^(South|North)$/.test(country)) { n -= 1; country = `${parts[n]}, ${country}`; } // "Korea, South (KOR)"
  const rm = n >= 2 ? /^(.*?)\s*\(([A-Z]{2})\)/.exec(parts[n - 1]) : null;
  if (cm[2] === "USA" && rm) return { city: parts[n - 2], region: rm[1], short: `${parts[n - 2]}, ${rm[2]}` };
  return { city: null, region: country, short: country };
}

function currentStrip(m) {
  const c = m.datasets.current;
  return h("div", { class: "strip", role: "note", "aria-label": "Dataset" }, h("div", { class: "wrap" },
    h("span", { class: "lead" }, h("span", { "aria-hidden": "true" }, "● "), "Current snapshot"),
    h("span", {}, `DailyMed ${c.dailymed_release}`),
    h("span", {}, `FDA registration ${c.fda_registration_as_of}`),
    h("span", { class: "sr-only" }, "A dated snapshot: it does not reflect the most current/accurate data available "
      + "from NLM, and it is not the 2023 historical replay."),
    h("a", { class: "link", href: "#/rocky-mount-2023" }, "2023 case study (separate) →")));
}

function historicalStrip(m) {
  return h("div", { class: "strip hist", role: "note", "aria-label": "Dataset" }, h("div", { class: "wrap" },
    h("span", { class: "lead" }, h("span", { "aria-hidden": "true" }, "◆ "), `Historical · data as of ${m.datasets.historical.cutoff}`),
    h("span", { class: "muted" }, "Archived labels, not the current snapshot"),
    h("a", { class: "link", href: `#/facility/${ROCKY_MOUNT}` }, "Current Rocky Mount view →")));
}

// ------------------------------------------------------------------------------------------------ home
function searchIndex(fac) {
  const hay = new Map();
  for (const f of fac.values()) hay.set(f.duns, [f.firm_name, f.address, ...f.spl_names].filter(Boolean).join(" | ").toLowerCase());
  return (raw) => {
    const tokens = raw.toLowerCase().split(/[\s,;]+/).filter((t) => t && t !== "fei" && t !== "duns")
      .map((t) => t.replace(/^(fei|duns)[:#]/, "")).filter(Boolean);
    if (tokens.join("").length < 3) return null;
    const hits = [];
    for (const f of fac.values()) {
      if (tokens.every((t) => f.duns.includes(t) || f.fei === t || hay.get(f.duns).includes(t))) hits.push(f);
    }
    return hits.sort((x, y) => mfgTotal(y) - mfgTotal(x) || x.duns.localeCompare(y.duns));
  };
}

function resultRow(f) {
  const p = placeOf(f.address);
  const sub = [p ? p.short : null, STATUS_SHORT[f.status] || f.status, f.fei ? `FEI ${f.fei}` : null].filter(Boolean).join(" · ");
  return h("li", {}, h("a", { class: "row-link", href: `#/facility/${f.duns}` },
    h("div", { class: "row-main" },
      h("p", { class: "row-title" }, f.firm_name || f.spl_names.join("; ") || `DUNS ${f.duns}`),
      h("p", { class: "row-sub" }, sub, h("span", { class: "sm-only" }, ` · DUNS ${f.duns} · ${fmt(mfgTotal(f))} MANUFACTURE`))),
    h("span", { class: "row-meta" }, h("span", {}, `DUNS ${f.duns}`), h("span", {}, `${fmt(mfgTotal(f))} MANUFACTURE`)),
    arrow()));
}

function evidencePath() {
  const steps = [
    ["SPL label version", "A versioned DailyMed label document for one product."],
    ["MANUFACTURE assertion", "The label’s establishment section names an operation."],
    ["DUNS", "The establishment identifier stated in the label."],
    ["FEI", "FDA registration record asserting that DUNS maps to this FEI."],
    ["Physical establishment", "The registered address. Registration does not confirm active production at any date."],
  ];
  return h("figure", { class: "path", "aria-labelledby": "ep-cap" },
    h("figcaption", { id: "ep-cap", class: "eyebrow" }, "How a link is documented"),
    h("ol", {}, steps.map(([k, d], i) => h("li", {},
      i < steps.length - 1 ? h("span", { class: "stem", "aria-hidden": "true" }) : null,
      h("span", { class: "node", "aria-hidden": "true" }),
      h("p", { class: "k" }, h("span", {}, String(i + 1).padStart(2, "0")), "  ", k),
      h("p", { class: "d" }, d)))),
    h("p", { class: "foot" }, "Each step is a source record. A missing step lowers confidence to ", h("i", {}, "tentative"),
      " or ", h("i", {}, "unknown"), "."));
}

async function home() {
  const [m, idx, historical] = await Promise.all([
    load("manifest.json"), load("current/facilities.json"), load("historical/rocky_mount_2023.json"),
  ]);
  const fac = facilityIndex(idx);
  const find = searchIndex(fac);
  const c = m.datasets.current;
  const baseline = historical.metrics.E.B1_all_hospira_00409;
  const shortlist = historical.metrics.E.graph_rocky_mount_direct;
  const reduction = (100 * (1 - shortlist.N / baseline.N)).toFixed(1);
  const warnings = historical.outcome.distinct_package_ndc_11;
  setTitle("");
  const results = h("div", { class: "results" });
  const live = h("p", { class: "sr-only", role: "status", "aria-live": "polite" });
  const input = h("input", { id: "q", type: "search", autocomplete: "off", spellcheck: "false",
    placeholder: "e.g. Rocky Mount, NC", "aria-describedby": "q-help" });
  input.value = lastQuery;

  const render = (text, submitted) => {
    const hits = find(text);
    results.replaceChildren();
    if (hits === null) {
      live.textContent = "";
      if (submitted) results.append(h("p", { class: "status-note" }, "Type at least 3 characters: a DUNS, an FEI, a firm name, a city or a street."));
      return;
    }
    if (submitted && hits.length === 1) { location.hash = `#/facility/${hits[0].duns}`; return; }
    if (!hits.length) {
      live.textContent = `No establishment matches ${text.trim()}.`;
      results.append(h("div", { class: "status-note" },
        h("p", {}, `No establishment matches “${text.trim()}”.`),
        h("p", { class: "muted" }, `The search covers the ${fmt(fac.size)} establishment DUNS named in the current labels. `
          + "A site the labels never name will not appear.")));
      return;
    }
    const count = h("p", { class: "count", tabindex: "-1" }, `${plural(hits.length, "establishment")} match`
      + (hits.length > 50 ? "; showing the 50 with the most MANUFACTURE assertions." : "."));
    results.append(count, h("ul", { "aria-label": "Matching establishments" }, hits.slice(0, 50).map(resultRow)));
    live.textContent = count.textContent;
    if (submitted) count.focus();
  };
  input.addEventListener("input", () => { lastQuery = input.value; render(input.value, false); });

  const form = h("form", { class: "search", role: "search", onsubmit: (e) => { e.preventDefault(); lastQuery = input.value; render(input.value, true); } },
    h("label", { for: "q", class: "eyebrow" }, "Search factories by name, city, DUNS or FEI"),
    h("div", { class: "search-box" }, input, h("button", { type: "submit" }, "Find site", h("span", { "aria-hidden": "true" }, " →"))),
    h("div", { class: "try" }, h("span", {}, "Try"), PROMPTS.map((p) => h("button", { type: "button", class: "link",
      onclick: () => { input.value = p; lastQuery = p; render(p, true); } }, p))),
    h("p", { class: "search-help small muted", id: "q-help" }, `All ${fmt(fac.size)} establishment DUNS named in the current `
      + "labels are searchable by DUNS, FEI, FDA-registered name and address, and the names labels use. A shared name or "
      + "town does not mean the same facility: identity comes only from DUNS and FEI."));

  const ex = EXAMPLES.map((d) => fac.get(d));
  const unresolved = fac.get("080105003"); // NOT_FOUND identity, never treated as a confirmed physical site
  const exampleRows = ex.map((f) => h("li", {},
    h("a", { class: "row-link", href: `#/facility/${f.duns}` },
      h("div", { class: "row-main" },
        h("p", { class: "row-title" }, placeOf(f.address).short),
        h("p", { class: "row-sub" },
          `${f.firm_name} · ${fmt(f.mfg_products)} products with documented manufacturing assertions`)),
      h("span", { class: "row-meta" }, "Explore evidence"), arrow())));
  if (unresolved) {
    exampleRows.push(h("li", {},
      h("a", { class: "row-link", href: `#/facility/${unresolved.duns}` },
        h("div", { class: "row-main" },
          h("p", { class: "row-title" }, "Unresolved manufacturing site"),
          h("p", { class: "row-sub" },
            `${fmt(unresolved.mfg_unknown)} UNKNOWN assertions · DUNS ${unresolved.duns}; no registered physical site resolved`)),
        h("span", { class: "row-meta" }, "Inspect missing evidence"), arrow())));
  }
  const examples = h("div", { class: "examples" },
    h("div", { class: "list-head" },
      h("h3", { class: "eyebrow" }, "Guided evidence examples"),
      h("span", { class: "eyebrow" }, "2026 label snapshot")),
    h("ul", {}, exampleRows));

  show(
    h("section", { class: "wrap hero story" },
      h("div", {},
        h("p", { class: "eyebrow" }, "Factory evidence · A real investigation"),
        h("h1", { class: "display story-title" }, "A drug factory is disrupted. ", h("em", {}, "What should we check?")),
        h("p", { class: "lede" },
          "Drug labels and FDA factory registrations contain clues about which medicines are linked to a site, ",
          "but the records are scattered. Fineprint connects them and shows the original evidence—including what is missing."),
        h("a", { class: "story-action", href: "#/rocky-mount-2023" },
          "See the 2023 Rocky Mount investigation", arrow()),
        h("p", { class: "story-note" },
          "Historical replay using records published by ", historical.cutoff,
          ". This is an investigation shortlist, not a shortage forecast.")),
      h("aside", { class: "story-results", "aria-label": "Rocky Mount historical evaluation results" },
        h("p", { class: "eyebrow" }, "2023 factory disruption · historical test"),
        h("p", { class: "story-question" }, "How many packages would an investigator need to check?"),
        h("div", { class: "story-comparison" },
          h("div", {}, h("span", { class: "story-number" }, fmt(baseline.N)),
            h("span", { class: "story-label" }, "Company-wide shortlist")),
          h("div", {}, h("span", { class: "story-number pine" }, fmt(shortlist.N)),
            h("span", { class: "story-label" }, "Facility-linked shortlist"))),
        h("p", { class: "story-improvement" }, `${reduction}%`, " fewer candidates to investigate"),
        h("p", { class: "story-recall" },
          "Both approaches recovered ", h("b", {}, `${shortlist.X} of ${warnings}`),
          " package codes on Pfizer's later low-inventory warning list."),
        h("p", { class: "story-disclosure" },
          "Measured on one historical event, not validated shortage predictions or proof of production."))),
    h("section", { class: "wrap explore-section", "aria-labelledby": "explore-title" },
      h("div", { class: "explore-heading" },
        h("p", { class: "eyebrow" }, "Explore the evidence · " + c.dailymed_release),
        h("h2", { class: "section-title", id: "explore-title" }, "Which medicines do published labels connect to a factory?"),
        h("p", { class: "explore-intro" },
          "Find a manufacturing establishment to see the medicines its labels name, the type of operation, ",
          "and the supporting FDA records. This ", c.dailymed_release,
          " snapshot is separate from the 2023 historical test.")),
      h("div", { class: "explore-grid" },
        h("div", {}, form, results, live, examples),
        h("details", { class: "explore-method" },
          h("summary", {}, "How does Fineprint connect a medicine and a factory?"),
          evidencePath()))),
    h("section", { class: "wrap", "aria-label": "Corpus and sources" },
      h("div", { class: "stats" },
        h("div", { class: "stat" }, h("p", { class: "stat-n" }, fmt(c.fingerprints.spl_document.rows)), h("p", { class: "stat-l" }, "label documents parsed")),
        h("div", { class: "stat" }, h("p", { class: "stat-n" }, fmt(fac.size)), h("p", { class: "stat-l" }, "establishments named in current labels")),
        h("div", { class: "sources" }, h("p", { class: "eyebrow" }, "Sources and limits"),
          h("p", {}, `Current-label snapshot of DailyMed human prescription SPL (${c.dailymed_release}) and FDA establishment `
            + `registration (${c.fda_registration_as_of}). The graph represents published statements, not verified lot manufacture, inventory or shortage risk. `,
            h("a", { class: "link", href: "#/about" }, "Read the data limitations →"))))),
  );
  if (lastQuery) render(lastQuery, false);
}

// -------------------------------------------------------------------------------------------- facility
async function facility(duns) {
  const [m, idx] = await Promise.all([load("manifest.json"), load("current/facilities.json")]);
  const f = facilityIndex(idx).get(duns);
  if (!f) return facilityNotFound(m, duns);
  const isExample = f.example;
  const bundle = isExample || mfgTotal(f) ? await load(isExample ? `current/examples/${duns}.json` : `current/manufacture/${shardOf(duns)}.json`) : null;
  const rank = { DIRECT: 0, TENTATIVE: 1, UNKNOWN: 2 };
  const all = (bundle ? facilityRows(bundle, f) : []).sort((x, y) => rank[x.confidence] - rank[y.confidence]
    || (x.product_ndc_5_4 || "~").localeCompare(y.product_ndc_5_4 || "~") || x.set_id.localeCompare(y.set_id)
    || x.evidence_id - y.evidence_id);
  const src = f.identity_source ? idx.identity_sources[f.identity_source] : null;
  const place = placeOf(f.address);
  const name = f.firm_name || f.spl_names[0] || null;
  const byCity = !!(place && place.city && f.firm_name);
  const heading = byCity ? place.short : name || `DUNS ${duns}`;
  setTitle(byCity ? `${place.short} — ${f.firm_name}` : heading);

  const siteCount = mfgTotal(f);
  const head = h("section", { class: "wrap fac-head" },
    h("p", { class: "eyebrow" }, `Facility · ${place ? place.region : STATUS_SHORT[f.status] || f.status}`),
    h("h1", {}, heading, byCity ? h("span", { class: "sub" }, h("span", { class: "dash" }, " — "), f.firm_name) : null),
    h("p", { class: "fac-intro" }, siteCount
      ? `In this dated snapshot, ${fmt(f.mfg_products)} distinct products have ${fmt(siteCount)} manufacturing statements naming this establishment.`
      : "This establishment is named in drug labels, but none of the exported statements names it for MANUFACTURE."),
    h("p", { class: "fac-scope" },
      "These are statements from labels in the ", m.datasets.current.dailymed_release,
      " release, not confirmation of current production, inventory or shortage risk.",
      duns === ROCKY_MOUNT ? [" ", h("a", { class: "link", href: "#/rocky-mount-2023" },
        "See the separate 2023 historical investigation →")] : null));

  const body = h("section", { class: "wrap fac-body" },
    h("h2", { class: "section-title" }, "What do these drug labels say?"),
    h("p", { class: "counts" },
      summary("DIRECT", f.mfg_direct), " · ", summary("TENTATIVE", f.mfg_tentative), " · ", summary("UNKNOWN", f.mfg_unknown),
      h("span", { class: "other" },
        "DIRECT means the label makes a product-specific manufacturing statement and the facility identity passes Fineprint's checks; "
        + "it is not an independently verified production record.")),
    all.length ? assertionTable(f, all, isExample) : noManufacture(f),
    h("details", { class: "technical-details" },
      h("summary", {}, "Inspect registration identity, source records and caveats"),
      h("dl", { class: "meta" },
        h("div", {}, h("dt", { class: "eyebrow" }, "DUNS"), h("dd", {}, duns)),
        h("div", {}, h("dt", { class: "eyebrow" }, "FEI"), h("dd", {}, f.fei || "none resolved")),
        h("div", {}, h("dt", { class: "eyebrow" }, "Site status"), h("dd", {}, f.status)),
        h("div", { class: "src" }, h("dt", { class: "eyebrow" }, "Sources"), h("dd", {}, h("ul", {},
          src ? h("li", {}, ext(src.url, "FDA registration")) : null,
          h("li", {}, ext("https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm", "DailyMed SPL")))))),
      identityRecord(f, src, place)),
    h("div", { class: "legend" }, ["DIRECT", "TENTATIVE", "UNKNOWN"].map((k) => h("p", {},
      h("span", { class: "dw" }, dot(k)), h("span", {}, h("b", {}, CONF_LABEL[k]), `: ${CONFIDENCE[k]}`)))),
    unresolvedSection(f, all, isExample));
  show(currentStrip(m), head, body);
}

function facilityNotFound(m, duns) {
  setTitle("Not found");
  show(currentStrip(m),
    h("section", { class: "wrap fac-head" }, h("p", { class: "eyebrow" }, "Facility"), h("h1", {}, `DUNS ${duns}`)),
    h("section", { class: "wrap fac-body" }, h("div", { class: "status-note" },
      h("p", {}, "No label in the current release names this DUNS as an establishment."),
      h("p", { class: "muted" }, "That does not mean the site does not exist; it means these labels do not name it."),
      h("p", {}, h("a", { class: "link pine", href: "#/" }, "Back to search →")))));
}

function summary(c, n) {
  return h("span", { class: "sum" }, dot(c), h("span", { class: "mono" }, fmt(n)), ` ${CONF_LABEL[c].toLowerCase()}`);
}

function kv(label, ...value) {
  return h("div", { class: "kv" }, h("dt", { class: "eyebrow" }, label), h("dd", {}, ...value));
}

function identityRecord(f, src, place) {
  return h("dl", { class: "kv-grid two", "aria-label": "Identity record" },
    kv("Status", h("span", { class: "mono" }, f.status), h("span", { class: "note" }, STATUS[f.status] || "")),
    kv("Registered as", f.firm_name ? `${f.firm_name}, ${f.address}` : "No registration line",
      place ? null : f.firm_name ? null : h("span", { class: "note" }, "No physical site is resolved for this DUNS.")),
    kv("Evidence", src ? [ext(src.url, src.name), ` (${src.kind}, file dated ${src.label}), line ${f.identity_line}`,
      h("span", { class: "note" }, `Registration expires ${f.expires || "not stated"}.`)] : "No registration line"),
    kv("Same FEI", f.fei_other_duns.length ? f.fei_other_duns.map((d, i) => [i ? ", " : "", h("a", { class: "link", href: `#/facility/${d}` }, d)])
      : "No other DUNS lists this FEI.", f.fei_changed ? h("span", { class: "note" }, REASONS["identity:fei_changed_across_snapshots"]) : null),
    kv("Label names", f.spl_names.join("; ") || "—", h("span", { class: "note" }, "Shown for reference; never used to resolve identity.")),
    kv("Company role", f.labeler_documents ? `Also the labeler on ${plural(f.labeler_documents, "current label")}.`
      : "Not a labeler in the current labels.", f.labeler_documents
      ? h("span", { class: "note" }, "A labeler is a company role, not a factory, and is not counted as manufacturing.") : null));
}

function noManufacture(f) {
  return h("div", { class: "toolbar" }, h("div", { class: "status-note" },
    h("p", {}, "No MANUFACTURE assertion names this establishment in the current labels."),
    h("p", { class: "muted" }, "This export lists MANUFACTURE rows for every establishment; other operations are counted above. "
      + "For all operations run ", h("code", {}, `python -I scripts/fp.py facility ${f.duns} --operation all`), ".")));
}

function assertionTable(f, all, isExample) {
  const state = { text: "", op: "MANUFACTURE", conf: "ALL", limit: pageSize() };
  const box = h("div");
  const count = h("p", { class: "count-line", "aria-live": "polite" });
  const opOf = (r) => state.op === "all" || r.operation === state.op;
  const filtered = () => all.filter((r) => opOf(r) && (state.conf === "ALL" || r.confidence === state.conf) && matches(r, state.text));
  const opName = () => (state.op === "all" ? "" : `${state.op} `);
  const filterInput = h("input", { id: "flt", class: "input", type: "search", autocomplete: "off",
    placeholder: "Filter product, NDC or set ID", oninput: (e) => { state.text = e.target.value.trim(); state.limit = pageSize(); redraw(); } });
  const seg = h("div", { class: "seg", role: "group", "aria-label": "Filter by evidence status" },
    [["ALL", "All"], ["DIRECT", "Direct"], ["TENTATIVE", "Tentative"], ["UNKNOWN", "Unknown"]].map(([k, l]) =>
      h("button", { type: "button", "data-conf": k, "aria-pressed": String(k === state.conf),
        onclick: () => { state.conf = k; state.limit = pageSize(); syncSeg(); redraw(); } }, l)));
  const syncSeg = () => seg.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.conf === state.conf)));
  const exportBtn = h("button", { type: "button", class: "btn", onclick: () => {
    const tag = [state.op, state.conf === "ALL" ? null : state.conf, state.text ? "filtered" : null].filter(Boolean).join("_");
    download(`fineprint_${f.duns}_${tag}.csv`, toCSV(CURRENT_CSV_COLUMNS, filtered().map(currentCsvRow)));
  } }, "Export CSV ", h("span", { "aria-hidden": "true" }, "↓"));
  const ops = [...new Set(all.map((r) => r.operation))].sort();
  const opSelect = isExample ? h("select", { id: "op", class: "select", "aria-label": "Operation",
    onchange: (e) => { state.op = e.target.value; state.limit = pageSize(); redraw(); } },
  ["MANUFACTURE", ...ops.filter((o) => o !== "MANUFACTURE")].map((o) => h("option", { value: o }, o)),
  h("option", { value: "all" }, "All operations")) : null;
  const clear = () => { state.text = ""; filterInput.value = ""; state.conf = "ALL"; state.limit = pageSize(); syncSeg(); redraw(); filterInput.focus(); };

  const redraw = () => {
    const rows = filtered();
    const ofOp = all.filter(opOf).length;
    count.textContent = `Showing ${fmt(rows.length)} of ${fmt(ofOp)} ${opName()}assertions. The CSV holds the `
      + `${rows.length === ofOp ? "" : "filtered "}rows shown, with every source field, link and hash.`;
    exportBtn.disabled = !rows.length;
    if (!rows.length) {
      const measured = state.conf !== "ALL" && !all.some((r) => opOf(r) && r.confidence === state.conf);
      box.replaceChildren(h("div", { class: "empty", role: "status" },
        h("p", { class: "t" }, "No assertions match."),
        h("p", { class: "s" }, measured ? `This site has 0 ${state.conf.toLowerCase()} ${opName()}assertions. That is a `
          + "measured result, not missing data." : "Try a different term or clear the filters."),
        h("button", { type: "button", class: "link", onclick: clear }, "Clear filters")));
      return;
    }
    const shown = rows.slice(0, state.limit);
    box.replaceChildren(wide.matches ? edgeTable(f, shown) : edgeCards(f, shown),
      rows.length > shown.length ? h("div", { class: "more" }, `Showing the first ${fmt(shown.length)} here; the CSV has all ${fmt(rows.length)}.`,
        h("button", { type: "button", class: "btn", onclick: () => { state.limit = Infinity; redraw(); } }, `Show all ${fmt(rows.length)}`)) : null);
  };
  const resize = () => { if (state.limit !== Infinity) state.limit = pageSize(); redraw(); };
  wide.addEventListener("change", resize);
  cleanups.push(() => wide.removeEventListener("change", resize));
  const wrap = h("div", {},
    h("div", { class: "toolbar" },
      h("div", { class: "title" }, h("h2", {}, isExample ? "Operation assertions" : "Manufacturing assertions")),
      h("div", { class: "controls" }, h("label", { class: "sr-only", for: "flt" }, "Filter by product, NDC, labeler or set ID"),
        filterInput, opSelect, seg, exportBtn)),
    count, box);
  redraw();
  return wrap;
}

// SPL dosage forms are an upper-case controlled vocabulary; tables show them in sentence case (the drawer and CSV
// keep the source value). Labelers are shown only where they differ from the establishment's registered firm.
const sentence = (s) => (!s || /[a-z]/.test(s) ? s : s.charAt(0) + s.slice(1).toLowerCase());
const otherLabelers = (f, r) => (r.labelers || []).filter((l) => l.toLowerCase() !== (f.firm_name || "").toLowerCase());
const productLine = (f, r) => [sentence(r.dosage_form), otherLabelers(f, r).length ? `labeler ${otherLabelers(f, r).join("; ")}` : null]
  .filter(Boolean).join(" · ");
const statusCell = (r) => [h("span", { class: "status" }, dot(r.confidence), CONF_LABEL[r.confidence]),
  r.reasons.length ? h("ul", { class: "reasons" }, r.reasons.map((x) => h("li", {}, REASONS[x] || x))) : null];
const versionLink = (r) => ext(links.label(r.set_id), `${r.set_id.slice(0, 8)}…`);
const versionCell = (r) => [versionLink(r), ` v${r.version}`, h("br"), `published ${r.published_date || "date unknown"}`];

function evButton(f, r, block) {
  const what = r.product_name ? `${r.product_name}, NDC ${r.product_ndc_5_4}` : `evidence ${r.evidence_id}`;
  return h("button", { type: "button", class: `btn ev${block ? " full" : ""}`, "aria-haspopup": "dialog",
    "aria-label": `View source evidence for ${r.operation}, ${what}`, onclick: (e) => openDrawer(f, r, e.currentTarget) },
  "Evidence →");
}

function edgeTable(f, rows) {
  return h("table", { class: "data" },
    h("caption", { class: "sr-only" }, "Operation assertions naming this establishment, one row per graph edge"),
    h("thead", {}, h("tr", {}, ["NDC", "Product", "Operation", "Status", "Label version"].map((c) => h("th", { scope: "col", class: "eyebrow" }, c)),
      h("th", { scope: "col" }, h("span", { class: "sr-only" }, "Evidence")))),
    h("tbody", {}, rows.map((r) => h("tr", {},
      h("td", { class: "ndc" }, r.product_ndc_5_4 || "—"),
      h("td", {}, r.product_ndc_5_4
        ? [h("span", { class: "prod" }, r.product_name || "Unnamed product"), h("span", { class: "sub" }, productLine(f, r))]
        : [h("span", { class: "prod" }, "No product resolved"), h("span", { class: "sub" }, `labeler ${(r.labelers || []).join("; ")}`)]),
      h("td", { class: "op" }, r.operation),
      h("td", {}, statusCell(r)),
      h("td", { class: "ver" }, versionCell(r)),
      h("td", { class: "act" }, evButton(f, r))))));
}

function edgeCards(f, rows) {
  return h("ul", { class: "cards", "aria-label": "Operation assertions naming this establishment" }, rows.map((r) => h("li", { class: "card" },
    h("p", { class: "ndc" }, r.product_ndc_5_4 ? `NDC ${r.product_ndc_5_4}` : "No product resolved"),
    h("p", { class: "name" }, r.product_name || `labeler ${(r.labelers || []).join("; ")}`),
    h("p", { class: "form" }, productLine(f, r)),
    h("dl", {},
      h("div", {}, h("dt", { class: "eyebrow" }, "Operation"), h("dd", { class: "mono" }, r.operation)),
      h("div", {}, h("dt", { class: "eyebrow" }, "Status"), h("dd", {}, statusCell(r))),
      h("div", { class: "wide" }, h("dt", { class: "eyebrow" }, "Label version"),
        h("dd", { class: "mono small" }, versionLink(r), ` v${r.version} · ${r.published_date || "date unknown"}`))),
    h("div", { class: "act" }, evButton(f, r, true)))));
}

function unresolvedSection(f, all, isExample) {
  const counts = new Map(); // reason -> Map(operation -> assertions)
  for (const r of all) {
    if (r.confidence === "DIRECT") continue;
    for (const x of r.reasons) {
      if (!counts.has(x)) counts.set(x, new Map());
      counts.get(x).set(r.operation, (counts.get(x).get(r.operation) || 0) + 1);
    }
  }
  const found = [];
  if (f.status !== "CURRENT_REGISTERED") found.push(h("li", {}, h("b", {}, "Identity. "), h("span", { class: "muted" }, STATUS[f.status])));
  for (const [k, ops] of counts) {
    found.push(h("li", {}, h("b", {}, [...ops].map(([op, n]) => `${op} ${fmt(n)}`).join(", ") + ". "), h("span", { class: "muted" }, REASONS[k] || k)));
  }
  if (!found.length) found.push(h("li", {}, all.length ? "Every exported assertion for this establishment is DIRECT." : "No assertions are exported for this establishment."));
  return h("section", { class: "block", "aria-labelledby": "missing" },
    h("h2", { id: "missing", class: "section-title" }, "Missing or unresolved evidence"),
    h("div", { class: "two-col" },
      h("div", {}, h("p", { class: "eyebrow" }, "In this export"), h("ul", { class: "note-list" }, found)),
      h("div", {}, h("p", { class: "eyebrow" }, "What this page cannot show"), h("ul", { class: "note-list" },
        h("li", {}, h("b", {}, "Unnamed sites. "), h("span", { class: "muted" }, "Products whose labels name no establishment at all, "
          + "or name this site under another DUNS. Nationally, 23% of products come from labels with no establishment section.")),
        h("li", {}, h("b", {}, "Other labels. "), h("span", { class: "muted" }, "Labels outside the loaded set (only human "
          + "prescription labels in the dated release), and anything published after it.")),
        h("li", {}, h("b", {}, "Supply. "), h("span", { class: "muted" }, "Volume, inventory, sole-source status or shortage risk. "
          + "A documented manufacturing link is exposure to a site, not a prediction that a product will be short.")),
        isExample ? null : h("li", {}, h("b", {}, "Other operations. "), h("span", { class: "muted" }, "Packing, labeling and testing "
          + "operations are counted but not listed here. For all operations run "), h("code", {}, `python -I scripts/fp.py facility ${f.duns} --operation all`), ".")))));
}

// -------------------------------------------------------------------------------------- evidence drawer
function openDrawer(f, r, trigger) {
  if (closeDrawer) closeDrawer(false);
  const outside = [document.querySelector(".skip"), document.querySelector(".site-header"), main, document.querySelector(".site-footer")];
  const closeBtn = h("button", { type: "button", class: "btn", onclick: () => close() }, "Close · Esc");
  const title = r.product_name || (r.product_ndc_5_4 ? `NDC ${r.product_ndc_5_4}` : "No product resolved");
  const panel = h("div", { class: "dlg-panel" },
    h("div", { class: "dlg-top" }, h("p", { class: "eyebrow" }, "Source evidence"), closeBtn),
    h("p", { class: "ndc" }, r.product_ndc_5_4 ? `NDC ${r.product_ndc_5_4}` : `Evidence ${r.evidence_id}`),
    h("h2", { id: "ev-title" }, title),
    h("p", { class: "form" }, [r.dosage_form, (r.labelers || []).join("; ")].filter(Boolean).join(" · ")),
    h("div", { class: "verdict" },
      h("p", { class: "status" }, dot(r.confidence), `${CONF_LABEL[r.confidence]} · ${r.operation}`),
      h("p", {}, CONFIDENCE[r.confidence]),
      r.reasons.length ? h("ul", {}, r.reasons.map((x) => h("li", {}, REASONS[x] || x))) : null),
    h("dl", { class: "kv-grid" },
      kv("Evidence ID", h("span", { class: "mono" }, String(r.evidence_id))),
      kv("Establishment", `${f.firm_name || f.spl_names[0] || "Unregistered"} · DUNS ${r.establishment_duns}`,
        h("span", { class: "note" }, `${r.identity_status}${r.fei ? ` · FEI ${r.fei}` : ""}`)),
      kv("Product NDC", r.product_ndc_5_4 ? h("span", { class: "mono" }, `${r.product_ndc_5_4} (label: ${r.product_ndc_raw})`) : "none"),
      kv("Package NDCs", r.package_ndcs_11.length ? h("span", { class: "mono" }, r.package_ndcs_11.join(" ")) : "none listed"),
      kv("SPL set ID", h("span", { class: "mono" }, r.set_id)),
      kv("Label version", h("span", { class: "mono" }, `v${r.version}`), ` · ${r.version_selection}`),
      kv("Document ID", h("span", { class: "mono" }, r.document_id)),
      kv("Dates", `published ${r.published_date || "unknown"}; effective ${r.effective_date || "unknown"}`),
      kv("Product scope", h("span", { class: "mono" }, r.product_scope), `; operation product code ${r.operation_product_code || "none"}`),
      kv("XML location", h("code", {}, r.xml_location)),
      kv("Release file", h("span", { class: "mono" }, `${r.source_part} → ${r.archive_member} → ${r.xml_member}`)),
      kv("XML SHA-256", h("code", {}, r.xml_sha256))),
    h("p", { class: "links" }, ext(links.label(r.set_id), "DailyMed label"), ext(links.versionZip(r.set_id, r.version), "This version (ZIP)"),
      ext(links.fdaXml(r.document_id), "FDA SPL XML"), ext(links.history(r.set_id), "Version history")),
    h("p", { class: "closing" }, "This shows that a label documents this operation at this establishment. It does not show "
      + "current production volume or inventory, or that this is the only supplier."));
  const root = h("div", { class: "dlg", role: "dialog", "aria-modal": "true", "aria-labelledby": "ev-title" },
    h("div", { class: "dlg-overlay", "aria-hidden": "true", onclick: () => close() }), panel);
  const onKey = (e) => {
    if (e.key === "Escape") { e.preventDefault(); close(); return; }
    if (e.key !== "Tab") return;
    const els = [...panel.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')];
    const first = els[0], last = els[els.length - 1];
    const inside = panel.contains(document.activeElement);
    if (e.shiftKey && (!inside || document.activeElement === first)) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && (!inside || document.activeElement === last)) { e.preventDefault(); first.focus(); }
  };
  function close(restore = true) {
    document.removeEventListener("keydown", onKey);
    root.remove();
    outside.forEach((el) => { if (el) el.inert = false; });
    document.body.classList.remove("lock");
    closeDrawer = null;
    if (restore) (trigger && trigger.isConnected ? trigger : main.querySelector("#flt") || main).focus();
  }
  document.addEventListener("keydown", onKey);
  outside.forEach((el) => { if (el) el.inert = true; });
  document.body.classList.add("lock");
  document.body.append(root);
  closeBtn.focus();
  closeDrawer = close;
}

// ------------------------------------------------------------------------------------- historical case
async function caseStudy() {
  const [m, hist] = await Promise.all([load("manifest.json"), load("historical/rocky_mount_2023.json")]);
  setTitle("Rocky Mount, July 2023");
  const all = historicalRows(hist);
  const E = hist.metrics.E, M = hist.metrics.M;
  const B1 = E.B1_all_hospira_00409, B2 = E.B2_injectables, G = E.graph_rocky_mount_direct;
  const P = hist.outcome.distinct_package_ndc_11;
  const cutoff = hist.cutoff;
  const pct = (x) => `${(100 * x).toFixed(1)}%`;
  const pkgs = hist.packages.map((raw) => Object.fromEntries(hist.package_columns.map((c, i) => [c, raw[i]])));
  const srcIdx = hist.provenance_columns.indexOf("sources");
  const recovered = pkgs.filter((p) => p.graph_flag && p.on_warning_list);
  const archivalOnly = recovered.filter((p) => p.provenance.every((v) => !v[srcIdx].includes("A"))).length;
  const unknown = pkgs.filter((p) => p.classification.startsWith("UNKNOWN_")).length;
  const missed = pkgs.filter((p) => p.classification === "NOT_IN_COHORT").map((p) => p.package_ndc_11);

  const fig = (n, l) => h("div", {}, h("dt", { class: "sr-only" }, l), h("dd", { class: "n" }, n), h("dd", { class: "l", "aria-hidden": "true" }, l));
  const barRow = (label, sub, n, strong) => h("div", { class: "bar-row" },
    h("p", { class: `who${strong ? " strong" : ""}` }, label, h("span", {}, sub)),
    h("div", { class: "bar-line" },
      h("div", { class: "hbar", role: "img", "aria-label": `${label}: ${fmt(n)} packages` }, h("i", { class: strong ? "strong" : null, style: `width:${(100 * n) / B1.N}%` })),
      h("span", { class: "v" }, fmt(n))));
  const recall = (label, x) => h("div", { class: "strip-row" }, h("p", { class: "who" }, label),
    h("div", { class: "bar-line" },
      h("div", { class: "cells", style: `grid-template-columns:repeat(${P},minmax(0,1fr))`, role: "img", "aria-label": `${label}: ${x} of ${P} warning NDCs recovered` },
        Array.from({ length: P }, (_, i) => h("span", { class: i < x ? "hit" : null }))),
      h("span", { class: "v" }, `${x}/${P}`)));
  const suppRow = (label, k, strong) => h("tr", {},
    h("th", { scope: "row", class: strong ? "strong" : null }, label), h("td", {}, fmt(k.N)), h("td", {}, `${k.X}/${k.positives}`),
    h("td", {}, k.reduction_vs_B1 ? pct(k.reduction_vs_B1) : "—"));
  const suppGroup = (label, ...rows) => h("tbody", {}, h("tr", { class: "group" }, h("th", { scope: "rowgroup", colspan: "4" }, label)), rows);
  const caveat = (t, ...rest) => h("li", {}, h("b", {}, t), " ", h("span", { class: "muted" }, ...rest));
  const timeline = [
    [cutoff, "Cutoff", "Only label versions published on or before this date are admissible. Both shortlists are built from them."],
    [hist.event.slice(0, 10), "Tornado", "A tornado damages Pfizer's Hospira plant in Rocky Mount, North Carolina."],
    ["2023-07-21", "Warning list", `Pfizer publishes ${P} package NDCs it expected to run low. Used only for scoring, after the freeze.`],
  ];

  show(
    historicalStrip(m),
    h("article", { class: "wrap case" },
      h("header", { class: "case-head" },
        h("div", {},
          h("p", { class: "eyebrow" }, "Case study · Rocky Mount, NC · retrospective replay"),
          h("h1", { class: "case-title" }, "A facility-based list was ", h("em", {}, `${pct(G.reduction_vs_B1)} shorter`),
            " and found the same warned packages."),
          h("p", { class: "lede" }, `Using only labels published by ${cutoff}, the day before the tornado, fineprint compared two `
            + `ways to shortlist Hospira packages for review. Both were then scored against the ${P} package NDCs Pfizer later warned about.`)),
        h("dl", { class: "figs" },
          fig(fmt(G.N), `vs ${fmt(B1.N)} packages to review`),
          fig(`−${pct(G.reduction_vs_B1)}`, "shorter shortlist"),
          fig(`${G.X}/${P}`, B1.X === G.X ? "warning NDCs found by both" : "warning NDCs found"))),

      h("section", { class: "results-sec", "aria-labelledby": "results-h" },
        h("h2", { id: "results-h", class: "sr-only" }, "Results"),
        h("figure", { "aria-labelledby": "fig1" },
          h("figcaption", { id: "fig1", class: "figcap" }, h("span", { class: "eyebrow ink" }, "Fig. 1 · Shortlist size"),
            h("span", { class: "scale" }, `bar length ∝ packages · axis 0–${B1.N}`)),
          h("div", { class: "bars" },
            barRow("Company-wide", "All Hospira 00409 packages", B1.N, false),
            barRow("Facility graph", "Packages whose pre-cutoff label lists MANUFACTURE at Rocky Mount", G.N, true)),
          h("div", { class: "axis-row", "aria-hidden": "true" }, h("span"),
            h("div", { class: "axis" }, h("span", {}, "0"), h("span", {}, String(Math.round(B1.N / 2))), h("span", {}, String(B1.N))))),
        h("div", { class: "fig2", role: "group", "aria-labelledby": "fig2" },
          h("p", { id: "fig2", class: "figcap" }, h("span", { class: "eyebrow ink" }, "Fig. 2 · Warning-list recovery"),
            h("span", { class: "scale" }, `1 cell = 1 of Pfizer's ${P} warning NDCs · not positioned within Fig. 1`)),
          h("div", { class: "strips" }, recall("Company-wide", B1.X), recall("Facility graph", G.X)),
          h("p", { class: "key" }, h("span", {}, h("i", { class: "hit", "aria-hidden": "true" }), "Recovered"),
            h("span", {}, h("i", { "aria-hidden": "true" }), `Missed (${missed.length} sterile empty vials, no drug label)`))),
        h("div", { class: "supp" },
          h("p", { id: "supp-cap", class: "eyebrow" }, "Supplementary baselines"),
          h("p", { class: "supp-note" }, `Company-wide: all Hospira 00409 packages. Facility graph: packages with a DIRECT Rocky Mount `
            + `MANUFACTURE link. Cohort E holds the ${fmt(hist.cohort_sizes.E)} eligible packages from today's DailyMed Hospira search and `
            + `FDA's May 2023 NDC directory; cohort M is the ${fmt(hist.cohort_sizes.M)} of them listed in that directory.`),
          h("div", { class: "scroll-x", role: "region", "aria-labelledby": "supp-cap", tabindex: "0" },
            h("table", {},
              h("thead", {}, h("tr", {}, h("th", { scope: "col", class: "eyebrow" }, "Shortlist"),
                ["Packages", "Recovered", "Shorter by"].map((c) => h("th", { scope: "col", class: "eyebrow r" }, c)))),
              suppGroup(`Cohort E · ${fmt(hist.cohort_sizes.E)} packages`, suppRow("Company-wide", B1), suppRow("Injectables only", B2),
                suppRow("Facility graph", G, true)),
              suppGroup(`Cohort M · ${fmt(hist.cohort_sizes.M)} packages`, suppRow("Company-wide", M.B1_all_hospira_00409),
                suppRow("Injectables only", M.B2_injectables), suppRow("Facility graph", M.graph_rocky_mount_direct, true)),
              suppGroup("Both cohorts", h("tr", {}, h("th", { scope: "row" }, "Already short before the event"),
                h("td", { class: "ne", colspan: "3" }, "Not evaluable: no package-level shortage data was published before the cutoff."))))))),

      h("section", { class: "block", "aria-labelledby": "seq" },
        h("h2", { id: "seq", class: "section-title" }, "Sequence"),
        h("ol", { class: "seq" }, timeline.map(([d, t, s]) => h("li", {}, h("span", { class: "pin", "aria-hidden": "true" }),
          h("p", { class: "d" }, d), h("p", { class: "t" }, t), h("p", { class: "s" }, s)))),
        h("p", { class: "amber-note" }, "Amber marks historical time, not risk.")),

      h("section", { class: "block two-col" },
        h("div", {},
          h("h2", { class: "section-title", id: "caveats" }, "What the result does not show"),
          h("ul", { class: "note-list", "aria-labelledby": "caveats", style: "margin-top:16px" },
            caveat("Not a forecast.", "A label link documents a manufacturing site. This is not shortage prediction: it does not "
              + "predict which supply will fail."),
            caveat("Not precision.", `The ${fmt(hist.flagged_not_listed.E)} flagged packages that are not on Pfizer's list are not `
              + "false positives. The list covers low inventory after warehouse damage, not everything made at the plant."),
            caveat(`${missed.length} misses had no label.`, `${missed.join(" and ")} are sterile empty vials, for which no drug `
              + "label exists, so no label-based method could find them."),
            caveat("Archive completeness is unproven.", "DailyMed's all-labels-on-a-date export was not obtained, and one label's "
              + "pre-cutoff version could not be retrieved."),
            caveat(`${archivalOnly} hits relied on retired labels.`, `${archivalOnly} of the ${recovered.length} recovered NDCs appear only `
              + "in retired labels that today's DailyMed search does not return. They were recovered from FDA's SPL-by-document-ID "
              + "store and a 2023 monthly archive."),
            caveat("Labels under-report sites.", `${unknown} of ${fmt(hist.cohort_sizes.E)} packages have no usable manufacturing `
              + "evidence. None of Pfizer's NDCs fell in that group; that is a property of this event, not a guarantee."),
            caveat("The identity record predates 2023.", "Rocky Mount's identity rests on a 2015 facility filing and a 2022-10-13 "
              + "registration record. Its 2023 registration status is not established."),
            caveat("Exposure is not shortage.", "A product with a documented Rocky Mount link may have other sites or stock; one "
              + "without may still depend on the plant through unlisted steps."))),
        h("div", { class: "method" },
          h("h2", { class: "section-title" }, "How it was tested"),
          h("p", { style: "margin-top:16px" }, h("b", {}, "Retrospective replay. "), `Shortlists were rebuilt from label versions published by `
            + `${cutoff} and a frozen cohort, then scored against Pfizer's list only after the freeze.`),
          h("p", {}, h("b", {}, "Pre-registered, then frozen. "), "The method, cohorts, baselines and metrics were committed before the "
            + "outcome was unsealed. The frozen inputs are tagged ", h("code", {}, hist.seal.tag), " (manifest SHA-256 ",
          h("code", {}, `${hist.seal.manifest_sha256.slice(0, 16)}…`), "), and scoring refuses to run if any frozen file differs. "
            + "After unsealing, only two disclosed text-extraction fixes were made."),
          h("p", {}, h("b", {}, "Not blind. "), "The researcher and assistant had seen Pfizer's positives before this work, and the "
            + "five DST-00 probe packages were chosen with that knowledge. They are not part of any rule. No blinding is claimed. ",
          ext(`${REPO}/blob/main/docs/EVALUATION_REPORT.md`, "Evaluation protocol and disclosed contamination")),
          h("p", { class: "aside" }, "Pre-registration and the freeze limit leakage, but this is not a blind or independent test. "
            + "Treat the result as a careful retrospective replay."),
          h("p", { class: "small muted" }, "The outcome list was retrieved from ", ext(hist.outcome.url, "fda.gov"),
            " after the freeze; it is not redistributed here. Full method: ",
            ext(`${REPO}/blob/main/docs/historical_panel_plan.md`, "pre-registered plan"), "."))),

      cohortSection(all, cutoff),
      h("a", { class: "report-link", href: `${REPO}/blob/main/docs/CASE_STUDY.md`, rel: "noopener", target: "_blank" },
        "Read the full case study on GitHub", h("span", { class: "sr-only" }, " (opens in new tab)"), arrow("↗"))),
  );
}

function cohortSection(all, cutoff) {
  const state = { text: "", cls: "all", flagged: false, listed: false, limit: pageSize() };
  const count = h("p", { class: "count-line", "aria-live": "polite" });
  const box = h("div");
  const filtered = () => all.filter((r) => (state.cls === "all" || r.classification === state.cls)
    && (!state.flagged || r.graph_flag) && (!state.listed || r.on_warning_list)
    && (!state.text || [r.package_ndc_11, r.product_ndc_raw, r.set_id, r.form].some((v) => v && v.toLowerCase().includes(state.text.toLowerCase()))));
  const exportBtn = h("button", { type: "button", class: "btn",
    onclick: () => download("fineprint_rocky_mount_2023.csv", toCSV(HISTORICAL_CSV_COLUMNS, filtered())) },
  "Export CSV ", h("span", { "aria-hidden": "true" }, "↓"));
  const textInput = h("input", { id: "hq", class: "input", type: "search", autocomplete: "off", placeholder: "Filter NDC, set ID or form",
    oninput: (e) => { state.text = e.target.value.trim(); state.limit = pageSize(); redraw(); } });
  const clsSelect = h("select", { id: "hc", class: "select", "aria-label": "Classification",
    onchange: (e) => { state.cls = e.target.value; state.limit = pageSize(); redraw(); } },
  h("option", { value: "all" }, "All classifications"), [...new Set(all.map((r) => r.classification))].sort().map((c) => h("option", { value: c }, c)));
  const check = (key, label) => h("label", { class: "check" }, h("input", { type: "checkbox",
    onchange: (e) => { state[key] = e.target.checked; state.limit = pageSize(); redraw(); } }), label);
  const clear = () => {
    Object.assign(state, { text: "", cls: "all", flagged: false, listed: false, limit: pageSize() });
    textInput.value = ""; clsSelect.value = "all";
    section.querySelectorAll(".check input").forEach((i) => { i.checked = false; });
    redraw(); textInput.focus();
  };
  const redraw = () => {
    const rows = filtered();
    count.textContent = `Showing ${fmt(rows.length)} of ${fmt(all.length)} rows (one row per package and label version). `
      + "The CSV holds the rows shown.";
    exportBtn.disabled = !rows.length;
    if (!rows.length) {
      box.replaceChildren(h("div", { class: "empty", role: "status" }, h("p", { class: "t" }, "No packages match."),
        h("p", { class: "s" }, "Try a different term or clear the filters."), h("button", { type: "button", class: "link", onclick: clear }, "Clear filters")));
      return;
    }
    const shown = rows.slice(0, state.limit);
    box.replaceChildren(wide.matches ? histTable(shown, cutoff) : histCards(shown),
      rows.length > shown.length ? h("div", { class: "more" }, `Showing the first ${fmt(shown.length)} here; the CSV has all ${fmt(rows.length)}.`,
        h("button", { type: "button", class: "btn", onclick: () => { state.limit = Infinity; redraw(); } }, `Show all ${fmt(rows.length)}`)) : null);
  };
  const resize = () => { if (state.limit !== Infinity) state.limit = pageSize(); redraw(); };
  wide.addEventListener("change", resize);
  cleanups.push(() => wide.removeEventListener("change", resize));
  const section = h("section", { class: "block", "aria-labelledby": "cohort-h" },
    h("div", { class: "toolbar stack" },
      h("div", { class: "title" }, h("h2", { id: "cohort-h" }, "Every package in the frozen cohort")),
      h("div", { class: "controls" }, h("label", { class: "sr-only", for: "hq" }, "Filter by NDC, set ID or form"), textInput, clsSelect,
        check("flagged", "Flagged by fineprint"), check("listed", "On Pfizer's list"), exportBtn)),
    count, box,
    h("dl", { class: "legend-cls" }, Object.entries(CLASSES).map(([k, v]) => h("div", {}, h("dt", {}, h("b", {}, k)), h("dd", {}, v)))));
  redraw();
  return section;
}

const histVersion = (r) => (r.set_id ? [ext(r.document_url, `${r.set_id.slice(0, 8)}… v${r.version}`), h("br"),
  `${r.published_date} · ${r.document_kind}`] : "—");
const histXml = (r, label = "Rocky Mount MANUFACTURE element") => (r.rocky_mount_manufacture_locs.length
  ? h("details", { class: "xml" }, h("summary", {}, label), h("code", {}, r.rocky_mount_manufacture_locs.join(" "))) : null);
const may2023 = (r) => (r.in_may_2023_listing == null ? "—" : r.in_may_2023_listing ? "yes" : "no");

function histTable(rows, cutoff) {
  return h("div", { class: "scroll-x", role: "region", "aria-label": "Frozen 2023 cohort", tabindex: "0" }, h("table", { class: "data cohort" },
    h("caption", { class: "sr-only" }, "Frozen 2023 cohort, one row per package and label version"),
    h("thead", {}, h("tr", {}, [["Package NDC"], ["Classification"], ["Flagged", "flagged by fineprint"], ["Pfizer", "on Pfizer's list"],
      ["May 2023", "in FDA's May 2023 NDC directory"], ["Form"], [`Label version ≤ ${cutoff}`]].map(([c, full]) =>
      h("th", { scope: "col", class: "eyebrow", title: full || null }, c, full ? h("span", { class: "sr-only" }, ` (${full})`) : null)))),
    h("tbody", {}, rows.map((r) => h("tr", {},
      h("td", { class: "ndc" }, r.package_ndc_11),
      h("td", {}, h("span", { class: "hist-cls" }, r.classification), r.note ? h("span", { class: "sub" }, r.note) : null),
      h("td", { class: "flag" }, r.graph_flag ? "yes" : "—"),
      h("td", { class: "flag" }, r.on_warning_list ? "yes" : "—"),
      h("td", { class: "flag" }, may2023(r)),
      h("td", { class: "form" }, sentence(r.form) || "—"),
      h("td", { class: "ver" }, histVersion(r), histXml(r)))))));
}

function histCards(rows) {
  return h("ul", { class: "cards", "aria-label": "Frozen 2023 cohort, one row per package and label version" }, rows.map((r) => h("li", { class: "card" },
    h("p", { class: "ndc" }, `Package ${r.package_ndc_11}`),
    h("p", { class: "name hist-cls" }, r.classification),
    r.note ? h("p", { class: "form" }, r.note) : null,
    h("dl", {},
      h("div", {}, h("dt", { class: "eyebrow" }, "Flagged by fineprint"), h("dd", { class: "mono" }, r.graph_flag ? "yes" : "—")),
      h("div", {}, h("dt", { class: "eyebrow" }, "On Pfizer's list"), h("dd", { class: "mono" }, r.on_warning_list ? "yes" : "—")),
      h("div", {}, h("dt", { class: "eyebrow" }, "May 2023 directory"), h("dd", { class: "mono" }, may2023(r))),
      h("div", {}, h("dt", { class: "eyebrow" }, "Form"), h("dd", {}, sentence(r.form) || "—")),
      h("div", { class: "wide" }, h("dt", { class: "eyebrow" }, "Label version"), h("dd", { class: "mono small" }, histVersion(r))),
      r.rocky_mount_manufacture_locs.length ? h("div", { class: "wide" }, h("dt", { class: "eyebrow" }, "Rocky Mount MANUFACTURE"),
        h("dd", {}, histXml(r, "XML location"))) : null))));
}

// ------------------------------------------------------------------------------------------------ about
async function about() {
  const m = await load("manifest.json");
  const c = m.datasets.current, hd = m.datasets.historical;
  setTitle("About the data");
  show(h("div", { class: "wrap page" },
    h("p", { class: "eyebrow" }, "Data · sources · checksums"),
    h("h1", {}, "About the data"),
    h("p", { class: "lede" }, h("b", {}, `${m.attribution}. `), m.currency),
    h("p", { class: "lede" }, m.independence),
    h("section", { class: "block", "aria-labelledby": "a-cur" },
      h("h2", { id: "a-cur", class: "section-title" }, "Current-release graph"),
      h("ul", { class: "prose" },
        h("li", {}, `DailyMed human prescription SPL release ${c.dailymed_release}: ${c.release_parts.length} parts, SHA-256 recorded `
          + `below; ${c.daily_updates_applied} daily updates applied.`),
        h("li", {}, `FDA establishment registration (DECRS) files as of ${c.fda_registration_as_of}, plus dated archived files used to `
          + "mark identities as stale."),
        h("li", {}, `Graph build ${c.graph_build.build_id}, rules ${c.graph_build.rule_version}, code `,
          ext(`${REPO}/commit/${c.graph_build.code_commit}`, c.graph_build.code_commit.slice(0, 7)), `, finished ${c.graph_build.finished_at}.`),
        h("li", {}, `Exported: ${c.scope}. Not exported: ${c.not_exported.join("; ")}.`)),
      h("div", { class: "scroll-x", role: "region", "aria-labelledby": "parts-cap", tabindex: "0", style: "margin-top:24px" },
        h("table", { class: "files" }, h("caption", { id: "parts-cap", class: "eyebrow", style: "text-align:left;padding-bottom:8px" }, "Release parts"),
          h("thead", {}, h("tr", {}, h("th", { scope: "col", class: "eyebrow" }, "File"), h("th", { scope: "col", class: "eyebrow r" }, "Bytes"),
            h("th", { scope: "col", class: "eyebrow" }, "SHA-256"))),
          h("tbody", {}, c.release_parts.map((p) => h("tr", {}, h("td", {}, ext(p.url, p.name)),
            h("td", { class: "r" }, fmt(p.bytes)), h("td", {}, h("code", {}, p.sha256)))))))),
    h("section", { class: "block", "aria-labelledby": "a-hist" },
      h("h2", { id: "a-hist", class: "section-title" }, "Historical replay"),
      h("p", { class: "prose" }, hd.description),
      h("ul", { class: "prose", style: "margin-top:16px" }, Object.entries(hd.inputs).map(([p, s]) => h("li", {},
        ext(`${REPO}/blob/main/${p}`, p), " ", h("code", {}, `${s.slice(0, 16)}…`))))),
    h("section", { class: "block", "aria-labelledby": "a-how" },
      h("h2", { id: "a-how", class: "section-title" }, "How these files were made"),
      h("div", { class: "prose method" },
        h("p", {}, "Generated by ", ext(`${REPO}/blob/main/${m.generated_by.script}`, m.generated_by.script),
          ` from the PostgreSQL graph and the committed evidence. ${m.generated_by.deterministic}; re-running the export on the same `
          + `database reproduces every data file byte for byte. ${m.csv}`),
        h("p", {}, m.privacy),
        h("p", {}, h("a", { class: "link", href: "data/manifest.json" }, "Download the manifest"),
          " (every file with its SHA-256 and row count). ", `Code license: ${m.license.code}. ${m.license.data}`),
        h("p", {}, "Typefaces: Newsreader, DM Sans and JetBrains Mono, self-hosted under the SIL Open Font License 1.1 (",
          h("a", { class: "link", href: "fonts/LICENSE-newsreader.txt" }, "Newsreader"), ", ",
          h("a", { class: "link", href: "fonts/LICENSE-dm-sans.txt" }, "DM Sans"), ", ",
          h("a", { class: "link", href: "fonts/LICENSE-jetbrains-mono.txt" }, "JetBrains Mono"),
          "). The site loads nothing from third-party servers."))),
  ));
}

// ---------------------------------------------------------------------------------------------- router
async function route() {
  if (location.hash && !location.hash.startsWith("#/")) return;
  if (closeDrawer) closeDrawer(false);
  cleanups.forEach((fn) => fn());
  cleanups = [];
  const hash = location.hash.replace(/^#\/?/, "");
  const [view, arg] = hash.split("/");
  const section = view === "facility" ? "facility" : view === "rocky-mount-2023" ? "history" : view === "about" ? "about" : "home";
  document.querySelectorAll(".site-header [data-nav]").forEach((l) => {
    if (l.dataset.nav !== section) l.removeAttribute("aria-current");
    else l.setAttribute("aria-current", l.getAttribute("href") === `#/${hash}` || (section === "home") ? "page" : "true");
  });
  show(h("div", { class: "wrap loading" }, h("p", { class: "muted" }, "Loading…")));
  try {
    if (view === "facility" && /^\d{9}$/.test(arg || "")) await facility(arg);
    else if (view === "rocky-mount-2023") await caseStudy();
    else if (view === "about") await about();
    else await home();
  } catch (err) {
    show(h("div", { class: "wrap page" }, h("h1", {}, "Could not load the data"), h("p", { class: "lede" }, String(err.message || err)),
      h("p", { class: "lede" }, h("a", { class: "link", href: "#/" }, "Back to search →"))));
  }
  window.scrollTo(0, 0);
  if (!firstRoute) {
    const title = main.querySelector("h1");
    if (title) { title.tabIndex = -1; title.focus({ preventScroll: true }); } else main.focus({ preventScroll: true });
  }
  firstRoute = false;
}

document.querySelector(".skip").addEventListener("click", (e) => {
  e.preventDefault();
  const title = main.querySelector("h1");
  if (title) { title.tabIndex = -1; title.focus(); } else main.focus();
});
window.addEventListener("hashchange", route);
route();
