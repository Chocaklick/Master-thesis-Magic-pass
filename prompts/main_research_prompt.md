# MASTER THESIS — END-TO-END DATA COLLECTION, CAUSAL ANALYSIS, MACHINE LEARNING AND DECISION-SUPPORT PIPELINE

## 0. ROLE AND GENERAL OBJECTIVE

You are acting as a senior Data Scientist, Data Engineer, Business Analytics researcher and research assistant.

You are working on a Master's thesis in Business Analytics about Swiss ski resorts, hotel overnight stays, snow vulnerability and membership in the Magic Pass multi-resort ski pass.

Your mission is NOT simply to run a regression or train a machine-learning model.

You must build a complete, reproducible and academically defensible analytical pipeline going from:

1. audit of existing data;
2. identification of missing information;
3. external data collection;
4. rigorous source documentation and provenance;
5. data cleaning and entity resolution;
6. construction of a station × municipality × time analytical database;
7. descriptive analysis;
8. retrospective evaluation of Magic Pass adoption;
9. investigation of heterogeneous treatment effects;
10. predictive / causal machine-learning experiments;
11. segmentation of ski resorts;
12. scoring of non-member resorts;
13. uncertainty and out-of-distribution analysis;
14. development of a Business Analytics decision-support framework;
15. robustness and validation;
16. final recommendation about which modelling strategy is actually supported by the available data.

Do NOT assume in advance that neural networks, causal forests, XGBoost, Difference-in-Differences or any particular model will be appropriate.

The empirical characteristics of the dataset must determine which models are defensible.

The priority is scientific validity, traceability, reproducibility and decision usefulness — NOT model complexity.

---

# 1. CENTRAL BUSINESS QUESTION

The project should investigate the following general question:

> To what extent can the observed effects of Magic Pass adoption on hotel overnight stays be used to identify Swiss ski destinations with the highest potential tourism benefit from joining a multi-resort ski pass?

A more operational formulation is:

> Can we learn from resorts that have already joined Magic Pass which types of non-member Swiss ski resorts could potentially experience the largest increase in hotel overnight stays following membership?

The final objective is therefore to construct a Business Analytics decision-support framework for non-member resorts.

Do NOT describe the final output as an estimate of the financial profitability of joining Magic Pass unless financial data sufficient to establish profitability are available.

Prefer terminology such as:

* Magic Pass Tourism Opportunity Score;
* Membership Opportunity Score;
* Tourism Uplift Potential;
* Predicted Hotel-Night Uplift;
* Strategic Opportunity Matrix.

---

# 2. RESEARCH QUESTIONS

Organise the analysis around the following questions.

## RQ1 — Historical effect

How did hotel overnight stays evolve following Magic Pass adoption compared with comparable non-member destinations?

## RQ2 — Heterogeneous effects

Does the observed post-adoption response differ according to characteristics such as:

* altitude;
* snow conditions;
* snow reliability;
* ski-area size;
* lift infrastructure;
* hotel capacity;
* accessibility;
* market orientation;
* initial tourism intensity;
* geographic region;
* proximity to population centres;
* proximity to other Magic Pass resorts?

## RQ3 — Prediction / Business Analytics

Can observable destination characteristics be used to identify non-member resorts whose profiles resemble the resorts for which Magic Pass membership was associated with favourable tourism outcomes?

## RQ4 — Decision support

Can these results be transformed into a transparent and uncertainty-aware decision-support framework for ski resorts, municipalities and tourism stakeholders?

---

# 3. IMPORTANT SCIENTIFIC PRINCIPLE

Never confuse:

CORRELATION

with

CAUSAL EFFECT

with

PREDICTION

with

BUSINESS RECOMMENDATION.

These four concepts must remain explicitly separated throughout the project.

For example, a resort joining Magic Pass and subsequently experiencing more hotel nights does NOT automatically mean Magic Pass caused the increase.

Likewise, a machine-learning model predicting high hotel nights does NOT imply that joining Magic Pass would increase hotel nights.

The central quantity of interest, when data allow it, is conceptually:

tau_i = E[Y_i(1) - Y_i(0) | X_i]

where:

Y_i(1) = tourism outcome if destination i is exposed to Magic Pass;

Y_i(0) = tourism outcome if destination i is not exposed;

X_i = observable characteristics of destination i.

Because both potential outcomes cannot be observed simultaneously, all causal estimates must be presented with appropriate assumptions and uncertainty.

---

# 4. FIRST TASK — AUDIT ALL EXISTING FILES

Before downloading ANYTHING, inspect every file already present in the project directory.

Known files may include files such as:

* nuitée_commune_final.csv
* bergfex_stations_ski_suisse_par_region.csv
* stations_ski_geocoded_a_verifier_complet.csv
* assignations_stations_final_clean.csv
* clusters_stations_final_clean.csv
* wms_layers_importants_these_ski.csv
* WMS capabilities XML files from geo.admin.ch

Search the project directory for additional CSV, XLSX, JSON, GeoJSON, SHP, GPKG, XML, Parquet, PDF or other relevant files.

For EVERY existing dataset:

