# FastAPI Contract — `/api/v1`

## 1. Service URLs

| Resource | Development URL |
|---|---|
| API base | `http://127.0.0.1:8000/api/v1` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |
| OpenAPI JSON | `http://127.0.0.1:8000/api/v1/openapi.json` |
| React dev UI | `http://localhost:5173` |

The React dev server proxies `/api/*` to `http://127.0.0.1:8000`. `VITE_API_BASE_URL` may point the client directly to another API base. Backend CORS defaults allow localhost/127.0.0.1 on ports 5173 and 4173.

Backend environment variables actually read by the application:

| Variable | Meaning |
|---|---|
| `ROUTING_DATASET_PATH` | override bundled dataset JSON path |
| `CORS_ORIGINS` | comma-separated exact origins |

## 2. General conventions

- Media type: `application/json`.
- IDs are case-sensitive strings.
- Request models are strict: unknown fields are rejected (`extra="forbid"`).
- GeoJSON coordinates are `[longitude, latitude]`.
- `request_id` is a new UUID per generated search/compare/multi response.
- Traffic/route output is deterministic for the same code, dataset and request except `request_id` and measured `runtime_ms`.
- Cost weights are non-negative and normalized internally; their ratio matters.
- This is an educational API, not a live traffic/dispatch service.

### 2.1 Enum registry

Algorithms:

```text
bfs
dfs
ucs
dijkstra
astar
greedy_best_first
bidirectional_dijkstra
ida_star
```

Heuristics:

```text
zero
haversine
travel_time
traffic_aware
```

Scenarios:

```text
normal
morning_rush
evening_rush
heavy_rain
incident
```

Multi-route methods:

```text
nearest_neighbor
held_karp
two_opt
simulated_annealing
```

### 2.2 Cost weights

```json
{
  "distance": 0.25,
  "travel_time": 0.50,
  "traffic_delay": 0.20,
  "risk": 0.05
}
```

Each number is in `[0,100]`; at least one must be positive. Backend normalizes the four numbers to sum to 1, then uses kilometres, travel minutes, delay minutes and `risk × kilometres`. The HTTP field is `traffic_delay`, while the React view model calls this slider `congestion`.

## 3. Error envelope

All application and request-validation errors share a top-level `error` object:

```json
{
  "error": {
    "code": "unknown_node",
    "message": "Unknown start node 'missing'",
    "details": {
      "role": "start",
      "node_id": "missing",
      "available_nodes": ["..."]
    }
  }
}
```

| HTTP | Typical code | Cause |
|---:|---|---|
| 422 | `validation_error` | enum/range/length/strict-field Pydantic validation |
| 422 | `unknown_node` | start, goal or stop not present |
| 422 | `invalid_search_configuration` | invalid algorithm/heuristic at engine boundary |
| 422 | `duplicate_algorithms` | repeated compare algorithm |
| 422 | `duplicate_start` / `duplicate_stops` | invalid multi-stop identity set |
| 422 | `invalid_multi_route_method` | unknown method at engine boundary |
| 422 | `too_many_stops` | Held–Karp over 10 stops |
| 422 | `multi_route_unreachable` | no finite order visits all stops under scenario |
| 422 | `multi_route_failed` | optimizer rejected configuration |
| 503 | `service_unavailable` | engine not present in application state |

Most malformed values are rejected by enums/models before engine-specific codes are reached. A dataset load error normally aborts application startup rather than serving partial graph state.

## 4. `GET /health`

Readiness plus active dataset identity.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Bundled snapshot response shape:

```json
{
  "status": "ok",
  "service": "Da Nang Emergency Route Lab API",
  "version": "1.0.0",
  "dataset_id": "danang-central-emergency-osm-2026",
  "dataset_version": "1.0.0",
  "node_count": 512,
  "directed_edge_count": 1007
}
```

This is process/dataset readiness only; it does not assert internet tile access or live-traffic health.

## 5. `GET /metadata`

