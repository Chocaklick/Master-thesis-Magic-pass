# Methodological literature register

This register closes the three methodological citation gaps identified in the thesis claim map. Metadata were checked against original publisher pages and DOI records on 2026-09-25. The references support method definitions and limitations; they do not override the project-specific identification gates or turn the descriptive Path C analysis into causal evidence.

- Peer-reviewed references: **7**
- Methodological claim groups covered: **3 / 3**
- Unique DOI values: **7**

## Causal identification, staggered adoption and interference

### `HUDGENS_HALLORAN_2008_INTERFERENCE`

- Reference: Michael G. Hudgens and M. Elizabeth Halloran (2008). “Toward Causal Inference With Interference.” *Journal of the American Statistical Association*, 103(482), 832-842. https://doi.org/10.1198/016214508000000292
- Verified publisher page: https://www.tandfonline.com/doi/abs/10.1198/016214508000000292
- Use in this thesis: Formalises direct, indirect, total and overall causal effects when treatment can affect other units within groups.
- Interpretive boundary: Its estimands and unbiased estimators rely on a specified grouped-interference setting and experimental assignment; the thesis uses it to motivate the spillover threat, not to estimate those effects.

### `CALLAWAY_SANTANNA_2021_DID`

- Reference: Brantly Callaway and Pedro H. C. Sant'Anna (2021). “Difference-in-Differences with multiple time periods.” *Journal of Econometrics*, 225(2), 200-230. https://doi.org/10.1016/j.jeconom.2020.12.001
- Verified publisher page: https://www.sciencedirect.com/science/article/pii/S0304407620303948
- Use in this thesis: Provides group-time average treatment effects and inference for staggered Difference-in-Differences with heterogeneous treatment timing and effects.
- Interpretive boundary: The method still requires a defensible comparison group and an explicit parallel-trends assumption; its availability does not identify the present design.

### `SUN_ABRAHAM_2021_EVENT_STUDIES`

- Reference: Liyang Sun and Sarah Abraham (2021). “Estimating dynamic treatment effects in event studies with heterogeneous treatment effects.” *Journal of Econometrics*, 225(2), 175-199. https://doi.org/10.1016/j.jeconom.2020.09.006
- Verified publisher page: https://www.sciencedirect.com/science/article/pii/S030440762030378X
- Use in this thesis: Shows how conventional two-way fixed-effect event-study coefficients can be contaminated under staggered timing and heterogeneous effects.
- Interpretive boundary: The proposed estimator addresses heterogeneous timing, not invalid donors, spillovers, treatment ambiguity or destination-scope error.

## Causal machine-learning feasibility

### `WAGER_ATHEY_2018_CAUSAL_FORESTS`

- Reference: Stefan Wager and Susan Athey (2018). “Estimation and Inference of Heterogeneous Treatment Effects using Random Forests.” *Journal of the American Statistical Association*, 113(523), 1228-1242. https://doi.org/10.1080/01621459.2017.1319839
- Verified publisher page: https://www.tandfonline.com/doi/abs/10.1080/01621459.2017.1319839
- Use in this thesis: Develops causal forests for heterogeneous treatment effects and inference under a potential-outcomes framework with unconfoundedness.
- Interpretive boundary: The theoretical guarantees do not replace treatment identification, unconfoundedness, overlap or adequate effective sample size.

### `KUNZEL_ET_AL_2019_METALEARNERS`

- Reference: Sören R. Künzel, Jasjeet S. Sekhon, Peter J. Bickel and Bin Yu (2019). “Metalearners for estimating heterogeneous treatment effects using machine learning.” *Proceedings of the National Academy of Sciences*, 116(10), 4156-4165. https://doi.org/10.1073/pnas.1804597116
- Verified publisher page: https://www.pnas.org/doi/10.1073/pnas.1804597116
- Use in this thesis: Organises supervised learners into S-, T-, X- and related strategies for estimating conditional average treatment effects.
- Interpretive boundary: Flexible outcome learning does not by itself justify a causal estimand, remove confounding or create stable heterogeneity information from a very small treated sample.

## Clustering validation and partition stability

### `HUBERT_ARABIE_1985_PARTITIONS`

- Reference: Lawrence Hubert and Phipps Arabie (1985). “Comparing partitions.” *Journal of Classification*, 2, 193-218. https://doi.org/10.1007/BF01908075
- Verified publisher page: https://link.springer.com/article/10.1007/BF01908075
- Use in this thesis: Provides chance-corrected partition-comparison foundations used for adjusted Rand stability diagnostics.
- Interpretive boundary: Partition agreement measures stability relative to another partition; it does not establish that either partition is substantively correct.

### `ROUSSEEUW_1987_SILHOUETTES`

- Reference: Peter J. Rousseeuw (1987). “Silhouettes: A graphical aid to the interpretation and validation of cluster analysis.” *Journal of Computational and Applied Mathematics*, 20, 53-65. https://doi.org/10.1016/0377-0427(87)90125-7
- Verified publisher page: https://www.sciencedirect.com/science/article/pii/0377042787901257
- Use in this thesis: Defines the silhouette display and average silhouette width used to assess cluster tightness and separation.
- Interpretive boundary: Silhouette quality evaluates geometry in the selected feature space; it does not validate commercial destination identities or causal relevance.

## Editorial rule

Retain the `source_id` values as auditable temporary citation keys. Convert the displayed references to the university's required citation style only at final typesetting, without changing titles, years, journals, pages or DOI values.