1. inspect column names;
2. inspect data types;
3. count rows;
4. count unique resorts;
5. count unique municipalities;
6. inspect temporal coverage;
7. identify geographic identifiers;
8. identify missing values;
9. identify duplicates;
10. identify potential join keys;
11. identify suspicious values;
12. identify whether the information is raw, manually collected, derived or model-generated;
13. identify its source if documented.

Create:

data_audit.csv

with at least:

file_name
dataset_description
n_rows
n_columns
temporal_start
temporal_end
n_resorts
n_municipalities
geographic_level
potential_join_keys
important_variables
missingness_summary
known_source
quality_notes
recommended_use

DO NOT recollect data already available and sufficiently reliable.

---

# 5. NON-NEGOTIABLE DATA PROVENANCE SYSTEM

Every external data point or dataset used in the thesis MUST be traceable.

Create immediately:

data_sources_master.csv

This is one of the most important outputs of the entire project.

Required columns:

source_id
variable_name
variable_description
source_organisation
source_dataset_name
source_page_url
direct_download_url
api_endpoint
api_parameters
wms_layer
geocat_metadata_url
retrieval_method
retrieval_date
original_file_name
local_raw_file
processed_file
geographic_level
temporal_resolution
temporal_start
temporal_end
unit
license
access_conditions
transformation_applied
quality_notes
confidence_level
manual_verification
notes

Every collected variable must be connected to a source_id.

NEVER store a value obtained from the internet without storing its provenance.

If data come from HTML scraping, preserve:

* page URL;
* page title;
* access date;
* relevant HTML/table where legally and technically feasible.

If data come from an API, preserve:

* endpoint;
* parameters;
* query;
* date;
* raw response.

If data come from WMS/WFS/geo.admin.ch, preserve:

* service URL;
* layer identifier;
* CRS;
* query parameters;
* metadata URL;
* extraction method.

If data come from a PDF, preserve:

* original PDF;
* URL;
* page number;
* extraction method;
* extracted value.

If a value is manually verified, document this.

NEVER invent missing data.

Use NA when reliable information cannot be found.

---

# 6. RAW DATA IMMUTABILITY

Create the following structure:

/data_raw
/data_interim
/data_processed
/data_external
/metadata
/logs
/reports
/figures
/models
/notebooks
/src
/tests

Never overwrite raw files.

All downloaded data must first be stored unchanged in /data_raw or /data_external.

Processed data must be generated programmatically from raw data.

Where practical, store:

* retrieval timestamp;
* checksum/hash;
* source URL;
* file size.

The entire pipeline should be rerunnable.

---

# 7. RESORT MASTER TABLE

Construct a canonical ski resort table:

resort_master.csv

One row = one ski resort / ski area.

Create a stable internal identifier:

resort_id

Possible columns:

resort_id
resort_name_canonical
resort_name_original
alternative_names
municipality_name
municipality_bfs_id
canton
tourism_region
latitude
longitude
altitude_base_m
altitude_top_m
altitude_midpoint_m
vertical_drop_m
ski_area_km
number_slopes
number_lifts
number_gondolas
number_chairlifts
number_drag_lifts
snowmaking_share
magic_pass_member
magic_pass_entry_date
magic_pass_entry_season
hotel_capacity
population
nearest_city
distance_nearest_city_km
travel_time_nearest_city
distance_nearest_rail_station
accessibility_metrics
source_ids

Never merge resorts based only on approximate name similarity without validation.

Use coordinates, municipality, canton and alternative names.

Create:

entity_resolution_log.csv

with:

original_name
canonical_name
match_method
match_score
manual_review
decision
notes

---

# 8. MAGIC PASS MEMBERSHIP HISTORY — CRITICAL VARIABLE

Construct a complete longitudinal history of Magic Pass membership.

Target table:

magic_pass_membership_history.csv

Columns:

resort_id
resort_name
member
entry_date_exact
entry_season
exit_date
source_url
source_type
source_date
confidence
notes

Priority sources:

1. official Magic Pass material;
2. archived Magic Pass pages;
3. official ski resort announcements;
4. official tourism organisations;
5. credible press;
6. secondary sources only when necessary.

Whenever possible, find the exact season or date at which each resort entered.

Distinguish:

* founding members;
* later entrants;
* resorts entering through group/operator agreements;
* resorts whose names changed;
* merged ski areas.

If sources disagree, record the disagreement rather than silently choosing one.

The treatment variable should eventually allow:

MagicPass_it = 1 after resort i enters Magic Pass, 0 before.

Also create:

event_time_it = time relative to adoption.

---

# 9. HOTEL OVERNIGHT STAYS — PRIMARY OUTCOME

Use the existing municipality-level overnight stay dataset as the starting point.

Audit:

nuitée_commune_final.csv

Determine:

* exact source;
* frequency;
* time coverage;
* whether observations represent hotels only;
* whether domestic/foreign visitors are separated;
* whether arrivals are available;
* whether hotel establishments/rooms/beds are available;
* treatment of suppressed/confidential values;
* changes in municipality boundaries.

Preserve the finest temporal frequency available, preferably monthly.

Potential outcomes:

hotel_overnights
hotel_arrivals
domestic_overnights
foreign_overnights
hotel_beds
hotel_rooms
hotel_establishments
occupancy_rate
average_length_of_stay

