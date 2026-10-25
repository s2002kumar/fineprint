-- DST-08 research prototype: source-NDC lineage, applied ONLY to a scratch database by fineprint.lineage.build.
-- Not a numbered migration: it never runs on the production database, and no national row is changed.

CREATE SCHEMA lineage;

CREATE TABLE lineage.build (
    build_id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at      timestamptz NOT NULL DEFAULT now(),
    finished_at     timestamptz,
    status          text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed')),
    rule_version    text NOT NULL,
    graph_build_id  bigint NOT NULL REFERENCES national.graph_build,   -- the DIRECT edges this build reads
    code_commit     text,
    code_dirty      boolean,
    outputs         jsonb NOT NULL DEFAULT '{}'
);

-- Dosage form and active ingredients (UNII, strength) of every product and kit part in a canonical document, read from
-- the release XML: used only to reject a reference whose cited source contradicts it.
CREATE TABLE lineage.product_attributes (
    product_pk       bigint PRIMARY KEY REFERENCES national.product,
    form_code        text,
    active           jsonb NOT NULL,     -- sorted [[unii, num value, num unit, den value, den unit], ...]
    characteristics  jsonb NOT NULL,     -- imprint, color, shape, size, score, flavor as stated (lineage.characteristics)
    build_id         bigint NOT NULL REFERENCES lineage.build
);

-- SOURCE_NDC_REFERENCE: one row per asEquivalentEntity element of a product or kit part in a canonical document.
CREATE TABLE lineage.source_reference (
    reference_pk             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    build_id                 bigint NOT NULL REFERENCES lineage.build,
    document_pk              bigint NOT NULL REFERENCES national.spl_document,   -- the citing (repackager) SPL
    product_pk               bigint NOT NULL REFERENCES national.product,        -- the citing product or kit part
    product_kind             text NOT NULL CHECK (product_kind IN ('product', 'kit_part')),
    product_ndc_raw          text,
    product_ndc_5_4          text,
    loc                      text NOT NULL,                                      -- the asEquivalentEntity element
    class_code               text,
    equivalence_code         text,
    equivalence_code_system  text,
    source_code_raw          text,                                               -- verbatim definingMaterialKind code
    source_code_system       text,
    source_code_pattern      text NOT NULL CHECK (source_code_pattern IN ('product', 'package', 'malformed', 'missing')),
    source_ndc_5_4           text,       -- only for a product-pattern code in the NDC system; never from a package code
    validity                 text NOT NULL CHECK (validity IN ('VALID', 'NOT_EQUIV_CLASS', 'NOT_SAME_EQUIVALENCE',
                                 'NOT_NDC_CODE_SYSTEM', 'PACKAGE_CODE_NOT_PRODUCT_CODE', 'MALFORMED_OR_MISSING_CODE',
                                 'SELF_REFERENCE', 'MULTIPLE_SOURCES_FOR_PRODUCT')),
    UNIQUE (document_pk, loc),
    CHECK ((source_ndc_5_4 IS NOT NULL) = (source_code_pattern = 'product' AND source_code_system = '2.16.840.1.113883.6.69'))
);
CREATE INDEX source_reference_product ON lineage.source_reference (product_pk);
CREATE INDEX source_reference_ndc ON lineage.source_reference (product_ndc_5_4);
CREATE INDEX source_reference_source_ndc ON lineage.source_reference (source_ndc_5_4);

