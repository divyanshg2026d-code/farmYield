"""Load and prepare India's district-level crop production records."""
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "india_crop_production.csv"
FEATURES = ["state", "district", "season", "year"]
TARGET = "yield_tonnes_ha"


def load_training_data(csv_path: str | None = None) -> tuple[pd.DataFrame, str]:
    """Filter the public historical table to rice and derive yield = production / area."""
    path = Path(csv_path) if csv_path else DATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}. See README for the source and setup.")
    raw = pd.read_csv(path, low_memory=False)
    required = {"State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")
    df = raw.loc[raw["Crop"].astype(str).str.strip().str.casefold() == "rice"].copy()
    df["Area"] = pd.to_numeric(df["Area"], errors="coerce")
    df["Production"] = pd.to_numeric(df["Production"], errors="coerce")
    df["Crop_Year"] = pd.to_numeric(df["Crop_Year"], errors="coerce")
    df = df.dropna(subset=["State_Name", "District_Name", "Season", "Crop_Year", "Area", "Production"])
    df = df[(df["Area"] > 0) & (df["Production"] > 0)].copy()
    df["yield_tonnes_ha"] = df["Production"] / df["Area"]
    df = df.rename(columns={"State_Name": "state", "District_Name": "district", "Season": "season", "Crop_Year": "year"})
    df["year"] = df["year"].astype(int)
    return df[FEATURES + [TARGET]].reset_index(drop=True), f"India rice production dataset ({path.name})"