Construct transformations:

log_overnights = log(1 + overnight_stays)

year_on_year_growth

winter_overnights

summer_overnights

winter_share

overnights_per_bed

overnights_per_capita

If hotel capacity is available, distinguish demand growth from capacity growth.

---

# 10. STATION → MUNICIPALITY EXPOSURE

This is a critical methodological problem.

A ski resort can:

* lie in one municipality;
* span multiple municipalities;
* attract tourists staying in neighbouring municipalities;
* share a municipality with another resort.

Use existing station-municipality assignments and clusters as the initial solution.

Validate them.

Construct:

resort_municipality_crosswalk.csv

with:

resort_id
municipality_bfs_id
municipality_name
relationship_type
weight
assignment_method
distance_km
confidence
manual_validation
notes

Possible relationship types:

direct
primary
secondary
tourism_cluster
nearby_accommodation_market

Do NOT arbitrarily double-count municipal overnight stays when several resorts share one municipality.

Test multiple aggregation strategies if necessary.

---

# 11. GEOGRAPHIC DATA — SWISSTOPO / GEO.ADMIN.CH

Inspect the existing WMS capabilities files and important-layer list.

Identify relevant official layers before searching elsewhere.

Potential geographic variables include:

* winter lifts;
* terrain elevation;
* public transport;
* roads;
* settlements;
* municipal boundaries;
* travel infrastructure;
* topography.

A particularly relevant existing official layer is expected to be:

ch.swisstopo.bahnen-winter

Use official metadata to understand precisely what it represents.

Do not assume WMS is the optimal extraction format. Search for corresponding downloadable geodata, WFS, STAC, OGC API or official files when available.

For every geographic layer document:

layer_name
layer_title
provider
metadata_url
service_url
CRS
geometry_type
date/version
variables derived from it

Use EPSG:2056 for Swiss spatial calculations where appropriate.

---

# 12. SNOW AND CLIMATE DATA

Snow vulnerability is central to the thesis.

Collect the best historically available and reproducible snow/climate indicators.

Prioritise official or scientifically established sources.

Investigate sources such as:

* MeteoSwiss;
* SLF;
* Copernicus;
* ERA5-Land;
* Swiss federal geodata;
* other validated scientific datasets.

Potential variables:

snow_depth
snow_cover_days
days_snow_depth_gt_10cm
days_snow_depth_gt_20cm
days_snow_depth_gt_30cm
snowfall
temperature
precipitation
freezing_days
rain_on_snow indicators
snow_season_start
snow_season_end

Derive long-term features such as:

mean_winter_snow
snow_variability
snow_reliability
snow_trend
temperature_trend
low_snow_frequency
extreme_low_snow_years

Where station-level meteorological observations are unavailable, document the spatial interpolation or grid extraction procedure.

Potentially calculate conditions at several elevations:

base
mid-mountain
top

Do not pretend that a meteorological station several kilometres away directly represents ski-slope conditions without documenting this limitation.

---

# 13. SKI RESORT CHARACTERISTICS

Collect or validate:

skiable_km
number_of_lifts
lift_types
base_altitude
top_altitude
vertical_drop
orientation/aspect if feasible
terrain distribution
snowmaking capacity
beginner/intermediate/advanced slope composition if available
historical ski-pass price if available
parking/access characteristics

Possible sources may include:

* official resort websites;
* Bergfex;
* Skiresort.info;
* Swiss federal geodata;
* tourism organisations;
* archived resort pages.

Prefer official sources where possible.

For commercial/secondary sources, document terms of use and avoid prohibited scraping.

Do not bypass CAPTCHAs or technical access restrictions.

---

# 14. ACCESSIBILITY FEATURES

Accessibility could be highly predictive of Magic Pass attractiveness.

Construct features such as:

distance_to_nearest_major_city
travel_time_to_nearest_major_city
distance_to_nearest_train_station
public_transport_access
distance_to_motorway
population_within_30min
population_within_60min
population_within_90min
population_within_120min

If feasible, estimate catchment population.

Potential relevant urban markets include major Swiss population centres, but do NOT hard-code assumptions without testing.

Accessibility must be computed reproducibly.

Document routing source and method.

---

# 15. TOURISM AND LOCAL ECONOMIC STRUCTURE

Where available, collect municipality-level variables such as:

population
employment
employment_in_accommodation
employment_in_food_services
tourism-related establishments
hotel_beds
hotel_rooms
number_hotels
second_home_share
municipal economic indicators
tourism intensity

Potential derived metrics:

overnights_per_capita

hotel_beds_per_capita

tourism_employment_share

tourism_dependence_index

Again, use official Swiss statistics wherever possible.

Do not use an arbitrary composite index without clearly documenting its construction.

---

# 16. COMPETITION AND NETWORK FEATURES

Construct spatial/business features capturing the ski-resort environment.

Examples:

distance_to_nearest_ski_resort
number_resorts_within_25km
number_resorts_within_50km
number_magic_pass_resorts_within_50km
nearest_magic_pass_distance
regional_magic_pass_penetration
ski_km_within_50km
competitive_density

