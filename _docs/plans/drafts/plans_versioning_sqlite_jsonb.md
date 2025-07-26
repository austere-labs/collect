# JSONB-based Plan Versioning System for SQLite3

A modern approach for versioning plans using SQLite's JSONB support combined with temporal versioning patterns. This system separates current plans from historical versions while storing flexible document content as JSONB for optimal performance.

## Requirements

- SQLite 3.45.0+ (for JSONB support)
- Python 3.7+
- sqlite3 module (included in Python standard library)

## Database Schema Design

```sql
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

-- Metrics time-series table (optimized for plan tracking)
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
```

## Implementation

```python
import sqlite3
import json
import hashlib
from datetime import datetime

class PlanVersionManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self._setup_jsonb()
        
    def _setup_jsonb(self):
        """Enable JSONB support if available"""
        self.conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        
    def create_version(self, plan_id, data, change_summary=None):
        """Create a new version of a plan"""
        cursor = self.conn.cursor()
        
        # Convert data to JSONB and calculate hash
        json_data = json.dumps(data, sort_keys=True)
        content_hash = hashlib.sha256(json_data.encode()).hexdigest()
        
        # Check if content actually changed
        cursor.execute("""
            SELECT content_hash FROM plans WHERE id = ?
        """, (plan_id,))
        
        current = cursor.fetchone()
        if current and current[0] == content_hash:
            return None  # No changes detected
        
        # Archive current version if exists
        if current:
            cursor.execute("""
                INSERT INTO plan_history 
                    (id, version, data, content_hash, created_at, change_summary)
                SELECT id, version, data, content_hash, created_at, ?
                FROM plans WHERE id = ?
            """, (change_summary, plan_id))
            
            # Increment version
            cursor.execute("""
                UPDATE plans 
                SET data = jsonb(?), 
                    version = version + 1,
                    content_hash = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json_data, content_hash, plan_id))
        else:
            # Create new plan
            cursor.execute("""
                INSERT INTO plans (id, data, content_hash)
                VALUES (?, jsonb(?), ?)
            """, (plan_id, json_data, content_hash))
        
        self.conn.commit()
        return content_hash
    
    def get_version_history(self, plan_id, limit=None):
        """Retrieve version history using window functions"""
        query = """
            WITH all_versions AS (
                SELECT id, version, data, created_at, 
                       'current' as status
                FROM plans WHERE id = ?
                UNION ALL
                SELECT id, version, data, created_at,
                       'historical' as status  
                FROM plan_history WHERE id = ?
            )
            SELECT *, 
                   LAG(data) OVER (ORDER BY version) as prev_data,
                   LEAD(version) OVER (ORDER BY version) as next_version
            FROM all_versions
            ORDER BY version DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
            
        cursor = self.conn.cursor()
        cursor.execute(query, (plan_id, plan_id))
        return cursor.fetchall()
    
    def get_current_plan(self, plan_id):
        """Get the current version of a plan"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, data, version, created_at, updated_at
            FROM plans WHERE id = ?
        """, (plan_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'data': json.loads(row[2]),
                'version': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            }
        return None
    
    def get_specific_version(self, plan_id, version):
        """Get a specific version of a plan"""
        cursor = self.conn.cursor()
        
        # Check current version first
        cursor.execute("""
            SELECT data, version, created_at, updated_at
            FROM plans 
            WHERE id = ? AND version = ?
        """, (plan_id, version))
        
        row = cursor.fetchone()
        if row:
            return {
                'data': json.loads(row[0]),
                'version': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'is_current': True
            }
        
        # Check history
        cursor.execute("""
            SELECT data, version, created_at, archived_at, change_summary
            FROM plan_history 
            WHERE id = ? AND version = ?
        """, (plan_id, version))
        
        row = cursor.fetchone()
        if row:
            return {
                'data': json.loads(row[0]),
                'version': row[1],
                'created_at': row[2],
                'archived_at': row[3],
                'change_summary': row[4],
                'is_current': False
            }
        
        return None
    
    def rollback_to_version(self, plan_id, target_version, change_summary=None):
        """Rollback a plan to a specific version"""
        # Get the target version data
        target = self.get_specific_version(plan_id, target_version)
        if not target:
            raise ValueError(f"Version {target_version} not found for plan {plan_id}")
        
        # Create a new version with the old data
        return self.create_version(
            plan_id, 
            target['data'], 
            change_summary or f"Rollback to version {target_version}"
        )
    
    def search_plans(self, filters):
        """Search plans using JSONB queries"""
        conditions = []
        params = []
        
        for key, value in filters.items():
            conditions.append(f"data ->> '$.{key}' = ?")
            params.append(value)
        
        query = f"""
            SELECT id, name, data, version, updated_at
            FROM plans
            WHERE {' AND '.join(conditions)}
            ORDER BY updated_at DESC
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        results = []
        for row in cursor:
            results.append({
                'id': row[0],
                'name': row[1],
                'data': json.loads(row[2]),
                'version': row[3],
                'updated_at': row[4]
            })
        
        return results
    
    def add_metrics(self, plan_id, version, metrics):
        """Add metrics for a specific plan version"""
        cursor = self.conn.cursor()
        
        for metric_name, values in metrics.items():
            if isinstance(values, dict):
                # Handle time-series data
                for step, value in values.items():
                    cursor.execute("""
                        INSERT INTO plan_metrics 
                        (plan_id, version, metric_name, step, value, timestamp)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (plan_id, version, metric_name, int(step), float(value)))
            else:
                # Handle single value
                cursor.execute("""
                    INSERT INTO plan_metrics 
                    (plan_id, version, metric_name, step, value, timestamp)
                    VALUES (?, ?, ?, 0, ?, CURRENT_TIMESTAMP)
                """, (plan_id, version, metric_name, float(values)))
        
        self.conn.commit()
    
    def get_metrics(self, plan_id, version=None, metric_name=None):
        """Retrieve metrics for a plan"""
        query = """
            SELECT metric_name, step, value, timestamp
            FROM plan_metrics
            WHERE plan_id = ?
        """
        params = [plan_id]
        
        if version is not None:
            query += " AND version = ?"
            params.append(version)
        
        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)
        
        query += " ORDER BY metric_name, step"
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        metrics = {}
        for row in cursor:
            name, step, value, timestamp = row
            if name not in metrics:
                metrics[name] = {}
            metrics[name][step] = {
                'value': value,
                'timestamp': timestamp
            }
        
        return metrics
```

