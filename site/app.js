// Facility Evidence Explorer: a static view of exported fineprint graph records. All text from source
// records is inserted with textContent (never parsed as HTML).
import {
  CONFIDENCE, CURRENT_CSV_COLUMNS, HISTORICAL_CSV_COLUMNS, REASONS, STATUS, currentCsvRow, facilityIndex,
  facilityRows, historicalRows, links, matches, shardOf, toCSV,
} from "./explorer-core.js";

const REPO = "https://github.com/s2002kumar/fineprint";
const EXAMPLES = ["093132819", "030606222"];
const main = document.getElementById("main");
const cache = new Map();

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
const a = (href, text, ext) => h("a", ext ? { href, rel: "noopener", target: "_blank" } : { href }, text);
const fmt = (n) => Number(n).toLocaleString("en-US");
const show = (...nodes) => main.replaceChildren(...nodes.flat(Infinity).filter((x) => x != null && x !== false));

async function load(path) {
  if (!cache.has(path)) {
    cache.set(path, fetch(`data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
      return r.json();
    }));
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

function banner(kind, m) {
  if (kind === "current") {
    const c = m.datasets.current;
    return h("p", { class: "banner current" },
      h("strong", {}, "Current-release graph. "),
      `DailyMed human prescription labels, release ${c.dailymed_release}; FDA establishment registration files as of `
      + `${c.fda_registration_as_of}. A dated snapshot: it does not reflect the most current/accurate data available `
      + "from NLM, and it is not the 2023 historical replay.");
  }
  return h("p", { class: "banner historical" },
    h("strong", {}, "Historical replay, kept separate from the current graph. "),
    `Only label versions published on or before ${m.datasets.historical.cutoff}, frozen before the outcome list was `
    + "retrieved. Nothing on this page comes from the 2026 release.");
}

function setTitle(t) {
  document.title = t ? `${t} · fineprint explorer` : "fineprint · Facility Evidence Explorer";
}

// ------------------------------------------------------------------------------------------------ home
async function home() {
  const [m, idx] = await Promise.all([load("manifest.json"), load("current/facilities.json")]);
  const fac = facilityIndex(idx);
  setTitle("");
  const results = h("div", { "aria-live": "polite" });
  const input = h("input", { id: "q", type: "search", autocomplete: "off", placeholder: "e.g. 093132819, FEI 1021343, Hospira, Rocky Mount" });
  const run = () => {
    const t = input.value.trim().toLowerCase().replace(/^fei[:\s]*/, "");
    results.replaceChildren();
    if (t.length < 3) return;
    const hits = [];
    for (const f of fac.values()) {
      if (f.duns.includes(t) || (f.fei && f.fei === t) || (f.firm_name || "").toLowerCase().includes(t)
          || (f.address || "").toLowerCase().includes(t)
          || f.spl_names.some((n) => n.toLowerCase().includes(t))) hits.push(f);
    }
    hits.sort((x, y) => (y.mfg_direct + y.mfg_tentative + y.mfg_unknown) - (x.mfg_direct + x.mfg_tentative + x.mfg_unknown)
      || x.duns.localeCompare(y.duns));
    results.append(h("p", {}, `${fmt(hits.length)} establishment${hits.length === 1 ? "" : "s"} match`
      + (hits.length > 50 ? "; showing the 50 with the most MANUFACTURE assertions." : ".")));
    if (hits.length) results.append(facilityTable(hits.slice(0, 50)));
  };
  input.addEventListener("input", run);
  const ex = EXAMPLES.map((d) => fac.get(d));
  show(
    h("h1", {}, "Facility Evidence Explorer"),
    h("p", { class: "lede" }, "FDA drug labels name the establishments that manufacture, pack, label or test each "
      + "product, by DUNS number. fineprint links those statements to FDA registration records and keeps the exact "
      + "label version and XML element behind each link. This site is a static export of that graph: no server, "
      + "no live data."),
    banner("current", m),
    h("h2", {}, "Start with an example"),
    h("ul", { class: "cards" }, ex.map((f) => h("li", {},
      h("a", { href: `#/facility/${f.duns}`, class: "card" },
        h("strong", {}, `${f.firm_name}, ${cityOf(f.address)}`),
        h("span", {}, `DUNS ${f.duns} · FEI ${f.fei}`),
        h("span", {}, `${fmt(f.mfg_direct)} DIRECT MANUFACTURE assertions · ${fmt(f.mfg_unknown + f.mfg_tentative)} `
          + "unresolved"))))),
    h("h2", {}, "Look up an establishment"),
    h("p", {}, `All ${fmt(fac.size)} establishment DUNS named in the current labels are searchable. MANUFACTURE `
      + "assertions are exported for every one of them; the two examples above also include packing, labeling and "
      + "testing operations."),
    h("label", { for: "q" }, "DUNS, FEI, name or registered address"), input,
    h("p", { class: "note" }, "Text matches FDA-registered firm names and addresses and the names labels use. A "
      + "shared name or town does not mean the same facility; identity comes only from DUNS and FEI."),
    results,
    h("h2", {}, "Historical case study"),
    h("p", {}, a("#/rocky-mount-2023", "Rocky Mount, July 2023"),
      ": a separate, frozen replay that uses only records published before the tornado and compares the result "
      + "with Pfizer's public warning list."),
  );
}

