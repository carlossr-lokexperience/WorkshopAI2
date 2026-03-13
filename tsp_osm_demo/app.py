from __future__ import annotations

import random
from typing import List

import folium
import streamlit as st
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from streamlit_folium import st_folium

from routing import (
    Stop,
    build_summary_df,
    compute_pairwise_data,
    geocode_place,
    load_graph,
    route_metric_from_order,
    route_paths_from_order,
    segments_to_latlon,
)

st.set_page_config(page_title="TSP Urban Demo", layout="wide")

DEFAULT_PLACE = "Madrid, Spain"


# -----------------------------
# SESSION STATE
# -----------------------------

if "place_name" not in st.session_state:
    st.session_state.place_name = DEFAULT_PLACE

if "graph" not in st.session_state:
    st.session_state.graph = None

if "stops" not in st.session_state:
    st.session_state.stops: List[Stop] = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "graph_loaded_for" not in st.session_state:
    st.session_state.graph_loaded_for = None

if "status_msg" not in st.session_state:
    st.session_state.status_msg = ""


# -----------------------------
# HELPERS
# -----------------------------

def format_metric(value, metric_name):
    if value >= 10**9:
        return "unreachable"

    if metric_name == "length":
        return f"{value / 1000:.2f} km"
    elif metric_name == "travel_time":
        return f"{value / 60:.1f} min"
    return f"{value:.0f}"


def solve_tsp_ortools(distance_matrix: List[List[int]]) -> List[int]:
    n = len(distance_matrix)
    if n < 2:
        return [0]

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 5

    solution = routing.SolveWithParameters(search_parameters)
    if solution is None:
        raise RuntimeError("OR-Tools could not find a TSP solution.")

    order = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        order.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    order.append(manager.IndexToNode(index))

    return order


def create_base_map(center, zoom_start=12):
    return folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles="OpenStreetMap",
        control_scale=True
    )


def add_stops_to_map(m, stops: List[Stop]):
    bounds = []

    for i, stop in enumerate(stops):
        color = "red" if stop.kind == "depot" else "blue"

        folium.Marker(
            location=[stop.lat, stop.lon],
            popup=f"{i} - {stop.name}",
            tooltip=f"{i} - {stop.name}",
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

        bounds.append((stop.lat, stop.lon))

    if bounds:
        m.fit_bounds(bounds)

    return m


def add_snapped_points_to_map(m, snapped_info):
    for i, (_, lat, lon, snap_dist) in enumerate(snapped_info):
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color="darkgreen",
            fill=True,
            fill_opacity=0.9,
            popup=f"Snapped node {i} ({snap_dist:.1f} m away)"
        ).add_to(m)
    return m


def add_stop_snap_connectors(m, stops, snapped_info):
    for stop, (_, slat, slon, _) in zip(stops, snapped_info):
        folium.PolyLine(
            [[stop.lat, stop.lon], [slat, slon]],
            color="black",
            weight=1.5,
            opacity=0.45,
            dash_array="4,4"
        ).add_to(m)
    return m


def add_route_segments(m, route_segments_latlon, color="green", weight=5, opacity=0.85):
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


def random_stops_around_center(center_lat: float, center_lon: float, n: int = 6):
    stops = []
    for i in range(n):
        lat = center_lat + random.uniform(-0.03, 0.03)
        lon = center_lon + random.uniform(-0.04, 0.04)
        stops.append(
            Stop(
                name=f"demo_stop_{i+1}",
                lat=lat,
                lon=lon,
                kind="stop"
            )
        )
    return stops


def invalidate_graph_if_place_changed(new_place_name: str):
    new_place_name = new_place_name.strip()
    current_place = st.session_state.place_name.strip()

    if new_place_name and new_place_name != current_place:
        st.session_state.place_name = new_place_name
        st.session_state.graph = None
        st.session_state.graph_loaded_for = None
        st.session_state.last_result = None
        st.session_state.stops = []
        st.session_state.status_msg = f"Location changed to: {new_place_name}. Load or auto-load new network."


# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:
    st.header("Configuration")

    place_name_input = st.text_input("Place / area", value=st.session_state.place_name)
    invalidate_graph_if_place_changed(place_name_input)

    route_weight = st.selectbox(
        "Optimization metric",
        options=["length", "travel_time"],
        index=0,
        help="length = meters, travel_time = seconds (if available)"
    )

    if st.button("Load street network", use_container_width=True):
        try:
            st.session_state.graph = load_graph(st.session_state.place_name)
            st.session_state.graph_loaded_for = st.session_state.place_name
            st.session_state.last_result = None
            st.session_state.status_msg = f"Street network loaded for: {st.session_state.place_name}"
        except Exception as e:
            st.session_state.graph = None
            st.session_state.status_msg = f"Could not load network: {e}"

    if st.button("Clear stops", use_container_width=True):
        st.session_state.stops = []
        st.session_state.last_result = None
        st.session_state.status_msg = "Stops cleared."

    if st.button("Load demo stops", use_container_width=True):
        try:
            if (
                st.session_state.graph is None
                or st.session_state.graph_loaded_for != st.session_state.place_name
            ):
                st.session_state.graph = load_graph(st.session_state.place_name)
                st.session_state.graph_loaded_for = st.session_state.place_name

            center_lat, center_lon = geocode_place(st.session_state.place_name)
            demo = random_stops_around_center(center_lat, center_lon, n=6)

            st.session_state.stops = [
                Stop(name="Depot", lat=center_lat, lon=center_lon, kind="depot"),
                *demo
            ]
            st.session_state.last_result = None
            st.session_state.status_msg = f"Demo stops loaded for {st.session_state.place_name}."
        except Exception as e:
            st.session_state.status_msg = f"Could not generate demo stops: {e}"

    st.divider()
    st.subheader("Add stop manually")

    stop_name = st.text_input("Stop label", value="")
    stop_query = st.text_input("Address / place", value="")

    if st.button("Add stop", use_container_width=True):
        if not stop_query.strip():
            st.session_state.status_msg = "Write an address or place first."
        else:
            try:
                # Make sure graph corresponds to current place
                if (
                    st.session_state.graph is None
                    or st.session_state.graph_loaded_for != st.session_state.place_name
                ):
                    st.session_state.graph = load_graph(st.session_state.place_name)
                    st.session_state.graph_loaded_for = st.session_state.place_name

                lat, lon = geocode_place(stop_query.strip())
                kind = "depot" if len(st.session_state.stops) == 0 else "stop"
                name = stop_name.strip() if stop_name.strip() else stop_query.strip()

                st.session_state.stops.append(
                    Stop(name=name, lat=lat, lon=lon, kind=kind)
                )
                st.session_state.last_result = None
                st.session_state.status_msg = f"Added: {name}"
            except Exception as e:
                st.session_state.status_msg = f"Could not geocode stop: {e}"

    st.divider()
    solve_clicked = st.button("Solve TSP", type="primary", use_container_width=True)


# -----------------------------
# HEADER
# -----------------------------

st.title("🗺️ TSP Urban Demo on Real Streets")
st.caption("OpenStreetMap + OSMnx + OR-Tools + Folium + Streamlit")

if st.session_state.status_msg:
    st.info(st.session_state.status_msg)


# -----------------------------
# AUTO LOAD CURRENT PLACE GRAPH
# -----------------------------

if (
    st.session_state.graph is None
    or st.session_state.graph_loaded_for != st.session_state.place_name
):
    try:
        with st.spinner(f"Loading street network for {st.session_state.place_name}..."):
            st.session_state.graph = load_graph(st.session_state.place_name)
            st.session_state.graph_loaded_for = st.session_state.place_name
    except Exception as e:
        st.error(f"Could not download street network for this place: {e}")


# -----------------------------
# SOLVE TSP
# -----------------------------

