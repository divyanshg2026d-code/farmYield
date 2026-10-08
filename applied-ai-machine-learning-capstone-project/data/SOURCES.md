# FarmYield data-source and quality audit

## Active training data

`raw/india_crop_production.csv` is the updated district/season/crop production table used by the app. It contains 407,315 records across crops and crop-year labels 1997-2022. The rice slice has 25,073 rows before cleaning; the loader retains 25,024 rows after removing missing or nonpositive measurements. The updated series includes rice through 2022 (reported as 2022-23 in its source documentation), compared with the previous bundled file's 1997-2015 coverage and 15,104 rice rows before cleaning. The prepared dataset has 721 district labels across 33 state/UT labels.

The source repository states that the updated file is the Directorate of Economics & Statistics series downloaded from the official India Data Portal and converted to the legacy column format. Its file is a public mirror, not a direct download from the government portal. Byte identity with the official file and redistribution licensing of this mirrored copy have not been independently verified. The mirror README reports that, for 2005, 99.9% of matching district/crop/season rows had identical area and 98% had identical production. A local case-insensitive comparison across district names matched 773 overlapping rice keys; area matched exactly for 99.7% and production for 96.8% of those matched keys. District renaming explains some unmatched rows.

Sources: [Government of India district-wise crop-production catalog](https://www.data.gov.in/catalog/district-wise-season-wise-crop-production-statistics-0), [India Data Portal](https://www.data.gov.in/), [updated public mirror and its data-update notes](https://github.com/Ankush-Manhas840/crop-yield-prediction/blob/master/README.md), [mirrored CSV](https://github.com/Ankush-Manhas840/crop-yield-prediction/blob/master/data/crop_production.csv).

## Cleaning and safeguards

- Trim text fields before filtering; match crop names without case sensitivity.
- Accept both the legacy DES column names and Dataful's standardized column names. Fiscal-year labels such as `2024-25` map to the first year (`2024`).
- Exclude pre-aggregated `Total` season rows so that component seasons are not counted twice.
- Recompute target yield as production tonnes / area hectares. Remove records with missing fields or nonpositive area/production.
- Collapse exact duplicate yield keys, but stop with an error if conflicting yields exist for the same state, district, season, and year.
- No yield outlier threshold is imposed. Extreme values remain available for inspection instead of being silently discarded.

Three retained rice records exceed 20 tonnes/hectare, including one above 50; the maximum is 223.73 tonnes/hectare. These are not automatically discarded because the source does not provide enough evidence to establish which are errors. Validate extreme values and units before treating the model as an operational forecast. The annual observation count also varies over time; the model uses whole-year chronological splits, with the final three years held out (2020-2022).

## Newer source discovered, not bundled

Dataful lists a standardized Rice dataset with 29,523 rows, 12 columns, 1997-98 to 2024-25, an LGD district code, and a 15 September 2026 update date. The session could preview the data while signed in, but the full CSV download is paywalled. No purchase was made and the data was not used in the app. This is a possible future refresh if the team has an authorized download and can validate its licensing and schema.

## Weather integration

No weather variables are merged yet. Candidate data include [daily district-wise rainfall from data.gov.in](https://ap.data.gov.in/resource/daily-district-wise-rainfall-data) and [ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview). Before joining, establish stable geographic keys, date coverage, seasonal aggregation, and a forecast cut-off. Do not use full-season weather that occurs after the claimed prediction date.

## Interpretation

This remains a historical district-season benchmark. Area and production generate the target but are not model features. The dataset has no farm-level soil, input, weather, or cost records, so it cannot support a causal claim, farm-specific recommendation, weather-driven forecast, or quantified ROI by itself.
