// Pure functions shared by the browser (app.js) and the verification script
// (scripts/verify_explorer_csv.py runs them under Node). No DOM, no network.

export const DAILYMED = "https://dailymed.nlm.nih.gov/dailymed";

export const links = {
  label: (setId) => `${DAILYMED}/drugInfo.cfm?setid=${setId}`,
  versionZip: (setId, v) => `${DAILYMED}/getFile.cfm?type=zip&setid=${setId}&version=${v}`,
  history: (setId) => `${DAILYMED}/services/v2/spls/${setId}/history.json`,
  fdaXml: (docId) => `https://www.accessdata.fda.gov/spl/data/${docId}/${docId}.xml`,
};

// Plain-language meaning of every reason code the graph can attach to an edge (src/fineprint/graph.py).
export const REASONS = {
  "spl:no_duns": "The label names the establishment without a DUNS number.",
  "scope:no_product_scope": "The label states the operation without saying which product it covers.",
  "scope:unmatched_code": "The operation names a product code that matches no product in the label.",
  "identity:NOT_FOUND": "This DUNS is in none of the loaded FDA registration files, so no physical site is resolved.",
  "identity:STALE_REGISTERED": "This DUNS is listed only in an older FDA registration file, not the current one.",
  "identity:CURRENT_REGISTERED_NO_FEI": "The current FDA registration file lists this DUNS without an FEI.",
  "identity:CURRENT_EXCLUDED": "This DUNS is in FDA's excluded-registrations file.",
  "identity:AMBIGUOUS_MULTIPLE_FEI": "This DUNS is listed with more than one FEI.",
  "identity:registration_expired": "The registration line used has passed its expiration date.",
  "identity:fei_changed_across_snapshots": "The FEI listed for this DUNS differs between registration files.",
  "version_selection:ambiguous": "The release holds conflicting candidates for this label's current version.",
};

export const STATUS = {
  CURRENT_REGISTERED: "Listed in the current FDA registration file with an FEI and address.",
  CURRENT_REGISTERED_NO_FEI: "Listed in the current FDA registration file, but without an FEI.",
  CURRENT_EXCLUDED: "Listed in FDA's excluded-registrations file.",
  STALE_REGISTERED: "Not in the current FDA registration file; found only in an older, dated file.",
  AMBIGUOUS_MULTIPLE_FEI: "Listed with more than one FEI; no single site is chosen.",
  NOT_FOUND: "Not found in any loaded FDA registration file. Labels name it, but no physical site is resolved.",
};

export const CONFIDENCE = {
  DIRECT: "The label names this DUNS for this product, and the DUNS resolves to a currently registered FEI.",
  TENTATIVE: "The label names this DUNS for this product, but the identity or label version has a caveat.",
  UNKNOWN: "An operation is asserted, but the site or the product it covers cannot be resolved.",
};

export function record(columns, row) {
  const o = {};
  columns.forEach((c, i) => { o[c] = row[i]; });
  return o;
}

export function facilityIndex(index) {
  const byDuns = new Map();
  for (const row of index.rows) byDuns.set(row[0], record(index.columns, row));
  return byDuns;
}

export function shardOf(duns) {
  return duns.slice(0, 2);
}

// One flat row per graph edge (operation assertion) naming `duns`, joined with its product and label version.
export function facilityRows(bundle, fac) {
  const out = [];
  for (const raw of bundle.edges) {
    const e = record(bundle.edge_columns, raw);
    if (e.duns !== fac.duns) continue;
    const p = e.product == null ? null : record(bundle.product_columns, bundle.products[String(e.product)]);
    const d = record(bundle.document_columns, bundle.documents[e.set_id]);
    out.push({
      evidence_id: e.evidence_id, confidence: e.confidence, reasons: e.reasons, operation: e.operation,
      establishment_duns: e.duns, identity_status: fac.status, fei: fac.fei,
      registered_firm_name: fac.firm_name, registered_address: fac.address,
      product_ndc_5_4: p ? p.ndc_5_4 : null, product_ndc_raw: p ? p.ndc_raw : null,
      product_name: p ? p.name : null, dosage_form: p ? p.dosage_form : null,
      package_ndcs_11: p ? p.packages_11 : [], labelers: d.labelers,
      set_id: e.set_id, version: d.version, document_id: d.document_id, published_date: d.published_date,
      effective_date: d.effective_date, version_selection: d.selection_class, product_scope: e.scope,
      operation_product_code: e.operation_product_code, xml_location: e.loc, source_part: d.part,
      archive_member: d.member, xml_member: d.xml_member, xml_sha256: d.xml_sha256,
    });
  }
  return out;
}