if solve_clicked:
    if st.session_state.graph is None:
        st.error("Load a street network first.")
    elif len(st.session_state.stops) < 3:
        st.warning("Add at least 3 stops (including the depot) to solve TSP.")
    else:
        try:
            graph = st.session_state.graph
            stops = st.session_state.stops

            with st.spinner("Computing distance matrix and solving TSP..."):
                snapped_info, matrix, paths = compute_pairwise_data(graph, stops, weight=route_weight)

                manual_order = list(range(len(stops))) + [0]
                tsp_order = solve_tsp_ortools(matrix)

                manual_metric = route_metric_from_order(matrix, manual_order)
                tsp_metric = route_metric_from_order(matrix, tsp_order)

                manual_segments = route_paths_from_order(paths, manual_order)
                tsp_segments = route_paths_from_order(paths, tsp_order)

                manual_segments_latlon = segments_to_latlon(graph, manual_segments)
                tsp_segments_latlon = segments_to_latlon(graph, tsp_segments)

                summary_df = build_summary_df(stops, tsp_order[:-1], snapped_info)

                st.session_state.last_result = {
                    "manual_order": manual_order,
                    "tsp_order": tsp_order,
                    "manual_metric": manual_metric,
                    "tsp_metric": tsp_metric,
                    "manual_segments_latlon": manual_segments_latlon,
                    "tsp_segments_latlon": tsp_segments_latlon,
                    "summary_df": summary_df,
                    "metric_name": route_weight,
                    "matrix": matrix,
                    "snapped_info": snapped_info,
                }

                st.session_state.status_msg = "TSP solved successfully."

        except Exception as e:
            st.session_state.last_result = None
            st.error(f"Could not solve TSP: {e}")


# -----------------------------
# LAYOUT
# -----------------------------

left_col, right_col = st.columns([2.2, 1.1])

with left_col:
    st.subheader("Map")

    if len(st.session_state.stops) > 0:
        center = [st.session_state.stops[0].lat, st.session_state.stops[0].lon]
    else:
        try:
            lat, lon = geocode_place(st.session_state.place_name)
            center = [lat, lon]
        except Exception:
            center = [40.4168, -3.7038]

    m = create_base_map(center=center, zoom_start=12)
    m = add_stops_to_map(m, st.session_state.stops)

    if st.session_state.last_result is not None:
        m = add_snapped_points_to_map(m, st.session_state.last_result["snapped_info"])
        m = add_stop_snap_connectors(m, st.session_state.stops, st.session_state.last_result["snapped_info"])

        m = add_route_segments(
            m,
            st.session_state.last_result["manual_segments_latlon"],
            color="gray",
            weight=4,
            opacity=0.45
        )
        m = add_route_segments(
            m,
            st.session_state.last_result["tsp_segments_latlon"],
            color="green",
            weight=6,
            opacity=0.9
        )

    st_folium(m, height=720, use_container_width=True)


with right_col:
    st.subheader("Stops")

    if len(st.session_state.stops) == 0:
        st.info("No stops added yet.")
    else:
        preview_rows = []
        for i, s in enumerate(st.session_state.stops):
            preview_rows.append({
                "idx": i,
                "name": s.name,
                "type": s.kind,
                "lat": round(s.lat, 6),
                "lon": round(s.lon, 6),
            })
        st.dataframe(preview_rows, use_container_width=True)

    if st.session_state.last_result is not None:
        st.subheader("Optimized route")

        metric_name = st.session_state.last_result["metric_name"]
        manual_metric = st.session_state.last_result["manual_metric"]
        tsp_metric = st.session_state.last_result["tsp_metric"]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Manual route", format_metric(manual_metric, metric_name))
        with col2:
            st.metric("TSP route", format_metric(tsp_metric, metric_name))

        if manual_metric < 10**9 and tsp_metric < 10**9 and manual_metric > 0:
            improvement = 100 * (manual_metric - tsp_metric) / manual_metric
            st.metric("Improvement", f"{improvement:.1f}%")
        else:
            st.metric("Improvement", "N/A")

        st.caption(f"Metric used: {metric_name}")

        st.dataframe(
            st.session_state.last_result["summary_df"],
            use_container_width=True
        )

        with st.expander("Distance matrix"):
            st.dataframe(st.session_state.last_result["matrix"], use_container_width=True)
    else:
        st.info("Solve the TSP to see route metrics and visit order.")