"""Compare a historical baseline, Random Forest, and tuned XGBoost on future years."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

from .data import FEATURES, TARGET

CATEGORICAL = ["state", "district", "season"]
NUMERICAL = ["year"]
GROUP_KEYS = ["state", "district", "season"]


class DistrictSeasonMean:
    """Simple, interpretable baseline: historical mean by district and season."""
    def fit(self, X: pd.DataFrame, y: pd.Series):
        grouped = X[GROUP_KEYS].copy()
        grouped["target"] = np.asarray(y)
        self.means = grouped.groupby(GROUP_KEYS)["target"].mean().to_dict()
        self.global_mean = float(np.mean(y))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        keys = X[GROUP_KEYS].itertuples(index=False, name=None)
        return np.asarray([self.means.get(tuple(key), self.global_mean) for key in keys], dtype=float)


def _preprocessor() -> ColumnTransformer:
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median"), NUMERICAL),
        ("categorical", categorical, CATEGORICAL),
    ])


def build_pipeline(model_name: str = "random_forest", **params) -> Pipeline:
    if model_name == "random_forest":
        estimator = RandomForestRegressor(
            n_estimators=300, max_depth=16, min_samples_leaf=3,
            max_features=0.8, random_state=42, n_jobs=-1, **params
        )
    elif model_name == "xgboost":
        estimator = XGBRegressor(
            objective="reg:squarederror", eval_metric="mae", tree_method="hist",
            n_estimators=400, learning_rate=0.05, max_depth=4,
            min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
            reg_lambda=5, random_state=42, n_jobs=-1, verbosity=0, **params
        )
    else:
        raise ValueError(f"Unknown model: {model_name}")
    return Pipeline([("preprocess", _preprocessor()), ("model", estimator)])


def _year_folds(frame: pd.DataFrame, n_splits: int = 5) -> list[tuple[np.ndarray, np.ndarray]]:
    """Split whole years, so records from one year cannot appear in train and validation."""
    years = np.asarray(sorted(frame["year"].unique()))
    split_count = min(n_splits, len(years) - 2)
    if split_count < 2:
        raise ValueError("At least four training years are needed for forward-chaining validation.")
    splitter = TimeSeriesSplit(n_splits=split_count)
    folds = []
    row_years = frame["year"].to_numpy()
    for train_year_idx, valid_year_idx in splitter.split(years):
        train_years, valid_years = years[train_year_idx], years[valid_year_idx]
        folds.append((np.flatnonzero(np.isin(row_years, train_years)),
                      np.flatnonzero(np.isin(row_years, valid_years))))
    return folds


def _baseline_cv(frame: pd.DataFrame, folds: list[tuple[np.ndarray, np.ndarray]]) -> float:
    fold_maes = []
    for train_idx, valid_idx in folds:
        train_fold, valid_fold = frame.iloc[train_idx], frame.iloc[valid_idx]
        baseline = DistrictSeasonMean().fit(train_fold[FEATURES], train_fold[TARGET])
        fold_maes.append(mean_absolute_error(valid_fold[TARGET], baseline.predict(valid_fold[FEATURES])))
    return float(np.mean(fold_maes))


def _metrics(y_true, y_pred) -> dict:
    return {"MAE (t/ha)": mean_absolute_error(y_true, y_pred),
            "RMSE (t/ha)": mean_squared_error(y_true, y_pred) ** 0.5,
            "R²": r2_score(y_true, y_pred)}


def train_evaluate(df: pd.DataFrame) -> dict:
    """Tune XGBoost on expanding year folds, compare candidates, then score final years."""
    years = sorted(df["year"].unique())
    if len(years) < 8:
        raise ValueError("At least eight distinct years are needed for temporal validation.")
    cutoff = years[-3]
    train = df[df["year"] < cutoff].sort_values("year").reset_index(drop=True)
    test = df[df["year"] >= cutoff].sort_values("year").reset_index(drop=True)
    X_train, y_train = train[FEATURES], train[TARGET]
    X_test, y_test = test[FEATURES], test[TARGET]
    cv_folds = _year_folds(train)

    baseline = DistrictSeasonMean().fit(X_train, y_train)
    baseline_pred = baseline.predict(X_test)
    baseline_cv_mae = _baseline_cv(train, cv_folds)

    rf = build_pipeline("random_forest")
    rf_cv_scores = cross_val_score(rf, X_train, y_train, cv=cv_folds,
                                   scoring="neg_mean_absolute_error", n_jobs=1)
    rf_cv_mae, rf_cv_std = -float(rf_cv_scores.mean()), float(rf_cv_scores.std())
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)

    xgb = build_pipeline("xgboost")
    search = RandomizedSearchCV(
        xgb,
        param_distributions={
            "model__n_estimators": [200, 400, 600],
            "model__max_depth": [3, 4, 6],
            "model__learning_rate": [0.03, 0.05, 0.1],
            "model__min_child_weight": [1, 5, 10],
            "model__subsample": [0.75, 0.9],
            "model__colsample_bytree": [0.75, 0.9],
            "model__reg_lambda": [1, 5, 10],
        },
        n_iter=6, scoring="neg_mean_absolute_error", cv=cv_folds,
        random_state=42, n_jobs=1, refit=True,
    )
    search.fit(X_train, y_train)
    xgb_cv_mae = -float(search.best_score_)
    xgb_cv_std = float(search.cv_results_["std_test_score"][search.best_index_])
    xgb_pred = search.best_estimator_.predict(X_test)

    candidate_pipelines = {"Random Forest": rf, "XGBoost": search.best_estimator_}
    cv_scores = {"District-season historical mean": baseline_cv_mae,
                 "Random Forest": rf_cv_mae, "XGBoost": xgb_cv_mae}
    selected_name = min(cv_scores, key=cv_scores.get)
    selected_model = (baseline if selected_name == "District-season historical mean"
                      else candidate_pipelines[selected_name])
    predictions = {"District-season historical mean": baseline_pred,
                   "Random Forest": rf_pred, "XGBoost": xgb_pred}
    comparison_rows = []
    for name, pred in predictions.items():
        comparison_rows.append({"Model": name, "CV MAE (t/ha)": cv_scores[name], **_metrics(y_test, pred)})
    leaderboard = pd.DataFrame(comparison_rows).sort_values("CV MAE (t/ha)").reset_index(drop=True)

    if selected_name == "District-season historical mean":
        importance = pd.DataFrame(columns=["Feature", "MAE increase"])
    else:
        perm = permutation_importance(selected_model, X_test, y_test, n_repeats=5,
                                      random_state=42, scoring="neg_mean_absolute_error", n_jobs=-1)
        importance = pd.DataFrame({"Feature": FEATURES, "MAE increase": perm.importances_mean}).sort_values("MAE increase", ascending=False)
    chosen_pred = predictions[selected_name]
    chosen_metrics = _metrics(y_test, chosen_pred)
    test_detail = test.copy()
    test_detail["predicted_yield"] = chosen_pred
    test_detail["absolute_error"] = np.abs(y_test.to_numpy() - chosen_pred)
    test_detail["signed_error"] = chosen_pred - y_test.to_numpy()
    error_by_region = (test_detail.groupby(["state", "season"], as_index=False)
                       .agg(records=(TARGET, "size"), mae_t_ha=("absolute_error", "mean"),
                            mean_bias_t_ha=("signed_error", "mean"))
                       .sort_values("mae_t_ha", ascending=False))
    error_by_year = (test_detail.groupby("year", as_index=False)
                     .agg(records=(TARGET, "size"), mae_t_ha=("absolute_error", "mean"),
                          mean_bias_t_ha=("signed_error", "mean")))
    return {"pipeline": selected_model, "model_name": selected_name,
            "mae": chosen_metrics["MAE (t/ha)"], "rmse": chosen_metrics["RMSE (t/ha)"],
            "r2": chosen_metrics["R²"], "cv_mae": cv_scores[selected_name],
            "cv_mae_std": {"District-season historical mean": float("nan"),
                           "Random Forest": rf_cv_std, "XGBoost": xgb_cv_std}.get(selected_name),
            "importance": importance, "leaderboard": leaderboard,
            "error_by_region": error_by_region, "error_by_year": error_by_year,
            "xgb_best_params": search.best_params_,
            "test": test_detail,
            "train_end": int(train["year"].max()), "test_start": int(test["year"].min()),
            "test_end": int(test["year"].max())}


def predict(pipeline, values: dict) -> float:
    row = pd.DataFrame([{name: values[name] for name in FEATURES}])
    return float(pipeline.predict(row)[0])
