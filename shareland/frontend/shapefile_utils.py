import json
import os
import tempfile
import zipfile

import geopandas as gpd
from django.core.exceptions import ValidationError

# CRS candidates tried (in order) when the shapefile has no .prj file and
# the coordinates are clearly projected (not decimal degrees).
# Ordered by likelihood for Italian archaeological datasets.
_PROJECTED_CRS_CANDIDATES = [
    'EPSG:32633',  # WGS 84 / UTM zone 33N — Italian peninsula (12-18°E)
    'EPSG:32632',  # WGS 84 / UTM zone 32N — northern Italy / Alps (6-12°E)
    'EPSG:25833',  # ETRS89 / UTM zone 33N
    'EPSG:25832',  # ETRS89 / UTM zone 32N
    'EPSG:3004',   # Monte Mario / Italy zone 2 (false E 2 520 000, eastern)
    'EPSG:3003',   # Monte Mario / Italy zone 1 (false E 1 500 000, western)
    'EPSG:23033',  # ED50 / UTM zone 33N
    'EPSG:23032',  # ED50 / UTM zone 32N
]

# Geographic window for validation: Italy + surrounding area.
# Narrow enough to reject false positives (e.g. Gauss-Boaga mapping to Spain).
_EUROPE_BOUNDS = (5, 35, 20, 48)  # (min_lon, min_lat, max_lon, max_lat)


def extract_geojson_from_shapefile(uploaded_file):
    """
    Extract ALL features from an uploaded shapefile as a GeoJSON FeatureCollection.
    Supports Polygon, MultiPolygon, LineString, MultiLineString, Point, MultiPoint.
    Used for Evidence (multi-geometry support).
    """
    filename = getattr(uploaded_file, 'name', '') or ''
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_name = os.path.basename(filename) or 'upload.zip'
            tmp_upload = os.path.join(tmpdir, safe_name)
            with open(tmp_upload, 'wb') as fh:
                for chunk in uploaded_file.chunks():
                    fh.write(chunk)
            shp_path = _locate_shp(tmp_upload, tmpdir, filename)
            return _geojson_from_shp(shp_path)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"Could not read shapefile: {exc}") from exc


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

        return sorted(shp_files)[0]

    if original_name.lower().endswith('.shp'):
        return tmp_upload

    raise ValidationError(
        "Unsupported file type. Please upload a .zip archive that contains "
        "the shapefile components (.shp, .dbf, .shx)."
    )


def _safe_extract(zip_path, dest_dir):
    """Extract a zip, rejecting any entry that would escape dest_dir (zip-slip)."""
    real_dest = os.path.realpath(dest_dir)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            target = os.path.realpath(os.path.join(real_dest, member))
            if not target.startswith(real_dest + os.sep) and target != real_dest:
                raise ValidationError(
                    "Invalid zip file: path traversal entry detected."
                )
        zf.extractall(real_dest)


def _guess_crs(gdf):
    """
    Try to identify the CRS for a shapefile that has no .prj file.

    - If coordinates are in decimal-degree range → returns 'EPSG:4326'.
    - Otherwise tries common Italian/European projected CRS codes and picks
      the first one whose WGS-84 reprojection falls within Europe.
    - Returns None if no candidate matches.
    """
    minx, miny, maxx, maxy = gdf.total_bounds

    # Looks like geographic decimal degrees already
    if -180 <= minx and maxx <= 180 and -90 <= miny and maxy <= 90:
        return 'EPSG:4326'

    # Projected coordinates — probe candidates
    min_lon, min_lat, max_lon, max_lat = _EUROPE_BOUNDS
    for code in _PROJECTED_CRS_CANDIDATES:
        try:
            reprojected = gdf.set_crs(code, allow_override=True).to_crs('EPSG:4326')
            rx1, ry1, rx2, ry2 = reprojected.total_bounds
            if min_lon <= rx1 and rx2 <= max_lon and min_lat <= ry1 and ry2 <= max_lat:
                return code
        except Exception:
            continue

    return None


def _geometry_to_string(shp_path):
    """
    Read the first feature from a .shp file and return a WGS-84 coordinate string.

    - When no CRS is defined: auto-detects from coordinate range / common CRS list.
    - Reprojects to WGS84 (EPSG:4326) if the file uses a different CRS.
    - Accepts Polygon and MultiPolygon (uses the largest polygon of a MultiPolygon).
    """
    gdf = gpd.read_file(shp_path)

    if gdf.empty:
        raise ValidationError("The shapefile contains no features.")

    if gdf.crs is None:
        guessed = _guess_crs(gdf)
        if guessed is None:
            raise ValidationError(
                "The shapefile has no coordinate reference system (CRS) and the "
                "coordinates could not be identified automatically. "
                "Please re-export the file with an explicit CRS "
                "(e.g. EPSG:4326 for geographic or EPSG:32632 for UTM zone 32N)."
            )
        gdf = gdf.set_crs(guessed, allow_override=True).to_crs(epsg=4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    geom = gdf.geometry.iloc[0]

    if geom is None or geom.is_empty:
        raise ValidationError("The first feature in the shapefile has no geometry.")

    if geom.geom_type == 'MultiPolygon':
        geom = max(geom.geoms, key=lambda g: g.area)
    elif geom.geom_type != 'Polygon':
        raise ValidationError(
            f"Expected a Polygon or MultiPolygon, got '{geom.geom_type}'. "
            "Please upload a shapefile with polygon features."
        )

    coords = list(geom.exterior.coords)
    return '(' + ','.join(f'({x:.6f},{y:.6f})' for x, y in coords) + ')'


def _geojson_from_shp(shp_path):
    """Read all features, reproject to WGS84, return as GeoJSON FeatureCollection dict."""
    _SUPPORTED = {'Polygon', 'MultiPolygon', 'LineString', 'MultiLineString', 'Point', 'MultiPoint'}

    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        raise ValidationError("The shapefile contains no features.")

    if gdf.crs is None:
        guessed = _guess_crs(gdf)
        if guessed is None:
            raise ValidationError(
                "The shapefile has no CRS and it could not be identified automatically. "
                "Re-export with an explicit CRS (e.g. EPSG:4326 or EPSG:32632)."
            )
        gdf = gdf.set_crs(guessed, allow_override=True).to_crs(epsg=4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf = gdf[gdf.geometry.geom_type.isin(_SUPPORTED)]
    if gdf.empty:
        raise ValidationError(
            "No supported geometry types (Polygon, MultiPolygon, LineString, Point) "
            "found in the shapefile."
        )

    return json.loads(gdf[['geometry']].to_json())
