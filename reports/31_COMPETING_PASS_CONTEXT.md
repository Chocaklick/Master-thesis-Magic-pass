# Qualified competing-pass roster context

## Scope

This review uses checksum-cached official material for three products: **AlpsPass 2026/2027**, **Meilenweiss at the retrieval-date snapshot**, and **Schneepass Zentralschweiz 2026/2027**. The versioned register contains **43 official pass-area rows**: 11 AlpsPass regions, 17 Meilenweiss regions and 15 Schneepass regions.

AlpsPass is deliberately split into **four unlimited core regions** and **seven partner regions providing three free ski days**. Meilenweiss is recorded as a current annual-pass roster without inventing a season label. Schneepass is recorded as a winter-2026/2027 included-region roster. These benefit tiers are never flattened into a single equivalent treatment intensity.

## Conservative entity linking

The official-area register contains explicit reviewed links to supplied resort IDs. It does not fuzzy-match names at runtime. This preserves mixed clusters: for example, Arosa Lenzerheide can be linked without automatically assigning Chur-Brambrüesch, and Pizol can be linked without automatically assigning Mastrils or Tristeli.

- supplied resort listings linked to at least one reviewed roster: **55 / 271**
- lift clusters containing at least one linked listing: **29 / 162**
- clusters with only partial listing-level links: **10**
- apparent Path C candidates containing at least one linked listing: **22 / 104**
- listing or cluster rows treated as verified absence from the competing-pass market: **0**
- competing-pass fields approved as causal/pre-treatment model features: **0**

## Interpretation limit

A non-link means only **not linked in these three reviewed official rosters**. It does not prove that a destination has no competing pass, no regional alliance, no reciprocal benefit, or no unenumerated component coverage. Two products are season-specific 2026/2027 snapshots and Meilenweiss is a retrieval-date snapshot; they do not reconstruct historical competition around Magic Pass entry dates. The separate bounded Top4 reconstruction in `reports/41_HISTORICAL_COMPETING_PASS_CONTEXT.md` supplies dated positive-presence evidence for one product only and does not change the interpretation of these current non-links. The fields are therefore descriptive current business context only. `competing_pass_market_absence_verified` and `competing_pass_feature_approved` remain false for every row, and no uplift or composite score is populated.

## Outputs

- `config/competing_pass_roster_2026_27.csv`
- `data_processed/resort_competing_pass_context.csv`
- `data_processed/path_c_cluster_competing_pass_context.csv`
- `reports/competing_pass_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified roster context appended)
