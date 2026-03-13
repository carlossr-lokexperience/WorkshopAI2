import folium


def create_base_map(center, zoom_start=14):
    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles="OpenStreetMap",
        control_scale=True
    )
    return m


def add_stops_to_map(m, stops):
    bounds = []

    for i, stop in enumerate(stops):
        color = "red" if stop.kind == "depot" else "blue"

        folium.Marker(
            location=[stop.lat, stop.lon],
            popup=f"{i} - {stop.name}",
            tooltip=f"{i} - {stop.name}",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

        bounds.append((stop.lat, stop.lon))

    if bounds:
        m.fit_bounds(bounds)

    return m


def add_route_segments(m, route_segments_latlon, color="green", weight=5, opacity=0.8):
    all_points = []

    for segment in route_segments_latlon:
        if len(segment) >= 2:
            folium.PolyLine(
                segment,
                color=color,
                weight=weight,
                opacity=opacity
            ).add_to(m)

            all_points.extend(segment)

    if all_points:
        m.fit_bounds(all_points)

    return m