function cityOf(addr) {
  const m = /,\s*([^,]+),\s*[^,]*\(([A-Z]{2})\)/.exec(addr || "");
  return m ? `${m[1]}, ${m[2]}` : "";
}

function facilityTable(list) {
  return h("div", { class: "scroll", tabindex: "0", role: "region", "aria-label": "Matching establishments" },
    h("table", {},
      h("thead", {}, h("tr", {}, ["DUNS", "Registered name and address", "Identity", "MANUFACTURE assertions",
        "Other operations"].map((c) => h("th", { scope: "col" }, c)))),
      h("tbody", {}, list.map((f) => h("tr", {},
        h("td", {}, a(`#/facility/${f.duns}`, f.duns)),
        h("td", {}, f.firm_name ? `${f.firm_name} — ${f.address}` : h("em", {}, `no registration found; labels say: ${f.spl_names.join("; ")}`)),
        h("td", {}, f.status),
        h("td", {}, `${fmt(f.mfg_direct)} direct · ${fmt(f.mfg_tentative)} tentative · ${fmt(f.mfg_unknown)} unknown`),
        h("td", {}, Object.entries(f.other_operations).map(([k, v]) => `${k} ${fmt(v)}`).join(" · ") || "—"))))));
}

// -------------------------------------------------------------------------------------------- facility
async function facility(duns) {
  const [m, idx] = await Promise.all([load("manifest.json"), load("current/facilities.json")]);
  const f = facilityIndex(idx).get(duns);
  if (!f) {
    setTitle("Not found");
    show(h("h1", {}, `DUNS ${duns}`), banner("current", m),
      h("p", {}, "No label in the current release names this DUNS as an establishment. That does not mean the site "
        + "does not exist; it means these labels do not name it."), h("p", {}, a("#/", "Back to search")));
    return;
  }
  const isExample = f.example;
  const bundle = await load(isExample ? `current/examples/${duns}.json` : `current/manufacture/${shardOf(duns)}.json`)
    .catch(() => null);
  const rank = { DIRECT: 0, TENTATIVE: 1, UNKNOWN: 2 };
  const all = (bundle ? facilityRows(bundle, f) : []).sort((x, y) => rank[x.confidence] - rank[y.confidence]
    || (x.product_ndc_5_4 || "~").localeCompare(y.product_ndc_5_4 || "~") || x.set_id.localeCompare(y.set_id)
    || x.evidence_id - y.evidence_id);
  setTitle(f.firm_name || `DUNS ${duns}`);
  const src = f.identity_source ? idx.identity_sources[f.identity_source] : null;

  const state = { text: "", op: "MANUFACTURE", conf: new Set(["DIRECT", "TENTATIVE", "UNKNOWN"]) };
  const tableBox = h("div");
  const count = h("p", { "aria-live": "polite", class: "count" });
  const filtered = () => all.filter((r) => (state.op === "all" || r.operation === state.op)
    && state.conf.has(r.confidence) && matches(r, state.text));
  const redraw = () => {
    const rows = filtered();
    const ofOp = all.filter((r) => state.op === "all" || r.operation === state.op).length;
    count.textContent = `${fmt(rows.length)} of ${fmt(ofOp)} ${state.op === "all" ? "" : state.op + " "}assertions shown.`;
    tableBox.replaceChildren(edgeTable(rows.slice(0, 500)),
      rows.length > 500 ? h("p", { class: "note" }, `Showing the first 500; the CSV has all ${fmt(rows.length)}.`) : "");
  };
  const ops = [...new Set(all.map((r) => r.operation))].sort();
  const controls = h("form", { class: "controls", onsubmit: (e) => e.preventDefault() },
    h("div", {}, h("label", { for: "filter" }, "Filter by NDC, product, labeler or set ID"),
      h("input", { id: "filter", type: "search", oninput: (e) => { state.text = e.target.value.trim(); redraw(); } })),
    isExample ? h("div", {}, h("label", { for: "op" }, "Operation"),
      h("select", { id: "op", onchange: (e) => { state.op = e.target.value; redraw(); } },
        ["MANUFACTURE", ...ops.filter((o) => o !== "MANUFACTURE"), "all"].map((o) => h("option", { value: o }, o))))
      : null,
    h("fieldset", {}, h("legend", {}, "Evidence status"),
      ["DIRECT", "TENTATIVE", "UNKNOWN"].map((c) => h("label", { class: "check" },
        h("input", { type: "checkbox", checked: true, onchange: (e) => {
          e.target.checked ? state.conf.add(c) : state.conf.delete(c); redraw(); } }), ` ${c}`))),
    h("div", {}, h("button", { type: "button", onclick: () => download(`fineprint_${duns}_${state.op}.csv`,
      toCSV(CURRENT_CSV_COLUMNS, filtered().map(currentCsvRow))) }, "Download CSV of shown rows")));

  show(
    h("p", {}, a("#/", "← All establishments")),
    h("h1", {}, f.firm_name ? `${f.firm_name}${cityOf(f.address) ? ", " + cityOf(f.address) : ""}` : `DUNS ${duns}`),
    banner("current", m),
    h("h2", {}, "Establishment identity"),
    h("dl", { class: "facts" },
      h("dt", {}, "DUNS"), h("dd", {}, duns),
      h("dt", {}, "Identity status"), h("dd", {}, h("code", {}, f.status), " — ", STATUS[f.status] || ""),
      h("dt", {}, "FEI"), h("dd", {}, f.fei || "none resolved"),
      h("dt", {}, "Registered name and address"), h("dd", {}, f.firm_name ? `${f.firm_name}, ${f.address}` : "none"),
      h("dt", {}, "Registration evidence"), h("dd", {}, src
        ? [a(src.url, src.name, true), ` (${src.kind}, file dated ${src.label}), line ${f.identity_line}; expires ${f.expires || "not stated"}`]
        : "no registration line"),
      h("dt", {}, "Other DUNS with this FEI"), h("dd", {}, f.fei_other_duns.length
        ? f.fei_other_duns.map((d, i) => [i ? ", " : "", a(`#/facility/${d}`, d)]) : "none"),
      h("dt", {}, "Names used in labels"), h("dd", {}, (f.spl_names.join("; ") || "—"), " ",
        h("span", { class: "note" }, "(shown for reference; never used to resolve identity)")),
      h("dt", {}, "Company role"), h("dd", {}, f.labeler_documents
        ? `Also the labeler on ${fmt(f.labeler_documents)} current labels. A labeler is a company role, not a factory, `
          + "and is not counted as manufacturing." : "Not a labeler in the current labels.")),
    h("h2", {}, "Documented operations"),
    h("p", {}, `MANUFACTURE: ${fmt(f.mfg_direct)} DIRECT, ${fmt(f.mfg_tentative)} TENTATIVE, ${fmt(f.mfg_unknown)} `
      + `UNKNOWN, covering ${fmt(f.mfg_products)} products. Other operations: `
      + (Object.entries(f.other_operations).map(([k, v]) => `${k} ${fmt(v)}`).join(", ") || "none") + "."),
    isExample ? null : h("p", { class: "note" }, "This export carries the MANUFACTURE assertions for this "
      + "establishment; other operations are counted above. For all operations run ",
      h("code", {}, `python -I scripts/fp.py facility ${duns} --operation all`), "."),
    h("dl", { class: "legend" }, Object.entries(CONFIDENCE).map(([k, v]) => [h("dt", {}, k), h("dd", {}, v)])),
    controls, count, tableBox,
    unresolvedSection(f, all, isExample),
  );
  redraw();
}

