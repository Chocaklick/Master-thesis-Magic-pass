# Donor competing-pass and local-shock audit

Generated reproducibly by `src/causal_inference/build_donor_external_shock_audit.py` from a versioned manual review whose cited official publications are checksum-cached.

## Result

The network screen left seven pairs beyond 50 km from every resolved Magic Pass point. The complete official annual rosters document that each donor station label (including the reviewed spelling and place variants) was absent from Magic Pass at the relevant anchor season. That resolves the principal historical-membership question raised for these candidates.

The same official-source review finds a donor-specific tourism or infrastructure shock overlapping every treatment post window. Consequently **all seven remote pairs are excluded from priority consideration and zero deep-audit candidates remain**. Historical Magic nonmembership is necessary for a donor, but it is not sufficient when the donor itself changes materially.

| Treatment | Donor | Complete Magic roster checked | Competing pass evidence | Local-shock review | Decision |
|---|---|---|---|---|---|
| anniviers_magic_portfolio | 3782 Corviglia St. Moritz | MAGIC_2017 p. 6;8 | SnowPass Graubünden | contemporaneous_corviglia_restaurant_repositioning_pricing_and_infrastructure_changes_documented | exclude_contemporaneous_local_tourism_shock |
| bumbach | 3102 Jakobsbad - Kronberg | MAGIC_2023 p. 5 | — | contemporaneous_operator_investment_and_weather_sensitive_winter_change_documented | exclude_contemporaneous_local_tourism_shock |
| bumbach | 3714 Splügen Rheinwald | MAGIC_2023 p. 5 | graubündenCARD | contemporaneous_snowmaking_children_lift_management_pricing_and_demand_changes_documented | exclude_contemporaneous_local_tourism_shock |
| espace_dent_blanche | 3847 Minschuns - Val Müstair | MAGIC_2018 p. 2 | SnowPass Graubünden | contemporaneous_gondola_snowmaking_and_resort_investment_trajectory_documented | exclude_contemporaneous_local_tourism_shock |
| moleson | 3102 Jakobsbad - Kronberg | MAGIC_2017 p. 6;8 | — | contemporaneous_major_talstation_investment_documented | exclude_contemporaneous_local_tourism_shock |
| saas_fee | 3752 Samnaun Silvretta Arena Samnaun / Ischgl | MAGIC_2019_APRIL p. 2 | SnowPass Graubünden | contemporaneous_visnitzbahn_capacity_upgrade_and_cross_border_domain_documented | exclude_contemporaneous_local_tourism_shock |
| saas_fee | 3782 Corviglia St. Moritz | MAGIC_2019_APRIL p. 2 | SnowPass Graubünden / TopCard | contemporaneous_celerina_lift_piste_and_major_operator_investment_documented | exclude_contemporaneous_local_tourism_shock |

## Evidence qualifications

- Roster absence is a direct statement about the checked station/place labels in a complete annual publication. It is not reinterpreted as corporate-register proof that no hidden affiliate arrangement existed.
- Exact operator participation in SnowPass or TopCard remains weaker than the roster evidence where only a regional publication was available. The exclusion decisions do not depend on resolving that remaining tariff detail because the local-shock evidence is independently sufficient.
- Corviglia/Celerina has contemporaneous restaurant, pricing, lift, piste and investment changes; Splügen has snowmaking, children-lift, management and demand changes; Minschuns has a publicly financed access/snowmaking project trajectory; Samnaun replaced the Visnitz chairlift in 2019; and Kronberg has its own capital projects.
- The Minschuns source documents approval and intended access replacement, not completed construction. The exclusion is therefore based on the financing/anticipation trajectory within the post window, not on an invented commissioning date.
- Samnaun remains a cross-border domain. Austrian demand, access, policy and tourism shocks lie outside the current Swiss covariate panel and reinforce, but are not required for, its exclusion.

## Identification decision

Of 35 shortlisted pairs, 15 are deprioritised within 30 km of the resolved network, 13 are deprioritised at 30–50 km, and all seven remote pairs are excluded for contemporaneous donor-specific tourism or infrastructure shocks. The pre-trend shortlist therefore contains **no surviving control candidate and no approved causal control**.

Detailed outputs are `reports/donor_external_shock_evidence.csv` and `data_processed/donor_shortlist_final_audit.csv`.