Returns the client-discoverable registry:

```text
api
dataset
graph
algorithms[]
heuristics[]
scenarios[]
multi_route_methods[]
defaults
trace_schema
```

Selected shapes:

```json
{
  "api": {
    "name": "Da Nang Emergency Route Lab API",
    "version": "1.0.0",
    "contract_version": "2026-08-05"
  },
  "graph": {
    "node_count": 512,
    "directed_edge_count": 1007,
    "distance_lower_bound_scale": 0.998783081,
    "max_speed_kph": 60.0,
    "bounding_box": {
      "south": 16.0142064,
      "west": 108.1856676,
      "north": 16.1014314,
      "east": 108.2575782
    }
  },
  "defaults": {
    "algorithm": "astar",
    "heuristic": "travel_time",
    "scenario": "normal",
    "cost_weights": {
      "distance": 0.25,
      "travel_time": 0.5,
      "traffic_delay": 0.2,
      "risk": 0.05
    },
    "multi_route_method": "nearest_neighbor"
  }
}
```

The runtime bounding box is calculated from actual stored node coordinates. It can extend beyond the query box because Overpass returns referenced way nodes and the builder may use a way's available-node centre. Client code should consume response values rather than hard-code counts/bounds.

Algorithm metadata fields:

```text
id, label, family, weighted, heuristic_required,
complete, optimality, description
```

Heuristic fields:

```text
id, label, description, admissible, consistent, warning
```

## 6. `GET /graph`

```http
GET /api/v1/graph?scenario=morning_rush
```

Query:

| Name | Required | Default | Values |
|---|---:|---|---|
| `scenario` | no | `normal` | scenario enum |

Response:

```text
dataset
summary
scenario
nodes[]
directed_edges[]
graph_geojson
```

Node:

```json
{
  "id": "hospital_way_372433638",
  "name": "Bệnh viện Đà Nẵng",
  "kind": "hospital",
  "lat": 16.0726877,
  "lon": 108.215515,
  "attributes": {
    "osm_type": "way",
    "osm_id": 372433638,
    "emergency_destination": true,
    "snap_distance_m": 133.13
  }
}
```

The hospital example above reflects the bundled snapshot; use the endpoint rather than hard-coding it for regenerated datasets.

Directed edge:

```json
{
  "id": "osm_path_...",
  "source": "osm_...",
  "target": "osm_...",
  "distance_m": 420.5,
  "speed_kph": 40.0,
  "road_name": "Đường ...",
  "road_class": "secondary",
  "risk": 0.12,
  "emergency_access": true,
  "attributes": {
    "osm_way_ids": [123456],
    "bridge": false,
    "flood_prone": false,
    "incident_prone": false,
    "close_during_incident": false,
    "overlay_provenance": "deterministic synthetic educational layer",
    "geometry": [[108.2, 16.06], [108.21, 16.065]]
  },
  "geometry": [[108.2, 16.06], [108.21, 16.065]],
  "traffic": {
    "edge_id": "osm_path_...",
    "scenario": "morning_rush",
    "multiplier": 1.54,
    "effective_speed_kph": 25.974026,
    "free_flow_time_s": 37.845,
    "travel_time_s": 58.2813,
    "delay_s": 20.4363,
    "congestion": "heavy",
    "closed": false,
    "reason": "Morning rush hour; major-road demand; stable edge variation"
  }
}
```

Numeric values in the edge example are illustrative. When closed, `effective_speed_kph=0`, `travel_time_s=null`, `delay_s=null`, `congestion="closed"`.

`graph_geojson` is a FeatureCollection with exactly one LineString feature per directed edge. Feature properties include edge ID, endpoints, name/class, distance, scenario, congestion, closed and multiplier.

## 7. `POST /search`

### 7.1 Request

