# Backup Validation Report: shareland_db_backup_20260112_120858.dump

## ✅ Backup File Status: **VALID FOR RESTORE**

### File Information
- **File**: `shareland_db_backup_20260112_120858.dump`
- **Size**: 330KB
- **Format**: PostgreSQL custom database dump - v1.16-0
- **Source PostgreSQL Version**: 17.7 (Ubuntu 17.7-3.pgdg22.04+1)
- **Target PostgreSQL Version**: 16 (Docker container)

### Database Name Mismatch
- **Backup Database Name**: `shareland_db`
- **Current Database Name**: `Open_Landscapes`
- **Status**: ✅ **OK** - The import function will drop and recreate the database, so the name mismatch is not an issue.

### Version Compatibility
- **PostgreSQL Version Mismatch**: Backup created with 17.7, target is 16
- **Status**: ✅ **OK** - The `import_database` function handles this by:
  1. Converting custom format dump to SQL using `pg_restore`
  2. Preprocessing SQL to remove version-specific settings (e.g., `transaction_timeout`)
  3. Using `psql` with `ON_ERROR_STOP=off` to continue on non-critical errors

### Table Structure Validation
The backup contains all expected tables:
- ✅ `research` - Main research table
- ✅ `site` - Site information
- ✅ `bibliography` - Bibliography references
- ✅ `image` - Image metadata
- ✅ `research_author` - Research-author relationships
- ✅ `site_research` - Site-research relationships
- ✅ `site_bibliography` - Site-bibliography relationships
- ✅ `archaeological_evidence` - Archaeological evidence
- ✅ `arch_ev_research` - Evidence-research relationships
- ✅ And all other expected tables

### Deprecated Tables Handling
- **Deprecated Tables**: `author` (removed in migration 0015)
- **Status**: ✅ **OK** - The import function automatically:
  - Skips `CREATE TABLE` statements for deprecated tables
  - Skips `INSERT INTO` statements for deprecated tables
  - Skips foreign key constraints referencing deprecated tables
  - Allows `DROP TABLE` statements (safe)

### Compatibility with Current Database Structure
- **Current Tables**: All tables match the backup structure
- **Status**: ✅ **Compatible** - The backup contains the same table structure as the current database

### Import Function Capabilities
The `import_database` function in `shareland/frontend/views.py` will:
1. ✅ Accept the `.dump` file (custom format)
2. ✅ Convert it to SQL format automatically
3. ✅ Preprocess SQL to handle:
   - `transaction_timeout` removal
   - Deprecated table skipping
   - `DROP TABLE IF EXISTS ... CASCADE` additions
   - `ON CONFLICT DO NOTHING` for INSERT statements
   - Error handling for `ALTER SEQUENCE OWNED BY` statements
4. ✅ Drop and recreate the database
5. ✅ Restore all data
6. ✅ Run Django migrations after restore to ensure system tables are up-to-date

## ⚠️ Important Notes

1. **Data Loss Warning**: The restore process will **DROP** the current `Open_Landscapes` database and recreate it. All current data will be lost.

2. **Backup Source**: This backup is from `shareland_db` database, but will be restored to `Open_Landscapes` (the import function handles this).

3. **PostgreSQL Version**: The version mismatch (17.7 → 16) is handled automatically, but some PostgreSQL 17-specific features might not be restored.

4. **Migration State**: After restore, Django migrations will be run automatically to ensure the database schema matches the current Django models.

## ✅ Recommendation

**This backup is SAFE to use for restore.** The import function is designed to handle:
- Custom format dumps (`.dump` files)
- Version mismatches
- Deprecated tables
- Database name differences

You can proceed with the restore using the `/database-import/` interface.










