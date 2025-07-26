-- Create plans tables for plan storage, versioning, and metrics
-- depends: 

-- Current plans table
CREATE TABLE plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical versions table
CREATE TABLE plan_history (
    id TEXT,
    version INTEGER,
    data JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT,
    PRIMARY KEY (id, version)
);

/* 
The `plan_metrics` table is designed to track numerical metrics for different versions of plans over time. It serves as a time-series database for monitoring plan execution progress and performance.

 Key features:
- **Multi-version tracking**: Tracks metrics across different plan versions
- **Step-based measurements**: Records values at specific execution steps
- **Flexible metric types**: Can store any named metric (execution time, resource usage, success rates, etc.)
- **Time-series data**: Timestamps enable trend analysis and performance monitoring
- **Composite primary key**: Ensures unique entries per plan/version/metric/step combination

This allows tracking things like build times, test pass rates, or custom KPIs as plans evolve through their lifecycle.
*/
CREATE TABLE plan_metrics (
    plan_id TEXT,
    version INTEGER,
    metric_name TEXT,
    step INTEGER,
    value REAL,
    timestamp TIMESTAMP,
    PRIMARY KEY (plan_id, version, metric_name, step)
);

-- Performance-critical indexes
CREATE INDEX idx_plans_hash ON plans(content_hash);
CREATE INDEX idx_plans_updated ON plans(updated_at);
CREATE INDEX idx_history_created ON plan_history(created_at);
CREATE INDEX idx_metrics_time ON plan_metrics(timestamp);

-- Expression indexes on JSONB fields for common queries
CREATE INDEX idx_plan_status ON plans(data ->> '$.status');
CREATE INDEX idx_plan_type ON plans(data ->> '$.type');
