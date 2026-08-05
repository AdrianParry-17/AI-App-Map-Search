# Lab 1 Rubric & Submission Checklist

Use this as a release gate. “Evidence present” means a source artifact exists; it does **not** mean the final PDF, screenshots, slides, video or ZIP have already been produced.

Status legend:

- ✅ implementation/document evidence present;
- 🧪 must rerun/record evidence on the final commit;
- 🧑 human/group artifact or decision still required;
- ⚠️ claim must include a limitation/condition.

## 1. Evaluation criteria (100 points)

| Criterion | Pts | Current evidence | Final verification / remaining work | Status |
|---|---:|---|---|---|
| Vietnamese traffic context and realistic scenario | 10 | Đà Nẵng ambulance scenario in UI, API description and `TECHNICAL_REPORT.md` | Capture a real UI run and explain why ETA/congestion matter | ✅ 🧪 |
| Graph modeling, dataset and cost function | 15 | 512 nodes, 1,007 directed runtime edges; OSM snapshot + synthetic overlays; normalized 4-part cost; `DATASET.md` | Record checksum; show topology vs synthetic provenance in report/presentation | ✅ 🧪 |
| Required BFS, DFS, UCS, A* | 20 | Implemented in `backend/app/algorithms.py`; unified contract and tests | Run pytest on final commit; demo expansion/frontier/cost behavior | ✅ 🧪 |
| At least two additional algorithms | 10 | Dijkstra, Greedy Best-First, Bidirectional Dijkstra, IDA* (4 extras) | Explain conditions/limits; do not report Greedy/IDA* guarantees incorrectly | ✅ ⚠️ |
| Multi-location optimization | 10 | Nearest Neighbor, 2-opt, exact Held–Karp, seeded SA + 2-opt | Demo original/requested vs optimized order; show exact vs approximate | ✅ 🧪 |
| GUI and visual search process | 10 | React/Vite, Leaflet, selectable map, trace playback, metrics, Compare, Learn | Run frontend build; capture screenshots and video from actual app | ✅ 🧪 🧑 |
| Route explanation and alternative comparison | 10 | Explanation object, cost breakdown, optimality warnings, deterministic single-edge-exclusion alternative | Demo one primary/alternative; state alternative algorithm's exact scope | ✅ 🧪 ⚠️ |
| Technical report quality | 10 | Source report + data/algorithm/API/rubric docs | Fill group data, add actual screenshots/test output, proofread, export PDF | ✅ 🧑 |
| Demo video quality | 5 | Script and shot plan only | Record, edit, upload, verify link permissions/audio/readability | 🧑 |

## 2. Requirement-by-requirement traceability

### 2.1 General submission requirements

- [ ] Group has 3–5 students.
- [ ] One representative is named.
- [ ] ZIP is named exactly `[[GroupID]].zip`.
- [ ] ZIP contains `[[GroupID - SC]].txt` with an accessible source-code link.
- [ ] ZIP contains `[[GroupID - Report]].pdf`.
- [ ] ZIP contains `[[GroupID - Slide]].pptx` or `.pdf`.
- [ ] ZIP contains `[[GroupID - Video]].txt` with an accessible demo-video link.
- [ ] ZIP contains `[[GroupID - Data]].zip` or `.txt` with dataset/data description.
- [ ] Links are tested in a private/incognito browser not signed in as an owner.
- [ ] ZIP is extracted and opened once on a clean path before upload.

### 2.2 Scenario and modeling

- [x] Vietnamese urban context: central Đà Nẵng.
- [x] Realistic problem: ambulance route to a medical destination.
- [x] Directed graph; outgoing and incoming indexes.
- [x] Nodes represent intersections/gateways/bridge access/hospital POIs.
- [x] Edges represent contracted road segments.
- [x] Distance, ETA, congestion state, road type and direction are available.
- [x] Optional risk factors include synthetic flood/incident/bridge effects.
- [x] Two-location search.
- [x] Multi-location order + route.
- [ ] In final report, include one formal state/goal/transition definition and graph diagram.

### 2.3 Cost function

- [x] Uses distance + travel time + traffic delay/congestion + risk exposure.
- [x] User controls weight ratios; backend normalizes weights.
- [x] All cost components are non-negative for route algorithms.
- [x] Closed edges are removed rather than assigned a finite penalty.
- [x] Breakdown reports units/components/total.
- [ ] Final presentation verbally distinguishes “congestion label 1–5 for UI” from numeric delay used in cost.
- [ ] Show at least one scenario or weight change that alters route or ETA.

### 2.4 Dataset minimum and provenance

- [x] ≥20 nodes: 512.
- [x] ≥30 edges: 756 stored base records / 1,007 directed runtime edges.
- [x] Real locations/topology from OSM snapshot.
- [x] OSM timestamp, bounding/query metadata and IDs retained.
- [x] Traffic/risk provenance explicitly synthetic deterministic.
- [x] Dataset bundled as JSON and documented.
- [x] Visible OSM attribution in map/footer.
- [x] Record SHA-256 of submission snapshot in `DATASET.md` (`39FF8A…5FC10`).
- [ ] Keep attribution and ODbL link visible in exported report/slides/video where map/data appear.