-- Resolution of each reference against the canonical products of the same graph build, and its eligibility.
CREATE TABLE lineage.source_resolution (
    reference_pk            bigint PRIMARY KEY REFERENCES lineage.source_reference,
    resolution              text NOT NULL CHECK (resolution IN ('RESOLVED', 'MULTIPLE_CANDIDATES', 'ONLY_SAME_SET',
                                'ONLY_KIT_PART', 'ONLY_NON_CANONICAL_VERSION', 'NO_CANDIDATE', 'NOT_RESOLVED_INVALID')),
    n_candidates            integer NOT NULL,
    candidate_product_pks   bigint[] NOT NULL,
    source_product_pk       bigint REFERENCES national.product,
    source_document_pk      bigint REFERENCES national.spl_document,
    source_set_id           text,
    source_version          integer,
    source_selection_class  text,
    source_cites_source     boolean,
    chain                   text CHECK (chain IN ('SINGLE_HOP', 'MULTI_HOP', 'CYCLE', 'ENDS_AT_UNRESOLVED_REFERENCE',
                                'NOT_APPLICABLE')),
    consistency             text CHECK (consistency IN ('CONSISTENT', 'FORM_DIFFERS', 'ACTIVE_DIFFERS', 'INCOMPLETE',
                                'NOT_APPLICABLE')),
    source_has_direct       boolean,
    status                  text CHECK (status IN ('ELIGIBLE', 'EXCLUDED')),
    reasons                 text[]
);

-- SOURCE_LINKED_MANUFACTURING_EVIDENCE: an eligible reference joined to one DIRECT MANUFACTURE edge of the source
-- product. The citing SPL, the source SPL, the source's own assertion and the FDA registration line are all kept.
CREATE TABLE lineage.source_linked_evidence (
    reference_pk                 bigint NOT NULL REFERENCES lineage.source_reference,
    source_assertion_pk          bigint NOT NULL REFERENCES national.operation_edge,
    linked_product_pk            bigint NOT NULL REFERENCES national.product,      -- the repackaged/relabeled product
    source_product_pk            bigint NOT NULL REFERENCES national.product,
    citing_document_pk           bigint NOT NULL REFERENCES national.spl_document,
    source_document_pk           bigint NOT NULL REFERENCES national.spl_document,
    duns                         text NOT NULL,
    fei                          text,
    registration_pk              bigint REFERENCES national.registration_record,
    registration_source_file_id  bigint REFERENCES national.source_file,
    build_id                     bigint NOT NULL REFERENCES lineage.build,
    PRIMARY KEY (reference_pk, source_assertion_pk),
    CHECK (linked_product_pk <> source_product_pk)
);
CREATE INDEX source_linked_evidence_product ON lineage.source_linked_evidence (linked_product_pk);

-- Physical characteristics of each resolved reference against its source, in the current release. Rule v1 does not
-- read this table; rule v2 sends every conflict through the version-aware check (dst08_lineage_v2.sql).
CREATE TABLE lineage.physical_check (
    reference_pk  bigint PRIMARY KEY REFERENCES lineage.source_reference,
    outcome       text NOT NULL CHECK (outcome IN ('IMPRINT_EQUAL_ALL_EQUAL', 'IMPRINT_EQUAL_OTHER_DIFFERS', 'IMPRINT_DIFFERS',
                      'NO_IMPRINT_OTHERS_EQUAL', 'NO_IMPRINT_OTHER_DIFFERS', 'NOTHING_COMPARABLE')),
    conflict      boolean NOT NULL,      -- a characteristic stated on both sides differs (the post-hoc diagnostic's test)
    differing     text[] NOT NULL,
    strict        jsonb NOT NULL,        -- per characteristic: SAME, DIFFERS or ONE_SIDE
    per           jsonb NOT NULL         -- per characteristic as rule v2 reads it (lineage.physical_compare)
);

-- Coverage per product. The DIRECT tier is national.v_product_manufacturing_status unchanged; SOURCE_LINKED is a
-- separate tier reached only by products that are not DIRECT.
CREATE VIEW lineage.v_product_coverage AS
SELECT s.product_pk, s.set_id, s.version, s.ndc_raw, s.ndc_product_5_4,
       s.manufacturing_status AS direct_tier_status,
       CASE WHEN s.manufacturing_status = 'DIRECT' THEN 'DIRECT'
            WHEN EXISTS (SELECT 1 FROM lineage.source_linked_evidence e WHERE e.linked_product_pk = s.product_pk)
                 THEN 'SOURCE_LINKED'
            ELSE s.manufacturing_status END AS coverage_tier
FROM national.v_product_manufacturing_status s;