function edgeTable(rows) {
  return h("div", { class: "scroll", tabindex: "0", role: "region", "aria-label": "Operation assertions" },
    h("table", {},
      h("caption", { class: "sr-only" }, "Operation assertions naming this establishment, one row per graph edge"),
      h("thead", {}, h("tr", {}, ["Status", "Operation", "Product", "Package NDCs", "Labeler", "Label version",
        "Source"].map((c) => h("th", { scope: "col" }, c)))),
      h("tbody", {}, rows.map((r) => h("tr", {},
        h("td", {}, h("span", { class: `tag ${r.confidence.toLowerCase()}` }, r.confidence),
          r.reasons.length ? h("ul", { class: "reasons" }, r.reasons.map((x) => h("li", {}, REASONS[x] || x))) : null),
        h("td", {}, r.operation),
        h("td", {}, r.product_ndc_5_4
          ? [h("strong", { class: "nw" }, r.product_ndc_5_4), " ", r.product_name || "", h("br"), h("span", { class: "note" }, r.dosage_form || "")]
          : h("em", {}, "not tied to a product")),
        h("td", {}, packages(r.package_ndcs_11)),
        h("td", {}, (r.labelers || []).join("; ")),
        h("td", {}, a(links.label(r.set_id), `${r.set_id.slice(0, 8)}…`, true), ` v${r.version}`, h("br"),
          h("span", { class: "note" }, "published ", nw(r.published_date || "date unknown"))),
        h("td", {}, sourceDetails(r)))))));
}

