import json
import re

from django.db import migrations


def _parse_legacy(geometry_str):
    """Convert ((lon,lat),(lon,lat),...) → GeoJSON FeatureCollection string."""
    if not geometry_str:
        return geometry_str
    raw = geometry_str.strip()
    if raw.startswith('{') or raw.startswith('['):
        return raw  # already GeoJSON, skip
    matches = re.findall(r'\((-?[\d.]+),(-?[\d.]+)\)', raw)
    if not matches:
        return raw
    # shapefile_utils writes (lon, lat), parse_geometry_string swaps to [lat,lon]
    # Here we keep the original (lon, lat) order for GeoJSON coordinates
    ring = [[float(lon), float(lat)] for lon, lat in matches]
    return json.dumps({
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {}
        }]
    })


def migrate_forward(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # 1. Read existing polygon values as text before altering the column
        cursor.execute(
            "SELECT id, geometry::text FROM archaeological_evidence WHERE geometry IS NOT NULL"
        )
        rows = cursor.fetchall()

        # 2. Change column type from PostgreSQL 'polygon' to 'text'
        cursor.execute(
            "ALTER TABLE archaeological_evidence ALTER COLUMN geometry TYPE text USING geometry::text"
        )

        # 3. Convert legacy ((lon,lat),...) strings to GeoJSON
        for ev_id, geom_text in rows:
            if not geom_text:
                continue
            converted = _parse_legacy(geom_text)
            if converted != geom_text:
                cursor.execute(
                    "UPDATE archaeological_evidence SET geometry = %s WHERE id = %s",
                    [converted, ev_id]
                )


def migrate_backward(apps, schema_editor):
    pass  # GeoJSON is a superset; reversing is not necessary


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0005_alter_sitesettings_id_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
