# Annual Magic Pass winter/summer offering review

## Purpose

The annual launch publications provide the cleanest available evidence for two distinct questions:

1. Was a reviewed destination listed in the Magic Pass for that season?
2. Did the publication mark it as winter-only or summer-winter?

The second question matters because a hotel-demand effect need not be confined to the ski season. Membership, summer lift access and daily lift operation are nevertheless different concepts and remain separate in the data.

## Method

Seven dated annual publications were rendered and visually inspected page by page or as a single official image:

| Season | Source | Page | Evidence form |
|---|---|---:|---|
| 2017/2018 | `MAGIC_2017` | 8 | Founding pass validity limited to the winter season |
| 2018/2019 | `MAGIC_2018` | 2 | Full base roster plus a complete named list of 16 summer destinations |
| 2020/2021 | `MAGIC_2020_MAP` | 1 | Complete official map with separate winter, summer-winter, Glacier 3000 and baths symbols |
| 2022/2023 | `MAGIC_2022_DOSSIER` | 6 | Complete map with `HIVER` and `ÉTÉ-HIVER` symbols |
| 2023/2024 | `MAGIC_2023` | 5 | Complete map with `HIVER` and `ÉTÉ-HIVER` symbols |
| 2024/2025 | `MAGIC_2024_MAP` | 1 | Dated complete map with winter and summer-winter symbols |
| 2025/2026 | `MAGIC_2025` | 5 | Numbered list of 99 destinations with a symbol beside every label |

The transcription is stored in `metadata/magic_pass_season_offering_evidence.json`. The derived fields are joined to `data_processed/magic_pass_membership_status_by_season.csv`. Each row retains the source ID, one-based page or single-image locator, evidence type, exact published labels and a scope qualification for composite destinations.

## Results

The review classifies 58 active destination-unit seasons for the 14 reviewed analytical units. Thirty-six have documented summer access for at least one published component label; 22 are winter-only or belong to the founding winter-only pass.

Composite units are not flattened. For example:

- In 2022/2023, Villars-Gryon is marked summer-winter while Les Diablerets is winter-only.
- In 2020/2021, Les Diablerets carries the summer-winter lift symbol while Villars-Gryon carries a separate baths-option symbol; the latter is not reclassified as a lift-season symbol.
- Espace Dent Blanche is repeatedly mixed: Evolène is marked summer-winter while Arolla and La Forclaz are winter-only in the reviewed maps.
- From 2023/2024, the Reichenbach portfolio is mixed: Kiental is summer-winter while Faltschen is winter-only.
- In 2025/2026, the reviewed Gstaad operator domain mixes summer-winter components with winter-only components.

The output therefore exposes both `summer_access_documented` and the component labels supporting that flag. A destination-unit flag means at least one listed component has summer access; it never implies that every component does.

## Remaining modality gaps

The main 2021/2022 official dossier is checksum-cached. Its statement that the network expands by five named stations closes membership continuity when combined with the complete official 2020/2021 map. It documents aggregate totals of 40 winter stations and 21 summer destinations, but does not provide a station-by-station modality roster. Individual 2021/2022 summer status therefore remains unknown.

Individual winter/summer modality remains unclassified where no complete named annual list or symbol map has been recovered, especially 2019/2020 and 2021/2022. These cells remain explicit unknowns; annual membership continuity is never treated as proof that summer access is unchanged.

## Causal interpretation

The annual register materially improves treatment description and prevents winter-only and four-season offers from being conflated. It does not change the current Path C decision. Summer access is not proof of operation on every day, visitation intensity, hotel-market exposure, absence of simultaneous investment or a valid untreated comparison group. All causal treatment and control approval flags remain false.
