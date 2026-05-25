-- UNGUESS / Esercizio Megaditta - layer relazionale normalizzato + knowledge layer AI
-- Dialect: PostgreSQL. Lo schema è intenzionalmente RAG-aware mantenendo le entità in 3NF.

CREATE TABLE workspaces (
    workspace_id        TEXT PRIMARY KEY,
    workspace_name      TEXT,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE methodologies (
    methodology_id      BIGSERIAL PRIMARY KEY,
    methodology_name    TEXT UNIQUE NOT NULL,
    description         TEXT
);

CREATE TABLE clients (
    client_id           BIGSERIAL PRIMARY KEY,
    workspace_id        TEXT NOT NULL REFERENCES workspaces(workspace_id),
    client_name         TEXT NOT NULL,
    country_code        CHAR(2),
    UNIQUE (workspace_id, client_name)
);

CREATE TABLE project_managers (
    manager_id          BIGSERIAL PRIMARY KEY,
    workspace_id        TEXT NOT NULL REFERENCES workspaces(workspace_id),
    full_name           TEXT NOT NULL,
    UNIQUE (workspace_id, full_name)
);


CREATE TABLE projects (
    project_id          TEXT NOT NULL,
    workspace_id        TEXT NOT NULL REFERENCES workspaces(workspace_id),
    client_id           BIGINT REFERENCES clients(client_id),
    methodology_id      BIGINT REFERENCES methodologies(methodology_id),
    manager_id          BIGINT REFERENCES project_managers(manager_id),
    project_name        TEXT NOT NULL,
    research_topic      TEXT,
    country_code        CHAR(2),
    sample_size         INTEGER CHECK (sample_size >= 0),
    status              TEXT CHECK (status IN ('Completed','In Progress','On Hold','Cancelled')),
    budget_eur          NUMERIC(12,2) CHECK (budget_eur >= 0),
    start_date          TIMESTAMPTZ,
    end_date            TIMESTAMPTZ,
    notes               TEXT,
    has_date_issue      BOOLEAN DEFAULT false,
    PRIMARY KEY (workspace_id, project_id),
    CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date OR has_date_issue = true)
);

CREATE TABLE panelists (
    workspace_id        TEXT NOT NULL REFERENCES workspaces(workspace_id),
    panelist_id         TEXT NOT NULL,
    email_hash          TEXT,
    phone_hash          TEXT,
    pii_version         TEXT DEFAULT 'sha256-v1',
    updated_at          TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (workspace_id, panelist_id)
);

CREATE TABLE support_agents (
    agent_id            BIGSERIAL PRIMARY KEY,
    workspace_id        TEXT NOT NULL REFERENCES workspaces(workspace_id),
    full_name           TEXT NOT NULL,
    UNIQUE (workspace_id, full_name)
);

CREATE TABLE interactions (
    interaction_id      TEXT PRIMARY KEY,
    workspace_id        TEXT NOT NULL REFERENCES workspaces(workspace_id),
    panelist_id         TEXT,
    project_id          TEXT,
    agent_id            BIGINT REFERENCES support_agents(agent_id),
    interaction_date    TIMESTAMPTZ,
    channel             TEXT CHECK (channel IN ('Email','Chat','Phone')),
    issue_type          TEXT,
    issue_description   TEXT NOT NULL,
    resolution          TEXT,
    resolved            BOOLEAN,
    resolution_time_hours NUMERIC(8,2) CHECK (resolution_time_hours >= 0),
    satisfaction_score  INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5),
    FOREIGN KEY (workspace_id, panelist_id) REFERENCES panelists(workspace_id, panelist_id),
    FOREIGN KEY (workspace_id, project_id) REFERENCES projects(workspace_id, project_id)
);

CREATE TABLE faq_documents (
    faq_id              TEXT PRIMARY KEY,
    section             TEXT,
    question            TEXT NOT NULL,
    answer              TEXT NOT NULL,
    language_code       TEXT DEFAULT 'it',
    source_updated_at   TIMESTAMPTZ
);

CREATE TABLE ingestion_runs (
    ingestion_run_id    UUID PRIMARY KEY,
    source_name         TEXT NOT NULL,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ,
    status              TEXT NOT NULL,
    records_read        INTEGER DEFAULT 0,
    records_written     INTEGER DEFAULT 0,
    records_rejected    INTEGER DEFAULT 0,
    quality_report_uri  TEXT
);

CREATE INDEX idx_projects_workspace_status ON projects(workspace_id, status);
CREATE INDEX idx_projects_workspace_topic ON projects(workspace_id, research_topic);
CREATE INDEX idx_interactions_workspace_project ON interactions(workspace_id, project_id);
CREATE INDEX idx_interactions_issue_date ON interactions(workspace_id, issue_type, interaction_date DESC);
CREATE INDEX idx_chunks_workspace_source ON document_chunks(workspace_id, source_type, created_at DESC);
CREATE INDEX idx_chunks_metadata_gin ON document_chunks USING GIN(metadata);