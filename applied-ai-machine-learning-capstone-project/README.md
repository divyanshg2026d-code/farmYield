# FarmYield — India Rice Yield Planning

A Streamlit capstone prototype for comparing historical rice yield records across Indian states, districts, seasons, and crop years.

## Dataset and scope

The included `data/raw/india_crop_production.csv` is a public mirror of India's district-wise, season-wise crop production statistics. The Government of India's Open Government Data catalog describes the source as district/crop/season/year records with cultivated area (hectares) and production (tonnes), under the Government Open Data License — India. The raw file contains 246,091 records across crops; the rice slice contains 15,104 records, years 1997–2015, and 33 state/UT labels. The loader removes records with missing/nonpositive area or production and derives `yield_tonnes_ha = Production / Area`.

Primary catalog: [District-wise, season-wise crop production statistics](https://www.data.gov.in/catalog/district-wise-season-wise-crop-production-statistics-0) and [resource page](https://www.data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997). Download mirror used for the bundled CSV: [GitHub raw file](https://raw.githubusercontent.com/dibyendubiswas1998/Crop-Production-Analysis/main/DATA/crop_production.csv). The mirror is a convenience; cite the official catalog in project materials and verify current licensing/provenance with your instructor before redistribution.

See [data/SOURCES.md](data/SOURCES.md) for the current data freshness audit and candidate official weather/yield sources. The app must remain labeled as historical analysis until more recent target records are verified and aligned.

**Scope limitation:** this source has no soil, fertilizer, weather, farm-level observations, or costs. The product is therefore a historical district-level benchmark, not an in-season/farm-specific prediction or input optimizer. The interface states this limitation.

## Start the app

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
streamlit run app.py
```

The app loads the bundled CSV by default. To try a replacement file, enter its path in the sidebar. Expected raw columns: `State_Name`, `District_Name`, `Crop_Year`, `Season`, `Crop`, `Area`, and `Production`.

## Model and evaluation

- `src/data.py`: loads the source, isolates Rice, removes invalid area/production values, and calculates tonnes per hectare.
- `src/model.py`: district-season historical-mean baseline, Random Forest, and XGBoost regression candidates.
- `app.py`: executive-facing district/season/year explorer, model comparison leaderboard, selected-model estimate, and permutation importance.

Numeric year values are median-imputed; state/district/season are mode-imputed and one-hot encoded. The Random Forest starts with 300 trees, depth 16, leaf size 3, and `max_features=0.8`. XGBoost uses squared-error regression and a six-draw randomized search over tree count, depth, learning rate, row/column subsampling, minimum child weight, and L2 regularization. Whole years are kept together in expanding forward-chaining folds; the final three years remain a separate holdout. Model choice is based on training-period CV MAE, and holdout scores are reported for the district-season baseline, Random Forest, and tuned XGBoost.

This remains an historical benchmark. The bundled file still ends in 2015 and has no weather features, so XGBoost is an algorithm comparison—not a replacement for modern data or evidence of future-year forecasting ability. Before capstone claims, refresh yield records, join weather only if coverage and geography align, rerun the same time-aware evaluation, and analyze subgroup errors. Permutation importance is associative, not causal. Displayed performance values may differ from independently reprocessed variants.

## Business hypothesis to validate

Regional procurement and cooperative planning teams may use historical district-season yield benchmarks to support sourcing, storage, and transport planning. Establish value only with stakeholder interviews and a pilot against actual planning costs and outcomes. The dataset alone does not establish ROI or prove that model use improves decisions.

## Capstone next steps

1. Confirm a stakeholder and narrow the decision: regional rice sourcing, transport, or storage planning.
2. Verify the official resource version, units, license, missingness, and district/season definitions; save source snapshots and processing notes.
3. Compare the district-season baseline, Random Forest, and tuned XGBoost with the same time-aware split.
4. Create residual plots and subgroup error analysis; document under-represented regions and unstable records.
5. Quantify any ROI with stakeholder-provided baseline costs and measured pilot results; do not infer savings from MAE alone.
