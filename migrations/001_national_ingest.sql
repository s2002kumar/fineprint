-- DST-01: CURRENT national ingest of DailyMed human-Rx full-release parts.
-- Schema "national" holds current-release sources ONLY (enforced by CHECK on source_role).
-- Historical (pre-2023-07-18) evidence never enters this schema.
-- Rows are raw assertions with citations; no facility identity resolution happens here (DST-02).

CREATE SCHEMA IF NOT EXISTS national;

CREATE TABLE national.source_file (
    source_file_id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kind                    text NOT NULL CHECK (kind IN ('dailymed_human_rx_full_part', 'dailymed_zip_metadata')),
    source_role             text NOT NULL CHECK (source_role = 'current'),
    name                    text NOT NULL,
    url                     text NOT NULL,
    release_label           text NOT NULL,          -- advertised Last Modified of the release, e.g. 2026-10-16
    advertised_md5          text,
    advertised_files        integer,
    advertised_size         text,
    etag                    text,
    http_last_modified      text,
    content_length          bigint NOT NULL,
    bytes                   bigint NOT NULL,
    sha256                  text NOT NULL UNIQUE,
    md5                     text NOT NULL,
    md5_matches_advertised  boolean,
    retrieved_started_at    timestamptz,
    retrieved_completed_at  timestamptz NOT NULL,
    local_path              text NOT NULL,          -- relative to $FINEPRINT_DATA, never inside the repo
    registered_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE national.ingest_run (
    run_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz,
    status       text NOT NULL DEFAULT 'running'
                 CHECK (status IN ('running', 'completed', 'completed_with_failures', 'interrupted', 'failed')),
    code_commit  text,
    code_dirty   boolean,
    python       text,
    platform     text,
    args         jsonb NOT NULL DEFAULT '{}',
    stats        jsonb NOT NULL DEFAULT '{}'
);

-- Official DailyMed per-zip metadata (UPLOAD_DATE is the documented publication date source).
CREATE TABLE national.dailymed_zip_metadata (
    source_file_id   bigint NOT NULL REFERENCES national.source_file,
    zip_file_name    text NOT NULL,
    set_id           text NOT NULL,
    spl_version      integer,
    upload_date_raw  text,
    upload_date      date,
    title            text,
    PRIMARY KEY (source_file_id, zip_file_name)
);

CREATE TABLE national.spl_document (
    document_pk             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    set_id                  text NOT NULL,
    version                 integer NOT NULL,
    document_id             text,
    document_type_code      text,
    document_type_name      text,
    effective_time_raw      text,
    effective_date          date,
    xml_sha256              text NOT NULL,
    xml_bytes               integer NOT NULL,
    source_file_id          bigint NOT NULL REFERENCES national.source_file,   -- first source seen in
    member_name             text NOT NULL,
    xml_member_name         text NOT NULL,
    member_name_date        date,           -- YYYYMMDD filename prefix; semantics undocumented, NOT a publication date
    published_date          date,           -- from dailymed_zip_metadata.upload_date only; NULL = unknown
    published_date_source   text,
    has_establishment_block boolean NOT NULL,
    n_products              integer NOT NULL,
    n_packages              integer NOT NULL,
    n_establishments        integer NOT NULL,
    n_operation_assertions  integer NOT NULL,
    anomalies               jsonb NOT NULL DEFAULT '[]',
    first_run_id            bigint NOT NULL REFERENCES national.ingest_run,
    UNIQUE (set_id, version, xml_sha256)
);
CREATE INDEX spl_document_set_version ON national.spl_document (set_id, version);

-- Processing state per archive member: the unit of resume and of failure isolation.
CREATE TABLE national.archive_member (
    source_file_id  bigint NOT NULL REFERENCES national.source_file,
    member_name     text NOT NULL,
    member_index    integer NOT NULL,
    member_bytes    bigint NOT NULL,
    member_sha256   text,
    status          text NOT NULL CHECK (status IN ('loaded', 'duplicate', 'failed')),
    document_pk     bigint REFERENCES national.spl_document,
    run_id          bigint NOT NULL REFERENCES national.ingest_run,
    processed_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_file_id, member_name),
    CHECK ((status = 'failed') = (document_pk IS NULL))
);

CREATE TABLE national.dead_letter (
    dead_letter_pk  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id          bigint NOT NULL REFERENCES national.ingest_run,
    source_file_id  bigint NOT NULL REFERENCES national.source_file,
    member_name     text NOT NULL,
    member_sha256   text,
    stage           text NOT NULL CHECK (stage IN ('outer_member', 'nested_zip', 'xml', 'db_insert')),
    error_kind      text NOT NULL,
    error_detail    text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_file_id, member_name)
);

-- Organizations exactly as they appear in a document's author hierarchy.
-- role 'labeler' is a company, never a facility; only 'establishment' rows carry operations.
CREATE TABLE national.organization_mention (
    org_pk       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_pk  bigint NOT NULL REFERENCES national.spl_document ON DELETE CASCADE,
    loc          text NOT NULL,
    role         text NOT NULL,
    depth        smallint NOT NULL,
    name         text,
    duns         text,                    -- first DUNS id; NULL = no DUNS given
    duns_all     text[] NOT NULL,
    fei_all      text[] NOT NULL,
    ids          jsonb NOT NULL,
    address      jsonb,
    UNIQUE (document_pk, loc)
);
CREATE INDEX organization_mention_duns ON national.organization_mention (duns);
CREATE INDEX organization_mention_role ON national.organization_mention (role);

