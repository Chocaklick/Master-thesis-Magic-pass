# Destination scope concordance audit

## Question

Can the municipalities containing the supplied destination component points reproduce the municipality scopes already reviewed for hotel outcomes? This is a transferability diagnostic for the candidate point-container layer, not a construction or validation of tourism catchments.

## Result

- exact municipality-set matches: **10 / 11**;
- all reviewed links recovered: **11 / 12** (91.7% recall);
- point-scope precision: **100.0%**; no component-point municipality lies outside its reviewed outcome scope;
- definition-linked core proxies: **7 / 7** exact;
- separately reviewed complete scopes: **3 / 4** exact, recovering **4 / 5** municipality links;
- missing reviewed municipality: **Meiringen-Hasliberg: 785**.

## Interpretation

The seven core-proxy matches are expected because those scopes were explicitly defined from the component's core municipality; they are not independent validation. The informative comparison is the four complete observed municipal scopes: three are reproduced exactly, while the Meiringen point alone does not recover Hasliberg. Point containment is therefore a useful, conservative core-municipality descriptor, but it can omit an outcome municipality even in this small reviewed set.

No candidate-scope transfer is approved. A component-point municipality set is not a visitor catchment, a hotel market, an observed origin market or a pre-treatment causal covariate. The audit supports retaining candidate point-container ratios as qualified descriptive context only; it does not justify filling `tourism_dependence`, changing analogue matching or producing a composite ranking.

## Outputs

- `reports/destination_scope_concordance_audit.csv`
- `reports/destination_scope_concordance_audit_summary.json`
- `reports/37_DESTINATION_SCOPE_CONCORDANCE_AUDIT.md`
