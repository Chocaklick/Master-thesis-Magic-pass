# Master Thesis — Swiss Ski Resort Analytics

This repository is the reproducible technical workspace for a Master's thesis in Business Analytics on Swiss ski resorts, hotel overnight stays, Magic Pass adoption, climate and snow conditions, and decision support for resorts that are not currently Magic Pass members.

## Research objective

The full project mission is saved in [prompts/main_research_prompt.md](prompts/main_research_prompt.md). It defines the research questions, data requirements, feasibility gates, checkpoints, and final deliverables for subsequent work.

The long-term objective is to combine defensible data engineering, causal/econometric analysis, machine learning, and geospatial analysis. Checkpoint 1 and the initial treatment/panel feasibility gates are complete. No treatment-effect model or opportunity score has been fitted because the current evidence does not yet support causal treatment coding.

A central methodological distinction is preserved throughout the project:

```text
ski lifts -> lift clusters -> ski resorts

ski resorts -> tourism destinations -> one or more municipalities -> overnight stays
```

A resort assignment is not automatically a municipality assignment.

## Current status

- Local Git repository initialized on `main`.
- Local Python 3.12 virtual environment created in `.venv/`.
- Eleven supplied raw files are hashed, profiled, and preserved as immutable inputs.
- The existing 242-cluster/1,805-lift layer has been validated without reclustering.
- A 31,248-row municipality-month hotel-demand panel, a separate 31,248-row official HESTA capacity panel, daily SLF snow proxies, daily MeteoSwiss temperature/precipitation proxies, a current point-municipality crosswalk, official Magic Pass evidence, and a resort-level data-quality table are reproducibly generated.
- The 18 candidate entry/outcome links have been collapsed into 14 reviewed destination units. Eleven have an explicit outcome scope and form a 1,848-row diagnostic destination-month panel; three incomplete composite scopes are excluded. Capacity is complete for 1,637 destination-months, snow for 1,733, and temperature/precipitation for 1,744.
- The current feasibility decision is Path C: exploratory segmentation/analogue decision support. Causal modelling remains gated by treatment-intensity validation, remaining time-varying confounders, spillovers, control contamination, and snow-proxy representativeness.
- The official 2020/2021 network map and the 2021/2022 launch dossier close all remaining active-season continuity gaps for the 14 reviewed units. Eleven enter the outcome panel and seven also have 24 observed pre and post months, but zero treatments or controls are causally approved. See [the membership evidence review](reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md).
- All 26 unmatched historical labels have a conservative scope classification. Official follow-up resolves the five previously uncertain Swiss/overlapping cases as directory gaps or many-to-many relations, never identity matches. Resolving the current Sattel-Hochstuckli label leaves 52 apparent control municipalities and 404 mechanical treatment-donor pairs at 30 km (366 at 50 km). A descriptive pre-trend screen prioritises 35 pairs for manual review without approving any control. Seven annual publications distinguish winter from summer-winter access for 58 reviewed unit-seasons. See [the scope review](reports/09_ENTITY_SCOPE_AND_DONOR_REVIEW.md), [the annual offering review](reports/10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md), and [the donor screen](reports/11_DONOR_PRETREND_SCREEN.md).
- A 168-month deterministic calendar table now supplies winter/summer, holiday-peak, Easter-month, and broad COVID-sensitivity flags to every reviewed destination-month row. The COVID interval is a robustness flag, not a canton-specific legal chronology. See [the temporal-control review](reports/12_TEMPORAL_CONTROLS.md).
- The first snow-proxy robustness test compares the selected SLF station with the next-nearest eligible station for all 15 reviewed resort components. Eleven comparisons have high/moderate descriptive agreement, while four are low; snow remains an external-station proxy and causally unapproved. See [the SLF sensitivity review](reports/13_SNOW_PROXY_SENSITIVITY.md).
- The donor screen now checks proximity to the entire resolved Magic Pass network: 15 of 35 shortlisted pairs use a municipality within 30 km of another resolved Magic resort point, and only seven lie beyond 50 km from every resolved point. See [the network spillover audit](reports/14_DONOR_NETWORK_SPILLOVER_AUDIT.md).
- The seven geographically remote pairs were checked against the complete official Magic Pass roster for each anchor season: all seven donor station/place labels are absent. Official operator and government evidence nevertheless identifies an overlapping donor-specific tourism, pricing, access or infrastructure shock for every pair. The 35-pair shortlist is therefore exhausted and zero controls are approved. See [the external-shock audit](reports/16_DONOR_EXTERNAL_SHOCK_AUDIT.md).
- Following the researcher's distance idea, 2,046 destination–municipality rows compare all 186 hotel municipality series around the same reviewed destination. Six of seven descriptive ≤30 km versus >50 km contrasts are positive, but every effect/exposure flag remains false. See [the distance-gradient diagnostic](reports/15_TREATMENT_DISTANCE_GRADIENT.md).
- Checkpoints 4–5 are formally failed under the present donor and effective-sample design. Path C v0.2 instead segments 156 feature-complete linked lift clusters into two current structural groups and produces transparent analogues for 104 apparent non-member candidates. Twenty-five candidates are strong extrapolations from the eight reviewed treated references. A min/median/max aggregation audit retains `k=2`, but only 11 candidates are stable on every recorded segment/analogue/OOD criterion; row-level sensitivity is exposed in the decision-support export. Predicted-uplift and composite-score fields remain blank. See [the Path C decision](reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md), [the segmentation/analogue review](reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md), and [the aggregation-sensitivity review](reports/19_PATH_C_AGGREGATION_SENSITIVITY.md).
- Path C v0.3 adds official 2025 STATPOP population and complete-year HESTA intensity ratios as qualified point-container context. This covers 52 of 162 clusters and 39 of 104 candidates. It does not define destination catchments: every tourism-dependence approval flag remains false and the generic tourism-dependence field remains blank. See [the tourism-context review](reports/20_TOURISM_DEPENDENCE_CONTEXT.md).
- Path C v0.4 adds qualified Swiss straight-line population context for all 162 clusters. Seven superseded STATPOP identifiers are reconciled through five checksum-cached official OFS municipality mutations, preserving all 9,127,125 residents across the 2,110 municipality geometries dated 1 January 2026. Distances to municipalities above three population thresholds and population inside four radii are exposed as sensitivity fields—not travel times or catchments. Distance to the official country boundary and radius-specific truncation flags make the omitted foreign population explicit. Every accessibility approval flag remains false and the generic score stays blank. See [the accessibility-context review](reports/21_ACCESSIBILITY_CONTEXT.md).
- Path C v0.5 adds official ARE NPVM travel-time context dated 30 June 2025. Of 271 listing coordinates, 170 fall exactly in a traffic zone, 98 high-alpine Swiss points use the nearest zone intersecting their independently resolved current municipality (distance retained, maximum 3.64 km), and three French points remain missing. All 104 candidates have cluster-level road/public-transport context, but it is zonal model output—not live routing, rail-only access, a validated arrival node or a destination catchment—so approval flags remain false and the generic score stays blank. See [the transport-accessibility review](reports/22_TRANSPORT_ACCESSIBILITY_CONTEXT.md).
- Path C v0.6 adds official OFT/BAV straight-line proximity to 27,325 passenger stops and 1,717 train-capable stops, using exact published stop and mode codes. The 268 Swiss listing points are covered; three French listings remain missing because the source is not a complete French stop universe. Across clusters, the median of median distances is 0.33 km to any passenger stop and 4.39 km to a train station. All 104 candidates retain usable cluster context, but one cross-border cluster is partial. The metric is not a route, timetable, service-frequency or validated-arrival-node measure, so its approval flag remains false and the generic score stays blank. See [the stop-proximity review](reports/23_PUBLIC_TRANSPORT_STOP_CONTEXT.md).
- Path C v0.7 adds official winter-2026 GTFS Static journey context from every hotel municipality's main served stop to each reviewed destination's algorithmic bus/train arrival node. Five morning and seven return requests on a weekday and Saturday yield 49,104 samples across 2,046 destination–municipality pairs; 38,504 are feasible under the declared limits and 1,104 pairs are complete at every sampled time. Official historical snapshots were identified for seven exposure-winter timetable years, but none of the 2018–2025 services has yet been compared. The measure therefore remains current descriptive context, not a historically stable or causal accessibility feature. See [the journey review](reports/24_PUBLIC_TRANSPORT_JOURNEY_CONTEXT.md) and [the historical audit plan](reports/25_PUBLIC_TRANSPORT_HISTORICAL_AUDIT.md).
- Path C v0.8 adds a versioned review of all 15 destination arrival nodes against the generated official stop table. Eight stops explicitly name a lift or ski access, one names the destination locality, and six are retained transparently as village/local-centre proxies under the researcher-authorised fallback rule. Every node is within 2.1 km of its supplied component point and in the same current municipality; 14 occur on both sampled service days, while Grimentz–Le Boccard has a weekday warning. Approval is descriptive only: door-to-lift walking and historical continuity remain unverified. See [the arrival-node review](reports/26_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW.md).
- Path C v0.9 geometrically reconstructs all 98 municipality-constrained NPVM zone assignments. The deterministic selection and stored distances are exact, but 50 of the 73 proxy-using clusters have no exactly contained listing point for an internal sensitivity comparison; this includes 28 apparent candidates. Geometry validation therefore does not become route, historical or causal validation. See [the NPVM proxy audit](reports/27_TRANSPORT_ZONE_PROXY_AUDIT.md).
- Path C v0.10 compares geographic distance and scheduled public-transport time for the same 2,046 destination–municipality pairs. Ten destinations support a bidirectional rank comparison: the median distance–round-trip correlation is 0.743, while 225 pairs have transit rank at least 0.25 worse than distance rank suggests. Distance is therefore retained as informative but not interchangeable with transit accessibility. See [the distance–transport comparison](reports/28_DISTANCE_TRANSPORT_COMPARISON.md).
- Path C v0.11 adds the official Eurostat Census Grid 2021 version 3 as harmonised cross-border population context. The checksum-verified source contains 4,595,932 rows; 181,598 cells are retained near the linked clusters. Foreign-only population occurs within 30 km for 73 of 104 candidates and within 120 km for all 104; the median foreign-only share across all clusters is 20.6% at 60 km and 36.7% at 120 km. Mixed border cells and 13 spatially unallocated national records remain explicit. These are residential straight-line totals, not visitor catchments or travel-time markets, so approval flags remain false and the generic score stays blank. See [the cross-border population review](reports/29_CROSS_BORDER_POPULATION_CONTEXT.md).
- Path C v0.12 adds the current official FEDRO/ASTRA national-road axes. The checksum-verified File Geodatabase contains 3,084 main, feeder, connection and ramp features. Straight-line proximity is available for 268 Swiss listing points and complete for 103 of 104 candidates; the cross-border Portes du Soleil cluster remains partial. The median cluster-median distance is 6.81 km to a main national-road axis and 6.79 km to any published axis. Because the source does not classify motorways or usable entrances, these fields are not labelled motorway access, remain causally unapproved and do not populate the generic score. See [the national-road proximity review](reports/30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md).
- Path C v0.13 adds a checksum-verified official roster review for AlpsPass 2026/2027, the current Meilenweiss snapshot, and Schneepass Zentralschweiz 2026/2027. The versioned register retains 43 named pass areas and distinguishes the four unlimited AlpsPass core regions from its seven three-free-ski-days partner regions. Explicit resort-ID links cover 55 supplied listings in 29 clusters; 22 of 104 apparent candidates contain at least one linked listing. Mixed clusters remain partial rather than inheriting status wholesale. A non-link does not prove absence from the competing-pass market, historical competition is not reconstructed, and no causal or composite field is populated. See [the competing-pass review](reports/31_COMPETING_PASS_CONTEXT.md).
- Path C v0.14 adds complete current spatial context among the 162 preserved directory-linked lift clusters. Its 26,082 ordered non-self pairs produce focal-excluded counts at 25 and 50 km for all directory clusters, resolved current Magic clusters, reviewed competing-pass-linked clusters and their union. Candidates have medians of 8 other directory clusters within 25 km, 26 within 50 km and 9 other reviewed pass-network clusters within 50 km. These are straight-line diagnostics over provisional current clusters—not historical market structure, travel time, true competitor counts or causal network exposure. See [the network-context review](reports/32_PATH_C_NETWORK_CONTEXT.md).
- Path C v0.15 audits the geographic definition behind those counts without rebuilding the preserved clusters. Fifty-three clusters contain multiple supplied listing points; their median diameter is 6.54 km and the maximum is 46.35 km. All 26,082 ordered non-self pairs now retain minimum, median, coordinate-wise-median and maximum listing-point distance rules. Candidate neighbour counts change across those rules often enough that no single density is promoted as verified market structure; all coherence and feature-approval flags remain false. See [the cluster-geography sensitivity review](reports/33_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY.md).
- Path C v0.16 adds the planned SwissMetNet alternative-station sensitivity. Ten next-nearest stations support all 15 reviewed component comparisons and an alternative 1,749-row destination-month panel. Component temperature- and precipitation-anomaly correlations have medians of 0.967 and 0.815; all components receive high or moderate descriptive agreement. This supports regional anomaly robustness but is not independent gridded or piste validation, so causal weather approval remains false. See [the weather-station sensitivity review](reports/34_WEATHER_STATION_SENSITIVITY.md).
- Path C v0.17 adds the official 1 km MeteoSwiss TabsM/RhiresM gridded monthly sensitivity. All 2,385 component-month cells are complete and median station-grid anomaly correlations are 0.983 for temperature and 0.942 for precipitation, but Axalp and Meiringen-Hasliberg have low agreement because their valley station and resort-grid temperature anomalies diverge. The products use distinct gridding/monthly analysis but remain station-informed rather than an independent measurement network; no causal weather field is approved. See [the gridded-weather sensitivity review](reports/35_WEATHER_GRIDDED_SENSITIVITY.md).
- Path C v0.18 adds the peer-reviewed SPASS OSHD-CLQM 1 km daily gridded-snow sensitivity for ten common winters. Around the selected stations, all 15 components have high or moderate agreement with the model (median relative depth difference 25.9%); around the resort points, eight are low and the median difference rises to 61.9%. This isolates spatial station-to-resort representativeness as the main weakness. SPASS is calibrated against a snow-assimilating SLF model and is not an independent measurement network or piste observation, so causal approval remains false. See [the gridded-snow sensitivity review](reports/36_SNOW_GRIDDED_SENSITIVITY.md).
- Path C v0.19 adds a separate current tourism-intensity layer for the exact municipality scopes already used by the 11 reviewed destination outcomes. All 11 scopes are complete in STATPOP–HESTA 2025 across 12 municipality links; four are complete observed municipal scopes and seven remain explicit core-municipality proxies. This is stronger than assigning a destination from one listing point but still is neither a validated visitor catchment nor a pre-treatment feature. Candidate tourism dependence, causal approval and the generic composite field remain blank. See [the municipal tourism-context review](reports/20_TOURISM_DEPENDENCE_CONTEXT.md).
- Path C v0.20 audits whether component-point municipalities reproduce those reviewed outcome scopes. Ten of 11 sets match and 11 of 12 municipality links are recovered, but all seven core-proxy matches are definition-linked. Among the four separately reviewed complete scopes, only three match exactly: the Meiringen point omits Hasliberg's second municipality. The result supports point containment only as conservative descriptive core context; no candidate-scope transfer or tourism-catchment approval follows. See [the destination-scope concordance audit](reports/37_DESTINATION_SCOPE_CONCORDANCE_AUDIT.md).
- GitHub synchronization is configured: `main` tracks `origin/main` at `https://github.com/Chocaklick/Master-thesis-Magic-pass.git`.

