-- DST-08 research prototype, rule dst08-lineage-v2: the version-aware physical check, applied ONLY to a scratch
-- database by fineprint.lineage.validate_v2 after a lineage build. It reads the v1 tables and never changes them, so
-- the v1 counts and evidence stay measurable beside v2. No national row is changed.

DROP VIEW IF EXISTS lineage.v_product_coverage_v2;
DROP TABLE IF EXISTS lineage.source_linked_evidence_v2, lineage.resolution_v2, lineage.version_check,
    lineage.source_version_document, lineage.validation_v2;

CREATE TABLE lineage.validation_v2 (
    validation_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at        timestamptz NOT NULL DEFAULT now(),
    finished_at       timestamptz,
    status            text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed')),
    rule_version      text NOT NULL,
    build_id          bigint NOT NULL REFERENCES lineage.build,    -- the v1 build it reads
    manifest_sha256   text NOT NULL,                               -- the frozen history manifest
    outputs           jsonb NOT NULL DEFAULT '{}'
);

-- Every historical label version in the manifest, with its own provenance (DailyMed version archive).
CREATE TABLE lineage.source_version_document (
    set_id          text NOT NULL,
    version         integer NOT NULL,
    published_at    date,              -- DailyMed history service
    status          text NOT NULL,     -- ok, or why the version could not be used
    url             text,
    retrieved_at    text,
    zip_sha256      text,
    xml_sha256      text,
    document_id     text,
    effective_time  text,
    PRIMARY KEY (set_id, version)
);

-- One row per v1-eligible reference whose citing and current source labels state a conflicting characteristic.
CREATE TABLE lineage.version_check (
    reference_pk              bigint PRIMARY KEY REFERENCES lineage.source_reference,
    citing_ndc                text NOT NULL,
    citing_set_id             text NOT NULL,
    citing_version            integer NOT NULL,
    citing_published_at       date,              -- the relevant date D
    citing_date_basis         text NOT NULL,     -- dailymed_history, release_metadata or unknown
    source_code_cited         text NOT NULL,
    source_ndc                text NOT NULL,     -- the source product's own code in the release
    source_set_id             text NOT NULL,
    source_version_now        integer NOT NULL,
    source_published_now      date,
    source_history_status     text NOT NULL,
    applicable_version        integer,           -- latest source version published on or before D
    applicable_published_at   date,
    applicable_document_id    text,
    applicable_xml_sha256     text,
    conflicting               text[] NOT NULL,   -- characteristics that differ in the current release
    citing_characteristics    jsonb NOT NULL,
    applicable_characteristics jsonb,
    at_applicable             jsonb,             -- per characteristic, citing against the applicable version
    at_current                jsonb NOT NULL,    -- per characteristic, citing against the current source label
    sites_at_applicable       text[],            -- DUNS with MANUFACTURE scoped to the cited code in the applicable version
    sites_now_direct          text[] NOT NULL,   -- the source product's current DIRECT MANUFACTURE DUNS
    continuing_sites          text[],
    versions_matching         integer[] NOT NULL,     -- other source versions the citing description matches
    versions_unretrievable    integer[] NOT NULL,
    canonical_xml_matches_release boolean,       -- the archive's copy of the release version is byte-identical
    classification            text NOT NULL CHECK (classification IN ('NOTATION_ONLY', 'VERSION_DRIFT_RESOLVED',
                                  'MULTIPLE_VALID_PRESENTATIONS', 'MISSING_COMPARISON_EVIDENCE', 'UNRESOLVED_AMBIGUITY',
                                  'CONFIRMED_CONFLICT')),
    detail                    text NOT NULL
);

-- Every reference under rule v2. A reference without a version check keeps its v1 status and reasons.
CREATE TABLE lineage.resolution_v2 (
    reference_pk  bigint PRIMARY KEY REFERENCES lineage.source_reference,
    status        text NOT NULL CHECK (status IN ('ELIGIBLE', 'EXCLUDED')),
    reasons       text[] NOT NULL,
    basis         text NOT NULL CHECK (basis IN ('v1', 'version_check'))
);

-- SOURCE_LINKED_MANUFACTURING_EVIDENCE under v2: the v1 rows of v2-eligible references; for a reference that passed the
-- version check, only the sites the source named both when the citing label was published and now.
CREATE TABLE lineage.source_linked_evidence_v2 (
    reference_pk         bigint NOT NULL REFERENCES lineage.source_reference,
    source_assertion_pk  bigint NOT NULL REFERENCES national.operation_edge,
    linked_product_pk    bigint NOT NULL REFERENCES national.product,
    source_product_pk    bigint NOT NULL REFERENCES national.product,
    duns                 text NOT NULL,
    PRIMARY KEY (reference_pk, source_assertion_pk)
);
CREATE INDEX source_linked_evidence_v2_product ON lineage.source_linked_evidence_v2 (linked_product_pk);

CREATE VIEW lineage.v_product_coverage_v2 AS
SELECT s.product_pk, s.set_id, s.version, s.ndc_raw, s.ndc_product_5_4,
       s.manufacturing_status AS direct_tier_status,
       CASE WHEN s.manufacturing_status = 'DIRECT' THEN 'DIRECT'
            WHEN EXISTS (SELECT 1 FROM lineage.source_linked_evidence_v2 e WHERE e.linked_product_pk = s.product_pk)
                 THEN 'SOURCE_LINKED'
            ELSE s.manufacturing_status END AS coverage_tier
FROM national.v_product_manufacturing_status s;
