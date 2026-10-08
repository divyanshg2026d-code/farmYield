"""Load, validate, and prepare India district-season crop production records."""
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "india_crop_production.csv"
FEATURES = ["state", "district", "season", "year"]
TARGET = "yield_tonnes_ha"


def _standardize_source(raw: pd.DataFrame) -> pd.DataFrame:
    """Map either the DES legacy CSV or Dataful's standardized CSV to one schema."""
    legacy = {"State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production"}
    if legacy.issubset(raw.columns):
        return raw.rename(columns={
            "State_Name": "state", "District_Name": "district", "Crop_Year": "year",
            "Season": "season", "Crop": "crop", "Area": "area_ha", "Production": "production_tonnes",
        }).copy()

    standardized = {"state", "fiscal_year", "season", "crop", "area", "production"}
    district_column = "district_as_per_lgd" if "district_as_per_lgd" in raw else "district_as_per_source"
    if standardized.issubset(raw.columns) and district_column in raw:
        return raw.rename(columns={
            "fiscal_year": "year", district_column: "district",
            "area": "area_ha", "production": "production_tonnes",
        }).copy()

    raise ValueError(
        "Unsupported CSV schema. Expected DES columns (State_Name, District_Name, Crop_Year, "
        "Season, Crop, Area, Production) or Dataful columns (state, fiscal_year, district_as_per_lgd, "
        "season, crop, area, production)."
    )


def load_training_data(csv_path: str | None = None) -> tuple[pd.DataFrame, str]:
    """Prepare rice yield data, rejecting ambiguous keys and invalid measurements.

    Yield is consistently recomputed as production (tonnes) / area (hectares),
    rather than trusting a precomputed source field with unknown rounding.
    Fiscal-year labels such as ``2024-25`` map to their first calendar year.
    """
    path = Path(csv_path) if csv_path else DATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}. See README for the source and setup.")

    raw = pd.read_csv(path, low_memory=False)
    df = _standardize_source(raw)
    for column in ["state", "district", "season", "crop"]:
        df[column] = df[column].astype("string").str.strip()

    df = df[df["crop"].str.casefold() == "rice"].copy()
    df["year"] = df["year"].astype("string").str.extract(r"(\d{4})", expand=False)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["area_ha"] = pd.to_numeric(df["area_ha"], errors="coerce")
    df["production_tonnes"] = pd.to_numeric(df["production_tonnes"], errors="coerce")
    df = df.dropna(subset=["state", "district", "season", "year", "area_ha", "production_tonnes"])
    df = df[(df["state"] != "") & (df["district"] != "") & (df["season"] != "")]
    # Some standardized releases include a pre-aggregated season total; keeping it
    # alongside its component seasons would count the same production twice.
    df = df[df["season"].str.casefold() != "total"]
    df = df[(df["area_ha"] > 0) & (df["production_tonnes"] > 0)].copy()

    df["year"] = df["year"].astype(int)
    df["yield_tonnes_ha"] = df["production_tonnes"] / df["area_ha"]
    keys = ["state", "district", "season", "year"]
    # Exact duplicate exports can be safely collapsed. Conflicting rows need an
    # explicit source-level resolution and must not silently distort model scores.
    df = df.drop_duplicates(subset=keys + ["area_ha", "production_tonnes"])
    if df.duplicated(keys).any():
        examples = df.loc[df.duplicated(keys, keep=False), keys].head(3).to_dict("records")
        raise ValueError(f"Conflicting rice records share a state/district/season/year key: {examples}")

    prepared = df[FEATURES + [TARGET]].reset_index(drop=True)
    if prepared.empty:
        raise ValueError("No valid rice records remain after cleaning. Check the crop name and measurements.")
    label = f"Rice crop-production data - {path.name} - {prepared['year'].min()}-{prepared['year'].max()}"
    return prepared, label