export const CURRENT_CSV_COLUMNS = [
  "evidence_id", "confidence", "reasons", "operation", "establishment_duns", "identity_status", "fei",
  "registered_firm_name", "registered_address", "product_ndc_5_4", "product_ndc_raw", "product_name",
  "dosage_form", "package_ndcs_11", "labelers", "set_id", "version", "document_id", "published_date",
  "effective_date", "version_selection", "product_scope", "operation_product_code", "xml_location",
  "source_part", "archive_member", "xml_member", "xml_sha256", "dailymed_label_url", "fda_spl_xml_url",
];

export function currentCsvRow(r) {
  return { ...r, dailymed_label_url: links.label(r.set_id), fda_spl_xml_url: links.fdaXml(r.document_id) };
}

// One row per (package, label version) in the frozen historical cohort.
export function historicalRows(hist) {
  const out = [];
  for (const raw of hist.packages) {
    const p = record(hist.package_columns, raw);
    const provs = p.provenance.length ? p.provenance : [null];
    for (const pv of provs) {
      const v = pv ? record(hist.provenance_columns, pv) : {};
      out.push({
        package_ndc_11: p.package_ndc_11, classification: p.classification, graph_flag: p.graph_flag,
        on_warning_list: p.on_warning_list, in_may_2023_listing: p.in_may_2023_listing, b2: p.b2,
        set_id: v.set_id ?? null, version: v.version ?? null, product_ndc_raw: v.product_ndc_raw ?? null,
        package_ndc_raw: v.package_ndc_raw ?? null, form: v.form ?? null, routes: v.routes ?? [],
        sources: v.sources ?? null, manufacture_duns: v.manufacture_duns ?? [],
        rocky_mount_manufacture_locs: v.rocky_mount_manufacture_locs ?? [], document_kind: v.document_kind ?? null,
        document_url: v.document_url ?? null, published_date: v.published_date ?? null,
        effective_time: v.effective_time ?? null, xml_sha256: v.xml_sha256 ?? null, note: p.note,
      });
    }
  }
  return out;
}

export const HISTORICAL_CSV_COLUMNS = [
  "package_ndc_11", "classification", "graph_flag", "on_warning_list", "in_may_2023_listing", "b2", "set_id",
  "version", "product_ndc_raw", "package_ndc_raw", "form", "routes", "sources", "manufacture_duns",
  "rocky_mount_manufacture_locs", "document_kind", "document_url", "published_date", "effective_time",
  "xml_sha256", "note",
];

export function cell(v) {
  if (v == null) return "";
  let s = Array.isArray(v) ? v.join("; ") : String(v);
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s; // stop spreadsheet formula execution
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function toCSV(columns, rows) {
  const lines = [columns.join(",")];
  for (const r of rows) lines.push(columns.map((c) => cell(r[c])).join(","));
  return lines.join("\r\n") + "\r\n";
}

export function matches(r, text) {
  if (!text) return true;
  const t = text.toLowerCase();
  return [r.product_ndc_5_4, r.product_ndc_raw, r.product_name, r.dosage_form, r.set_id, r.document_id,
          (r.labelers || []).join(" "), (r.package_ndcs_11 || []).join(" "), String(r.evidence_id)]
    .some((v) => v != null && String(v).toLowerCase().includes(t));
}
