#!/bin/bash

# Script to export all PostgreSQL tables to CSV files

OUTPUT_DIR="database_csv_exports"
mkdir -p "$OUTPUT_DIR"

echo "Exporting database tables to CSV files..."
echo "Output directory: $OUTPUT_DIR"
echo ""

# Get list of all tables
TABLES=$(docker exec shareland_postgres psql -U postgres -d shareland -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;" | tr -d ' ' | grep -v '^$')

TOTAL_TABLES=$(echo "$TABLES" | wc -l)
CURRENT=0

for TABLE in $TABLES; do
    CURRENT=$((CURRENT + 1))
    echo "[$CURRENT/$TOTAL_TABLES] Exporting table: $TABLE"
    
    # Export table to CSV
    docker exec shareland_postgres psql -U postgres -d shareland -c "\COPY (SELECT * FROM $TABLE) TO STDOUT WITH CSV HEADER" > "$OUTPUT_DIR/${TABLE}.csv"
    
    if [ $? -eq 0 ]; then
        ROW_COUNT=$(tail -n +2 "$OUTPUT_DIR/${TABLE}.csv" | wc -l)
        echo "  ✓ Exported $ROW_COUNT rows to ${TABLE}.csv"
    else
        echo "  ✗ Error exporting $TABLE"
    fi
done

echo ""
echo "Export complete! CSV files are in the '$OUTPUT_DIR' directory."
echo "Total tables exported: $TOTAL_TABLES"























