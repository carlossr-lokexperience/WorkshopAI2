from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import math
import networkx as nx
import osmnx as ox
import pandas as pd
import streamlit as st


@dataclass
class Stop:
    name: str
    lat: float
    lon: float
    kind: str = "stop"


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@st.cache_resource(show_spinner=False)
def load_graph(place_name: str):
    """
    Robust graph loader.

    Strategy:
    1. Try to obtain the place geometry.
    2. If the area is reasonably sized, use graph_from_place.
    3. If the area is too large or unavailable, geocode the place and use graph_from_point.
    """
    graph = None
    errors = []

    # Try to use place polygon if available and not huge
    try:
        gdf = ox.geocode_to_gdf(place_name)
        if gdf is not None and len(gdf) > 0:
            geom = gdf.geometry.iloc[0]
            centroid = geom.centroid
            center_lat = float(centroid.y)
            center_lon = float(centroid.x)

            bounds = geom.bounds
            west, south, east, north = bounds
            width_m = haversine_m((south + north) / 2, west, (south + north) / 2, east)
            height_m = haversine_m(south, (west + east) / 2, north, (west + east) / 2)

            max_dim_m = max(width_m, height_m)

            # If area is moderate, load full place graph
            if max_dim_m <= 25000:  # 25 km max dimension
                graph = ox.graph_from_place(place_name, network_type="drive", simplify=True)
            else:
                # Fallback to point graph around center
                dist = min(max(int(max_dim_m * 0.35), 3000), 12000)
                graph = ox.graph_from_point(
                    (center_lat, center_lon),
                    dist=dist,
                    network_type="drive",
                    simplify=True
                )
    except Exception as exc:
        errors.append(f"place-mode: {exc}")

    # If place mode failed, fallback to geocoded point
    if graph is None:
        try:
            lat, lon = ox.geocode(place_name)
            graph = ox.graph_from_point(
                (float(lat), float(lon)),
                dist=8000,
                network_type="drive",
                simplify=True
            )
        except Exception as exc:
            errors.append(f"point-mode: {exc}")

    if graph is None or len(graph.nodes) == 0:
        raise RuntimeError(
            f"Could not build a drivable graph for '{place_name}'. "
            f"Errors: {' | '.join(errors)}"
        )

    try:
        graph = ox.add_edge_speeds(graph)
        graph = ox.add_edge_travel_times(graph)
    except Exception:
        pass

    return graph


def geocode_place(query: str) -> Tuple[float, float]:
    lat, lon = ox.geocode(query)
    return float(lat), float(lon)


def snap_stop_to_graph(graph, stop: Stop):
    node = ox.distance.nearest_nodes(graph, X=stop.lon, Y=stop.lat)
    node = int(node)
    node_data = graph.nodes[node]

    snapped_lat = float(node_data["y"])
    snapped_lon = float(node_data["x"])
    snap_distance_m = haversine_m(stop.lat, stop.lon, snapped_lat, snapped_lon)

    return node, snapped_lat, snapped_lon, snap_distance_m


def shortest_path_nodes(graph, origin_node: int, dest_node: int, weight: str = "length") -> List[int]:
    return nx.shortest_path(graph, origin_node, dest_node, weight=weight)


def path_weight(graph, path: List[int], weight: str = "length") -> float:
    total = 0.0

    for u, v in zip(path[:-1], path[1:]):
        edge_data = graph.get_edge_data(u, v)
        if edge_data is None:
            continue

        best_key = min(edge_data, key=lambda k: edge_data[k].get(weight, float("inf")))
        total += float(edge_data[best_key].get(weight, 0.0))

    return total


def compute_pairwise_data(graph, stops: List[Stop], weight: str = "length"):
    snapped_info = [snap_stop_to_graph(graph, s) for s in stops]
    snapped_nodes = [x[0] for x in snapped_info]
    n = len(snapped_nodes)

    matrix = [[0 for _ in range(n)] for _ in range(n)]
    paths: Dict[Tuple[int, int], List[int]] = {}
    BIG_PENALTY = 10**9

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0
                paths[(i, j)] = [snapped_nodes[i]]
                continue

            try:
                path = shortest_path_nodes(graph, snapped_nodes[i], snapped_nodes[j], weight=weight)
                metric = path_weight(graph, path, weight=weight)
                matrix[i][j] = int(round(metric if metric > 0 else BIG_PENALTY))
                paths[(i, j)] = path
            except Exception:
                matrix[i][j] = BIG_PENALTY
                paths[(i, j)] = [snapped_nodes[i]]

    return snapped_info, matrix, paths


def route_metric_from_order(matrix: List[List[int]], order: List[int]) -> int:
    total = 0
    for i in range(len(order) - 1):
        total += int(matrix[order[i]][order[i + 1]])
    return total


def route_paths_from_order(paths: Dict[Tuple[int, int], List[int]], order: List[int]) -> List[List[int]]:
    segments = []
    for i in range(len(order) - 1):
        segments.append(paths[(order[i], order[i + 1])])
    return segments


def node_path_to_latlon(graph, node_path: List[int]) -> List[Tuple[float, float]]:
    coords = []
    for node in node_path:
        data = graph.nodes[node]
        coords.append((float(data["y"]), float(data["x"])))
    return coords


def segments_to_latlon(graph, segments: List[List[int]]) -> List[List[Tuple[float, float]]]:
    return [node_path_to_latlon(graph, seg) for seg in segments]


def build_summary_df(stops: List[Stop], order: List[int], snapped_info) -> pd.DataFrame:
    rows = []
    for position, idx in enumerate(order):
        s = stops[idx]
        _, slat, slon, snap_dist = snapped_info[idx]
        rows.append(
            {
                "visit_pos": position,
                "stop_index": idx,
                "name": s.name,
                "type": s.kind,
                "lat": s.lat,
                "lon": s.lon,
                "snap_lat": slat,
                "snap_lon": slon,
                "snap_distance_m": round(snap_dist, 1),
            }
        )
    return pd.DataFrame(rows)