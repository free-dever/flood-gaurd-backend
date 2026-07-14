"""
Flood Guard — Shared Feature Engineering
==========================================
Rolling-window precipitation features shared by the training pipeline
(data_prep/build_dataset.py) and the prediction batch job
(model_service/predict_flood_risk.py). Keeping this in one place guarantees
train/serve consistency — any change here changes both automatically.
"""

import pandas as pd

# Exact feature order the trained models expect.
MODEL_FEATURES = [
    "precip_3h", "precip_6h", "precip_12h", "precip_24h",
    "max_precip_1h_in_6h", "relative_humidity_pct", "month",
]


def engineer_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add rolling-window precipitation features (+ month) to an hourly weather
    DataFrame. Does NOT compute flood_label — that's training-only labeling
    logic and stays in data_prep/build_dataset.py.

    Input df must have columns: timestamp, precipitation_mm,
    relative_humidity_pct. Sorts by timestamp internally.

    Rows without a full rolling window (the first 23 rows of the input) get
    NaN in precip_24h etc. — callers decide whether to dropna() (training)
    or slice off only the rows they want to keep (serving).
    """
    df = df.sort_values("timestamp").reset_index(drop=True)

    p = df["precipitation_mm"]
    df["precip_3h"]  = p.rolling(3,  min_periods=3).sum()
    df["precip_6h"]  = p.rolling(6,  min_periods=6).sum()
    df["precip_12h"] = p.rolling(12, min_periods=12).sum()
    df["precip_24h"] = p.rolling(24, min_periods=24).sum()
    df["max_precip_1h_in_6h"] = p.rolling(6, min_periods=6).max()
    df["month"] = df["timestamp"].dt.month

    return df
