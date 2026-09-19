# AGENTS.md

## Session start

Read, in order: `PROJECT_STATE.md`, `README.md`, this file, and `logs/research_journal.md`. Inspect relevant prior outputs before repeating work.

Then read `prompts/main_research_prompt.md`, the authoritative project mission. Follow its research sequence, feasibility gates, and checkpoints alongside the latest user directions. The mission supersedes the initialization-only scope; preserve the existing clustering and the distinction between resort assignments and municipality exposure mappings.

## Core rules

- Use Python as the primary language and run important scripts from the project root.
- Use project-relative paths or centralized configuration; never commit user-specific absolute paths.
- Treat `data_raw/` and original files in `data_external/` as immutable. Derived data must go to `data_interim/` or `data_processed/` and never overwrite a source.
- Never fabricate data, definitions, sources, missing values, identifiers, or provenance. Mark uncertainty explicitly.
- Record every external source in `metadata/data_sources_master.csv` and every analytical variable in `metadata/data_dictionary.csv` when understood.
- Do not rebuild the existing ski-lift clustering without documented justification and approval. Audit its identifiers, assignments, ambiguity, and geographic plausibility first.
- Keep lift/cluster-to-resort assignment distinct from resort/destination-to-municipality assignment for overnight stays.
- Preserve stable IDs (`resort_id`, `cluster_id`, `municipality_id`, `bfs_id`) and original names; do not use names as the sole key.
- Treatment variables must be historically correct. Use pre-treatment information for predictive recommendation features unless explicitly justified otherwise.
- Prevent leakage. Do not treat repeated monthly observations from one resort as independent resorts. Prefer grouped and temporal validation over random row splitting where appropriate.
- A causal package does not make an estimate causal. State assumptions, identification strategy, diagnostics, and limits.
- Prefer interpretable, defensible methods over unnecessary complexity. Record failed experiments and negative results.
- Make long-running collection resumable with checkpoints; do not repeat completed downloads or manual verification without a documented reason.
- Do not delete existing research outputs or rewrite Git history without explicit justification and approval.
- Before ending major work, update `PROJECT_STATE.md` and append to `logs/research_journal.md`.

## Git and security

- Inspect `git status` before major changes and commit coherent milestones.
- Never commit `.venv/`, caches, secrets, credentials, or unreviewed large/proprietary data.
- Never force-push or delete remote branches unless explicitly authorized.
