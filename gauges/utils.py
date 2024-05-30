from math import asin, atan2, cos, degrees, radians, sin


def haversine_distance(lat1: float, lon1: float, distance_km: float, bearing: float) -> tuple[float, float]:
    R = 6371.0  # Earth radius in kilometers
    bearing = radians(bearing)

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = asin(sin(lat1) * cos(distance_km / R) + cos(lat1) * sin(distance_km / R) * cos(bearing))
    lon2 = lon1 + atan2(
        sin(bearing) * sin(distance_km / R) * cos(lat1),
        cos(distance_km / R) - sin(lat1) * sin(lat2),
    )

    return degrees(lat2), degrees(lon2)


def calculate_bbox(lat: float, lon: float, radius_km: float) -> str:
    lat_north, _lon_north = haversine_distance(lat, lon, radius_km, 0)
    lat_south, _lon_south = haversine_distance(lat, lon, radius_km, 180)
    _lat_east, lon_east = haversine_distance(lat, lon, radius_km, 90)
    _lat_west, lon_west = haversine_distance(lat, lon, radius_km, 270)

    return f"{min(lon_west, lon_east):.7f},{min(lat_south, lat_north):.7f},{max(lon_west, lon_east):.7f},{max(lat_south, lat_north):.7f}"