const nw = (s) => h("span", { class: "nw" }, s);
const ndcs = (list) => list.map((n, i) => [i ? " " : "", nw(n)]);

function packages(list) {
  if (!list || !list.length) return "—";
  if (list.length <= 3) return ndcs(list);
  return h("details", {}, h("summary", {}, nw(list[0]), ` +${list.length - 1} more`), ndcs(list.slice(1)));
}

function sourceDetails(r) {
  return h("details", { class: "source" }, h("summary", {}, `evidence ${r.evidence_id}`),
    h("dl", {},
      h("dt", {}, "Set ID / version"), h("dd", {}, `${r.set_id} v${r.version} (${r.version_selection})`),
      h("dt", {}, "Document ID"), h("dd", {}, r.document_id),
      h("dt", {}, "XML location"), h("dd", {}, h("code", {}, r.xml_location)),
      h("dt", {}, "Operation product code"), h("dd", {}, `${r.operation_product_code || "none"} (${r.product_scope})`),
      h("dt", {}, "Release part / member"), h("dd", {}, `${r.source_part} → ${r.archive_member} → ${r.xml_member}`),
      h("dt", {}, "XML SHA-256"), h("dd", {}, h("code", {}, r.xml_sha256)),
      h("dt", {}, "Effective date"), h("dd", {}, r.effective_date || "—")),
    h("p", {}, a(links.label(r.set_id), "DailyMed label", true), " · ",
      a(links.versionZip(r.set_id, r.version), "this version (ZIP)", true), " · ",
      a(links.fdaXml(r.document_id), "FDA SPL XML by document ID", true), " · ",
      a(links.history(r.set_id), "version history", true)));
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
  return h("section", { "aria-labelledby": "missing" },
    h("h2", { id: "missing" }, "Missing or unresolved evidence"),
    f.status !== "CURRENT_REGISTERED" ? h("p", {}, h("strong", {}, "Identity: "), STATUS[f.status]) : null,
    counts.size
      ? h("ul", {}, [...counts].map(([k, ops]) => h("li", {}, REASONS[k] || k, " ",
          h("strong", {}, `(${[...ops].map(([op, n]) => `${op} ${fmt(n)}`).join(", ")})`))))
      : h("p", {}, "Every exported assertion for this establishment is DIRECT."),
    h("p", {}, "What this page cannot show:"),
    h("ul", {},
      h("li", {}, "Products whose labels name no establishment at all, or name this site under another DUNS. "
        + "Nationally, 23% of products come from labels with no establishment section."),
      h("li", {}, "Labels outside the loaded set (only human prescription labels in the dated release), and anything "
        + "published after it."),
      h("li", {}, "Volume, inventory, sole-source status or shortage risk. A documented manufacturing link is "
        + "exposure to a site, not a prediction that a product will be short."),
      isExample ? null : h("li", {}, "Packing, labeling and testing operations are counted but not listed here.")));
}

