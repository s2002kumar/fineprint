-- DST-06: incremental refresh from official DailyMed update archives. Additive only.
-- Current release state = full-release members + update members, minus members an update's
-- files_deleted.txt retracts. No row from earlier migrations is modified.

ALTER TABLE national.source_file DROP CONSTRAINT source_file_kind_check;
ALTER TABLE national.source_file ADD CONSTRAINT source_file_kind_check CHECK (kind IN (
    'dailymed_human_rx_full_part', 'dailymed_zip_metadata', 'dailymed_spl_update',
    'fda_decrs_registration', 'fda_decrs_excluded', 'fda_decrs_registration_archived'));

ALTER TABLE national.set_version_selection DROP CONSTRAINT set_version_selection_selection_status_check;
ALTER TABLE national.set_version_selection ADD CONSTRAINT set_version_selection_selection_status_check
    CHECK (selection_status IN (
        'SINGLE_VERSION_METADATA_CONFIRMED', 'MULTI_VERSION_METADATA_SELECTED',
        'SINGLE_VERSION_NOT_IN_METADATA', 'SINGLE_VERSION_METADATA_LISTS_OTHER',
        'MULTI_VERSION_HIGHEST_NO_METADATA', 'MULTI_VERSION_HIGHEST_METADATA_LISTS_OTHER',
        'UNRESOLVED_SAME_VERSION_CONFLICT', 'UPDATE_NEWER_VERSION'));

-- Members an update archive declares deleted (files_deleted.txt), by zip basename.
CREATE TABLE national.release_retraction (
    update_source_file_id  bigint NOT NULL REFERENCES national.source_file,
    member_basename        text NOT NULL,
    listed_path            text NOT NULL,
    PRIMARY KEY (update_source_file_id, member_basename)
);
CREATE INDEX release_retraction_basename ON national.release_retraction (member_basename);
CREATE INDEX archive_member_document ON national.archive_member (document_pk);

CREATE TABLE national.refresh_run (
    refresh_id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at             timestamptz NOT NULL DEFAULT now(),
    finished_at            timestamptz,
    update_source_file_id  bigint NOT NULL REFERENCES national.source_file,
    build_before           bigint REFERENCES national.graph_build,
    build_after            bigint REFERENCES national.graph_build,
    summary                jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE national.refresh_change (
    refresh_id  bigint NOT NULL REFERENCES national.refresh_run,
    change      text NOT NULL CHECK (change IN ('added', 'removed', 'modified', 'carried_forward')),
    edge_key    text NOT NULL,
    before      jsonb,
    after       jsonb,
    PRIMARY KEY (refresh_id, change, edge_key)
);
