-- DST-02: current-version selection, dated facility identity, provenance graph projection.
-- Additive only: no DST-01 table or row is dropped or rewritten.

-- Registration evidence (FDA DECRS) joins the current-era sources; still role 'current' only.
ALTER TABLE national.source_file DROP CONSTRAINT source_file_kind_check;
ALTER TABLE national.source_file ADD CONSTRAINT source_file_kind_check CHECK (kind IN (
    'dailymed_human_rx_full_part', 'dailymed_zip_metadata',
    'fda_decrs_registration', 'fda_decrs_excluded', 'fda_decrs_registration_archived'));
ALTER TABLE national.source_file ADD COLUMN generated_at timestamptz;        -- publisher file timestamp (zip member mtime)
ALTER TABLE national.source_file ADD COLUMN captured_at timestamptz;         -- third-party archive capture time
ALTER TABLE national.source_file ADD COLUMN archive_digest_sha1_b32 text;    -- archive CDX digest, verified on load

-- DECRS rows. Contact names/emails and agent details are deliberately NOT stored.
CREATE TABLE national.registration_record (
    registration_pk      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_file_id       bigint NOT NULL REFERENCES national.source_file,
    line_no              integer NOT NULL,
    fei                  text,
    duns                 text,
    firm_name            text,
    address              text,
    expiration_date_raw  text,
    expiration_date      date,
    operations_raw       text,
    registrant_name      text,
    registrant_duns      text,
    exclusion_flag       text,
    UNIQUE (source_file_id, line_no)
);
CREATE INDEX registration_record_duns ON national.registration_record (duns);
CREATE INDEX registration_record_fei ON national.registration_record (fei);

-- One row per projection build; projection tables hold the latest build only.
CREATE TABLE national.graph_build (
    build_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    status        text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    rule_version  text NOT NULL,
    code_commit   text,
    code_dirty    boolean,
    inputs        jsonb NOT NULL DEFAULT '{}',
    outputs       jsonb NOT NULL DEFAULT '{}'
);

-- Canonical current version per set. All raw versions stay in spl_document.
CREATE TABLE national.set_version_selection (
    set_key               text PRIMARY KEY,            -- lower(set_id)
    set_id                text NOT NULL,
    document_pk           bigint REFERENCES national.spl_document,   -- NULL only when unresolved
    selected_version      integer,
    versions_in_release   integer[] NOT NULL,
    n_documents           integer NOT NULL,
    metadata_version      integer,                     -- official zip-metadata current version (NULL = set not listed)
    metadata_upload_date  date,
    selection_status      text NOT NULL CHECK (selection_status IN (
        'SINGLE_VERSION_METADATA_CONFIRMED', 'MULTI_VERSION_METADATA_SELECTED',
        'SINGLE_VERSION_NOT_IN_METADATA', 'SINGLE_VERSION_METADATA_LISTS_OTHER',
        'MULTI_VERSION_HIGHEST_NO_METADATA', 'MULTI_VERSION_HIGHEST_METADATA_LISTS_OTHER',
        'UNRESOLVED_SAME_VERSION_CONFLICT')),
    selection_class       text NOT NULL CHECK (selection_class IN ('confirmed', 'unconfirmed', 'ambiguous', 'unresolved')),
    published_date        date,                        -- of the selected document; official metadata only
    build_id              bigint NOT NULL REFERENCES national.graph_build,
    CHECK ((selection_class = 'unresolved') = (document_pk IS NULL))
);
CREATE INDEX set_version_selection_doc ON national.set_version_selection (document_pk);

