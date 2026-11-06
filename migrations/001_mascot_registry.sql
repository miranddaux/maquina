-- PROPOSAL ONLY. Do not execute during startup, installation or onboarding.
-- Review the target schema, database backup and user approval before application.
-- SQLite dialect. Existing project/video tables are deliberately not assumed.
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

CREATE TABLE mascot_versions (
    mascot_id TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('candidate', 'approved', 'retired')),
    config_sha256 TEXT NOT NULL CHECK (length(config_sha256) = 64),
    geometry_version TEXT NOT NULL,
    animation_version TEXT NOT NULL,
    config_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    PRIMARY KEY (mascot_id, version),
    UNIQUE (mascot_id, version, config_sha256, geometry_version, animation_version)
);

CREATE TABLE mascot_assets (
    asset_id INTEGER PRIMARY KEY,
    mascot_id TEXT NOT NULL,
    mascot_version TEXT NOT NULL,
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE (mascot_id, mascot_version, path),
    FOREIGN KEY (mascot_id, mascot_version)
        REFERENCES mascot_versions (mascot_id, version) ON DELETE RESTRICT
);

CREATE TABLE video_mascots (
    video_id TEXT PRIMARY KEY NOT NULL,
    mascot_id TEXT NOT NULL,
    mascot_version TEXT NOT NULL,
    config_sha256 TEXT NOT NULL CHECK (length(config_sha256) = 64),
    geometry_version TEXT NOT NULL,
    animation_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    FOREIGN KEY (mascot_id, mascot_version, config_sha256, geometry_version, animation_version)
        REFERENCES mascot_versions (mascot_id, version, config_sha256, geometry_version, animation_version)
        ON DELETE RESTRICT
);

-- Versions and frozen video assignments can only be superseded by new identities.
CREATE TRIGGER mascot_versions_immutable_update BEFORE UPDATE ON mascot_versions
BEGIN SELECT RAISE(ABORT, 'Mascot versions are immutable; publish a new version'); END;
CREATE TRIGGER mascot_versions_immutable_delete BEFORE DELETE ON mascot_versions
BEGIN SELECT RAISE(ABORT, 'Mascot version history must be retained'); END;
CREATE TRIGGER mascot_assets_immutable_update BEFORE UPDATE ON mascot_assets
BEGIN SELECT RAISE(ABORT, 'Versioned mascot assets are immutable'); END;
CREATE TRIGGER mascot_assets_immutable_delete BEFORE DELETE ON mascot_assets
BEGIN SELECT RAISE(ABORT, 'Versioned mascot asset history must be retained'); END;
CREATE TRIGGER video_mascots_immutable_update BEFORE UPDATE ON video_mascots
BEGIN SELECT RAISE(ABORT, 'Video mascot assignments are immutable'); END;
CREATE TRIGGER video_mascots_immutable_delete BEFORE DELETE ON video_mascots
BEGIN SELECT RAISE(ABORT, 'Video mascot assignment history must be retained'); END;

COMMIT;
