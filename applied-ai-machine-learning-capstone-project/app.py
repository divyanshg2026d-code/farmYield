from pathlib import Path

import streamlit as st

from src.data import DATA_PATH, load_training_data
from src.model import train_evaluate, predict

st.set_page_config(page_title="FarmYield | India Rice Planner", page_icon="🌾", layout="wide")
st.title("🌾 FarmYield")
st.subheader("India rice yield planning")
st.write("Explore historical district level rice yield benchmarks by state, district, season, and year. The model learns from historical production records; it does not observe farm-level soil, fertilizer, or weather conditions.")

with st.sidebar:
    st.header("Data source")
    csv_path = st.text_input("CSV path (optional)", value="")
    st.caption("Default data covers rice records from 1997 to 2022. You can also load a DES-format CSV or a standardized Dataful CSV.")

@st.cache_resource(show_spinner="Loading records and evaluating the model…")
def get_result(path: str, source_signature: tuple[int, int]):
    data, label = load_training_data(path or None)
    return data, label, train_evaluate(data)

try:
    active_path = Path(csv_path) if csv_path else DATA_PATH
    try:
        stat = active_path.stat()
        source_signature = (stat.st_mtime_ns, stat.st_size)
    except FileNotFoundError:
        source_signature = (-1, -1)
    data, source_label, result = get_result(csv_path, source_signature)
except Exception as exc:
    st.error(f"Could not prepare the model: {exc}")
    st.stop()

st.success(f"{source_label} · {len(data):,} valid rice records")
st.warning("This is a historical benchmark, not a farm-specific forecast. Yield is calculated as recorded production divided by recorded area. Historical associations do not establish cause or predict weather-driven changes.")
st.caption("The bundled 1997-2022 file is a public mirror of the DES / India Data Portal series. Its exact byte-for-byte match to the official download has not been verified. Very high reported yields are retained and should be reviewed against source records before operational use.")

left, right = st.columns([1, 1])
with left:
    st.header("Explore a historical season")
    state = st.selectbox("State / union territory", sorted(data["state"].unique()))
    district_options = sorted(data.loc[data["state"] == state, "district"].unique())
    district = st.selectbox("District", district_options)
    season_options = sorted(data.loc[(data["state"] == state) & (data["district"] == district), "season"].unique())
    season = st.selectbox("Season", season_options)
    test_years = sorted(data["year"].unique())[-3:]
    year = st.selectbox("Crop year (held-out validation years)", test_years, index=len(test_years)-1)
    actual_rows = data[(data["state"] == state) & (data["district"] == district) &
                       (data["season"] == season) & (data["year"] == year)]
    scenario = {"state": state, "district": district, "season": season, "year": year}
    estimate = max(0, predict(result["pipeline"], scenario))
    if not actual_rows.empty:
        actual = float(actual_rows["yield_tonnes_ha"].iloc[0])
        st.metric("Recorded yield", f"{actual:.2f} tonnes/ha", help="Derived from the historical area and production fields.")
        st.metric("Model estimate", f"{estimate:.2f} tonnes/ha", f"{estimate-actual:+.2f} vs recorded")
    else:
        st.metric("Model estimate", f"{estimate:.2f} tonnes/ha")
        st.caption("No matching historical record was found for this combination; this is a model estimate for the held-out period.")

with right:
    st.header("Model comparison")
    st.caption(f"Selected using forward-chaining validation on training years: **{result['model_name']}**")
    st.dataframe(result["leaderboard"], hide_index=True, width="stretch")
    m1, m2, m3 = st.columns(3)
    m1.metric("Test MAE", f"{result['mae']:.2f} t/ha")
    m2.metric("Test RMSE", f"{result['rmse']:.2f} t/ha")
    m3.metric("Test R²", f"{result['r2']:.2f}")
    st.caption(f"Final chronological holdout: train through {result['train_end']}, test {result['test_start']}–{result['test_end']}. Model selection uses earlier whole-year forward-chaining folds; test years are kept separate from tuning.")
    with st.expander("How the algorithms work"):
        st.write("**District-season mean:** a simple historical-average benchmark. **Random Forest:** averages many trees trained on varied samples. **XGBoost:** adds trees sequentially to improve earlier errors; its settings are selected with a small randomized search over forward-chaining year folds.")
        st.json(result["xgb_best_params"])
    st.subheader("Which inputs mattered most?")
    if result["importance"].empty:
        st.caption("The historical-average baseline was selected; it does not learn individual feature effects.")
    else:
        st.bar_chart(result["importance"].set_index("Feature"))
        st.caption("Permutation importance measures the test MAE change when an input is shuffled. It is a model diagnostic, not a causal explanation.")
    with st.expander("Where are the errors largest?"):
        st.dataframe(result["error_by_region"].head(15), hide_index=True, width="stretch")
        st.caption("Rows with very few test records are less reliable. Positive mean bias means the model overestimated yield on average.")
        st.bar_chart(result["error_by_year"].set_index("year")[["mae_t_ha"]])

st.divider()
st.subheader("Business use and limits")
st.write("Potential users: rice procurement teams, cooperatives, and regional agricultural planners comparing historical district-season yield levels for storage, transport, and sourcing plans. Validate with stakeholders before using this for operational decisions.")
st.info("The source table is aggregated at district/crop/season/year level. It lacks within-season weather, soil, input quantities, farm-level outcomes, and costs; this version cannot optimize fertilizer or claim farm-level ROI.")
st.divider()
st.subheader("Illustrative business case")
st.caption("Enter assumptions from a procurement team or pilot. These are scenario inputs, not measured FarmYield savings.")
roi_left, roi_right = st.columns(2)
with roi_left:
    annual_spend_crore = st.number_input(
        "Annual rice procurement spend (₹ crore)", min_value=0.0, value=0.0, step=1.0,
        help="Use the annual spend of the team that might use this planning tool.",
    )
    avoidable_share_pct = st.slider(
        "Share of spend potentially affected by better planning (%)", min_value=0, max_value=20, value=0,
        help="Set this only from a stakeholder estimate or measured pilot; leave at 0 until you have one.",
    )
with roi_right:
    adoption_pct = st.slider(
        "Expected adoption by the planning team (%)", min_value=0, max_value=100, value=0,
        help="The share of relevant planning activity expected to use the tool.",
    )
    annual_cost_lakh = st.number_input(
        "Annual tool and operating cost (₹ lakh)", min_value=0.0, value=0.0, step=1.0,
        help="Include any annual data, hosting, training, and support costs.",
    )
gross_value_lakh = annual_spend_crore * 100 * avoidable_share_pct / 100 * adoption_pct / 100
net_value_lakh = gross_value_lakh - annual_cost_lakh
value_col, cost_col, roi_col = st.columns(3)
value_col.metric("Illustrative annual value", f"₹{gross_value_lakh:,.1f} lakh")
cost_col.metric("Annual operating cost", f"₹{annual_cost_lakh:,.1f} lakh")
if annual_cost_lakh > 0:
    roi_pct = net_value_lakh / annual_cost_lakh * 100
    roi_col.metric("Illustrative net ROI", f"{roi_pct:,.0f}%")
else:
    roi_col.metric("Illustrative net value", f"₹{net_value_lakh:,.1f} lakh")
st.caption("Formula: (annual spend × potentially affected share × adoption rate) − annual tool cost. Validate every assumption in a stakeholder pilot; model accuracy alone does not establish financial value.")
