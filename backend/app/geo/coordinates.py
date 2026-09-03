"""Geo-coordinate utility functions for UdyamAI.

Provides conversions between lat/lng and WKT POINT format for PostGIS,
and a haversine distance function for verification/sorting.
"""

import math

# Earth's mean radius in meters
_EARTH_RADIUS_M = 6_371_000


def lat_lng_to_wkt(lat: float, lng: float) -> str:
    """Convert latitude/longitude to WKT POINT for PostGIS.

    WKT POINT format: 'POINT(lng lat)' — note lng first (GeoJSON/X-axis convention).
    """
    return f"POINT({lng} {lat})"


def wkt_to_lat_lng(wkt: str) -> tuple[float, float]:
    """Convert WKT POINT string back to (lat, lng).

    WKT POINT format: 'POINT(lng lat)' — returns (lat, lng).
    """
    coords = wkt.replace("POINT(", "").replace(")", "").strip().split()
    lng = float(coords[0])
    lat = float(coords[1])
    return lat, lng


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two points in meters.

    Uses the haversine formula — accurate enough for distances < 500 km.
    """
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return _EARTH_RADIUS_M * c


def km_to_meters(km: float) -> float:
    """Convert kilometers to meters."""
    return km * 1000.0


def meters_to_km(meters: float) -> float:
    """Convert meters to kilometers."""
    return meters / 1000.0
