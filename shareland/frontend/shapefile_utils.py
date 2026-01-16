import geopandas as gpd

def extract_geometry_from_shapefile(shapefile_path):
    """
    Extracts the geometry from a shapefile and returns it in a format suitable for Django.

    Args:
        shapefile_path (str): Path to the shapefile (.shp).

    Returns:
        str: Geometry in the format '((x1,y1),(x2,y2),...)'.
    """
    # Read the shapefile using geopandas
    gdf = gpd.read_file(shapefile_path)

    # Check if the GeoDataFrame is empty
    if gdf.empty:
        raise ValueError("The shapefile does not contain any geometries.")

    # Get the first geometry
    geometry = gdf.geometry.iloc[0]

    # Convert to a list of coordinates
    coords = list(geometry.exterior.coords)

    # Format the coordinates as a string
    formatted = '(' + ','.join(f'({x:.6f},{y:.6f})' for x, y in coords) + ')'

    return formatted