```json
{
  "start_id": "osm_420248644",
  "goal_id": "hospital_way_372433638",
  "algorithm": "astar",
  "heuristic": "travel_time",
  "scenario": "morning_rush",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.50,
    "traffic_delay": 0.20,
    "risk": 0.05
  },
  "include_trace": true,
  "max_trace_events": 1000,
  "max_expansions": 100000,
  "include_alternative": true
}
```

| Field | Required | Default / bounds |
|---|---:|---|
| `start_id`, `goal_id` | yes | 1–128 chars, must exist |
| `algorithm` | no | `astar` |
| `heuristic` | no | `travel_time`; validated even if algorithm does not use it |
| `scenario` | no | `normal` |
| `cost_weights` | no | backend defaults |
| `include_trace` | no | true |
| `max_trace_events` | no | 1,000; `0..10,000` |
| `max_expansions` | no | 100,000; `1..1,000,000` |
| `include_alternative` | no | true |

PowerShell:

```powershell
$body = @{
  start_id = 'osm_420248644'
  goal_id = 'hospital_way_372433638'
  algorithm = 'astar'
  heuristic = 'travel_time'
  scenario = 'morning_rush'
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/v1/search `
  -Method Post `
  -ContentType 'application/json' `
  -Body $body
```

### 7.2 Response shape

```text
request_id, status, found, start_id, goal_id,
algorithm, heuristic, scenario,
path, edge_ids, route_geojson,
metrics, trace, explanation, alternative, cost_breakdown
```

Abridged successful example (runtime/UUID may differ):

```json
{
  "request_id": "<uuid>",
  "status": "found",
  "found": true,
  "start_id": "osm_420248644",
  "goal_id": "hospital_way_372433638",
  "algorithm": {
    "id": "astar",
    "label": "A* Search",
    "family": "informed",
    "weighted": true,
    "heuristic_required": true,
    "complete": true,
    "optimality": "Optimal with an admissible, consistent heuristic.",
    "description": "Orders the frontier by accumulated cost plus an estimated remaining cost."
  },
  "heuristic": {
    "id": "travel_time",
    "label": "Optimistic travel-time lower bound",
    "description": "Uses straight-line distance at the graph's maximum free-flow speed.",
    "admissible": true,
    "consistent": true,
    "warning": null,
    "used": true
  },
  "path": ["osm_420248644", "...", "hospital_way_372433638"],
  "edge_ids": ["..."],
  "route_geojson": {
    "type": "LineString",
    "coordinates": [[108.216, 16.07], [108.215515, 16.0726877]]
  },
  "metrics": {
    "runtime_ms": 2.4,
    "visited_nodes": 26,
    "expanded_nodes": 26,
    "generated_nodes": 42,
    "frontier_peak": 18,
    "heuristic_calls": 42,
    "path_nodes": 9,
    "path_edges": 8,
    "hop_count": 8,
    "path_cost": 2.02075749,
    "trace_truncated": false,
    "distance_m": 1548.73,
    "free_flow_time_s": 120.395383,
    "travel_time_s": 173.499983,
    "traffic_delay_s": 53.1046,
    "risk_exposure": 0.214529
  }
}
```

Coordinate list above is shortened and not a valid representation of the full actual route geometry; the actual endpoint returns the complete LineString.

### 7.3 Cost breakdown

```json
{
  "weights": {
    "distance": 0.25,
    "travel_time": 0.5,
    "traffic_delay": 0.2,
    "risk": 0.05
  },
  "units": {
    "distance": "kilometres before weighting",
    "travel_time": "minutes before weighting",
    "traffic_delay": "minutes before weighting",
    "risk": "risk fraction × kilometres before weighting",
    "total_cost": "dimensionless weighted score"
  },
  "edge_count": 8,
  "distance_m": 1548.73,
  "free_flow_time_s": 120.395383,
  "travel_time_s": 173.499983,
  "traffic_delay_s": 53.1046,
  "risk_exposure": 0.214529,
  "components": {
    "distance": 0.3871825,
    "travel_time": 1.445833192,
    "traffic_delay": 0.177015333,
    "risk": 0.010726465
  },
  "total_cost": 2.02075749
}
```

These component values correspond to the documented sample route. The invariant is `sum(components.values()) == total_cost` within serialized rounding.

### 7.4 Trace

```json
{
  "schema_version": "1.0",
  "event_count": 3,
  "truncated": false,
  "events": [
    {
      "step": 0,
      "event": "start",
      "node_id": "osm_420248644",
      "parent_id": null,
      "edge_id": null,
      "direction": "forward",
      "frontier_size": 1,
      "explored_count": 0,
      "g_cost": 0.0,
      "h_cost": 1.1,
      "f_cost": 1.1,
      "depth": null,
      "message": ""
    }
  ]
}
```

Events can be `start`, `iteration`, `expand`, `discover`, `relax`, `prune`, `finish`. The example `event_count` and heuristic numbers are schematic. Bidirectional search uses `direction="backward"` for its reverse wave.

### 7.5 Explanation

```json
{
  "summary": "A* Search found an 8-edge route with weighted cost 2.020757.",
  "optimality": "Optimal with an admissible, consistent heuristic.",
  "heuristic_note": "Optimistic travel-time lower bound: ...",
  "traffic_note": "Higher delay on primary and arterial approaches to the city centre.",
  "cost_model": "total = ...; weights are normalized",
  "warnings": ["<dataset disclaimer>"]
}
```

For an unreachable/limited run, `path=[]`, `edge_ids=[]`, `route_geojson=null`, aggregate metrics/cost are zero except search effort, and summary explains the status.

### 7.6 Alternative

When enabled and available:

```text
algorithm, reason, path, edge_ids, route_geojson,
difference_percent, metrics, cost_breakdown
```

It is generated by running Dijkstra once per unique primary edge while blocking that edge, then keeping the cheapest different candidate. It may be `null`. `difference_percent` is relative to the primary route cost and can be negative when the requested primary algorithm itself is non-optimal.

## 8. `POST /compare`

### 8.1 Request

```json
{
  "start_id": "osm_420248644",
  "goal_id": "hospital_way_372433638",
  "algorithms": ["bfs", "ucs", "astar", "greedy_best_first"],
  "heuristic": "travel_time",
  "scenario": "morning_rush",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.50,
    "traffic_delay": 0.20,
    "risk": 0.05
  },
  "include_trace": false,
  "max_trace_events": 300,
  "max_expansions": 100000
}
```

Constraints:

- 2–8 unique algorithm enums;
- compare trace limit `0..2,000`, default 300;
- default `include_trace=false`;
- other fields follow search bounds.

There is no `include_alternative`: each nested run sets `alternative=null` to avoid multiplying work.

### 8.2 Response

```text
request_id
start_id
goal_id
scenario
runs[]
ranking[]
best_algorithm
agreement
```

Each `runs[]` item is a full SearchResponse without an alternative. Ranking order is:

1. found before not found;
2. lower `path_cost`;
3. fewer `expanded_nodes`;
4. lexical algorithm ID.

`runtime_ms` is displayed but not a ranking tie-breaker.

```json
{
  "ranking": [
    {
      "rank": 1,
      "algorithm": "astar",
      "found": true,
      "path_cost": 2.02075749,
      "expanded_nodes": 26,
      "runtime_ms": 2.4
    }
  ],
  "best_algorithm": "astar",
  "agreement": {
    "all_found": true,
    "same_path": false,
    "unique_path_count": 2,
    "path_groups": [
      {"edge_ids": ["..."], "algorithms": ["ucs", "astar"]}
    ]
  }
}
```

The numbers/groups above are abridged examples. Agreement compares exact ordered `edge_ids`, not only equal cost.

## 9. `POST /multi-route`

### 9.1 Request

```json
{
  "start_id": "osm_345351408",
  "stop_ids": [
    "hospital_way_372433638",
    "hospital_way_372433951",
    "hospital_node_729405662",
    "hospital_way_489789425"
  ],
  "method": "held_karp",
  "return_to_start": true,
  "scenario": "morning_rush",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.50,
    "traffic_delay": 0.20,
    "risk": 0.05
  },
  "seed": 42,
  "max_iterations": 2000,
  "max_expansions": 100000
}
```

| Field | Default / bounds |
|---|---|
| `start_id` | required, existing |
| `stop_ids` | 1–12 unique non-empty existing IDs; cannot contain start |
| `method` | `nearest_neighbor` |
| `return_to_start` | false |
| `scenario` | `normal` |
| `cost_weights` | defaults |
| `seed` | 42; `0..2,147,483,647` |
| `max_iterations` | 1,000; `1..100,000` |
| `max_expansions` | 100,000; `1..1,000,000` per pair search |

Held–Karp accepts at most 10 stops. `seed` affects simulated annealing only. `max_iterations` bounds 2-opt/annealing optimizer work, not pairwise Dijkstra.

The HTTP API does **not** accept `segment_algorithm`, `heuristic`, `objective` or `vehicle`. Pairwise segments are intentionally fixed to exact Dijkstra/zero heuristic; UI objectives are converted to `cost_weights` client-side.

### 9.2 Response

```text
request_id, status,
method, scenario,
start_id, requested_stop_ids, stop_order,
return_to_start, visit_sequence,
path, edge_ids, route_geojson,
segments[], metrics, cost_breakdown, explanation
```

Segment:

```json
{
  "from_id": "osm_345351408",
  "to_id": "hospital_way_489789425",
  "path": ["..."],
  "edge_ids": ["..."],
  "route_geojson": {"type": "LineString", "coordinates": [[108.2, 16.05], [108.21, 16.06]]},
  "cost_breakdown": {"...": "..."}
}
```

Metrics:

```json
{
  "runtime_ms": 20.7812,
  "pairwise_searches": 20,
  "pairwise_expanded_nodes": 5101,
  "optimizer_iterations": 48,
  "optimizer_improvements": 0,
  "stop_count": 4,
  "hop_count": 89,
  "path_cost": 28.523431994,
  "distance_m": 20161.92,
  "travel_time_s": 2503.720484,
  "traffic_delay_s": 746.173373
}
```

These values are from one documented sample run; `runtime_ms` should be read from a fresh response before quoting because it varies by machine/run. For `n` stops, successful construction makes `n(n+1)` pairwise searches because ordered directions are distinct.

`method.exact=true` only for Held–Karp. Approximate method explanation says that stop ordering is approximate while each selected segment is an exact Dijkstra path.

## 10. Frontend adapter notes

The backend contract deliberately uses mathematically explicit names; `frontend/src/api.ts` adapts them:

| Backend | React view model |
|---|---|
| `directed_edges` | `edges` |
| `road_name`, `road_class` | `name`, `road_type` |
| `traffic.travel_time_s` | `travel_time_min` |
| `cost_weights.travel_time` | `weights.time` |
| `cost_weights.traffic_delay` | `weights.congestion` |
| `algorithm.id` | `algorithm` string |
| `trace.events` | reconstructed `TraceStep[]` with frontier/visited sets |
| raw LineString | GeoJSON Feature wrapper used by UI |

API consumers outside this frontend should use the OpenAPI schema directly and should not assume the adapter's renamed fields.

## 11. Contract invariants worth testing

```text
len(edge_ids) == max(0, len(path)-1)
route_geojson.type == "LineString" when found
cost_breakdown.total_cost == metrics.path_cost
sum(cost_breakdown.weights.values()) == 1
sum(cost_breakdown.components.values()) == cost_breakdown.total_cost
len(graph_geojson.features) == len(directed_edges)
sorted(stop_order) == sorted(requested_stop_ids)
visit_sequence starts at start_id
visit_sequence ends at start_id iff return_to_start is true
```

Floating values are serialized with documented rounding in aggregate fields; use a numeric tolerance for recomputation from raw edge values.
