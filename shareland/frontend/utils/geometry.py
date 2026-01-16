"""
Geometry and map utilities for ShareLand frontend.
Handles parsing geometry strings and creating interactive Folium maps.
"""

import re
import folium


def parse_geometry_string(geometry_str):
    """
    Parse geometry string in format ((lon1,lat1),(lon2,lat2),...) 
    and return list of [lat, lon] tuples for Folium.
    
    Args:
        geometry_str: String representation of coordinates in format ((lon,lat),...)
        
    Returns:
        List of [lat, lon] tuples, or None if parsing fails
    """
    if not geometry_str:
        return None
    
    # Remove outer parentheses and split by coordinate pairs
    # Pattern: ((12.471998,41.846841),(12.473695,41.845806),...)
    geometry_str = geometry_str.strip()
    
    # Remove outer parentheses if present
    if geometry_str.startswith('((') and geometry_str.endswith('))'):
        geometry_str = geometry_str[1:-1]
    
    # Find all coordinate pairs using regex
    pattern = r'\(([\d.]+),([\d.]+)\)'
    matches = re.findall(pattern, geometry_str)
    
    if not matches:
        return None
    
    # Convert to list of [lat, lon] tuples (Folium expects lat, lon)
    coordinates = [[float(lat), float(lon)] for lon, lat in matches]
    
    return coordinates


def create_folium_map(geometry_str, research_title="Research Area"):
    """
    Create a Folium map with the geometry polygon.
    
    Args:
        geometry_str: String representation of coordinates
        research_title: Title to display on the map
        
    Returns:
        HTML string of the map, or None if geometry cannot be parsed
    """
    coordinates = parse_geometry_string(geometry_str)
    
    if not coordinates:
        return None
    
    # Calculate center of polygon
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Create map centered on polygon
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Add polygon to map
    folium.Polygon(
        locations=coordinates,
        color='blue',
        fill=True,
        fillColor='blue',
        fillOpacity=0.3,
        weight=2,
        popup=folium.Popup(research_title, max_width=300)
    ).add_to(m)
    
    # Add markers for first and last points
    if len(coordinates) > 0:
        folium.Marker(
            coordinates[0],
            popup=folium.Popup(f'Start point: {research_title}', max_width=200),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)
    
    # Convert map to HTML
    map_html = m._repr_html_()
    
    return map_html
