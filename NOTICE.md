# Data and service notice

The bundled road-network snapshot is derived from **OpenStreetMap** data and is
made available under the Open Data Commons Open Database License (ODbL) 1.0.

- Attribution: © OpenStreetMap contributors
- Copyright/license: <https://www.openstreetmap.org/copyright>
- Report a map issue: <https://www.openstreetmap.org/fixthemap>
- Extraction method: bounded Overpass query in `scripts/overpass_danang.ql`
- Snapshot metadata and OSM base timestamp: `backend/data/da_nang_osm_snapshot.json`

Traffic congestion, travel-time multipliers, incident closures, flood
susceptibility and risk values are deterministic educational simulations and
are not part of OpenStreetMap data.

The optional basemap loads standard OSM tiles only for the visible interactive
viewport and displays attribution. Do not bulk-download, prefetch or proxy those
tiles. For production or high-volume use, configure an appropriate provider.
