# Schema Extraction

## What This Covers

How the pipeline extracts table and column metadata from the source database, writes it to `metadata/<database>/schema_registry.json`, and tracks change-data-capture (CDC) status.

## Stage 4: Extract Source Schema

**Batch wrapper:** `scripts/batch/migration/windows/extract_schema.bat`
**Python module:** `scripts/python/migration/extract_schema.py`
**Schema extractor:** `scripts/schema_extractor.py`

### What It Does

1. Resolves effective source configuration.
2. Determines target metadata directory based on destination database type.
3. Writes effective source config to a temporary `source.conf` (backed up and restored after extraction).
4. Invokes `schema_extractor.py` with the destination database type as argument.
5. Reads `metadata/<database>/schema_registry.json` and `metadata/<database>/cdc_status.json`.
6. Prints extraction summary (tables, columns, changed tables).
7. Restores original `source.conf`.

### Why Destination Database Type Determines Metadata Path

The metadata directory is named after the **destination** database type, not the source. This is because the schema registry describes the schema as it will exist in the destination database (after type conversion).

Example: Extracting from MSSQL to MySQL writes metadata to `metadata/mysql/`.

## Schema Extractor Logic

### Connection

`schema_extractor.py` reads `source.conf` (via `load_source_config()`), which contains `SOURCE_DB_TYPE` and all source connection fields. The temporary `source.conf` written by `extract_schema.py` contains the full effective source config.

### Table Discovery

Database-specific queries retrieve user tables:

| Database | Query |
|----------|-------|
| MySQL | `SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()` |
| MSSQL | `SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_CATALOG = DB_NAME() AND TABLE_TYPE = 'BASE TABLE'` |
| PostgreSQL | `SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'public' AND TABLE_TYPE = 'BASE TABLE'` |

### Column Discovery

For each table, columns are retrieved in ordinal position order:

| Database | Query |
|----------|-------|
| MySQL | `SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION` |
| MSSQL | `SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_CATALOG = DB_NAME() AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION` |
| PostgreSQL | `SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'public' AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION` |

### CDC (Change Data Capture) Status

For each table, `detect_schema_changes()` compares the newly extracted columns against the existing `schema_registry.json`:

| Status | Meaning |
|--------|---------|
| `NEW` | Table not previously in registry |
| `CHANGED` | New columns added since last extraction |
| `DELETED` | Columns removed since last extraction |
| `UNCHANGED` | No column changes since last extraction |

CDC status is written to `metadata/<database>/cdc_status.json`.

## Output Artifacts

### schema_registry.json

Location: `metadata/<database>/schema_registry.json`

Structure:
```json
{
  "customers": [
    "customer_id",
    "customer_name",
    "email",
    "city",
    "created_at",
    "phone_number"
  ],
  "products": [
    "product_id",
    "product_name",
    "category",
    "price",
    "stock_quantity"
  ]
}
```

### cdc_status.json

Location: `metadata/<database>/cdc_status.json`

Structure:
```json
{
  "tables": {
    "customers": {
      "status": "UNCHANGED",
      "added_columns": [],
      "deleted_columns": []
    }
  }
}
```

### Column Normalization

Columns are normalized before storage:
- BOM characters (`\ufeff`) are stripped
- Whitespace is trimmed
- Table names are lowercased and spaces are replaced with underscores

## Example Extraction Output

From the actual test run:
```
Source Database  : MSSQL
Target Metadata  : metadata/mysql/

Found 3 table(s) in source database
Extracted columns from customers: ['customer_id', 'customer_name', 'email', 'city', 'created_at', 'phone_number']
CDC Status [customers] : UNCHANGED
Extracted columns from products: ['product_id', 'product_name', 'category', 'price', 'stock_quantity']
CDC Status [products] : UNCHANGED
Extracted columns from orders: ['order_id', 'customer_id', 'order_date', 'total_amount', 'status']
CDC Status [orders] : UNCHANGED

Tables Extracted : 3
Table : customers
  - customer_id
  - customer_name
  - email
  - city
  - created_at
  - phone_number
Table : products
  - product_id
  - product_name
  - category
  - price
  - stock_quantity
Table : orders
  - order_id
  - customer_id
  - order_date
  - total_amount
  - status
Changed Tables   : 0
```
