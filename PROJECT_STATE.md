# PROJECT STATE

## Project objective

Build a reproducible and scientifically defensible Business Analytics framework for Swiss ski resorts, integrating resort structure, hotel overnight stays, Magic Pass adoption, and climate/snow conditions. Later phases may estimate causal effects and support evidence-based recommendations for non-member resorts.

The authoritative project mission is `prompts/main_research_prompt.md`, preserved from the user's full research instructions. It defines the end-to-end research scope, scientific constraints, six checkpoints, feasibility gates, and expected deliverables. Method selection must follow the evidence and distinguish correlation, causality, prediction, and recommendations.

## Current phase

Main research mission adopted; awaiting existing source data for Checkpoint 1. Repository initialization and GitHub setup are complete. The project inventory was rechecked when saving the mission and still contains no thesis datasets.

## Last update

2026-09-20 01:06 CEST

## Completed work

- Inspected the initial workspace, operating system, Git, GitHub CLI availability, Python installations, virtual environments, and file inventory.
- Confirmed that the workspace was empty and was not a Git repository.
- Created the agreed directory structure without overwriting existing work.
- Created a local `.venv` with Python 3.12.7.
- Added initial dependency, ignore, provenance, documentation, and logging files.
- Created baseline initial-data and existing-cluster audit reports.
- Initialized a local Git repository on `main` and created the initial project commit.
- Verified the required 22 directories and 12 core files, CSV header schemas, TOML syntax, virtual environment, clean Git worktree, and repository integrity.
- Added this exact repository to the Windows user's Git `safe.directory` list so normal local Git commands work despite sandbox-created metadata ownership.
- Verified that the supplied GitHub repository was empty, configured it as `origin`, pushed `main`, and established upstream tracking to `origin/main`.

## Work currently in progress

No empirical work is in progress. The full research instructions have been saved and adopted as the project mission; this session records the mission and its links for future work.

## Next actions

Follow the sequence in `prompts/main_research_prompt.md`, beginning with Checkpoint 1:

1. Place existing thesis datasets in `data_raw/` without modifying them.
2. Audit each supplied dataset and update the two audit reports and metadata tables.
3. Commit and push the resulting verified audit milestone.

## Important methodological decisions

- Python is the primary language; the initialized target is Python 3.12.
- Raw and externally downloaded source files are immutable.
- Resort assignment and municipality assignment are separate methodological problems.
- Existing lift clustering will be inspected and validated, not automatically rebuilt.
- No source definitions, missing values, membership histories, or causal interpretations will be fabricated.
- Later predictive features should use pre-treatment information unless explicitly and defensibly justified.
- Validation must respect resort grouping and time; monthly rows are not independent resorts.

## Existing datasets

No data files were present in the project at initialization. The specifically expected CSV and WMS capabilities files were not found. See `reports/INITIAL_DATA_AUDIT.md`.

## External datasets collected

None.

## Main analytical datasets

None.

## Known data problems

- Existing thesis data have not yet been supplied to this repository.
- Variable definitions, encodings, delimiters, identifier integrity, missingness, duplicates, geographic levels, and temporal levels cannot yet be assessed.
- Magic Pass historical membership coverage is unknown.
- The station/resort-to-tourism-municipality crosswalk does not yet exist.

## Ambiguous cases requiring manual review

None identified because no data were available. Existing cluster assignments must be sampled geographically when the files arrive.

## Current sample size

Unknown; no analytical observations are available.

## Current Magic Pass treatment coverage

Unknown; no membership-history dataset has been collected or supplied.

## Current modelling feasibility

Not assessable. Modelling is intentionally deferred until the data inventory, identifiers, provenance, treatment history, and observational structure are validated.

## Models already tested

None.

## Rejected approaches and reasons

- Premature modelling: rejected because the source data and treatment history are not yet audited.
- Automatic reconstruction of ski-lift clusters: rejected because existing work should be understood and validated first.
- Inferring overnight-stay municipalities from a single resort/lift coordinate: rejected because tourism destinations may span one or more municipalities.

## Important file locations

- Authoritative research mission: `prompts/main_research_prompt.md`
- Initial data audit: `reports/INITIAL_DATA_AUDIT.md`
- Existing clustering audit: `reports/EXISTING_CLUSTER_AUDIT.md`
- Source provenance register: `metadata/data_sources_master.csv`
- Data dictionary: `metadata/data_dictionary.csv`
- Variable causal-role register: `metadata/variable_causal_role.csv`
- Research journal: `logs/research_journal.md`
- Data collection log: `logs/data_collection_log.csv`

## Open research questions

- What are the exact definitions and construction histories of the existing datasets?
- Can the existing lift-cluster assignments serve as a stable resort reference layer?
- What stable identifiers link resorts, destinations, municipalities, and overnight-stay observations?
- What is the historically correct Magic Pass membership timeline?
- Which climate/snow measures are available at defensible spatial and temporal resolutions?

## Immediate next action

Obtain the existing thesis data files, preserve them under `data_raw/`, and perform a non-destructive dataset audit before any collection or modelling.
