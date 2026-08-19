# Jenkins Pipeline Parameters

## What This Covers

Every parameter defined in the Windows migration Jenkinsfile, its type, default value, and purpose.

## Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SOURCE_DATABASE` | Choice | `MSSQL` | Source database type. Options: `MSSQL`, `MYSQL`, `POSTGRESQL` |
| `DESTINATION_DATABASE` | Choice | `MYSQL` | Destination database type. Options: `MSSQL`, `MYSQL`, `POSTGRESQL` |
| `SOURCE_HOST` | String | *(empty)* | Optional override for source host. Leave empty to use database config default |
| `SOURCE_PORT` | String | *(empty)* | Optional override for source port. Leave empty to use database config default |
| `SOURCE_DB` | String | *(empty)* | Optional override for source database name. Leave empty to use database config default |
| `SOURCE_SCHEMA` | String | *(empty)* | Optional override for source schema. Leave empty to use database config default |
| `SOURCE_USER` | String | *(empty)* | Optional override for source user. Leave empty to use database config default |
| `SOURCE_PASSWORD` | Password | *(empty)* | Optional override for source password. Leave empty to use database config default |
| `DESTINATION_HOST` | String | *(empty)* | Optional override for destination host. Leave empty to use database config default |
| `DESTINATION_PORT` | String | *(empty)* | Optional override for destination port. Leave empty to use database config default |
| `DESTINATION_DB` | String | *(empty)* | Optional override for destination database name. Leave empty to use database config default |
| `DESTINATION_SCHEMA` | String | *(empty)* | Optional override for destination schema. Leave empty to use database config default |
| `DESTINATION_USER` | String | *(empty)* | Optional override for destination user. Leave empty to use database config default |
| `DESTINATION_PASSWORD` | Password | *(empty)* | Optional override for destination password. Leave empty to use database config default |

## Parameter Categories

### Database Type Parameters

| Parameter | Purpose | How It Is Used |
|-----------|---------|----------------|
| `SOURCE_DATABASE` | Selects which database config file to load for the source | Maps to `config/windows/migration/<db_type>.conf` |
| `DESTINATION_DATABASE` | Selects which database config file to load for the destination | Maps to `config/windows/migration/<db_type>.conf` |

### Connection Override Parameters

These parameters allow runtime overrides of database configuration without editing config files. The pattern is identical for source and destination:

| Parameter Group | Fields |
|-----------------|--------|
| Source Override | `SOURCE_HOST`, `SOURCE_PORT`, `SOURCE_DB`, `SOURCE_SCHEMA`, `SOURCE_USER`, `SOURCE_PASSWORD` |
| Destination Override | `DESTINATION_HOST`, `DESTINATION_PORT`, `DESTINATION_DB`, `DESTINATION_SCHEMA`, `DESTINATION_USER`, `DESTINATION_PASSWORD` |

## Important Rules

1. **Empty string = no override.** An empty string value does NOT replace a configured default. Only non-empty values take precedence.
2. **Database type must be selected.** `SOURCE_DATABASE` and `DESTINATION_DATABASE` must be set to one of the three supported types.
3. **Same-endpoint prevention.** If source and destination resolve to the same database type, host, port, and database name, initialization fails.
4. **No default values for override parameters.** All override parameters default to empty string, ensuring they do not accidentally override configuration.

## Example: Full Parameter Set for MSSQL → MySQL

```
SOURCE_DATABASE = MSSQL
SOURCE_HOST     = localhost
SOURCE_PORT     = 1533
SOURCE_DB       = ecommerce_mssql
SOURCE_SCHEMA   = dbo
SOURCE_USER     = sa
SOURCE_PASSWORD = ********

DESTINATION_DATABASE = MYSQL
DESTINATION_HOST     = 127.0.0.1
DESTINATION_PORT     = 3306
DESTINATION_DB       = test_schema_1
DESTINATION_SCHEMA   =
DESTINATION_USER     = rootuser
DESTINATION_PASSWORD = ********
```

This is the exact parameter configuration observed in the actual test run documented in `jenkins_testing/outputs/#4 (1).txt`.