Also consider potential network effects:

Does membership become more attractive when nearby resorts are already Magic Pass members?

Treat these as hypotheses, not facts.

---

# 17. TEMPORAL CONTROL VARIABLES

Construct controls for:

year
month
winter season
school holidays
Christmas/New Year
Easter
Swiss public holidays where relevant
COVID period
COVID restrictions
exceptional weather years

Explicitly investigate 2020–2022 disruptions.

Do not simply delete COVID observations without testing sensitivity.

Potential specifications:

full sample with COVID controls

exclude most disrupted months

pre-COVID sample where relevant

post-COVID robustness

---

# 18. MASTER PANEL

Construct:

panel_resort_month.csv

or, depending on identification level:

panel_destination_month.csv

Each row should represent a destination × month.

Potential columns:

resort_id
date
year
month
season
municipality_bfs_id
overnight_stays
log_overnights
arrivals
hotel_beds
occupancy
magic_pass
event_time
snow_depth
snow_days
temperature
precipitation
ski_km
lift_count
base_altitude
top_altitude
vertical_drop
accessibility variables
tourism dependence
competition variables
COVID controls
regional variables
source_ids

Also construct a resort-level modelling table:

resort_features.csv

containing stable/pre-treatment features.

---

# 19. DATA LEAKAGE PREVENTION

This is essential.

When predicting Magic Pass treatment effects for non-member resorts, do NOT use variables that would only become known after treatment if they may themselves be caused by treatment.

Prefer pre-treatment characteristics for treatment-effect prediction.

Clearly classify variables as:

PRE-TREATMENT
TIME-VARYING EXOGENOUS
POTENTIAL MEDIATOR
POST-TREATMENT
OUTCOME

Create:

variable_causal_role.csv

---

# 20. DESCRIPTIVE ANALYSIS

Before modelling, generate extensive descriptive diagnostics.

At minimum:

distribution of overnight stays
distribution of resort size
altitude distribution
Magic Pass vs non-member comparison
geographic maps
membership adoption timeline
overnight stay time series
snow trends
correlation matrix
missingness matrix
resort clusters
pre-treatment differences

Create publication-quality figures.

Do not proceed directly to ML.

---

# 21. SAMPLE SIZE AND FEASIBILITY GATE

Before training complex models, calculate:

number_total_resorts
number_magic_pass_resorts
number_non_member_resorts
number_treated_with_known_entry_date
number_treated_with_24_months_pre
number_treated_with_36_months_pre
number_treated_with_24_months_post
number_treated_with_36_months_post
number_usable_controls
number_unique_treatment_dates

Generate:

model_feasibility_report.md

Explicitly answer:

Is the sample large enough for:

* fixed-effects panel regression?
* staggered Difference-in-Differences?
* matching?
* synthetic control?
* causal forest?
* X-Learner?
* DR-Learner?
* gradient boosting?
* random forest?
* neural network?

Do NOT run a neural network merely because monthly observations create many rows.

The effective independent sample for treatment heterogeneity may be closer to the number of resorts than the number of resort-month observations.

---

# 22. BASELINE DESCRIPTIVE / PANEL MODELS

Start with simple benchmarks.

Examples:

pooled regression

resort fixed effects

time fixed effects

resort + month/year fixed effects

Potential baseline:

# log(overnights_it + 1)

alpha_i
+
gamma_t
+
beta MagicPass_it
+
delta Snow_it
+
theta X_it
+
epsilon_it

Cluster standard errors at an appropriate level.

Document assumptions.

These models are benchmarks, not necessarily final causal estimates.

---

# 23. EVENT STUDY

Estimate event-time dynamics around Magic Pass entry.

Create indicators for periods before and after adoption.

Visualise coefficients.

Critical objective:

check pre-treatment trends.

If strong pre-trends exist, explicitly report that causal interpretation is weakened.

Analyse whether effects appear:

immediately
after one winter
after several seasons
temporarily
persistently

---

# 24. DIFFERENCE-IN-DIFFERENCES

Because treatment timing may be staggered, do not rely blindly on a naive two-way fixed-effects DiD.

Investigate modern staggered-adoption estimators appropriate to the data structure.

Compare:

simple DiD benchmark
event study
group-time treatment effects
alternative control groups

Check:

parallel trends
anticipation
treatment timing
composition changes
COVID overlap

Report ATT estimates with confidence intervals.

---

# 25. MATCHING / COMPARABLE CONTROLS

Construct comparable untreated resorts using pre-treatment characteristics.

Potential methods:

nearest-neighbour matching
propensity-score matching
Mahalanobis matching
coarsened exact matching

Matching variables may include:

pre-treatment overnight stays
pre-treatment growth
altitude
ski area size
hotel capacity
region
snow reliability
accessibility
tourism dependence

Check covariate balance before and after matching.

Never assume matching solves unobserved confounding.

---

# 26. SYNTHETIC CONTROL / SYNTHETIC DiD

For important treated resorts with long pre-treatment histories, test:

Synthetic Control

or

Synthetic Difference-in-Differences

when sufficient donor pools exist.

This can provide resort-specific case studies.

Store resort-level treatment-effect estimates where defensible.

---

