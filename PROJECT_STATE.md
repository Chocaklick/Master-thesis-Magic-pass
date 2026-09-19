# PROJECT STATE

## Project objective

Build a reproducible and scientifically defensible Business Analytics framework for Swiss ski resorts, integrating resort structure, hotel overnight stays, Magic Pass adoption, and climate/snow conditions. Later phases may estimate causal effects and support evidence-based recommendations for non-member resorts.

## Current phase

Repository initialization and data discovery. Infrastructure is ready locally; existing thesis datasets and the GitHub remote are not yet available.

## Last update

2026-09-20 00:26 CEST

## Completed work

- Inspected the initial workspace, operating system, Git, GitHub CLI availability, Python installations, virtual environments, and file inventory.
- Confirmed that the workspace was empty and was not a Git repository.
- Created the agreed directory structure without overwriting existing work.
- Created a local `.venv` with Python 3.12.7.
- Added initial dependency, ignore, provenance, documentation, and logging files.
- Created baseline initial-data and existing-cluster audit reports.
- Initialized a local Git repository on `main` and created the initial project commit.

## Work currently in progress

None. Initialization has stopped at the requested checkpoint.

## Next actions

1. Create an empty GitHub repository and provide its HTTPS or SSH URL.
2. Add the GitHub repository as `origin`, verify it, and push `main`.
3. Place existing thesis datasets in `data_raw/` without modifying them.
4. Audit each supplied dataset and update the two audit reports and metadata tables.

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

Obtain the empty GitHub repository URL and the existing thesis data files. Configure `origin` and push the initialized `main` branch, then perform a non-destructive dataset audit.
