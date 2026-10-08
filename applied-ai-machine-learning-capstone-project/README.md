# FarmYield — India Rice Yield Planning

A Streamlit capstone prototype for comparing historical rice yield records across Indian states, districts, seasons, and crop years.

## Dataset and scope

The default file, `data/raw/india_crop_production.csv`, is a public mirror of the DES / India Data Portal district-wise crop-production series. It covers crop-year labels 1997-2022. It has 407,315 rows across crops and 25,073 rice rows before cleaning; FarmYield retains 25,024 valid rice records. The previous 1997-2015 file is preserved at `data/archive/india_crop_production_1997_2015.csv` for comparison. The updated mirror's exact identity and redistribution terms have not been independently verified; see the data-source audit.

Primary catalog: [District-wise, season-wise crop production statistics](https://www.data.gov.in/catalog/district-wise-season-wise-crop-production-statistics-0). Updated public copy and source notes: [repository README](https://github.com/Ankush-Manhas840/crop-yield-prediction/blob/master/README.md) and [CSV](https://github.com/Ankush-Manhas840/crop-yield-prediction/blob/master/data/crop_production.csv). Cite the official catalog in project materials and confirm licensing/provenance before redistribution.

See [data/SOURCES.md](data/SOURCES.md) for data validation, lineage, caveats, and weather-source plans. The app remains labeled as historical analysis; its latest validation years are not a forward forecast.

**Scope limitation:** this source has no soil, fertilizer, weather, farm-level observations, or costs. The product is therefore a historical district-level benchmark, not an in-season/farm-specific prediction or input optimizer. The interface states this limitation.

## Start the app

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
streamlit run app.py
```

The app loads the updated bundled CSV by default. To try another file, enter its path in the sidebar. The loader supports both DES legacy columns (`State_Name`, `District_Name`, `Crop_Year`, `Season`, `Crop`, `Area`, `Production`) and standardized Dataful columns (`state`, `fiscal_year`, `district_as_per_lgd`, `season`, `crop`, `area`, `production`).

## Model and evaluation

- `src/data.py`: loads the source, isolates Rice, removes invalid area/production values, and calculates tonnes per hectare.
- `src/model.py`: district-season historical-mean baseline, Random Forest, and XGBoost regression candidates.
- `app.py`: executive-facing district/season/year explorer, model comparison leaderboard, selected-model estimate, and permutation importance.

Numeric year values are median-imputed; state/district/season are mode-imputed and one-hot encoded. The Random Forest starts with 300 trees, depth 16, leaf size 3, and `max_features=0.8`. XGBoost uses squared-error regression and a six-draw randomized search over tree count, depth, learning rate, row/column subsampling, minimum child weight, and L2 regularization. Whole years are kept together in expanding forward-chaining folds; the final three years remain a separate holdout. Model choice is based on training-period CV MAE, and holdout scores are reported for the district-season baseline, Random Forest, and tuned XGBoost.

This remains a historical benchmark. The refreshed file reaches crop-year 2022 but has no weather features, so XGBoost is an algorithm comparison—not a current-season forecaster. Extreme reported yields are retained for review; validate source units and outliers before operational use. Before capstone claims, join weather only if coverage and geography align, rerun the same time-aware evaluation, and analyze subgroup errors. Permutation importance is associative, not causal. Displayed performance values may differ from independently reprocessed variants.

## Business hypothesis to validate

Regional procurement and cooperative planning teams may use historical district-season yield benchmarks to support sourcing, storage, and transport planning. Establish value only with stakeholder interviews and a pilot against actual planning costs and outcomes. The dataset alone does not establish ROI or prove that model use improves decisions.

## Capstone next steps

1. Confirm a stakeholder and narrow the decision: regional rice sourcing, transport, or storage planning.
2. Verify the official resource version, units, license, missingness, and district/season definitions; save source snapshots and processing notes.
3. Compare the district-season baseline, Random Forest, and tuned XGBoost with the same time-aware split.
4. Create residual plots and subgroup error analysis; document under-represented regions and unstable records.
5. Quantify any ROI with stakeholder-provided baseline costs and measured pilot results; do not infer savings from MAE alone.
The illustrative ROI calculator uses editable team assumptions for procurement spend, potentially affected spend, adoption, and annual operating cost. These are scenario results, not measured savings; validate them in a stakeholder pilot before presenting them as business outcomes.
