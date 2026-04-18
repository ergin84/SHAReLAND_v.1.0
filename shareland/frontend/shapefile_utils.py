import os
import tempfile
import zipfile

import geopandas as gpd
from django.core.exceptions import ValidationError


def extract_geometry_from_shapefile(uploaded_file):
    """
    Extract the first polygon geometry from an uploaded shapefile.

    Accepts:
      - A .zip archive containing .shp + companion files (.dbf, .shx …)
        The .shp may be at the root of the zip or inside a subdirectory.
      - A bare .shp file (uncommon but supported).

    Returns:
      str: Geometry string in the format '((lon1,lat1),(lon2,lat2),…)' (WGS84).

    Raises:
      ValidationError with a user-readable message on any error.
    """
    filename = getattr(uploaded_file, 'name', '') or ''

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write the uploaded bytes to a real file so GDAL can open it
            # without going through /vsimem/ (which causes the pyogrio error).
            safe_name = os.path.basename(filename) or 'upload.zip'
            tmp_upload = os.path.join(tmpdir, safe_name)
            with open(tmp_upload, 'wb') as fh:
                for chunk in uploaded_file.chunks():
                    fh.write(chunk)

            shp_path = _locate_shp(tmp_upload, tmpdir, filename)
            return _geometry_to_string(shp_path)

    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"Could not read shapefile: {exc}") from exc


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _locate_shp(tmp_upload, tmpdir, original_name):
    """
    Given the saved upload path, return the absolute path to the .shp file.
    Handles zip archives (with files at root or in subdirectories) and bare .shp uploads.
    """
    if zipfile.is_zipfile(tmp_upload):
        extract_dir = os.path.join(tmpdir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        _safe_extract(tmp_upload, extract_dir)

        shp_files = [
            os.path.join(root, f)
            for root, _dirs, files in os.walk(extract_dir)
            for f in files
            if f.lower().endswith('.shp')
        ]

        if not shp_files:
            raise ValidationError(
                "No .shp file found inside the zip archive. "
                "Make sure the zip contains at least a .shp file together "
                "with its companion .dbf and .shx files."
            )

        # If multiple .shp files exist, pick the first one alphabetically
        return sorted(shp_files)[0]

    if original_name.lower().endswith('.shp'):
        return tmp_upload

    raise ValidationError(
        "Unsupported file type. Please upload a .zip archive that contains "
        "the shapefile components (.shp, .dbf, .shx)."
    )


def _safe_extract(zip_path, dest_dir):
    """Extract a zip file, rejecting any entry that would escape dest_dir (zip-slip)."""
    real_dest = os.path.realpath(dest_dir)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            target = os.path.realpath(os.path.join(real_dest, member))
            if not target.startswith(real_dest + os.sep) and target != real_dest:
                raise ValidationError(
                    "Invalid zip file: path traversal entry detected."
                )
        zf.extractall(real_dest)


def _geometry_to_string(shp_path):
    """
    Read the first feature from a .shp file and return a coordinate string.

    - Reprojects to WGS84 (EPSG:4326) if the file uses a different CRS.
    - Accepts Polygon and MultiPolygon (uses the largest polygon of a MultiPolygon).
    """
    gdf = gpd.read_file(shp_path)

    if gdf.empty:
        raise ValidationError("The shapefile contains no features.")

    # Reproject to WGS84 when needed
    if gdf.crs is None:
        raise ValidationError(
            "The shapefile has no coordinate reference system (CRS) defined. "
            "Please re-export it with a CRS (e.g. EPSG:4326 or UTM)."
        )
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    geom = gdf.geometry.iloc[0]

    if geom is None or geom.is_empty:
        raise ValidationError("The first feature in the shapefile has no geometry.")

    if geom.geom_type == 'MultiPolygon':
        # Use the largest polygon
        geom = max(geom.geoms, key=lambda g: g.area)
    elif geom.geom_type != 'Polygon':
        raise ValidationError(
            f"Expected a Polygon or MultiPolygon, got '{geom.geom_type}'. "
            "Please upload a shapefile with polygon features."
        )

    coords = list(geom.exterior.coords)
    return '(' + ','.join(f'({x:.6f},{y:.6f})' for x, y in coords) + ')'