See [PROJECT_STATE.md](PROJECT_STATE.md) for the authoritative current state and [logs/research_journal.md](logs/research_journal.md) for the chronological record.

## Repository structure

```text
config/               Versioned configuration
prompts/              Authoritative project mission and research instructions
data_raw/             Existing data supplied by the researcher; immutable
data_external/        Original versions of newly downloaded external data
data_interim/         Reproducible intermediate transformations
data_processed/       Final cleaned analytical datasets
metadata/             Provenance, variable definitions, and causal roles
src/                  Reusable Python code by analytical domain
notebooks/            Exploratory notebooks; not the sole home of key logic
tests/                Automated tests
models/               Serialized model artifacts (ignored by default)
figures/              Versionable research figures
reports/              Data and methodology audits
logs/                 Research journal and structured collection log
outputs/              Generated exports (ignored by default)
```

## Python setup

The initialized interpreter is Python 3.12.7. Use any local Python 3.12 interpreter to create the environment.

From PowerShell in the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,audit]"
```

On macOS or Linux with Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,audit]'
```

The core dependency set remains small. Install `.[dev,audit]` to reproduce the geospatial/PDF audit tools; statistical, causal, and machine-learning libraries should be added only when a feasibility gate justifies them.

## Reproducing the checkpoint pipeline