### 2.5 Required and additional route algorithms

- [x] BFS.
- [x] DFS.
- [x] UCS.
- [x] A*.
- [x] Dijkstra (additional).
- [x] Greedy Best-First (additional).
- [x] Bidirectional Dijkstra (additional).
- [x] IDA* (additional).
- [x] Same result/trace contract.
- [x] Completeness and optimality metadata.
- [ ] Final report includes actual final-commit comparison results, not only complexity theory.
- [ ] Video demonstrates at least BFS vs a weighted optimum and A* `g/h/f`.

### 2.6 Heuristics

- [x] `zero` baseline.
- [x] calibrated Haversine lower bound.
- [x] optimistic travel-time lower bound.
- [x] practical/non-admissible traffic-aware estimate.
- [x] Metadata states admissible and consistent flags.
- [x] Report/reference explains proof conditions.
- [ ] Demo explicitly warns that `traffic_aware` removes A*/IDA* optimality guarantee.

### 2.7 Multi-location

- [x] Efficient approximate baseline: Nearest Neighbor.
- [x] Local improvement: 2-opt.
- [x] Exact small-scale DP: Held–Karp, capped at 10 stops.
- [x] Seeded metaheuristic: Simulated Annealing + 2-opt.
- [x] Pairwise legs use directed exact Dijkstra.
- [x] Return-to-start option.
- [x] Output includes requested order, optimized order, visit sequence, segments, cost and explanation.
- [ ] Demo one approximate-vs-exact case and state that matching output does not prove the approximate method globally optimal.

### 2.8 GUI

- [x] Web-based React interface.
- [x] Traffic graph/city map and OSM geometry.
- [x] Select start, destination and intermediate stops by list or map.
- [x] Select algorithm, objective/weights, scenario and heuristic.
- [x] Search trace playback with current/frontier/visited reconstruction.
- [x] Final route and alternative styling.
- [x] Distance, ETA, total cost, expanded nodes, frontier peak and runtime cards.
- [x] Comparison chart/table.
- [x] Multi-stop mode.
- [x] Learning/algorithm metadata view.
- [x] Loading, backend health and error states.
- [ ] Verify responsive layout at desktop and one narrow viewport on final build.
- [ ] Verify map still conveys graph when `VITE_ENABLE_OSM_TILES=false`.

### 2.9 Route explanation

- [x] Why the route was selected: weighted cost and algorithm metadata.
- [x] Shortest/fastest/weighted-optimal condition is represented via objective weights and optimality text.
- [x] Traffic scenario description and breakdown.
- [x] High-congestion/closed edge visualization on map.
- [x] Different route candidate through single-edge-exclusion Dijkstra.
- [x] Alternative difference percentage.
- [x] Warnings for non-optimal algorithms/non-admissible heuristic/trace truncation/data disclaimer.
- [ ] In report/video, narrate one named segment difference rather than reading only totals.

## 3. Technical report section gate

The lab requires sections a–j. `TECHNICAL_REPORT.md` covers the technical source, but the group must complete the human artifacts.

| Required report section | Evidence/section | Gate |
|---|---|---|
| a. Group introduction | Report §A | Fill names, IDs, contributions, completion |
| b. Problem context | Report §2 | Add group-specific motivation if desired |
| c. Problem modeling | Report §3 | Ready; verify formula rendering after PDF export |
| d. Dataset | Report §4 + `DATASET.md` | Add checksum and optional appendix/sample records |
| e. Algorithm principles | Report §5–7 + `ALGORITHM_REFERENCE.md` | Select appropriate depth for page limit |
| f. Program flow | Report §8 Mermaid diagrams | Export diagrams correctly into PDF |
| g. Algorithm comparison | Report §10 | Rerun on final commit and record environment/repetitions |
| h. Multi-location | Report §7/§10.3 | Capture requested vs optimized order screenshot |
| i. Instructions/screenshots | Report §11 + `assets/` | Dashboard, A* result và Compare là ảnh chạy thật; cần bổ sung Multi/Incident/Learn khi chốt PDF |
| j. Limitations/future work | Report §13–14 | Ready; retain safety caveats |

### Required screenshot capture list

- [x] Route mode before run, selections visible (`assets/dashboard-overview.png`).
- [x] Route mode after run, full primary route and metrics visible (`assets/route-result.png`).
- [x] Trace playback, legend và current step visible (`assets/route-result.png`).
- [ ] Alternative route/card visible.
- [x] Compare mode with ≥4 algorithms (`assets/algorithm-compare.png`).
- [ ] Multi-stop requested and optimized order.
- [ ] Incident or heavy-rain scenario.
- [ ] Learn mode with heuristic admissibility.
- [ ] Optional Swagger/OpenAPI endpoint proof.

For each image: include a figure number, caption, input IDs/names, algorithm, heuristic, scenario, commit and OSM attribution if a map is visible.

## 4. Final automated verification

