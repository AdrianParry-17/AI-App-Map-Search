from __future__ import annotations

from collections import deque

from app.config import DEFAULT_DATASET_PATH
from app.costs import CostWeights
from app.engine import RoutingEngine
from app.loader import load_dataset


def test_default_osm_snapshot_loads_with_attribution_and_oriented_geometry():
    metadata, graph = load_dataset(DEFAULT_DATASET_PATH)
    assert metadata.id == "danang-central-emergency-osm-2026"
    assert metadata.license == "ODbL-1.0"
    assert metadata.attribution == "© OpenStreetMap contributors"
    assert len(graph.nodes) == 512
    assert len(graph.edges) == 1007
    for edge in graph.edges.values():
        geometry = graph.edge_coordinates(edge.id)
        source = graph.node(edge.source)
        target = graph.node(edge.target)
        assert geometry[0] == [source.lon, source.lat]
        assert geometry[-1] == [target.lon, target.lat]

    # Every hospital is intended to be an emergency destination. The snapshot
    # connectors must therefore place all hospitals in the mutually reachable
    # road component despite nearby one-way OSM segments.
    hospitals = [node.id for node in graph.nodes.values() if node.kind == "hospital"]
    for start in hospitals:
        reached = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for edge in graph.neighbors(current):
                if edge.target not in reached:
                    reached.add(edge.target)
                    queue.append(edge.target)
        assert set(hospitals) <= reached


def test_search_route_uses_osm_polyline_vertices():
    metadata, graph = load_dataset(DEFAULT_DATASET_PATH)
    engine = RoutingEngine(metadata, graph)
    response = engine.search(
        start_id="hospital_node_729405662",
        goal_id="hospital_node_6539587371",
        algorithm="astar",
        heuristic="travel_time",
        scenario="normal",
        weights=CostWeights(),
        include_trace=False,
        max_trace_events=0,
        max_expansions=100_000,
        include_alternative=False,
    )
    assert response["found"]
    assert len(response["route_geojson"]["coordinates"]) > len(response["path"])
    expected_count = sum(len(graph.edge_coordinates(edge_id)) for edge_id in response["edge_ids"])
    expected_count -= max(0, len(response["edge_ids"]) - 1)
    assert len(response["route_geojson"]["coordinates"]) == expected_count
