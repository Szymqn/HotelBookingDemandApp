# BookWiseAI: Supporting Business Operations with Explainable Machine Learning Methods - A Case Study of Hotel Reservation Analysis

### Django web application that applies explainable machine learning to the Hotel Booking Demand dataset, providing hotel managers with interpretable cancellation predictions, demand forecasting, and data-driven business insights.

---

## Overview

### This system combines an XGBoost cancellation prediction model with SHAP (SHapley Additive exPlanations) to go beyond black-box predictions — every forecast is accompanied by a transparent explanation of which factors drove it and by how much. The goal is to turn raw reservation data into actionable operational intelligence.

**Key capabilities:**
- Cancellation risk prediction per booking using a trained XGBoost classifier
- SHAP-based explainability: waterfall charts, box plots, and global feature importance
- Operational dashboard with KPIs, month-over-month trends, and automated business insights
- Demand forecasting over historical arrival data
- Amadeus API integration for city search

---

## Architecture

```
Nginx (port 80)
  └── Gunicorn / Django 6 (port 8000)
        ├── bookings        — Booking model, CSV import management command
        ├── dashboard       — KPI overview, trend analysis, AI-generated insights
        ├── analytics       — SHAP analysis, waterfall & box-plot visualisations
        ├── ai_insights     — Global SHAP feature importance
        ├── demand_forecast — Historical arrival volume forecasting
        ├── api             — DRF endpoint wrapping Amadeus City Search
        ├── users           — Email-based custom user model, premium flag
        └── user_settings   — Per-user preferences

Redis ←→ Celery Worker
  └── Async SHAP artifact precomputation (shap_matrix.npy, shap_meta.json)
```

---

## ML Stack

| Component | Detail |
|-----------|--------|
| Dataset | [Hotel Booking Demand](https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand) — 119k reservations |
| Primary model | XGBoost classifier (`xgb_model.json`) with categorical feature support |
| Ensemble | Stacking model (`stacking_model.pkl`) |
| Explainability | SHAP — global importance, per-booking waterfall, box-plot distribution |
| Async compute | Celery task precomputes full SHAP matrix on first request; served from cache thereafter |

SHAP artifacts are precomputed once and stored as `ml_model/shap_matrix.npy` + `ml_model/shap_meta.json`. Subsequent requests are served from Django's cache (Redis), with a 1-hour TTL.

---

## Tech Stack

- **Backend:** Django 6.0.3, Django REST Framework 3.17
- **ML:** XGBoost 3.2, scikit-learn 1.8, SHAP 0.51, NumPy, pandas
- **Async:** Celery + Redis 7
- **Frontend:** Bootstrap 5, django-tables2, Chart.js (via templates)
- **Deployment:** Docker Compose — Nginx, Gunicorn, Celery, Redis
- **External API:** Amadeus Travel API (city search)
- **Python:** 3.13

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- The `hotel_bookings.csv` dataset placed in the `data/` directory
- An `.env` file (see below)
-
### Run with Docker

```bash
docker-compose up --build
```

This starts Nginx (port 80), Gunicorn, Celery, and Redis. The app is available at `http://localhost/`.

### Run locally (development)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py import_bookings  # imports hotel_bookings.csv into the database
python manage.py runserver
```

Start Celery in a separate terminal:

```bash
celery -A HotelBookingDemandApp worker -l info
```

---

## Loading the Dataset

The `import_bookings` management command reads `data/hotel_bookings.csv` and populates the `Booking` table:

```bash
python manage.py import_bookings
```

On first visit to the Analytics page, a Celery task is dispatched to precompute the SHAP matrix. The page polls until the computation is complete.

---

## Application Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/dashboard/` | Total bookings, average ADR, occupancy, MoM trends, AI insights |
| Analytics | `/analytics/` | SHAP waterfall (per booking), SHAP box plot (top 15 features), monthly charts |
| AI Insights | `/ai_insights/` | Global SHAP feature importance — top 5 drivers of cancellation |
| Demand Forecast | `/demand_forecast/` | Arrival volume over time |
| Bookings | `/bookings/` | Paginated booking table with filters |

### Dashboard AI Insights

The dashboard automatically derives three business observations from the data:
- **Peak season** — the busiest arrival month vs. the monthly average
- **Cancellation risk** — overall cancellation rate and count of non-refundable active bookings
- **Pricing opportunity** — ADR gap between City Hotel and Resort Hotel segments

---

## Running Tests

```bash
pytest
```

Test configuration is in `pytest.ini`. Each Django app has a `tests.py` module.

---

## Project Structure

```
HotelBookingDemandApp/
├── bookings/           # Core Booking model and CSV import command
├── dashboard/          # KPI dashboard and AI insights
├── analytics/          # SHAP analytics (Celery task, services, views)
├── ai_insights/        # Global feature importance view
├── demand_forecast/    # Demand over time
├── api/                # DRF + Amadeus city search
├── users/              # Custom email-based user model
├── user_settings/      # Per-user settings
├── ml_model/           # Trained model artifacts (xgb_model.json, stacking_model.pkl)
├── data/               # hotel_bookings.csv (not committed)
├── templates/          # Django HTML templates per app
├── static/             # CSS and JS assets
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
└── requirements.txt
```

---

## License

See [LICENSE](LICENSE).