With the original files available under ignored `data_raw/` and the previously cached official responses under ignored `data_external/`, run from the project root:

```powershell
.\.venv\Scripts\python.exe src\run_checkpoint_pipeline.py
```

To check or collect configured official evidence before rebuilding, add `--with-collection`. The collector reuses checksum-verified cached responses and logs every success or failure. The default pipeline performs no network access.

The run ends with the automated test suite. Main numbered reports currently run through `reports/30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md`, plus `reports/model_feasibility_report.md`.

## Data conventions

- Raw and externally downloaded files are immutable.
- Derived data never overwrite source data.
- Dataset values must trace to a source record or a documented derivation.
- Stable identifiers such as `resort_id`, `cluster_id`, `municipality_id`, and `bfs_id` are preferred over names as keys.
- Credentials belong in environment variables, never committed files.
- Raw, proprietary, sensitive, or large data are not stored in Git by default. Their metadata and reproducible acquisition/processing logic should be versioned.

## Git workflow

Use meaningful milestone commits on `main` (or short-lived feature branches for larger work). Before changing a pipeline, run `git status`; after verification, commit only the relevant files. Never force-push or rewrite shared history. Important milestones should be pushed once `origin` is configured.

## Persistent project memory

Every substantive session starts by reading, in order:

1. `PROJECT_STATE.md`
2. `README.md`
3. `AGENTS.md`
4. `logs/research_journal.md`

Then read `prompts/main_research_prompt.md` before research work.

Update the state file and journal before ending major work. The repository—not chat history—is the durable research record.
