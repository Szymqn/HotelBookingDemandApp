import calendar
import json
import os
import threading

import numpy as np
import pandas as pd
import xgboost as xgb

from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg, Count, F

from bookings.models import Booking

SHAP_MATRIX_PATH = str(settings.BASE_DIR / "ml_model" / "shap_matrix.npy")
SHAP_META_PATH = str(settings.BASE_DIR / "ml_model" / "shap_meta.json")

_lock = threading.Lock()
_loaded = False
_task_sent = False
MODEL = DF = FEATURE_ORDER = SHAP_MATRIX = EXPECTED_VALUE = None


def try_load_from_disk() -> bool:
    global _loaded, MODEL, DF, FEATURE_ORDER, SHAP_MATRIX, EXPECTED_VALUE

    if not os.path.exists(SHAP_MATRIX_PATH) or not os.path.exists(SHAP_META_PATH):
        return False

    with open(SHAP_META_PATH) as f:
        meta = json.load(f)

    FEATURE_ORDER = meta["feature_order"]
    EXPECTED_VALUE = meta["expected_value"]
    SHAP_MATRIX = np.load(SHAP_MATRIX_PATH)

    df = pd.read_csv(str(settings.BASE_DIR / "data" / "hotel_bookings.csv"))
    obj_cols = df.select_dtypes(include="object").columns
    if len(obj_cols):
        df[obj_cols] = df[obj_cols].astype("category")
    DF = df

    MODEL = xgb.XGBClassifier(enable_categorical=True)
    MODEL.load_model(str(settings.BASE_DIR / "ml_model" / "xgb_model.json"))

    _loaded = True
    return True


def _compute_artifacts_thread() -> None:
    """Run SHAP precomputation in a background thread (Celery fallback)."""
    try:
        from analytics.tasks import precompute_shap_artifacts

        precompute_shap_artifacts()
    except Exception:
        pass


def ensure_artifacts() -> bool:
    """Returns True if artifacts are ready, False if still computing."""
    global _task_sent

    if _loaded:
        return True

    with _lock:
        if _loaded:
            return True
        if try_load_from_disk():
            return True
        if not _task_sent:
            try:
                from analytics.tasks import precompute_shap_artifacts

                precompute_shap_artifacts.delay()
            except Exception:
                threading.Thread(target=_compute_artifacts_thread, daemon=True).start()
            _task_sent = True
        return False


def is_ready() -> bool:
    return _loaded or (
        os.path.exists(SHAP_MATRIX_PATH) and os.path.exists(SHAP_META_PATH)
    )


_FEATURE_NAME_MAP = {
    "lead_time": "Lead Time",
    "arrival_date_year": "Arrival Year",
    "arrival_date_month": "Arrival Month",
    "arrival_date_week_number": "Week of Year",
    "arrival_date_day_of_month": "Day of Month",
    "stays_in_weekend_nights": "Weekend Nights",
    "stays_in_week_nights": "Weekday Nights",
    "adults": "Number of Adults",
    "children": "Number of Children",
    "babies": "Number of Babies",
    "meal": "Meal Plan",
    "country": "Country of Origin",
    "market_segment": "Market Segment",
    "distribution_channel": "Distribution Channel",
    "is_repeated_guest": "Repeated Guest",
    "previous_cancellations": "Previous Cancellations",
    "previous_bookings_not_canceled": "Previous Non-Cancelled Bookings",
    "reserved_room_type": "Reserved Room Type",
    "assigned_room_type": "Assigned Room Type",
    "booking_changes": "Booking Changes",
    "deposit_type": "Deposit Type",
    "agent": "Booking Agent",
    "company": "Company",
    "days_in_waiting_list": "Days in Waiting List",
    "customer_type": "Customer Type",
    "adr": "Average Daily Rate",
    "required_car_parking_spaces": "Parking Spaces Required",
    "total_of_special_requests": "Special Requests",
    "reservation_status_date": "Reservation Status Date",
    "hotel": "Hotel Type",
}


