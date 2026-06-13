import json
import os

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from celery import shared_task
from celery.signals import worker_ready
from django.conf import settings

SHAP_MATRIX_PATH = str(settings.BASE_DIR / "ml_model" / "shap_matrix.npy")
SHAP_MATRIX_TMP_PATH = str(settings.BASE_DIR / "ml_model" / "shap_matrix_tmp.npy")
SHAP_META_PATH = str(settings.BASE_DIR / "ml_model" / "shap_meta.json")


@shared_task(name="analytics.precompute_shap_artifacts", time_limit=600)
def precompute_shap_artifacts():
    df = pd.read_csv(str(settings.BASE_DIR / "data" / "hotel_bookings.csv"))
    obj_cols = df.select_dtypes(include="object").columns
    if len(obj_cols):
        df[obj_cols] = df[obj_cols].astype("category")

    model = xgb.XGBClassifier(enable_categorical=True)
    model.load_model(str(settings.BASE_DIR / "ml_model" / "xgb_model.json"))
    feature_order = model.get_booster().feature_names
    X = df[feature_order]

    explainer = shap.TreeExplainer(model)
    sv_raw = explainer.shap_values(X)
    ev = explainer.expected_value

    if isinstance(sv_raw, list):
        shap_matrix = sv_raw[0]
        expected_value = float(ev[0] if isinstance(ev, (list, np.ndarray)) else ev)
    else:
        shap_matrix = sv_raw
        expected_value = float(ev if np.isscalar(ev) else ev[0])

    # Write matrix to temp file then rename atomically
    np.save(SHAP_MATRIX_TMP_PATH, shap_matrix)
    os.replace(SHAP_MATRIX_TMP_PATH, SHAP_MATRIX_PATH)

    with open(SHAP_META_PATH, "w") as f:
        json.dump(
            {"feature_order": list(feature_order), "expected_value": expected_value}, f
        )


@worker_ready.connect
def on_worker_ready(**kwargs):
    if not os.path.exists(SHAP_MATRIX_PATH):
        precompute_shap_artifacts.delay()
