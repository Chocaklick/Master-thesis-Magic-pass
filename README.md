# Master Thesis — Swiss Ski Resort Analytics

This repository is the reproducible technical workspace for a Master's thesis in Business Analytics on Swiss ski resorts, hotel overnight stays, Magic Pass adoption, climate and snow conditions, and decision support for resorts that are not currently Magic Pass members.

## Research objective

The long-term objective is to combine defensible data engineering, causal/econometric analysis, machine learning, and geospatial analysis. The repository is currently in the initialization and data-discovery phase. No treatment-effect model, opportunity score, or large-scale external collection has been started.

A central methodological distinction is preserved throughout the project:

```text
ski lifts -> lift clusters -> ski resorts

ski resorts -> tourism destinations -> one or more municipalities -> overnight stays
```

A resort assignment is not automatically a municipality assignment.

## Current status

- Local Git repository initialized on `main`.
- Local Python 3.12 virtual environment created in `.venv/`.
- Baseline folder structure and provenance schemas created.
- No thesis datasets were present at initialization; the existing-cluster audit therefore remains pending.
- No GitHub remote is configured yet because GitHub CLI is unavailable and no repository URL was supplied.

See [PROJECT_STATE.md](PROJECT_STATE.md) for the authoritative current state and [logs/research_journal.md](logs/research_journal.md) for the chronological record.

## Repository structure

```text
config/               Versioned configuration
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

The initialized interpreter is Python 3.12.7. Python was found at `C:\Users\Thibaud\anaconda3\python.exe`, although it is not currently on `PATH`.

From PowerShell in the project root:

```powershell
C:\Users\Thibaud\anaconda3\python.exe -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On macOS or Linux with Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

The initial dependency set is deliberately small. Add statistical, causal, geospatial, or machine-learning libraries only when a documented task requires them.

## Reproducing the initialization audits

The current audits describe an empty initial data inventory. To reproduce the baseline from the project root:

```powershell
git status
git remote -v
git branch --show-current
rg --files -g '!**/.git/**' -g '!**/.venv/**'
.\.venv\Scripts\python.exe --version
```

When thesis datasets are added, preserve originals under `data_raw/`, record provenance in `metadata/data_sources_master.csv`, and rerun a documented audit before transformations. The cluster audit must be updated only after the existing clustering files are available; the clustering must not be rebuilt as part of that audit.

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

Update the state file and journal before ending major work. The repository—not chat history—is the durable research record.
