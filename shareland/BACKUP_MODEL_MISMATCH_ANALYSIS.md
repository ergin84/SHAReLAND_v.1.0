# Backup Model Mismatch Analysis

## Summary
Analysis of potential mismatches between backup file `Open_Landscapes_backup_20260112_114129.dump` and current Django models.

## Key Findings

### 1. **Author Table - CRITICAL MISMATCH** ⚠️
- **Status**: The `author` table was **removed** in migration `0015_remove_author_models`
- **Migration History**:
  - Migration `0014_consolidate_author_into_user`: Migrates Author data to User/Profile
  - Migration `0015_remove_author_models`: Deletes the Author model/table
- **Impact**: If the backup contains the `author` table, it will cause conflicts during restore
- **Solution**: The restore function already handles this by:
  - Dropping tables with `DROP TABLE IF EXISTS ... CASCADE`
  - The `author` table will be dropped but data should have been migrated to User/Profile

### 2. **Anagraphic Table - POTENTIAL MISMATCH** ⚠️
- **Status**: Table still exists in models but may be deprecated
- **Current State**: Model exists but may not be actively used
- **Impact**: Low - table exists in both backup and models

### 3. **ResearchAuthor Table Structure Change**
- **Migration `0014`**: Changed `id_author` field from UUID (pointing to Author) to Integer (pointing to User)
- **Impact**: If backup has old structure with UUID FK, restore may fail
- **Solution**: Migration handles the conversion automatically

## Current Django Models (38 tables)

1. access_log
2. anagraphic
3. arch_ev_biblio
4. arch_ev_related_doc
5. arch_ev_research
6. arch_ev_sources
7. archaeological_evidence
8. archaeological_evidence_typology
9. audit_log
10. base_map
11. bibliography
12. chronology
13. country
14. first_discovery_method
15. functional_class
16. image
17. image_scale
18. image_type
19. intepretation_author
20. interpretation
21. interpretation_bibliography
22. investigation
23. investigation_type
24. municipality
25. physiography
26. positional_accuracy
27. positioning_mode
28. province
29. region
30. research
31. research_author
32. site
33. site_arch_evidence
34. site_bibliography
35. site_investigation
36. site_related_documentation
37. site_research
38. site_sources
39. site_toponymy
40. sources
41. sources_type
42. typology
43. typology_detail

## Tables That Should NOT Exist (Removed in Migrations)

- **author** - Removed in migration 0015 (consolidated into User/Profile)

## Recommendations

1. **Before Restoring Backup**:
   - Ensure all migrations are applied: `python manage.py migrate`
   - The restore function automatically handles:
     - Dropping existing tables with CASCADE
     - Removing `transaction_timeout` settings
     - Handling duplicate key violations with `ON CONFLICT DO NOTHING`
     - Wrapping problematic ALTER statements

2. **After Restoring Backup**:
   - Run migrations: `python manage.py migrate`
   - This ensures Django system tables (django_session, etc.) are created
   - The restore function should do this automatically, but verify if issues occur

3. **If Author Table Exists in Backup**:
   - The restore will drop it (due to CASCADE)
   - Author data should have been migrated to User/Profile in migration 0014
   - If backup is from before migration 0014, you may lose author data unless you restore to a version before that migration

## Verification Steps

To verify backup contents match models:

```bash
# List tables in backup
docker run --rm -v $(pwd)/database_csv_exports/backups:/backup postgres:16 \
  pg_restore --list /backup/Open_Landscapes_backup_20260112_114129.dump | grep TABLE

# Compare with current models
docker-compose exec django python manage.py shell -c "
from django.apps import apps
models = apps.get_app_config('frontend').get_models()
for m in sorted(models, key=lambda x: x._meta.db_table):
    print(m._meta.db_table)
"
```

## Improvements Made to Restore Function

The restore function has been updated to automatically handle mismatches:

1. **Deprecated Table Filtering**: 
   - Automatically skips `CREATE TABLE` statements for deprecated tables (like `author`)
   - Skips `INSERT INTO` statements for deprecated tables
   - Skips `ALTER TABLE` and constraint creation for deprecated tables
   - Skips foreign key constraints that reference deprecated tables

2. **Better Error Handling**:
   - Wraps problematic ALTER statements in DO blocks
   - Handles duplicate key violations with `ON CONFLICT DO NOTHING`
   - Uses `ON_ERROR_STOP=off` to continue on non-critical errors

3. **Automatic Migration**:
   - Runs Django system migrations after restore
   - Ensures `django_session` and other system tables exist

## Conclusion

The main mismatch is the **`author` table** which was removed in migration 0015. The restore function now automatically handles this by:
- Skipping all SQL statements related to the `author` table
- Allowing DROP statements (which are safe)
- Preventing foreign key constraint errors

The restore should now work smoothly without manual intervention for most cases.