# 27. HETEROGENEOUS TREATMENT EFFECTS

This is a central bridge between causal inference and Business Analytics.

Investigate whether the treatment response varies by:

altitude
snow reliability
ski area size
hotel capacity
accessibility
tourism dependence
domestic market orientation
regional competition
Magic Pass network density

Start with interpretable interactions.

Only then test causal ML.

---

# 28. CAUSAL MACHINE LEARNING

If sample size supports it, evaluate methods such as:

Causal Forest
Generalized Random Forest
X-Learner
T-Learner
S-Learner
DR-Learner

Do not treat these methods as magic.

Use appropriate cross-fitting where relevant.

Evaluate:

CATE stability
confidence intervals
feature importance
calibration
sensitivity to hyperparameters
sensitivity to sample composition

If sample size is insufficient, explicitly reject causal ML as the primary method.

That rejection is a valid scientific result.

---

# 29. STANDARD MACHINE LEARNING BENCHMARKS

Where appropriate, test:

Linear Regression
Ridge
Lasso
Elastic Net
Random Forest
Gradient Boosting
XGBoost / LightGBM if available
Support Vector Regression
k-nearest neighbours

A neural network may be tested ONLY as an experimental benchmark if sample size is remotely defensible.

It must not be selected simply because it is more sophisticated.

Use nested or carefully designed cross-validation.

---

# 30. IMPORTANT — GROUPED VALIDATION

Never randomly split resort-month observations in a way that puts observations from the same resort in both train and test sets if the objective is generalisation to unseen resorts.

Use:

GroupKFold by resort

Leave-One-Resort-Out

or comparable grouped validation.

For temporal forecasting components, use temporal validation.

Avoid leakage.

---

# 31. MODEL METRICS

Depending on task, report:

MAE
RMSE
R²
out-of-sample R²
rank correlation
calibration
confidence interval coverage

For uplift / treatment-effect models, use suitable uplift/CATE diagnostics where feasible.

Never choose the final model solely on in-sample R².

---

# 32. INTERPRETABILITY

For predictive models, investigate:

feature importance
permutation importance
SHAP values where appropriate
partial dependence
ALE plots

Interpret these as model explanations, NOT automatically as causal relationships.

Explicitly label:

predictive importance

versus

causal interpretation.

---

# 33. FALLBACK BUSINESS ANALYTICS MODEL

If causal ML is not supported by sample size, implement a second decision-support strategy.

Use:

clustering
similarity analysis
nearest-neighbour analogues
historical treatment response
multi-criteria decision analysis

Cluster resorts based on pre-treatment characteristics.

Potential methods:

K-means
hierarchical clustering
Gaussian mixtures
HDBSCAN if appropriate

Determine cluster count using:

silhouette
stability
interpretability

For every non-member resort identify:

most similar Magic Pass members

distance/similarity score

observed historical post-adoption patterns of those analogues

This approach may be more defensible than an overfitted CATE model.

---

# 34. TWO-DIMENSION DECISION FRAMEWORK

Do NOT immediately collapse everything into one opaque score.

Construct at least two conceptual dimensions.

## Dimension A — Opportunity

Estimated or analogue-based tourism uplift potential associated with Magic Pass membership.

## Dimension B — Strategic Need

Tourism dependence and climate/snow vulnerability.

Potential representation:

```
               HIGH OPPORTUNITY
                     |
  Strategic         |       High-potential
  opportunity       |       candidates
                     |
```

LOW NEED ----------------+---------------- HIGH NEED
|
Limited strategic |       Vulnerable but
relevance         |       uncertain benefit
|
LOW OPPORTUNITY

This framework may be more useful than a single ranking.

---

# 35. MAGIC PASS TOURISM OPPORTUNITY SCORE

Only after analysing the separate dimensions, test whether a composite score is useful.

Possible components:

Predicted_Uplift
Model_Confidence
Comparability
Hotel_Capacity
Tourism_Dependence
Snow_Vulnerability
Accessibility
Network_Fit

Do NOT arbitrarily assign weights.

Possible weighting approaches:

expert-defined scenarios
equal weights as benchmark
PCA/data-driven weights
sensitivity analysis
multi-criteria decision analysis

If weights cannot be scientifically justified, retain a dashboard/matrix instead of a single score.

---

# 36. UNCERTAINTY SCORE

Every recommendation must contain uncertainty.

Potential fields:

predicted_uplift
lower_ci
upper_ci
model_uncertainty
similarity_to_training_sample
out_of_distribution_score
data_quality_score
recommendation_confidence

Never output:

“Resort X should definitely join Magic Pass.”

Prefer:

“Under the model assumptions, Resort X exhibits characteristics similar to treated destinations associated with relatively favourable post-adoption tourism outcomes, although uncertainty remains substantial.”

---

# 37. OUT-OF-DISTRIBUTION DETECTION

This is essential when scoring non-member resorts.

A non-member resort may be unlike anything in the Magic Pass training sample.

Calculate a comparability / support metric.

Possible approaches:

Mahalanobis distance
nearest-neighbour distance
isolation forest
density estimation
propensity overlap

Flag resorts as:

good support
moderate extrapolation
strong extrapolation

