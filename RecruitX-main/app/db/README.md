# RecruitX Database Module

This module provides a SQLite-based persistent storage solution for the RecruitX system. It enables caching of API responses, storage of processed documents, and tracking of matching results.

## Features

- **Document Storage**: Store and retrieve processed documents
- **Entity Extraction**: Save entities extracted from documents
- **Matching Results**: Persist matching scores and details
- **API Response Caching**: Cache API responses to reduce costs and improve performance

## Components

### 1. Database Manager (`manager.py`)

The core database manager that handles:
- Connection pooling
- Transaction management
- Schema initialization
- CRUD operations

Implements the [Singleton pattern](https://en.wikipedia.org/wiki/Singleton_pattern) to ensure only one database connection is maintained.

### 2. Database API (`api.py`)

High-level API for database operations:
- Document storage and retrieval
- Entity management
- Matching results
- Search operations
- API response caching

### 3. Utilities (`utils.py`)

Helper functions for:
- Content hashing
- File metadata extraction
- Document type normalization
- JSON serialization/deserialization

## Schema

### Documents

```sql
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    content_hash TEXT UNIQUE,
    parsed_text TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Entities

```sql
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    entity_type TEXT NOT NULL,
    entity_value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents (id)
)
```

### Matches

```sql
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document1_id INTEGER,
    document2_id INTEGER,
    score REAL NOT NULL,
    match_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document1_id) REFERENCES documents (id),
    FOREIGN KEY (document2_id) REFERENCES documents (id)
)
```

### Cache

```sql
CREATE TABLE IF NOT EXISTS cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE,
    cache_value TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Usage

### Basic Usage

```python
from app.db.api import DatabaseAPI

# Initialize the API
db = DatabaseAPI()

# Store a document
doc_id = db.store_document_from_text(
    text="Sample document content",
    file_name="sample.txt",
    document_type="text",
    metadata={"source": "user_upload"}
)

# Store entities
entities = [
    {"entity_type": "skill", "entity_value": "Python", "confidence": 0.95},
    {"entity_type": "skill", "entity_value": "Database", "confidence": 0.88}
]
db.store_entities_for_document(doc_id, entities)

# Retrieve document with entities
document = db.get_document_with_entities(doc_id)
```

### API Caching

```python
from app.db.api import DatabaseAPI

# Initialize the API
db = DatabaseAPI()

# Check cache before making expensive API call
api_name = "gemini"
request_data = {"prompt": "Analyze this resume", "temperature": 0.1}

cached_response = db.get_cached_api_response(api_name, request_data)
if cached_response:
    return json.loads(cached_response)

# Make API call if not in cache
response = call_external_api(request_data)

# Cache the response
db.cache_api_response(
    api_name=api_name,
    request_data=request_data,
    response_data=json.dumps(response),
    ttl_seconds=3600 * 24  # 1 day cache
)
```

## Configuration

Configuration is done through the `config.toml` file:

```toml
[database]
db_path = "data/recruitx.db"
enable_cache = true
max_cache_entries = 10000
cleanup_interval = 3600  # 1 hour in seconds
```

Environment variables can also be used to override settings:

- `DB_PATH`: Override the database file path 