-- Create prompt tables for prompt storage, versioning, and metrics
-- depends: 

-- Current prompt table
CREATE TABLE prompt (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical versions table
CREATE TABLE prompt_history (
    id TEXT,
    version INTEGER,
    data JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT,
    PRIMARY KEY (id, version)
);

-- Metrics time-series table (optimized for prompt tracking)
CREATE TABLE prompt_metrics (
    prompt_id TEXT,
    version INTEGER,
    metric_name TEXT,
    step INTEGER,
    value REAL,
    timestamp TIMESTAMP,
    PRIMARY KEY (prompt_id, version, metric_name, step)
);

-- Performance-critical indexes
CREATE INDEX idx_prompt_hash ON prompt(content_hash);
CREATE INDEX idx_prompt_updated ON prompt(updated_at);
CREATE INDEX idx_prompt_history_created ON prompt_history(created_at);
CREATE INDEX idx_prompt_metrics_time ON prompt_metrics(timestamp);

-- Expression indexes on JSONB fields for common queries
CREATE INDEX idx_prompt_status ON prompt(data ->> '$.status');
CREATE INDEX idx_prompt_type ON prompt(data ->> '$.type');