Do not produce confident recommendations for strong extrapolation cases.

---

# 38. ROBUSTNESS TESTS

Test sensitivity to:

alternative station-municipality assignments
different treatment dates
different pre/post windows
COVID exclusions
winter-only outcomes
annual outcomes
monthly outcomes
log vs level outcomes
outlier removal
hotel-capacity controls
different matching methods
different snow variables
different model families
different scoring weights

Store results systematically.

---

# 39. PLACEBO TESTS

Where applicable:

fake treatment dates
pre-treatment placebo treatment
untreated-resort placebo
randomised treatment assignment

Use these to identify spurious model behaviour.

---

# 40. BUSINESS SCENARIO ANALYSIS

For selected non-member resorts, create scenarios.

For example:

Scenario A — conservative
Scenario B — central
Scenario C — optimistic

Report potential additional overnight stays as ranges rather than falsely precise point estimates.

If hotel capacity constraints imply the predicted increase would be impossible, flag this.

Distinguish:

percentage uplift

absolute overnight stays

capacity-adjusted feasible uplift

---

# 41. ECONOMIC INTERPRETATION

If reliable expenditure-per-overnight data become available, optionally estimate:

potential tourism expenditure associated with additional hotel nights.

But label this clearly as scenario analysis.

Do NOT equate tourism expenditure with:

ski-resort profit
Magic Pass revenue
municipal fiscal revenue

unless data specifically support those quantities.

---

# 42. DATA QUALITY SCORE

For each resort create a data-quality assessment.

Possible dimensions:

membership date confidence
geolocation confidence
municipality mapping confidence
snow data quality
hotel data coverage
infrastructure data quality
temporal coverage

Create:

resort_data_quality.csv

Do not hide weak observations.

---

# 43. SOURCE EVIDENCE REPORT

Generate:

reports/DATA_SOURCES.md

For EVERY source explain in plain language:

1. what the dataset contains;
2. who produces it;
3. why it is relevant;
4. exact URL;
5. how it was accessed;
6. retrieval date;
7. variables extracted;
8. transformations applied;
9. geographic coverage;
10. temporal coverage;
11. known limitations;
12. local raw file location.

The goal is that another researcher can reproduce the collection without asking the original analyst.

---

# 44. DATA DICTIONARY

Generate:

metadata/data_dictionary.csv

Required columns:

variable
table
description
unit
data_type
geographic_level
temporal_level
source_id
raw_or_derived
formula
causal_role
missing_share
notes

---

# 45. COLLECTION LOG

Generate:

logs/data_collection_log.csv

Each retrieval operation should include:

timestamp
source
URL/API
request
HTTP_status
output_file
rows_collected
success
error
notes

Failures must remain documented.

---

# 46. REPRODUCIBILITY

Create scripts rather than performing undocumented manual transformations.

Suggested structure:

src/
01_audit_existing_data.py
02_build_resort_master.py
03_collect_magic_pass_history.py
04_collect_ski_features.py
05_collect_geodata.py
06_collect_snow_weather.py
07_collect_tourism_controls.py
08_build_crosswalk.py
09_build_panel.py
10_descriptive_analysis.py
11_causal_analysis.py
12_causal_ml.py
13_predictive_models.py
14_clustering_similarity.py
15_build_opportunity_framework.py
16_robustness.py
17_generate_reports.py

Use configuration files for URLs and parameters where possible.

---

# 47. TESTS

Create automated tests for critical operations.

Examples:

no duplicate resort_id

unique municipality IDs

dates parse correctly

Magic Pass treatment never switches 1→0 unless documented exit

coordinates inside plausible Swiss bounds

overnight stays non-negative

altitude plausible

skiable kilometres non-negative

no train/test resort leakage

source_id exists for sourced variables

---

# 48. VISUAL OUTPUTS

Generate at least:

Map of all ski resorts

Map of Magic Pass members

Magic Pass adoption timeline

Distribution of altitude

Distribution of ski-area size

Hotel overnight-stay trends

Event-study graph

Snow vulnerability map

Treatment/control balance plots

Resort clustering plot

Feature importance plot

Opportunity vs Strategic Need matrix

Non-member resort opportunity map

Uncertainty/comparability map

Do not make visually attractive charts at the expense of statistical accuracy.

---

# 49. MODEL COMPARISON TABLE

Generate:

model_comparison.csv

Columns should include:

model_name
task
sample_size
n_resorts
n_treated
features
validation_method
MAE
RMSE
R2
out_of_sample_R2
causal_or_predictive
interpretability
uncertainty_available
major_assumptions
major_limitations
recommended_for_final_use

---

# 50. MODEL SELECTION PRINCIPLE

Final model selection must consider:

out-of-sample performance
causal credibility
sample size
stability
interpretability
uncertainty
business usefulness

NOT complexity.

A simple model that is stable and interpretable should be preferred over a sophisticated unstable model.

---

# 51. CRITICAL DECISION TREE

After initial data preparation, explicitly choose among these paths.

## PATH A — Strong data

If there are sufficiently many treated resorts, reliable treatment dates and long pre/post histories:

DiD/event study
→ causal ML
→ CATE
→ opportunity modelling
→ decision-support tool.