// ------------------------------------------------------------------------------------- historical case
async function caseStudy() {
  const [m, hist] = await Promise.all([load("manifest.json"), load("historical/rocky_mount_2023.json")]);
  setTitle("Rocky Mount, July 2023");
  const all = historicalRows(hist);
  const E = hist.metrics.E, M = hist.metrics.M;
  const pct = (x) => `${(100 * x).toFixed(1)}%`;
  const metricRow = (cohort, size, label, k) => h("tr", {},
    h("td", {}, cohort), h("th", { scope: "row" }, label), h("td", {}, fmt(k.N)),
    h("td", {}, `${k.X} / ${k.positives}`), h("td", {}, k.reduction_vs_B1 ? pct(k.reduction_vs_B1) : "—"));
  const state = { text: "", cls: "all", flagged: false, listed: false };
  const count = h("p", { "aria-live": "polite", class: "count" });
  const box = h("div");
  const filtered = () => all.filter((r) => (state.cls === "all" || r.classification === state.cls)
    && (!state.flagged || r.graph_flag) && (!state.listed || r.on_warning_list)
    && (!state.text || [r.package_ndc_11, r.product_ndc_raw, r.set_id, r.form].some((v) => v && v.toLowerCase().includes(state.text.toLowerCase()))));
  const redraw = () => {
    const rows = filtered();
    count.textContent = `${fmt(rows.length)} of ${fmt(all.length)} rows shown (one row per package and label version).`;
    box.replaceChildren(histTable(rows.slice(0, 500)),
      rows.length > 500 ? h("p", { class: "note" }, `Showing the first 500; the CSV has all ${fmt(rows.length)}.`) : "");
  };
  const classes = [...new Set(all.map((r) => r.classification))].sort();
  const pkgs = hist.packages.map((raw) => Object.fromEntries(hist.package_columns.map((c, i) => [c, raw[i]])));
  const srcIdx = hist.provenance_columns.indexOf("sources");
  const recovered = pkgs.filter((p) => p.graph_flag && p.on_warning_list);
  const archivalOnly = recovered.filter((p) => p.provenance.every((v) => !v[srcIdx].includes("A"))).length;
  const unknown = pkgs.filter((p) => p.classification.startsWith("UNKNOWN_")).length;
  const missed = pkgs.filter((p) => p.classification === "NOT_IN_COHORT").map((p) => p.package_ndc_11);
  show(
    h("p", {}, a("#/", "← Explorer home")),
    h("h1", {}, "Rocky Mount, July 2023: a historical replay"),
    banner("historical", m),
    h("p", {}, "On 2023-07-19 a tornado damaged Pfizer's Hospira plant in Rocky Mount, North Carolina "
      + `(DUNS ${hist.site.duns}, FEI ${hist.site.fei}). On July 21 Pfizer published a list of products it expected to `
      + "run low. The question tested here: using only labels published by the day before, could explicit "
      + "MANUFACTURE links to Rocky Mount have produced a shorter list to investigate than searching everything "
      + "Hospira sells, without missing the products Pfizer named?"),
    h("p", { class: "result" }, "fineprint turns fragmented FDA manufacturing records into an auditable "
      + "facility-to-drug graph. In a historical evaluation of Pfizer's 2023 Rocky Mount disruption, it identified "
      + "the same 63 publicly flagged NDCs as a company-wide search using a 46% shorter investigation list."),
    h("div", { class: "scroll", tabindex: "0", role: "region", "aria-label": "Benchmark" },
      h("table", {},
        h("caption", {}, "Candidates each method asks an investigator to check, and how many of Pfizer's 65 flagged "
          + "package NDCs are among them"),
        h("thead", {}, h("tr", {}, ["Cohort", "Method", "Candidates", "Flagged NDCs recovered", "Shorter than all-Hospira by"]
          .map((c) => h("th", { scope: "col" }, c)))),
        h("tbody", {},
          metricRow(`E (${fmt(hist.cohort_sizes.E)} packages)`, 0, "All Hospira 00409 packages (B1)", E.B1_all_hospira_00409),
          metricRow("E", 0, "Injectables only (B2)", E.B2_injectables),
          metricRow("E", 0, "fineprint: DIRECT Rocky Mount MANUFACTURE", E.graph_rocky_mount_direct),
          metricRow(`M (${fmt(hist.cohort_sizes.M)}, May 2023 FDA directory)`, 0, "All Hospira 00409 packages (B1)", M.B1_all_hospira_00409),
          metricRow("M", 0, "fineprint: DIRECT Rocky Mount MANUFACTURE", M.graph_rocky_mount_direct),
          h("tr", {}, h("td", {}, "both"), h("th", { scope: "row" }, "Already short before the event (B3)"),
            h("td", { colspan: "3" }, "not evaluable: no package-level shortage data published before the cutoff"))))),
    h("h2", {}, "What this does and does not show"),
    h("ul", {},
      h("li", {}, "It measures recall of a known warning list and the size of the list to investigate. It is not "
        + "shortage prediction and not a precision estimate."),
      h("li", {}, `${fmt(hist.flagged_not_listed.E)} flagged packages were not on Pfizer's list. They are not false `
        + "positives: the list covers low inventory after warehouse damage, not everything made at the plant."),
      h("li", {}, `The ${missed.length} missed NDCs (${missed.join(", ")}) are sterile empty vials, for which no drug `
        + "label exists, so no label-based method could find them."),
      h("li", {}, "Factory exposure is not shortage. A product with a documented Rocky Mount link may have other sites "
        + "or stock; a product without one may still depend on the plant through unlisted steps.")),
    h("h2", {}, "Limits of the archive"),
    h("ul", {},
      h("li", {}, "The 2023 label universe is not proven complete: DailyMed's all-labels-on-a-date export was not "
        + "obtained, and one label's pre-cutoff version could not be retrieved."),
      h("li", {}, `${archivalOnly} of the ${recovered.length} recovered NDCs appear only in retired labels that today's `
        + "DailyMed search does not return. They were recovered from FDA's SPL-by-document-ID store and a 2023 "
        + "monthly archive; without that step they would have been missed."),
      h("li", {}, `${unknown} of ${fmt(hist.cohort_sizes.E)} packages have no usable manufacturing evidence (no `
        + "establishment section, or no MANUFACTURE operation). None of Pfizer's NDCs fell in that group here; that "
        + "is a property of this event, not a guarantee."),
      h("li", {}, "Rocky Mount's identity rests on a 2022-10-13 FDA registration record and a 2015 facility filing; "
        + "its 2023 registration status is not established.")),
    h("h2", {}, "Every package in the frozen cohort"),
    h("form", { class: "controls", onsubmit: (e) => e.preventDefault() },
      h("div", {}, h("label", { for: "hq" }, "Filter by NDC, set ID or form"),
        h("input", { id: "hq", type: "search", oninput: (e) => { state.text = e.target.value.trim(); redraw(); } })),
      h("div", {}, h("label", { for: "hc" }, "Classification"),
        h("select", { id: "hc", onchange: (e) => { state.cls = e.target.value; redraw(); } },
          h("option", { value: "all" }, "all"), classes.map((c) => h("option", { value: c }, c)))),
      h("fieldset", {}, h("legend", {}, "Show only"),
        h("label", { class: "check" }, h("input", { type: "checkbox", onchange: (e) => { state.flagged = e.target.checked; redraw(); } }), " flagged by fineprint"),
        h("label", { class: "check" }, h("input", { type: "checkbox", onchange: (e) => { state.listed = e.target.checked; redraw(); } }), " on Pfizer's list")),
      h("div", {}, h("button", { type: "button", onclick: () => download("fineprint_rocky_mount_2023.csv",
        toCSV(HISTORICAL_CSV_COLUMNS, filtered())) }, "Download CSV of shown rows"))),
    h("dl", { class: "legend" },
      h("dt", {}, "DIRECT"), h("dd", {}, "The pre-cutoff label lists MANUFACTURE at Rocky Mount for this product. Flagged."),
      h("dt", {}, "OTHER_SITE"), h("dd", {}, "MANUFACTURE is listed only at other sites."),
      h("dt", {}, "RM_SECONDARY_ONLY"), h("dd", {}, "Rocky Mount appears only for packing, labeling or testing."),
      h("dt", {}, "UNKNOWN_*"), h("dd", {}, "The label has no establishment section, or no MANUFACTURE operation for it."),
      h("dt", {}, "NOT_IN_COHORT"), h("dd", {}, "On Pfizer's list, but no admissible pre-cutoff label was found.")),
    count, box,
    h("h2", {}, "Seal and sources"),
    h("p", {}, `Frozen inputs are tagged `, h("code", {}, hist.seal.tag), ` (manifest SHA-256 `,
      h("code", {}, hist.seal.manifest_sha256.slice(0, 16) + "…"), `). The outcome list was retrieved from `,
      a(hist.outcome.url, "fda.gov", true), ` after the freeze; it is not redistributed here. Full method: `,
      a(`${REPO}/blob/main/docs/EVALUATION_REPORT.md`, "evaluation report", true), " and ",
      a(`${REPO}/blob/main/docs/historical_panel_plan.md`, "pre-registered plan", true), "."),
  );
  redraw();
}

