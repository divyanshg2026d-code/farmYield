# Vibe Coding Log (working draft)

**Project:** FarmYield — India Rice Yield Planning  
**Purpose:** Record how AI-assisted development supports the team while the team remains responsible for algorithm choices and validation.

## Workflow used

- Used Codex to scaffold the initial prototype from the capstone brief.
- Initialized a local Git repository on `main` and added ignore rules for the project environment and local logs.
- Researched public agricultural sources and selected India's district/season/crop production statistics; adapted product scope to fields available in the data.
- Separated data loading, model construction/evaluation, and the executive-facing Streamlit interface.
- Refreshed the bundled crop table from a public mirror of the DES / India Data Portal series, extending the crop-year range from 1997-2015 to 1997-2022; preserved the previous version for comparison.
- Added loader checks for both legacy and standardized schemas, fiscal-year parsing, duplicate season totals, invalid area/production values, and conflicting district-season-year records.
- Recorded local data coverage and overlap checks. Marked the mirror's byte identity and redistribution terms as unverified rather than presenting them as confirmed.

## Prompting strategy

- Specified the target user, business decision, application framework, modules, and model evaluation needs.
- Requested transparent preprocessing, reproducible time-aware validation, error metrics, and permutation importance.
- Asked to align the product inputs with actual dataset fields and make limits visible in the interface/documentation.
- Added a district-season historical-mean baseline and XGBoost candidate beside Random Forest; model selection uses forward-chaining validation over whole years.

## Team review still required

- Verify source version, license, units, geographic coverage, and derived-yield assumptions with the course team.
- Confirm licensing and source-file provenance for redistribution; review three rice observations above 20 t/ha, including one above 50 t/ha.
- Add aligned weather inputs before claiming current-season forecasting.
- Re-run validation on the refreshed data and compare the district-season baseline, Random Forest, and tuned XGBoost.
- Review district naming/coverage changes and prepare subgroup error analysis on the new temporal holdout.
- Independently explain Random Forest behavior, preprocessing, hyperparameters, metrics, permutation importance, and failure modes.
- Replace this draft with the actual prompts, tools, dates, edits, and human decisions made by the team. Do not claim AI-generated work as independently authored analysis.