Run from a clean final commit and paste concise results into the report appendix/release notes.

```powershell
cd backend
python -m pytest
```

```powershell
cd frontend
npm ci
npm run lint
npm run build
```

Then run both servers and exercise:

- [x] `GET /api/v1/health` returns expected dataset/version/count.
- [x] `GET /api/v1/metadata` lists 8 algorithms, 4 heuristics and 4 multi methods.
- [x] `/graph?scenario=incident` has at least one closed edge.
- [x] A* safe-heuristic search finds a route and returns non-empty trace.
- [x] BFS and weighted algorithm can produce different cost/route behavior.
- [x] Compare accepts 2–8 unique algorithms.
- [x] Held–Karp rejects >10 stops with a clear 422 envelope.
- [x] Multi-stop exact case succeeds in the strongly connected core.
- [x] Unknown node returns structured 422.
- [x] Start=goal returns zero-cost route.
- [ ] Frontend shows backend-offline error without blank/crash.
- [ ] Browser console has no uncaught error on each mode.

Record:

| Check | Final value |
|---|---|
| Commit | Workspace chưa được khởi tạo Git; điền SHA sau khi nhóm tạo repository |
| Python / OS | Python 3.13.14 / Windows |
| Node / npm | Node 24.11.0 / npm 11.6.1 |
| Pytest | 28 passed; 89% statement coverage |
| Frontend | Vitest 4 passed; Vite production build passed; Playwright Edge e2e 2 passed |
| Dataset health counts | v1.0.0; 512 nodes; 1,007 directed edges; 24 hospitals; 552/552 hospital pairs reachable |

## 5. Demo video gate

The prepared script is in `DEMO_VIDEO_SCRIPT.md`; no video is claimed to exist yet.

- [ ] Original group-designed small graph example is shown.
- [ ] Start, goal, expansion order and frontier are explained.
- [ ] UCS/Dijkstra/A* `g`, and A*/Greedy `h`/`f`, are visible/explained.
- [ ] Actual project route search is demonstrated.
- [ ] Multi-location optimization is demonstrated.
- [ ] At least two traffic conditions are compared.
- [ ] Algorithm metrics are compared under identical input.
- [ ] Primary-vs-alternative reasoning is narrated.
- [ ] Exact vs approximate is stated accurately.
- [ ] Synthetic traffic and safety disclaimer are spoken/visible.
- [ ] OSM attribution is readable.
- [ ] Audio is intelligible and cursor/text are visible at final resolution.
- [ ] Upload link permission is verified externally.

## 6. Presentation slide gate

Suggested 10-slide deck:

1. team + contribution;
2. ambulance scenario and objective;
3. hybrid OSM/synthetic dataset provenance;
4. directed graph and cost formula;
5. required algorithms;
6. extra algorithms + heuristic conditions;
7. architecture/flow;
8. measured comparison and scenario sensitivity;
9. multi-stop exact vs approximate;
10. limitations, attribution and conclusion.

- [ ] No slide says traffic is live.
- [ ] No slide says BFS/DFS/Greedy are weighted optimal.
- [ ] No slide says A* optimal without naming heuristic condition.
- [ ] No slide calls 2-opt/SA globally optimal.
- [ ] Runtime chart labels environment/sample count.
- [ ] Map slides show © OpenStreetMap contributors / ODbL.

## 7. “Make no mistake” claim audit

Before submission, search report/slides/captions/transcript for these risky words and qualify them:

| Risky statement | Required correction |
|---|---|
| “real-time/live traffic” | “deterministic educational traffic simulation” |
| “real road data” alone | “OSM snapshot topology/tags; derived/synthetic traffic and risk” |
| “optimal route” | name objective, algorithm, heuristic condition, snapshot/scenario and expansion-budget assumption |
| “shortest route” | specify shortest distance, minimum hops or minimum weighted cost |
| “A* is fastest” | report measured run; say expansion/runtime depend on heuristic/input/machine |
| “IDA* unreachable” | distinguish `limit_reached` from `unreachable` |
| “second-shortest route” | “best candidate from single-primary-edge exclusion” |
| “Held–Karp solves TSP” | “exact stop order on the computed directed pairwise matrix, ≤10 stops” |
| “OSM traffic/risk” | OSM supplies topology/tags only; overlays are project-generated |
| “hospital is suitable” | POI label only; no capacity/capability validation |

## 8. Packaging rehearsal

- [ ] Freeze code and dataset; create release tag/commit.
- [ ] Rerun all checks and screenshots after freeze.
- [ ] Export Markdown/Mermaid to PDF and inspect fonts, Vietnamese diacritics, formulas, tables and links.
- [ ] Remove unresolved `[[...]]` placeholders from final artifacts.
- [ ] Remove secrets, local virtualenvs, `node_modules`, caches and build junk from submitted archive unless required.
- [ ] Include installation versions and commands.
- [ ] Include the data file or an explicit accessible data package/description as required.
- [ ] Confirm source/video links do not expire and are viewable without edit permission.
- [ ] Compare final ZIP contents against every filename required by the PDF brief.
