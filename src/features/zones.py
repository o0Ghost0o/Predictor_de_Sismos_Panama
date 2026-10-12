"""5 disjoint Panama zones covering 6.8-10.0N, 83.5-77W."""
ZONES = {
    "BOCAS":    {"lat_min": 8.8, "lat_max": 10.0, "lon_min": -83.5, "lon_max": -81.8},
    "CHIRIQUI": {"lat_min": 6.8, "lat_max": 8.8,  "lon_min": -83.5, "lon_max": -81.8},
    "CENTRAL":  {"lat_min": 8.0, "lat_max": 10.0, "lon_min": -81.8, "lon_max": -79.0},
    "AZUERO":   {"lat_min": 6.8, "lat_max": 8.0,  "lon_min": -81.8, "lon_max": -79.0},
    "DARIEN":   {"lat_min": 6.8, "lat_max": 10.0, "lon_min": -79.0, "lon_max": -77.0},
}

def assign_zone(lat: float, lon: float) -> str | None:
    for name, b in ZONES.items():
        if b["lat_min"] <= lat <= b["lat_max"] and b["lon_min"] <= lon <= b["lon_max"]:
            return name
    return None

def centroid(zone: str) -> tuple[float, float]:
    b = ZONES[zone]
    return ((b["lat_min"] + b["lat_max"]) / 2, (b["lon_min"] + b["lon_max"]) / 2)