function histTable(rows) {
  return h("div", { class: "scroll", tabindex: "0", role: "region", "aria-label": "Historical cohort" },
    h("table", {},
      h("caption", { class: "sr-only" }, "Frozen 2023 cohort, one row per package and label version"),
      h("thead", {}, h("tr", {}, ["Package NDC", "Classification", "fineprint flag", "On Pfizer list",
        "In May 2023 directory", "Form", "Label version (published ≤ cutoff)", "Rocky Mount MANUFACTURE element"]
        .map((c) => h("th", { scope: "col" }, c)))),
      h("tbody", {}, rows.map((r) => h("tr", {},
        h("td", {}, h("strong", { class: "nw" }, r.package_ndc_11)),
        h("td", {}, r.classification, r.note ? [h("br"), h("span", { class: "note" }, r.note)] : null),
        h("td", {}, r.graph_flag ? "flagged" : "—"),
        h("td", {}, r.on_warning_list ? "yes" : "—"),
        h("td", {}, r.in_may_2023_listing == null ? "—" : r.in_may_2023_listing ? "yes" : "no"),
        h("td", {}, r.form || "—"),
        h("td", {}, r.set_id ? [a(r.document_url, `${r.set_id.slice(0, 8)}… v${r.version}`, true), h("br"),
          h("span", { class: "note" }, nw(r.published_date), ` · ${r.document_kind}`)] : "—"),
        h("td", {}, r.rocky_mount_manufacture_locs.length
          ? h("details", {}, h("summary", {}, "XML location"), h("code", {}, r.rocky_mount_manufacture_locs.join(" ")))
          : "—"))))));
}