-- Identity of every establishment DUNS seen in canonical documents, from dated registration evidence.
CREATE TABLE national.duns_identity (
    duns                     text PRIMARY KEY,
    status                   text NOT NULL CHECK (status IN (
        'CURRENT_REGISTERED', 'CURRENT_REGISTERED_NO_FEI', 'CURRENT_EXCLUDED',
        'STALE_REGISTERED', 'AMBIGUOUS_MULTIPLE_FEI', 'NOT_FOUND')),
    fei                      text,
    registration_pk          bigint REFERENCES national.registration_record,  -- evidence row used
    evidence_source_file_id  bigint REFERENCES national.source_file,
    evidence_as_of           date,          -- publisher generation date of that registration file
    evidence_expiration      date,
    firm_name                text,
    address                  text,
    fei_history              jsonb NOT NULL DEFAULT '[]',   -- [{as_of, fei, address}] across all loaded snapshots
    fei_changed              boolean NOT NULL DEFAULT false,
    duns_sharing_fei         integer,       -- DUNS listed with this FEI in the evidence snapshot
    spl_names                text[] NOT NULL DEFAULT '{}',  -- informational only; never used to resolve
    build_id                 bigint NOT NULL REFERENCES national.graph_build
);
CREATE INDEX duns_identity_fei ON national.duns_identity (fei);

-- Physical facilities keyed by FDA Establishment Identifier.
CREATE TABLE national.facility (
    fei               text PRIMARY KEY,
    duns              text[] NOT NULL,
    firm_names        text[] NOT NULL,
    addresses         text[] NOT NULL,
    current_registered boolean NOT NULL,
    build_id          bigint NOT NULL REFERENCES national.graph_build
);

-- product -> operation -> DUNS -> facility, one edge per operation assertion in a canonical document.
CREATE TABLE national.operation_edge (
    assertion_pk        bigint PRIMARY KEY REFERENCES national.operation_assertion,
    document_pk         bigint NOT NULL REFERENCES national.spl_document,
    set_id              text NOT NULL,
    version             integer NOT NULL,
    selection_class     text NOT NULL,
    product_pk          bigint REFERENCES national.product,      -- NULL = operation not scoped to a product
    report_product_pk   bigint REFERENCES national.product,      -- kit part -> its kit product; else = product_pk
    product_scope       text NOT NULL,
    product_ndc_raw     text,
    product_ndc_5_4     text,
    operation_code      text NOT NULL,
    operation_name      text NOT NULL,
    is_manufacture      boolean NOT NULL,                        -- operation_code = 'C43360' only
    duns                text,                                    -- NULL = establishment given without DUNS
    identity_status     text NOT NULL,
    fei                 text,
    confidence          text NOT NULL CHECK (confidence IN ('DIRECT', 'TENTATIVE', 'UNKNOWN')),
    confidence_reasons  text[] NOT NULL,
    loc                 text NOT NULL,
    build_id            bigint NOT NULL REFERENCES national.graph_build
);
CREATE INDEX operation_edge_duns ON national.operation_edge (duns, is_manufacture);
CREATE INDEX operation_edge_fei ON national.operation_edge (fei);
CREATE INDEX operation_edge_product ON national.operation_edge (report_product_pk);
CREATE INDEX operation_edge_ndc ON national.operation_edge (product_ndc_5_4);

-- Manufacturing status of every product in a canonical document (kit parts roll up to their kit).
CREATE VIEW national.v_product_manufacturing_status AS
SELECT p.product_pk, s.set_id, s.selected_version AS version, s.selection_class, p.ndc_raw, p.ndc_product_5_4, p.name,
       CASE
         WHEN bool_or(e.confidence = 'DIRECT')    THEN 'DIRECT'
         WHEN bool_or(e.confidence = 'TENTATIVE') THEN 'TENTATIVE'
         WHEN bool_or(e.confidence = 'UNKNOWN')   THEN 'UNKNOWN_SITE'
         ELSE 'NO_MANUFACTURE_EVIDENCE'
       END AS manufacturing_status,
       count(DISTINCT e.duns) FILTER (WHERE e.is_manufacture) AS manufacture_duns,
       v.evidence_status
FROM national.set_version_selection s
JOIN national.product p ON p.document_pk = s.document_pk AND p.kind = 'product'
JOIN national.v_product_establishment_evidence v ON v.product_pk = p.product_pk
LEFT JOIN national.operation_edge e ON e.report_product_pk = p.product_pk AND e.is_manufacture
GROUP BY p.product_pk, s.set_id, s.selected_version, s.selection_class, p.ndc_raw, p.ndc_product_5_4, p.name,
         v.evidence_status;
