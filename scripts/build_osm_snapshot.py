"""Build a compact, directed teaching graph from a bounded Overpass response.

This script deliberately has no runtime geospatial dependency. It contracts OSM shape
points between intersections, preserves one-way direction, retains the original OSM ids
and geometry, and snaps hospital POIs onto the retained road graph. Traffic and hazard
values are deterministic educational overlays—not observations from OpenStreetMap.

Example:
    python scripts/build_osm_snapshot.py --input overpass.json \
        --output backend/data/da_nang_osm_snapshot.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


BBOX = [16.035, 108.190, 16.090, 108.250]
ROAD_CLASSES = {"primary", "secondary", "tertiary"}
DEFAULT_SPEED = {"primary": 50.0, "secondary": 40.0, "tertiary": 35.0}
BASE_RISK = {"primary": 0.08, "secondary": 0.12, "tertiary": 0.16}


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6_371_008.8 * math.asin(math.sqrt(value))


def stable_fraction(value: str) -> float:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / (2**64 - 1)


def parse_speed(value: Any, fallback: float) -> float:
    if isinstance(value, list):
        value = value[0] if value else None
    if not value:
        return fallback
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    if not match:
        return fallback
    speed = float(match.group(1))
    if "mph" in str(value).lower():
        speed *= 1.60934
    return min(90.0, max(10.0, speed))


def one_way_mode(tags: dict[str, Any]) -> int:
    value = str(tags.get("oneway", "")).lower()
    if value in {"-1", "reverse"}:
        return -1
    if value in {"yes", "true", "1"} or tags.get("junction") == "roundabout":
        return 1
    return 0


def largest_component(adjacency: dict[int, set[int]]) -> set[int]:
    unseen = set(adjacency)
    components: list[set[int]] = []
    while unseen:
        seed = next(iter(unseen))
        component = {seed}
        queue = deque([seed])
        unseen.remove(seed)
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return max(components, key=len)


def feature_center(element: dict[str, Any], coordinates: dict[int, tuple[float, float]]) -> tuple[float, float] | None:
    if element["type"] == "node":
        return float(element["lat"]), float(element["lon"])
    points = [coordinates[node_id] for node_id in element.get("nodes", []) if node_id in coordinates]
    if not points:
        return None
    return sum(point[0] for point in points) / len(points), sum(point[1] for point in points) / len(points)


def iter_pairs(values: Iterable[int]) -> Iterable[tuple[int, int]]:
    iterator = iter(values)
    try:
        previous = next(iterator)
    except StopIteration:
        return
    for current in iterator:
        yield previous, current
        previous = current


def build_snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    elements = raw.get("elements", [])
    coordinates = {
        int(element["id"]): (float(element["lat"]), float(element["lon"]))
        for element in elements
        if element.get("type") == "node" and "lat" in element and "lon" in element
    }
    road_ways = [
        element for element in elements
        if element.get("type") == "way" and element.get("tags", {}).get("highway") in ROAD_CLASSES
    ]
    if not road_ways:
        raise ValueError("The response contains no primary/secondary/tertiary road ways")

    adjacency: dict[int, set[int]] = defaultdict(set)
    segment_records: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    incident_records: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for way in road_ways:
        tags = way.get("tags", {})
        road_class = str(tags["highway"])
        record = {
            "way_id": int(way["id"]),
            "name": str(tags.get("name") or tags.get("ref") or "Đường chưa đặt tên"),
            "road_class": road_class,
            "speed_kph": parse_speed(tags.get("maxspeed"), DEFAULT_SPEED[road_class]),
            "mode": one_way_mode(tags),
            "bridge": str(tags.get("bridge", "")).lower() not in {"", "no", "false", "0"},
            "tunnel": str(tags.get("tunnel", "")).lower() not in {"", "no", "false", "0"},
            "lanes": tags.get("lanes"),
            "surface": tags.get("surface"),
        }
        way_nodes = [int(value) for value in way.get("nodes", []) if int(value) in coordinates]
        for index, (source, target) in enumerate(iter_pairs(way_nodes)):
            adjacency[source].add(target)
            adjacency[target].add(source)
            directional = {**record, "way_forward": (source, target)}
            segment_records[tuple(sorted((source, target)))].append(directional)
            incident_records[source].append(directional)
            incident_records[target].append(directional)

    component = largest_component(adjacency)
    adjacency = {node: {neighbor for neighbor in neighbors if neighbor in component} for node, neighbors in adjacency.items() if node in component}
    junctions = {node for node, neighbors in adjacency.items() if len(neighbors) != 2}
    if not junctions:
        junctions.add(next(iter(component)))

    def direction_allowed(source: int, target: int) -> bool:
        records = segment_records[tuple(sorted((source, target)))]
        for record in records:
            forward = tuple(record["way_forward"]) == (source, target)
            if record["mode"] == 0 or (record["mode"] == 1 and forward) or (record["mode"] == -1 and not forward):
                return True
        return False

    collapsed_paths: list[list[int]] = []
    visited_segments: set[tuple[int, int]] = set()
    for origin in sorted(junctions):
        for first in sorted(adjacency[origin]):
            segment_key = tuple(sorted((origin, first)))
            if segment_key in visited_segments:
                continue
            path = [origin, first]
            visited_segments.add(segment_key)
            previous, current = origin, first
            safety = 0
            while current not in junctions:
                candidates = adjacency[current] - {previous}
                if not candidates:
                    break
                following = next(iter(candidates))
                key = tuple(sorted((current, following)))
                if key in visited_segments:
                    break
                path.append(following)
                visited_segments.add(key)
                previous, current = current, following
                safety += 1
                if safety > len(component):
                    raise RuntimeError("Cycle guard tripped while contracting the road graph")
            if len(path) >= 2 and path[-1] in junctions and path[0] != path[-1]:
                collapsed_paths.append(path)

    road_names_by_junction: dict[int, list[str]] = {}
    for node_id in junctions:
        names = [record["name"] for record in incident_records[node_id] if record["name"] != "Đường chưa đặt tên"]
        road_names_by_junction[node_id] = [name for name, _ in Counter(names).most_common(3)]

    nodes: list[dict[str, Any]] = []
    for node_id in sorted(junctions):
        names = road_names_by_junction[node_id]
        adjacent_records = incident_records[node_id]
        is_bridge_access = any(record["bridge"] for record in adjacent_records)
        if len(names) >= 2:
            display_name = f"{names[0]} × {names[1]}"
        elif names:
            display_name = f"Nút {names[0]}"
        else:
            display_name = f"Giao lộ OSM {node_id}"
        degree = len(adjacency[node_id])
        nodes.append({
            "id": f"osm_{node_id}",
            "name": display_name,
            "kind": "bridge_access" if is_bridge_access else "gateway" if degree == 1 else "intersection",
            "lat": round(coordinates[node_id][0], 7),
            "lon": round(coordinates[node_id][1], 7),
            "attributes": {
                "osm_node_id": node_id,
                "road_names": names,
                "raw_degree": degree,
            },
        })

    edges: list[dict[str, Any]] = []
    for path_index, path in enumerate(collapsed_paths):
        pairs = list(iter_pairs(path))
        distance = sum(haversine_m(coordinates[source], coordinates[target]) for source, target in pairs)
        records = [record for source, target in pairs for record in segment_records[tuple(sorted((source, target)))]]
        weighted_names = Counter(record["name"] for record in records)
        road_names = [name for name, _ in weighted_names.most_common(2)]
        road_name = " / ".join(road_names)
        road_class = Counter(record["road_class"] for record in records).most_common(1)[0][0]
        speed = min(record["speed_kph"] for record in records)
        forward_allowed = all(direction_allowed(source, target) for source, target in pairs)
        backward_allowed = all(direction_allowed(target, source) for source, target in pairs)
        flags = {
            "bridge": any(record["bridge"] for record in records),
            "tunnel": any(record["tunnel"] for record in records),
        }
        seed = f"{path[0]}:{path[-1]}:{road_name}"
        simulated_flood_prone = stable_fraction(seed + ":flood") < (0.18 if flags["bridge"] else 0.10)
        incident_prone = stable_fraction(seed + ":incident") < 0.09
        close_during_incident = stable_fraction(seed + ":closure") < 0.025
        risk = BASE_RISK[road_class] + (0.10 if flags["bridge"] else 0.0) + (0.08 if simulated_flood_prone else 0.0)
        attributes = {
            "osm_way_ids": sorted({record["way_id"] for record in records}),
            "geometry": [[round(coordinates[node][1], 7), round(coordinates[node][0], 7)] for node in path],
            "bridge": flags["bridge"],
            "tunnel": flags["tunnel"],
            "flood_prone": simulated_flood_prone,
            "incident_prone": incident_prone,
            "close_during_incident": close_during_incident,
            "overlay_provenance": "deterministic synthetic educational layer",
        }
        edge_id = f"osm_path_{path_index}_{path[0]}_{path[-1]}"
        base = {
            "distance_m": round(max(distance, 1.0), 2),
            "speed_kph": round(speed, 1),
            "road_name": road_name,
            "road_class": road_class,
            "risk": round(min(risk, 1.0), 3),
            "emergency_access": True,
            "attributes": attributes,
        }
        if forward_allowed and backward_allowed:
            edges.append({
                "id": edge_id,
                "source": f"osm_{path[0]}",
                "target": f"osm_{path[-1]}",
                "bidirectional": True,
                "reverse_id": f"{edge_id}__reverse",
                **base,
            })
        else:
            if forward_allowed:
                edges.append({"id": f"{edge_id}__forward", "source": f"osm_{path[0]}", "target": f"osm_{path[-1]}", "bidirectional": False, **base})
            if backward_allowed:
                edges.append({"id": f"{edge_id}__backward", "source": f"osm_{path[-1]}", "target": f"osm_{path[0]}", "bidirectional": False, **base})

    hospital_elements = [
        element for element in elements
        if element.get("type") in {"node", "way"}
        and element.get("tags", {}).get("amenity") == "hospital"
        and element.get("tags", {}).get("name")
    ]
    junction_positions = [(node_id, coordinates[node_id]) for node_id in junctions]
    seen_hospital_names: set[str] = set()
    for hospital in sorted(hospital_elements, key=lambda item: (str(item.get("tags", {}).get("name")), int(item["id"]))):
        name = str(hospital["tags"]["name"]).strip()
        normalized_name = re.sub(r"\W+", "", name.casefold())
        if not normalized_name or normalized_name in seen_hospital_names:
            continue
        center = feature_center(hospital, coordinates)
        if center is None:
            continue
        nearest_id, nearest_position = min(junction_positions, key=lambda item: haversine_m(center, item[1]))
        access_distance = haversine_m(center, nearest_position)
        if access_distance > 1_500:
            continue
        seen_hospital_names.add(normalized_name)
        hospital_id = f"hospital_{hospital['type']}_{hospital['id']}"
        nodes.append({
            "id": hospital_id,
            "name": name,
            "kind": "hospital",
            "lat": round(center[0], 7),
            "lon": round(center[1], 7),
            "attributes": {
                "osm_type": hospital["type"],
                "osm_id": int(hospital["id"]),
                "emergency_destination": True,
                "snap_distance_m": round(access_distance, 2),
            },
        })
        edges.append({
            "id": f"hospital_access_{hospital['type']}_{hospital['id']}",
            "source": hospital_id,
            "target": f"osm_{nearest_id}",
            "distance_m": round(max(access_distance, 20.0), 2),
            "speed_kph": 20.0,
            "road_name": f"Lối tiếp cận {name}",
            "road_class": "service",
            "risk": 0.05,
            "emergency_access": True,
            "bidirectional": True,
            "attributes": {
                "synthetic_access_connector": True,
                "geometry": [[round(center[1], 7), round(center[0], 7)], [round(nearest_position[1], 7), round(nearest_position[0], 7)]],
                "overlay_provenance": "POI snapped to nearest retained OSM road junction",
            },
        })

    if len(nodes) < 20 or len(edges) < 30:
        raise ValueError(f"Dataset below lab minimum: {len(nodes)} nodes, {len(edges)} edges")

    timestamp = raw.get("osm3s", {}).get("timestamp_osm_base")
    return {
        "metadata": {
            "id": "danang-central-emergency-osm-2026",
            "name": "Đà Nẵng Central Emergency Mobility Graph",
            "city": "Đà Nẵng",
            "country": "Việt Nam",
            "version": "1.0.0",
            "source": "OpenStreetMap contributors via bounded Overpass snapshot; ODbL 1.0",
            "source_url": "https://www.openstreetmap.org/copyright",
            "overpass_query": "scripts/overpass_danang.ql",
            "osm_base_timestamp": timestamp,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bbox": BBOX,
            "network_filter": "primary|secondary|tertiary",
            "description": "Contracted directed road topology for an ambulance-routing AI search laboratory.",
            "disclaimer": "Road topology/tags come from OSM. Congestion, incidents, closures, flood susceptibility, risk and ETA are deterministic educational simulations—not live traffic or emergency advice.",
            "license": "ODbL-1.0",
            "attribution": "© OpenStreetMap contributors",
            "stats": {
                "raw_osm_road_nodes": len(component),
                "raw_osm_ways": len(road_ways),
                "contracted_road_nodes": len(junctions),
                "hospital_pois": len(seen_hospital_names),
                "stored_nodes": len(nodes),
                "stored_base_edges": len(edges),
            },
        },
        "nodes": nodes,
        "edges": edges,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Overpass JSON response")
    parser.add_argument("--output", type=Path, required=True, help="Output teaching-graph JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.input.open("r", encoding="utf-8") as source:
        raw = json.load(source)
    snapshot = build_snapshot(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as destination:
        json.dump(snapshot, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    stats = snapshot["metadata"]["stats"]
    print(f"Wrote {args.output}: {stats['stored_nodes']} nodes, {stats['stored_base_edges']} base edges")


if __name__ == "__main__":
    main()