## PATH B — Moderate data

If causal estimation is possible but heterogeneous-effect ML is underpowered:

DiD/event study
→ treatment-effect estimates
→ interpretable interactions
→ clustering/similarity
→ opportunity framework.

## PATH C — Weak treatment sample

If causal identification is too weak:

descriptive treatment analysis
→ resort segmentation
→ analogue matching
→ similarity scoring
→ exploratory decision-support tool.

Do not pretend PATH C provides causal predictions.

---

# 52. FINAL BUSINESS ANALYTICS DELIVERABLE

The desired final analytical output is not merely a regression table.

Create a decision-support dataset:

magic_pass_decision_support.csv

Potential fields:

resort_id
resort_name
current_magic_pass_status
predicted_uplift
uplift_lower
uplift_upper
opportunity_percentile
strategic_need
snow_vulnerability
tourism_dependence
accessibility_score
hotel_capacity
network_fit
comparability_score
OOD_flag
data_quality_score
closest_magic_pass_analogue_1
closest_magic_pass_analogue_2
closest_magic_pass_analogue_3
model_used
confidence
interpretation

Avoid presenting the output as an absolute truth.

---

# 53. DASHBOARD-READY OUTPUT

Prepare data that could later feed a Power BI, Tableau, Streamlit or Dash application.

A future dashboard should allow a decision-maker to select a ski resort and see:

resort characteristics

Magic Pass status

hotel-night history

snow history

similar resorts

estimated opportunity

uncertainty

strategic need

map

main model drivers

data-quality warnings

---

# 54. FINAL REPORTS

At completion generate:

reports/01_DATA_AUDIT.md

reports/02_DATA_COLLECTION.md

reports/03_DATA_QUALITY.md

reports/04_DESCRIPTIVE_ANALYSIS.md

reports/05_CAUSAL_ANALYSIS.md

reports/06_MODEL_EXPERIMENTS.md

reports/07_MODEL_SELECTION.md

reports/08_BUSINESS_ANALYTICS_FRAMEWORK.md

reports/09_LIMITATIONS.md

reports/10_FINAL_RECOMMENDATIONS.md

and:

reports/EXECUTIVE_SUMMARY.md

---

# 55. FINAL METHODOLOGICAL REPORT

The final report must explicitly answer:

1. How many ski resorts are available?

2. How many are Magic Pass members?

3. How many treated resorts have reliable entry dates?

4. How many have sufficient pre-treatment observations?

5. How many have sufficient post-treatment observations?

6. Are parallel trends plausible?

7. Is causal inference credible?

8. Is heterogeneous treatment-effect modelling statistically feasible?

9. Is Causal Forest feasible?

10. Is standard ML useful?

11. Is a neural network justified?

12. Is clustering/similarity more appropriate?

13. What is the most defensible final Business Analytics methodology?

14. Which variables appear most informative?

15. Which variables are missing?

16. What are the main sources of uncertainty?

17. Which additional data would most improve the model?

18. Can the final system reasonably be described as predictive, causal, exploratory or decision-support?

---

# 56. CRITICAL LIMITATIONS TO INVESTIGATE

Explicitly investigate:

selection into Magic Pass

reverse causality

pre-existing growth trends

simultaneous resort investments

changes in hotel capacity

COVID disruption

weather shocks

regional tourism trends

measurement error in resort-municipality mapping

treatment spillovers

Magic Pass network effects

other ski passes

resort mergers

municipality mergers

missing/confidential tourism observations

survivorship bias

limited treated sample

data leakage

extrapolation to non-member resorts

---

# 57. IMPORTANT SPILLOVER PROBLEM

A non-member resort located close to Magic Pass resorts may itself be indirectly affected.

Likewise, hotels in neighbouring municipalities may benefit from a Magic Pass resort.

Investigate spatial spillovers.

Potential variables:

distance_to_treated_resort
number_treated_neighbours
regional_treatment_share

Potential robustness analysis:

exclude controls very close to treated resorts.

Document the implications.

---

# 58. DO NOT FORCE A SINGLE SCORE

One of the possible findings may be that a single numerical ranking is misleading.

If so, produce instead:

a multi-dimensional dashboard

or

a 2×2 strategic matrix

or

a Pareto frontier

or

scenario-specific rankings.

The analytical design should serve the decision problem, not the opposite.

---

# 59. SOURCE PRIORITY

Use this hierarchy when collecting data:

1. Swiss federal official data
2. Cantonal official data
3. Municipal official data
4. Magic Pass official data
5. Official ski-resort/operator data
6. Official tourism organisations
7. Peer-reviewed/scientific data
8. Established industry databases
9. Reputable media
10. Secondary websites

Do not use low-quality aggregators when authoritative sources exist.

---

# 60. INTERNET RESEARCH RULE

When searching for data, do not stop at the first result.

For each important variable:

1. identify candidate sources;
2. compare authority;
3. compare temporal coverage;
4. compare geographic coverage;
5. compare machine-readability;
6. compare licensing;
7. select the best source;
8. document rejected alternatives when relevant.

---

# 61. NEVER FABRICATE

Never fabricate:

