# FarmYield data-source audit

## Current bundled target data

`raw/india_crop_production.csv` is a public mirror of India's district-wise crop-production table. The included copy has records from 1997–2015. Rice yield is derived as production divided by area. The government's catalog describes district/crop/season/year observations with area in hectares and production in tonnes, but the catalog/resource update date is metadata, not proof that the current downloadable records reach that year.

Sources: [Government crop-production catalog](https://www.data.gov.in/catalog/district-wise-season-wise-crop-production-statistics-0), [resource page](https://www.data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997), and [CSV mirror provenance](https://raw.githubusercontent.com/dibyendubiswas1998/Crop-Production-Analysis/main/DATA/crop_production.csv).

## Candidate updates to investigate

| Need | Candidate | What is known | Required check before use |
|---|---|---|---|
| More recent crop yield | [Gujarat area, production, and yield resource](https://www.data.gov.in/catalog/area-production-and-yield-major-crops-gujarat-state) | State-level official catalog record published in April 2025 | Download/API access, actual observation years, rice coverage, units, and district definitions |
| District rainfall | [Daily district-wise rainfall data](https://ap.data.gov.in/resource/daily-district-wise-rainfall-data) | Official daily district rainfall resource; catalog listing updated in October 2025 | Actual start/end dates, completeness, stable district names, and seasonal aggregation |
| Historical weather where district station data is incomplete | [ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview) | Global gridded land reanalysis from 1950 to present; approximately 0.1-degree grid and CC-BY-4.0 | Select grid cells for district boundaries, aggregate correctly, record that these are reanalysis estimates, and check data-access requirements |

The catalog dates above do not establish the observation period. Verify actual rows and missingness before choosing a geography. If recent yield data cannot be matched reliably with weather, retain the current app as a historical benchmark and do not describe it as a current-harvest forecaster.

## Forecast design requirement

Before joining weather to yield, choose a forecast cut-off (for example, four weeks before harvest). Create features only from data that would have been available by that date. Full-season observed rainfall or temperature cannot be used for a pre-harvest prediction if it occurs after the cut-off.
