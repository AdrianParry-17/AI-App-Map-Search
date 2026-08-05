# Da Nang Emergency Route Lab — backend

FastAPI backend for comparing classical search algorithms on a directed central
Da Nang road graph. The search core is standard-library Python and does **not**
use NetworkX. Traffic is a deterministic teaching overlay, not a live feed.

> Safety: the bundled road topology is an offline OSM-derived snapshot, while
> traffic/risk overlays are educational simulations. It is not a live or
> safety-certified dispatch graph. Never use it for actual emergency response.

## Run locally

Python 3.11–3.13 is recommended for the most predictable package support.

```powershell
cd backend
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI is at `http://127.0.0.1:8000/docs`. The React development origins
`localhost:5173`, `127.0.0.1:5173`, `localhost:4173` and `127.0.0.1:4173` are
enabled by default.

Run tests from this directory with `python -m pytest`.

## API (`/api/v1`)

- `GET /health` — process/dataset readiness.
- `GET /metadata` — algorithm, heuristic, traffic, optimizer and trace registries.
- `GET /graph?scenario=normal` — nodes and directed edges with scenario-adjusted
  traffic status, oriented edge polylines, and a GeoJSON FeatureCollection.
- `POST /search` — one start/goal run and a deterministic alternative route.
- `POST /compare` — run 2–8 algorithms under identical conditions.
- `POST /multi-route` — visit several stops using nearest-neighbor, exact
  Held–Karp, 2-opt, or seeded simulated annealing + 2-opt.

### Pair search request

```json
{
  "start_id": "emergency_115",
  "goal_id": "family_hospital",
  "algorithm": "astar",
  "heuristic": "travel_time",
  "scenario": "morning_rush",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.5,
    "traffic_delay": 0.2,
    "risk": 0.05
  },
  "include_trace": true,
  "max_trace_events": 1000,
  "max_expansions": 100000,
  "include_alternative": true
}
```

Algorithm IDs: `bfs`, `dfs`, `ucs`, `dijkstra`, `astar`,
`greedy_best_first`, `bidirectional_dijkstra`, `ida_star`.

Heuristic IDs: `zero`, `haversine`, `travel_time`, `traffic_aware`. Metadata
marks the first three admissible; `traffic_aware` intentionally demonstrates a
potentially faster but non-admissible estimate.

Scenario IDs: `normal`, `morning_rush`, `evening_rush`, `heavy_rain`,
`incident`.

Every successful pair response has this stable top-level shape:

```text
request_id, status, found, start_id, goal_id,
algorithm, heuristic, scenario,
path, edge_ids, route_geojson,
metrics, trace, explanation, alternative, cost_breakdown
```

`path` is an ordered node-ID array. `edge_ids` has exactly `len(path) - 1`
items. `route_geojson` is a GeoJSON `LineString` with `[longitude, latitude]`
coordinates assembled from each stored OSM edge polyline (not straight node
chords). `cost_breakdown.total_cost` equals `metrics.path_cost`.

Trace events always contain:

```text
step, event, node_id, parent_id, edge_id, direction,
frontier_size, explored_count, g_cost, h_cost, f_cost, depth, message
```

This lets React animate every algorithm with one renderer. Bidirectional
Dijkstra uses `direction: "forward" | "backward"`; other algorithms use
`forward`.

### Compare request

Uses the pair fields plus an `algorithms` array. `include_alternative` is omitted.
The response contains `runs`, cost/expansion `ranking`, `best_algorithm`, and
route `agreement` groups.

### Multi-route request

```json
{
  "start_id": "emergency_115",
  "stop_ids": ["dn_hospital", "family_hospital", "son_tra_clinic"],
  "method": "held_karp",
  "return_to_start": true,
  "scenario": "normal",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.5,
    "traffic_delay": 0.2,
    "risk": 0.05
  },
  "seed": 42,
  "max_iterations": 1000,
  "max_expansions": 100000
}
```

`held_karp` is capped at 10 stops; requests overall are capped at 12. All
pairwise legs use exact Dijkstra. Approximate optimizers are reproducible for a
given seed and input.

## OSM snapshot and replacement datasets

The default is `data/da_nang_osm_snapshot.json` (offline, bounded, with ODbL
metadata and OpenStreetMap attribution). `data/da_nang_central.json` remains a
small explicit teaching/test fixture only. Set `ROUTING_DATASET_PATH` to load a
different snapshot. A one-time Overpass/OSM export can use this schema:

Hospital POIs are joined to retained road junctions by clearly tagged synthetic
access connectors. Connectors target the mutually reachable road component so
all 24 emergency destinations can be routed both to and from; OSM road
directions themselves are left unchanged.

```json
{
  "metadata": {
    "id": "unique-id",
    "name": "Dataset name",
    "city": "Da Nang",
    "country": "Vietnam",
    "version": "1.0",
    "source": "OpenStreetMap contributors / query details",
    "description": "...",
    "generated_at": "optional ISO timestamp",
    "disclaimer": "optional"
  },
  "nodes": [
    {
      "id": "n1",
      "name": "Hospital or intersection",
      "kind": "hospital",
      "lat": 16.06,
      "lon": 108.22,
      "attributes": {"osm_node_id": 123}
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "n1",
      "target": "n2",
      "distance_m": 420.5,
      "speed_kph": 35,
      "road_name": "Road name",
      "road_class": "primary",
      "risk": 0.1,
      "emergency_access": true,
      "bidirectional": true,
      "reverse_id": "optional-custom-reverse-id",
      "reverse_speed_kph": 30,
      "attributes": {
        "osm_way_id": 456,
        "bridge": false,
        "incident_prone": false,
        "close_during_incident": false
      }
    }
  ]
}
```

Required metadata fields are `id` and `name`. Required node fields are
`id`, `name`, `lat`, and `lon`. Required edge fields are `id`, `source`,
`target`, and positive `distance_m`. IDs must be unique and edge endpoints must
exist. `bidirectional: true` expands one physical segment into two directed
edges; omit it when an importer already emits each direction explicitly.
Optional `attributes.geometry` is a GeoJSON-order coordinate array
`[[longitude, latitude], ...]`. The loader validates it, reverses it when its
orientation disagrees with `source -> target`, anchors both endpoints, and also
reverses it for generated reverse edges.
