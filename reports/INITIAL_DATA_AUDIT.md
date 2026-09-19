# Initial Data Audit

## Audit scope

This is the non-destructive baseline inspection performed during repository initialization on 2026-09-20. The working directory was inspected before project files were created. It contained no files or subdirectories and was not a Git repository.

## Environment findings

| Item | Finding |
|---|---|
| Operating system | Microsoft Windows NT 10.0.22621.0 |
| Shell | PowerShell |
| Git | 2.53.0.windows.2; installed and user name/email configured |
| Git repository at start | No |
| GitHub remote at start | No |
| GitHub CLI | Not installed or not on `PATH`; authentication could not be checked |
| `python` / `py` on `PATH` | No |
| Python installation found | Anaconda Python 3.12.7 at `C:\Users\Thibaud\anaconda3\python.exe` |
| Existing virtual environment | None |
| Created virtual environment | `.venv/`, Python 3.12.7, pip 24.2 |

## Data inventory

No CSV, XML, spreadsheet, geospatial, notebook, script, or other thesis data file was present in the project directory at the time of the baseline inspection.

### Expected files not found

- `nuitée_commune_final.csv`
- `bergfex_stations_ski_suisse_par_region.csv`
- `assignations_stations_final_clean.csv`
- `clusters_stations_final_clean.csv`
- `stations_ski_geocoded_a_verifier_complet.csv`
- `wms_layers_importants_these_ski.csv`
- WMS capabilities XML files from geo.admin.ch

Absence here means only that the files were not in this project directory; it does not assert that they do not exist elsewhere.

## Inspection results

Because no datasets were available, row counts, columns, geographic and temporal levels, identifiers, missingness, duplicates, inconsistencies, and cross-dataset relationships could not be evaluated. No classification as raw, manually constructed, intermediate, or final has been inferred from filenames alone.

## Data-quality concerns to test when files arrive

1. Encoding and delimiter consistency, especially for accented French/German/Italian place names.
2. Stable identifiers versus name-only joins and spelling variants.
3. Duplicate keys at the claimed geographic and temporal grain.
4. Missing-value encodings and undocumented sentinel values.
5. Municipality mergers and historically changing BFS identifiers.
6. Resort, tourism-destination, and municipality many-to-many relationships.
7. Construction date and provenance of manually cleaned or “final” datasets.
8. Coordinate reference systems, coordinate precision, and geographic plausibility.

## Required next audit

Place original files in `data_raw/` without editing them. For each file, record a checksum and provenance, then inspect schema, row count, key candidates, missingness, duplicates, value ranges, geographic/temporal grain, and relationships. Update `metadata/data_sources_master.csv`, `metadata/data_dictionary.csv`, this report, and `PROJECT_STATE.md` without replacing source files.
