# Annual Magic Pass winter/summer offering review

## Purpose

The annual launch publications provide the cleanest available evidence for two distinct questions:

1. Was a reviewed destination listed in the Magic Pass for that season?
2. Did the publication mark it as winter-only or summer-winter?

The second question matters because a hotel-demand effect need not be confined to the ski season. Membership, summer lift access and daily lift operation are nevertheless different concepts and remain separate in the data.

## Method

Six dated annual publications were rendered and visually inspected page by page:

| Season | Source | Page | Evidence form |
|---|---|---:|---|
| 2017/2018 | `MAGIC_2017` | 8 | Founding pass validity limited to the winter season |
| 2018/2019 | `MAGIC_2018` | 2 | Full base roster plus a complete named list of 16 summer destinations |
| 2022/2023 | `MAGIC_2022_DOSSIER` | 6 | Complete map with `HIVER` and `ÉTÉ-HIVER` symbols |
| 2023/2024 | `MAGIC_2023` | 5 | Complete map with `HIVER` and `ÉTÉ-HIVER` symbols |
| 2024/2025 | `MAGIC_2024_MAP` | 1 | Dated complete map with winter and summer-winter symbols |
| 2025/2026 | `MAGIC_2025` | 5 | Numbered list of 99 destinations with a symbol beside every label |

The transcription is stored in `metadata/magic_pass_season_offering_evidence.json`. The derived fields are joined to `data_processed/magic_pass_membership_status_by_season.csv`. Each row retains the source ID, one-based PDF page, evidence type, exact published labels and a scope qualification for composite destinations.

## Results

The review classifies 52 active destination-unit seasons for the 14 reviewed analytical units. Thirty-one have documented summer access for at least one published component label; 21 are winter-only or belong to the founding winter-only pass.

Composite units are not flattened. For example:

- In 2022/2023, Villars-Gryon is marked summer-winter while Les Diablerets is winter-only.
- Espace Dent Blanche is repeatedly mixed: Evolène is marked summer-winter while Arolla and La Forclaz are winter-only in the reviewed maps.
- From 2023/2024, the Reichenbach portfolio is mixed: Kiental is summer-winter while Faltschen is winter-only.
- In 2025/2026, the reviewed Gstaad operator domain mixes summer-winter components with winter-only components.

The output therefore exposes both `summer_access_documented` and the component labels supporting that flag. A destination-unit flag means at least one listed component has summer access; it never implies that every component does.

## Unresolved seasons

The main 2021/2022 official dossier has now been downloaded and checksum-cached successfully. It documents aggregate totals of 40 winter stations and 21 summer destinations, but it does not provide a station-by-station roster. It therefore does not resolve the seven remaining continuity gaps or individual summer status.

Individual winter/summer modality remains unclassified where no complete named annual list or symbol map has been recovered, especially 2019/2020 through 2021/2022. These cells remain explicit unknowns; they are not filled by carrying a later summer symbol backward.

## Causal interpretation

The annual register materially improves treatment description and prevents winter-only and four-season offers from being conflated. It does not change the current Path C decision. Summer access is not proof of operation on every day, visitation intensity, hotel-market exposure, absence of simultaneous investment or a valid untreated comparison group. All causal treatment and control approval flags remain false.