// ------------------------------------------------------------------------------------------------ about
async function about() {
  const m = await load("manifest.json");
  const c = m.datasets.current, hd = m.datasets.historical;
  setTitle("About the data");
  show(
    h("h1", {}, "About the data"),
    h("p", {}, h("strong", {}, m.attribution + ". "), m.currency),
    h("p", {}, m.independence),
    h("h2", {}, "Current-release graph"),
    h("ul", {},
      h("li", {}, `DailyMed human prescription SPL release ${c.dailymed_release}: ${c.release_parts.length} parts, `
        + `SHA-256 recorded below; ${c.daily_updates_applied} daily updates applied.`),
      h("li", {}, `FDA establishment registration (DECRS) files as of ${c.fda_registration_as_of}, plus dated `
        + "archived files used to mark identities as stale."),
      h("li", {}, `Graph build ${c.graph_build.build_id}, rules ${c.graph_build.rule_version}, code `,
        a(`${REPO}/commit/${c.graph_build.code_commit}`, c.graph_build.code_commit.slice(0, 7), true),
        `, finished ${c.graph_build.finished_at}.`),
      h("li", {}, `Exported: ${c.scope}. Not exported: ${c.not_exported.join("; ")}.`)),
    h("div", { class: "scroll", tabindex: "0", role: "region", "aria-label": "Release parts" },
      h("table", {}, h("caption", {}, "Release parts"),
        h("thead", {}, h("tr", {}, ["File", "Bytes", "SHA-256"].map((x) => h("th", { scope: "col" }, x)))),
        h("tbody", {}, c.release_parts.map((p) => h("tr", {}, h("td", {}, a(p.url, p.name, true)),
          h("td", {}, fmt(p.bytes)), h("td", {}, h("code", {}, p.sha256))))))),
    h("h2", {}, "Historical replay"),
    h("p", {}, hd.description),
    h("ul", {}, Object.entries(hd.inputs).map(([p, s]) => h("li", {}, a(`${REPO}/blob/main/${p}`, p, true), " ",
      h("code", {}, s.slice(0, 16) + "…")))),
    h("h2", {}, "How these files were made"),
    h("p", {}, "Generated by ", a(`${REPO}/blob/main/${m.generated_by.script}`, m.generated_by.script, true),
      ` from the PostgreSQL graph and the committed evidence. ${m.generated_by.deterministic}; re-running the export `
      + "on the same database reproduces every data file byte for byte. ", m.csv),
    h("p", {}, m.privacy),
    h("p", {}, a("data/manifest.json", "Download the manifest"), " (every file with its SHA-256 and row count). ",
      `Code license: ${m.license.code}. ${m.license.data}`),
  );
}

// ---------------------------------------------------------------------------------------------- router
async function route() {
  const hash = location.hash.replace(/^#\/?/, "");
  const [view, arg] = hash.split("/");
  show(h("p", { class: "note" }, "Loading…"));
  try {
    if (view === "facility" && /^\d{9}$/.test(arg || "")) await facility(arg);
    else if (view === "rocky-mount-2023") await caseStudy();
    else if (view === "about") await about();
    else await home();
  } catch (err) {
    show(h("h1", {}, "Could not load the data"), h("p", {}, String(err.message || err)));
  }
  document.querySelectorAll("nav a").forEach((l) => l.toggleAttribute("aria-current",
    l.getAttribute("href") === `#/${view || ""}` || (view === "facility" && l.getAttribute("href") === "#/")));
  main.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", route);
route();