-- Products and kit parts. ndc_product_5_4 is the normalized PRODUCT code; packages live elsewhere.
CREATE TABLE national.product (
    product_pk         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_pk        bigint NOT NULL REFERENCES national.spl_document ON DELETE CASCADE,
    parent_product_pk  bigint REFERENCES national.product ON DELETE CASCADE,
    kind               text NOT NULL CHECK (kind IN ('product', 'kit_part')),
    loc                text NOT NULL,
    ndc_raw            text,
    ndc_code_system    text,
    ndc_pattern        text,
    ndc_product_5_4    text,
    name               text,
    generic_name       text,
    dosage_form        text,
    routes             text[] NOT NULL DEFAULT '{}',
    approvals          jsonb NOT NULL DEFAULT '[]',
    marketing          jsonb NOT NULL DEFAULT '[]',
    section_code       text,
    UNIQUE (document_pk, loc),
    CHECK ((kind = 'kit_part') = (parent_product_pk IS NOT NULL))
);
CREATE INDEX product_ndc_5_4 ON national.product (ndc_product_5_4);
CREATE INDEX product_ndc_raw ON national.product (ndc_raw);
CREATE INDEX product_document ON national.product (document_pk);

-- Packages. ndc_package_5_4_2 is the normalized 11-digit PACKAGE code.
CREATE TABLE national.package (
    package_pk                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_pk               bigint NOT NULL REFERENCES national.spl_document ON DELETE CASCADE,
    product_pk                bigint NOT NULL REFERENCES national.product ON DELETE CASCADE,
    loc                       text NOT NULL,
    level                     smallint NOT NULL,
    ndc_raw                   text,
    ndc_pattern               text,
    ndc_package_5_4_2         text,
    contains_ndc_raw          text,
    form                      text,
    quantity_value            text,
    quantity_unit             text,
    marketing                 jsonb NOT NULL DEFAULT '[]',
    segments_match_product    boolean,       -- raw first-two-segment check against its product; NULL if a code is missing
    UNIQUE (document_pk, loc)
);
CREATE INDEX package_ndc_11 ON national.package (ndc_package_5_4_2);
CREATE INDEX package_ndc_raw ON national.package (ndc_raw);
CREATE INDEX package_product ON national.package (product_pk);

-- One row per (performance element, product code, DUNS): the raw operation assertion.
CREATE TABLE national.operation_assertion (
    assertion_pk           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_pk            bigint NOT NULL REFERENCES national.spl_document ON DELETE CASCADE,
    establishment_org_pk   bigint NOT NULL REFERENCES national.organization_mention ON DELETE CASCADE,
    duns                   text,             -- NULL = establishment without DUNS: identity UNKNOWN
    operation_code         text,             -- raw NCI code; the normalization key
    operation_name_raw     text,             -- verbatim displayName (case/whitespace vary)
    product_code_raw       text,             -- NULL = operation not scoped to any product
    product_code_system    text,
    product_code_5_4       text,
    product_pk             bigint REFERENCES national.product ON DELETE CASCADE,
    product_scope          text NOT NULL CHECK (product_scope IN ('product', 'kit_part', 'unmatched_code', 'no_product_scope')),
    loc                    text NOT NULL,
    qualifiers             jsonb NOT NULL DEFAULT '[]',
    UNIQUE NULLS NOT DISTINCT (document_pk, loc, product_code_raw, duns)
);
CREATE INDEX operation_assertion_duns_op ON national.operation_assertion (duns, operation_code);
CREATE INDEX operation_assertion_product ON national.operation_assertion (product_pk);
CREATE INDEX operation_assertion_doc ON national.operation_assertion (document_pk);

-- Normalized operation vocabulary, rebuilt from observed assertions after each run.
CREATE TABLE national.operation_type (
    operation_code   text PRIMARY KEY,
    canonical_name   text NOT NULL,
    observed_names   jsonb NOT NULL,
    assertions       bigint NOT NULL,
    refreshed_run_id bigint REFERENCES national.ingest_run
);

-- Evidence status per product. Missing evidence is never collapsed into "not manufactured".
CREATE VIEW national.v_product_establishment_evidence AS
SELECT p.product_pk, p.document_pk, d.set_id, d.version, p.kind, p.ndc_raw, p.ndc_product_5_4,
       CASE
         WHEN NOT d.has_establishment_block THEN 'NO_ESTABLISHMENT_BLOCK'
         WHEN EXISTS (SELECT 1 FROM national.operation_assertion a
                      WHERE a.product_pk = p.product_pk AND a.operation_code = 'C43360' AND a.duns IS NOT NULL)
              THEN 'EXPLICIT_MANUFACTURE'
         WHEN EXISTS (SELECT 1 FROM national.operation_assertion a
                      WHERE a.product_pk = p.product_pk AND a.operation_code = 'C43360')
              THEN 'MANUFACTURE_WITHOUT_DUNS'
         WHEN EXISTS (SELECT 1 FROM national.operation_assertion a WHERE a.product_pk = p.product_pk)
              THEN 'OTHER_OPERATIONS_ONLY'
         WHEN EXISTS (SELECT 1 FROM national.operation_assertion a
                      WHERE a.document_pk = p.document_pk AND a.product_scope = 'no_product_scope')
              THEN 'ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT'
         ELSE 'ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT'
       END AS evidence_status
FROM national.product p
JOIN national.spl_document d USING (document_pk);

-- Same set/version with different bytes: kept as separate documents, surfaced here.
CREATE VIEW national.v_version_conflicts AS
SELECT set_id, version, count(*) AS documents, array_agg(xml_sha256 ORDER BY xml_sha256) AS xml_sha256s
FROM national.spl_document GROUP BY set_id, version HAVING count(*) > 1;