## Usage Examples

```python
# Initialize the version manager
pvm = PlanVersionManager('plans.db')

# Create a new plan
plan_data = {
    'name': 'Data Processing Pipeline v1',
    'type': 'pipeline',
    'status': 'draft',
    'parameters': {
        'input_format': 'csv',
        'output_format': 'parquet',
        'batch_size': 1000
    },
    'steps': [
        {'name': 'validate', 'enabled': True},
        {'name': 'transform', 'enabled': True},
        {'name': 'aggregate', 'enabled': False}
    ]
}

# Create first version
pvm.create_version('pipeline-001', plan_data)

# Update the plan (automatically creates version 2)
plan_data['parameters']['batch_size'] = 5000
plan_data['status'] = 'active'
pvm.create_version('pipeline-001', plan_data, 'Increased batch size for performance')

# Get version history
history = pvm.get_version_history('pipeline-001')
for version in history:
    print(f"Version {version[1]}: {version[2]} - {version[4]}")

# Search for active plans
active_plans = pvm.search_plans({'status': 'active'})

# Add metrics for tracking
metrics = {
    'processing_time': {0: 45.2, 1: 43.8, 2: 44.1},
    'memory_usage': 2048.5,
    'success_rate': 0.98
}
pvm.add_metrics('pipeline-001', 2, metrics)

# Rollback if needed
pvm.rollback_to_version('pipeline-001', 1, 'Reverting batch size change')
```

## Performance Optimization

```python
# Enable WAL mode for better concurrency
conn.execute("PRAGMA journal_mode=WAL")

# Optimize page size for your workload
conn.execute("PRAGMA page_size=4096")

# Run optimization periodically
conn.execute("PRAGMA optimize")

# Use prepared statements for repeated queries
stmt = conn.prepare("""
    SELECT * FROM plans 
    WHERE data ->> '$.status' = ?
""")
```

## Performance Characteristics

- **JSONB provides 3x faster processing** compared to text JSON
- **5-10% smaller storage footprint** than regular JSON
- Expression indexes on JSONB fields enable efficient filtering without parsing JSON on every query
- The separated collections pattern ensures optimal query performance for current plans while maintaining complete history
- Window functions enable sophisticated version analysis and comparisons

## Advantages

1. **Flexible Schema Evolution**: JSONB allows schema changes without database migrations
2. **Excellent Performance**: Binary format with built-in indexing support
3. **Efficient Storage**: Current/history separation optimizes common queries
4. **Rich Querying**: SQL JSON operators enable complex filtering
5. **Version Analysis**: Window functions provide powerful version comparison capabilities
6. **Natural Fit**: JSONB is ideal for storing structured plan metadata

## Limitations

1. **SQLite Version Requirement**: Requires SQLite 3.45.0+ for JSONB support
2. **Storage Overhead**: Stores complete documents for each version (no delta compression)
3. **Complex Cross-Version Queries**: Analyzing changes across many versions requires custom logic
4. **Legacy Support**: JSONB not available in older SQLite versions

## Best Practices

1. **Hash Verification**: Always check content hash before creating new versions to avoid duplicates
2. **Index Strategy**: Create expression indexes for frequently queried JSONB fields
3. **Metrics Separation**: Store time-series metrics in dedicated table for better performance
4. **WAL Mode**: Use Write-Ahead Logging for better concurrent access
5. **Regular Maintenance**: Run `PRAGMA optimize` periodically for query performance
6. **Change Summaries**: Always provide meaningful change summaries for version tracking