def get_top_features(top_n: int = 5) -> list:
    """Top N features by mean |SHAP|, each as % of total model impact."""
    if SHAP_MATRIX is None:
        return []
    cache_key = f"top_features_{top_n}"
    data = cache.get(cache_key)
    if data:
        return data

    mean_abs = np.abs(SHAP_MATRIX).mean(axis=0)
    total = mean_abs.sum()
    top_idx = np.argsort(-mean_abs)[:top_n]

    out = []
    for rank, idx in enumerate(top_idx):
        raw = FEATURE_ORDER[idx]
        pct = round(float(mean_abs[idx] / total * 100), 1) if total > 0 else 0.0
        out.append(
            {
                "name": _FEATURE_NAME_MAP.get(raw, raw.replace("_", " ").title()),
                "percentage": pct,
                "rank": rank,
            }
        )

    cache.set(cache_key, out, 3600)
    return out


def get_box_plot(top_n: int = 15) -> list:
    cache_key = f"shap_box_{top_n}"
    data = cache.get(cache_key)
    if data:
        return data
    mean_abs = np.abs(SHAP_MATRIX).mean(axis=0)
    top_idx = np.argsort(-mean_abs)[:top_n]
    out = []
    for idx in top_idx:
        vals = SHAP_MATRIX[:, idx]
        q1, q3 = np.percentile(vals, [25, 75])
        out.append(
            {
                "x": FEATURE_ORDER[idx],
                "y": [
                    round(float(vals.min()), 6),
                    round(float(q1), 6),
                    round(float(np.median(vals)), 6),
                    round(float(q3), 6),
                    round(float(vals.max()), 6),
                ],
            }
        )
    cache.set(cache_key, out, 3600)
    return out


def get_monthly_aggregations() -> tuple:
    agg = cache.get("monthly_agg_v1")
    if agg:
        return agg
    raw = (
        Booking.objects.values("arrival_date_year", "arrival_date_month_number")
        .annotate(bookings=Count("id"), m_avg_adr=Avg("adr"))
        .order_by("arrival_date_year", "arrival_date_month_number")
    )
    labels, bookings_data, adr_data = [], [], []
    for r in raw:
        if r["bookings"] <= 0:
            continue
        labels.append(
            f"{calendar.month_abbr[r['arrival_date_month_number']]} {r['arrival_date_year']}"
        )
        bookings_data.append(r["bookings"])
        adr_data.append(round(r["m_avg_adr"] or 0, 2))
    agg = (
        labels,
        bookings_data,
        adr_data,
        round(Booking.objects.aggregate(Avg("adr"))["adr__avg"] or 0, 2),
        round(
            Booking.objects.annotate(
                total_nights=F("stays_in_weekend_nights") + F("stays_in_week_nights")
            ).aggregate(avg_total_nights=Avg("total_nights"))["avg_total_nights"]
            or 0,
            2,
        ),
    )
    cache.set("monthly_agg_v1", agg, 900)
    return agg


def get_waterfall_explanation(row_idx: int) -> dict:
    row_idx = max(0, min(row_idx, SHAP_MATRIX.shape[0] - 1))
    row_shap = SHAP_MATRIX[row_idx, :]
    row_features = DF.iloc[row_idx][FEATURE_ORDER]

    top_n = 14
    abs_vals = np.abs(row_shap)
    top_idx = np.argsort(-abs_vals)[:top_n]
    used = set(top_idx)

    contrib = []
    for idx in top_idx:
        val = row_shap[idx]
        raw_val = row_features.iloc[idx]
        contrib.append(
            {
                "feature": FEATURE_ORDER[idx],
                "shap": round(float(val), 6),
                "value": (
                    float(raw_val)
                    if isinstance(raw_val, (int, float, np.number))
                    else str(raw_val)
                ),
                "direction": "positive" if val >= 0 else "negative",
            }
        )

    if len(row_shap) > top_n:
        rest_sum = float(
            row_shap[[i for i in range(len(row_shap)) if i not in used]].sum()
        )
        contrib.append(
            {
                "feature": str(len(row_features) - top_n) + " OTHER FEATURES",
                "shap": round(rest_sum, 6),
                "value": "",
                "direction": "positive" if rest_sum >= 0 else "negative",
            }
        )

    prediction = EXPECTED_VALUE + float(row_shap.sum())
    return {
        "row_index": row_idx,
        "base_value": round(EXPECTED_VALUE, 6),
        "prediction": round(prediction, 6),
        "features": contrib,
    }
