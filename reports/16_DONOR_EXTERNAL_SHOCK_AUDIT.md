# Donor competing-pass and local-shock audit

Generated reproducibly by `src/causal_inference/build_donor_external_shock_audit.py` from a versioned manual review whose cited official publications are checksum-cached.

## Result

The network screen left seven pairs beyond 50 km from every resolved Magic Pass point. Official-source review now excludes the two Gonten/Kronberg pairs from priority consideration because independent local tourism investments overlap their treatment anchors. The remaining **5 pairs (4 unique donor municipalities)** remain only deep-audit candidates: all have a documented or strongly indicated competing Grisons pass environment, and none has complete proof of historical Magic nonmembership, accessibility stability, and absence of operator-specific investment.

| Treatment | Donor | Competing pass evidence | Local-shock review | Decision |
|---|---|---|---|---|
| anniviers_magic_portfolio | 3782 Corviglia St. Moritz | SnowPass Graubünden | specific_operator_investment_review_pending | retain_for_deeper_manual_audit_competing_pass_risk |
| bumbach | 3102 Jakobsbad - Kronberg | — | contemporaneous_operator_investment_and_weather_sensitive_winter_change_documented | exclude_contemporaneous_local_tourism_shock |
| bumbach | 3714 Splügen Rheinwald | graubündenCARD | specific_operator_investment_review_pending | retain_for_deeper_manual_audit_competing_pass_risk |
| espace_dent_blanche | 3847 Minschuns - Val Müstair | SnowPass Graubünden | specific_operator_investment_review_pending | retain_for_deeper_manual_audit_competing_pass_risk |
| moleson | 3102 Jakobsbad - Kronberg | — | contemporaneous_major_talstation_investment_documented | exclude_contemporaneous_local_tourism_shock |
| saas_fee | 3752 Samnaun Silvretta Arena Samnaun / Ischgl | SnowPass Graubünden | cross_border_domain_and_specific_operator_investment_review_pending | retain_for_deeper_manual_audit_competing_pass_risk |
| saas_fee | 3782 Corviglia St. Moritz | SnowPass Graubünden|TopCard | specific_operator_investment_review_pending | retain_for_deeper_manual_audit_competing_pass_risk |

## Evidence qualifications

- `regional_pass_environment_documented_operator_participation_not_exactly_proven` is deliberately weaker than exact operator membership. Regional SnowPass activity cannot by itself establish a specific operator's tariff validity.
- The 2022/23 graubündenCARD list names Splügen-Tambo immediately before the May 2023 anchor. The original 2023/24 publication was found in the official search index but returned HTTP 404 during reproducible collection, so anchor-season continuity remains unresolved.
- TopCard access in Upper Engadine around the Saas-Fee anchor is explicitly documented, but the original operator tariff still needs checking.
- Samnaun is a cross-border domain. Austrian demand, access, policy, snow and investment shocks remain outside the current Swiss covariate panel.
- Kronberg's reports show a diversified family/leisure destination with its own capital projects; it is not treated as a clean ski-only comparison municipality.

## Identification decision

This stage prioritises evidence collection; it does not turn any donor into a causal control. Of 35 shortlisted pairs, 15 are deprioritised within 30 km of the resolved network, 13 are deprioritised at 30–50 km, two are excluded for contemporaneous local tourism shocks, and five await deeper audit. **Approved causal controls: 0.**

Detailed outputs are `reports/donor_external_shock_evidence.csv` and `data_processed/donor_shortlist_final_audit.csv`.
