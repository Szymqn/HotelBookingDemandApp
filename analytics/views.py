import calendar
import json
import pickle
import shap
import threading

import numpy as np
import pandas as pd
import xgboost as xgb

from django.core.cache import cache
from django.db.models import Avg, F, Count
from django.shortcuts import render

from bookings.models import Booking

_lock = threading.Lock()
_loaded = False
MODEL = DF = FEATURE_ORDER = SHAP_MATRIX = EXPECTED_VALUE = None


def _load_artifacts():
    global _loaded, MODEL, DF, FEATURE_ORDER, SHAP_MATRIX, EXPECTED_VALUE
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        df = pd.read_csv('data/hotel_bookings.csv')
        obj_cols = df.select_dtypes(include='object').columns
        if len(obj_cols):
            df[obj_cols] = df[obj_cols].astype('category')
        MODEL = xgb.XGBClassifier(enable_categorical=True)
        MODEL.load_model('ml_model/xgb_model.json')
        FEATURE_ORDER = MODEL.get_booster().feature_names
        X = df[FEATURE_ORDER]
        explainer = shap.TreeExplainer(MODEL)
        sv_raw = explainer.shap_values(X)
        ev = explainer.expected_value
        if isinstance(sv_raw, list):
            SHAP_MATRIX = sv_raw[0]
            EXPECTED_VALUE = float(ev[0] if isinstance(ev, (list, np.ndarray)) else ev)
        else:
            SHAP_MATRIX = sv_raw
            EXPECTED_VALUE = float(ev if np.isscalar(ev) else ev[0])
        DF = df
        _loaded = True


def _get_box_plot(top_n=15):
    cache_key = f'shap_box_{top_n}'
    data = cache.get(cache_key)
    if data:
        return data
    mean_abs = np.abs(SHAP_MATRIX).mean(axis=0)
    top_idx = np.argsort(-mean_abs)[:top_n]
    out = []
    for idx in top_idx:
        vals = SHAP_MATRIX[:, idx]
        q1, q3 = np.percentile(vals, [25, 75])
        out.append({
            'x': FEATURE_ORDER[idx],
            'y': [round(float(vals.min()), 6),
                  round(float(q1), 6),
                  round(float(np.median(vals)), 6),
                  round(float(q3), 6),
                  round(float(vals.max()), 6)]
        })
    cache.set(cache_key, out, 3600)
    return out


def index(request):
    _load_artifacts()

    agg = cache.get('monthly_agg_v1')
    if not agg:
        raw = (Booking.objects
               .values('arrival_date_year', 'arrival_date_month_number')
               .annotate(bookings=Count('id'), m_avg_adr=Avg('adr'))
               .order_by('arrival_date_year', 'arrival_date_month_number'))
        labels, bookings_data, adr_data = [], [], []
        for r in raw:
            if r['bookings'] <= 0: continue
            labels.append(f"{calendar.month_abbr[r['arrival_date_month_number']]} {r['arrival_date_year']}")
            bookings_data.append(r['bookings'])
            adr_data.append(round(r['m_avg_adr'] or 0, 2))
        agg = (labels, bookings_data, adr_data,
               round(Booking.objects.aggregate(Avg('adr'))['adr__avg'] or 0, 2),
               round(Booking.objects
                     .annotate(total_nights=F('stays_in_weekend_nights') + F('stays_in_week_nights'))
                     .aggregate(avg_total_nights=Avg('total_nights'))['avg_total_nights'] or 0, 2))
        cache.set('monthly_agg_v1', agg, 900)
    labels, bookings_data, adr_data, avg_adr, avg_room_occupy = agg

    row_idx = int(request.GET.get('row', 79))
    row_idx = max(0, min(row_idx, SHAP_MATRIX.shape[0] - 1))
    row_shap = SHAP_MATRIX[row_idx, :]
    row_features = DF.iloc[row_idx][FEATURE_ORDER]

    contrib = []
    abs_vals = np.abs(row_shap)
    top_n = 14
    top_idx = np.argsort(-abs_vals)[:top_n]
    used = set(top_idx)
    for idx in top_idx:
        val = row_shap[idx]
        raw_val = row_features.iloc[idx]
        contrib.append({
            'feature': FEATURE_ORDER[idx],
            'shap': round(float(val), 6),
            'value': (float(raw_val) if isinstance(raw_val, (int, float, np.number)) else str(raw_val)),
            'direction': 'positive' if val >= 0 else 'negative'
        })

    if len(row_shap) > top_n:
        rest_sum = float(row_shap[[i for i in range(len(row_shap)) if i not in used]].sum())
        contrib.append({
            'feature': str(len(row_features)-top_n) +' OTHER FEATURES',
            'shap': round(rest_sum, 6),
            'value': '',
            'direction': 'positive' if rest_sum >= 0 else 'negative'
        })

    prediction = EXPECTED_VALUE + float(row_shap.sum())
    waterfall_payload = {
        'row_index': row_idx,
        'base_value': round(EXPECTED_VALUE, 6),
        'prediction': round(prediction, 6),
        'features': contrib
    }

    context = {
        'avg_adr': avg_adr,
        'avg_room_occupy': avg_room_occupy,
        'chart_label_json': json.dumps(labels),
        'chart_data_json': json.dumps(bookings_data),
        'chart_adr_json': json.dumps(adr_data),
        'shap_box_json': json.dumps(_get_box_plot()),
        'shap_waterfall_json': json.dumps(waterfall_payload),
    }
    return render(request, 'analytics/index.html', context)