URLs
membership dates
station characteristics
coordinates
snow observations
overnight stays
municipality mappings
model results
confidence intervals
source metadata.

If something cannot be verified, mark it:

UNKNOWN

or

NA

and explain why.

---

# 62. RESPECT ACCESS RESTRICTIONS

Do not circumvent:

CAPTCHAs
login walls
robots restrictions
paywalls
anti-bot systems
rate limits.

If automated collection is impossible:

document the source

document what data are available

create a manual_collection_needed.csv

and continue with other sources.

---

# 63. CHECKPOINTS

Do not build the entire project blindly.

Create checkpoints.

## CHECKPOINT 1 — Existing data

Report existing datasets and missing information.

## CHECKPOINT 2 — Treatment feasibility

Report number of usable Magic Pass treatments.

## CHECKPOINT 3 — Panel feasibility

Report temporal and geographic coverage.

## CHECKPOINT 4 — Causal feasibility

Report whether causal analysis is credible.

## CHECKPOINT 5 — ML feasibility

Report whether sample size supports each model family.

## CHECKPOINT 6 — Business decision framework

Select the final architecture.

Continue automatically unless a blocking ambiguity would materially change the research design.

---

# 64. EXPECTED SCIENTIFIC CONTRIBUTION

The project should aim to combine:

causal inference

machine learning

geospatial analytics

tourism analytics

climate/snow data

decision-support modelling.

However, methodological complexity is not itself a contribution.

The contribution should come from integrating these sources to address a real strategic decision faced by Swiss ski destinations.

---

# 65. POSSIBLE FINAL ARCHITECTURE

The preferred architecture, IF supported by data, is:

DATA ENGINEERING

↓

RESORT–MUNICIPALITY PANEL

↓

MAGIC PASS EVENT STUDY / DiD

↓

HETEROGENEOUS EFFECT ANALYSIS

↓

CAUSAL ML OR INTERPRETABLE HETEROGENEITY MODEL

↓

APPLICATION TO NON-MEMBERS

↓

UNCERTAINTY + SUPPORT CHECK

↓

OPPORTUNITY × STRATEGIC NEED MATRIX

↓

BUSINESS ANALYTICS DECISION-SUPPORT SYSTEM

If causal ML is unsupported:

DATA ENGINEERING

↓

DESCRIPTIVE / CAUSAL BENCHMARK

↓

CLUSTERING

↓

NEAREST TREATED ANALOGUES

↓

SIMILARITY-BASED OPPORTUNITY

↓

STRATEGIC NEED

↓

DECISION-SUPPORT SYSTEM.

---

# 66. STARTING INSTRUCTIONS

Start now.

Do NOT begin by downloading large external datasets.

First:

STEP 1:
scan the entire project directory.

STEP 2:
audit all existing datasets.

STEP 3:
identify what information already exists.

STEP 4:
construct the first version of data_sources_master.csv.

STEP 5:
construct the resort master list.

STEP 6:
audit station ↔ municipality mappings.

STEP 7:
determine how many resorts have hotel-night observations.

STEP 8:
determine current Magic Pass membership coverage.

STEP 9:
research historical Magic Pass entry dates.

STEP 10:
produce model_feasibility_report.md.

Only then determine which additional datasets should be collected.

---

# 67. PRIORITY ORDER FOR ADDITIONAL DATA

Unless the audit suggests otherwise, collect in approximately this order:

PRIORITY 1
Magic Pass membership and historical entry dates.

PRIORITY 2
Hotel-night outcome validation and hotel capacity.

PRIORITY 3
Station ↔ municipality mapping validation.

PRIORITY 4
Core resort characteristics.

PRIORITY 5
Altitude/topography/lift infrastructure.

PRIORITY 6
Snow and temperature history.

PRIORITY 7
Accessibility.

PRIORITY 8
Tourism dependence / municipality characteristics.

PRIORITY 9
Competition/network variables.

PRIORITY 10
Optional advanced variables.

Do not spend days collecting low-value features before confirming that the treatment/outcome structure is usable.

---

# 68. RESEARCH JOURNAL

Maintain:

logs/research_journal.md

After every major step write:

date
task
reason
method
result
problem encountered
decision made
next step

This journal should allow reconstruction of the entire research process for the Master's thesis methodology chapter.

---

# 69. NEGATIVE RESULTS

Preserve negative findings.

Examples:

Causal Forest unstable.

Neural network overfits.

Magic Pass entry dates unavailable for 30% of resorts.

Parallel-trend assumption fails.

Snowmaking data unavailable.

These are scientifically important findings.

Do not delete unsuccessful experiments.

Store them in:

reports/model_experiment_log.csv

---

# 70. FINAL PRINCIPLE

The final objective is NOT:

“Find the algorithm that gives the most impressive results.”

The objective is:

“Determine, from the available evidence, the most defensible analytical framework for estimating and communicating which Swiss ski destinations appear to have the greatest tourism opportunity associated with potential Magic Pass membership, while explicitly accounting for snow vulnerability, tourism dependence, destination characteristics, uncertainty and limitations.”

Every result must remain reproducible and traceable to its original data source.

Begin with the data audit and provenance system before any major external data collection or model fitting.

