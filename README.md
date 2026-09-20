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
- A 31,248-row municipality-month hotel-demand panel, a separate 31,248-row official HESTA capacity panel, daily SLF snow proxies, current point-municipality crosswalk, official Magic Pass evidence table, and resort-level data-quality table are reproducibly generated.
- The 18 candidate entry/outcome links have been collapsed into 14 reviewed destination units. Eleven have an explicit outcome scope and form a 1,848-row diagnostic destination-month panel; three incomplete composite scopes are excluded. Capacity is complete for 1,637 destination-months.
- The current feasibility decision is Path C: exploratory segmentation/analogue decision support. Causal modelling remains gated by membership continuity, remaining time-varying confounders, spillovers, control contamination, and snow-proxy representativeness.
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

The run ends with the automated test suite. Main checkpoint reports are `reports/01_DATA_AUDIT.md`, `reports/02_DATA_COLLECTION.md`, `reports/03_DATA_QUALITY.md`, `reports/04_DESTINATION_UNIT_REVIEW.md`, `reports/05_HOTEL_CAPACITY.md`, `reports/06_SNOW_SOURCE_AND_PROXY.md`, and `reports/model_feasibility_report.md`.

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
