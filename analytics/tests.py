import json
import os
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_analytics_globals():
    """Reset analytics service globals before every test so state never bleeds."""
    import analytics.services as svc

    svc._loaded = False
    svc._task_sent = False
    svc.MODEL = svc.DF = svc.FEATURE_ORDER = svc.SHAP_MATRIX = svc.EXPECTED_VALUE = None
    yield


@pytest.fixture
def feature_order():
    return ["lead_time", "stays_in_week_nights", "adr"]


@pytest.fixture
def fake_shap_matrix(feature_order):
    np.random.seed(42)
    return np.random.randn(100, len(feature_order))


@pytest.fixture
def fake_df(feature_order):
    np.random.seed(42)
    return pd.DataFrame(np.random.randn(100, len(feature_order)), columns=feature_order)


@pytest.fixture
def loaded_analytics(fake_shap_matrix, feature_order, fake_df):
    """Put the analytics service into a ready state with fake ML data."""
    import analytics.services as svc

    svc._loaded = True
    svc.SHAP_MATRIX = fake_shap_matrix
    svc.FEATURE_ORDER = feature_order
    svc.EXPECTED_VALUE = -1.5
    svc.DF = fake_df
    svc.MODEL = MagicMock()


# ─── precompute_shap_artifacts task ───────────────────────────────────────────


class TestPrecomputeTask:
    def test_writes_matrix_and_meta_to_disk(self, tmp_path, feature_order):
        matrix_path = str(tmp_path / "shap_matrix.npy")
        tmp_matrix_path = str(tmp_path / "shap_matrix_tmp.npy")
        meta_path = str(tmp_path / "shap_meta.json")

        expected_shap = np.array([[0.1, -0.2, 0.3], [0.4, 0.5, -0.6]])
        fake_df = pd.DataFrame(np.zeros((2, 3)), columns=feature_order)

        mock_model = MagicMock()
        mock_model.get_booster.return_value.feature_names = feature_order
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = expected_shap
        mock_explainer.expected_value = 0.5

        with (
            patch("analytics.tasks.SHAP_MATRIX_PATH", matrix_path),
            patch("analytics.tasks.SHAP_MATRIX_TMP_PATH", tmp_matrix_path),
            patch("analytics.tasks.SHAP_META_PATH", meta_path),
            patch("analytics.tasks.pd.read_csv", return_value=fake_df),
            patch("analytics.tasks.xgb.XGBClassifier", return_value=mock_model),
            patch("analytics.tasks.shap.TreeExplainer", return_value=mock_explainer),
        ):
            from analytics.tasks import precompute_shap_artifacts

            precompute_shap_artifacts()

        assert os.path.exists(matrix_path)
        assert os.path.exists(meta_path)
        np.testing.assert_array_equal(np.load(matrix_path), expected_shap)
        with open(meta_path) as f:
            meta = json.load(f)
        assert meta["feature_order"] == feature_order
        assert meta["expected_value"] == pytest.approx(0.5)

    def test_handles_list_shap_output(self, tmp_path, feature_order):
        """shap_values() returns a list for binary classifiers — task picks index 0."""
        matrix_path = str(tmp_path / "shap_matrix.npy")
        tmp_matrix_path = str(tmp_path / "shap_matrix_tmp.npy")
        meta_path = str(tmp_path / "shap_meta.json")

        class_0_shap = np.array([[0.1, 0.2, 0.3]])
        class_1_shap = np.array([[-0.1, -0.2, -0.3]])
        fake_df = pd.DataFrame(np.zeros((1, 3)), columns=feature_order)

        mock_model = MagicMock()
        mock_model.get_booster.return_value.feature_names = feature_order
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = [class_0_shap, class_1_shap]
        mock_explainer.expected_value = [0.3, 0.7]

        with (
            patch("analytics.tasks.SHAP_MATRIX_PATH", matrix_path),
            patch("analytics.tasks.SHAP_MATRIX_TMP_PATH", tmp_matrix_path),
            patch("analytics.tasks.SHAP_META_PATH", meta_path),
            patch("analytics.tasks.pd.read_csv", return_value=fake_df),
            patch("analytics.tasks.xgb.XGBClassifier", return_value=mock_model),
            patch("analytics.tasks.shap.TreeExplainer", return_value=mock_explainer),
        ):
            from analytics.tasks import precompute_shap_artifacts

            precompute_shap_artifacts()

        np.testing.assert_array_equal(np.load(matrix_path), class_0_shap)
        with open(meta_path) as f:
            meta = json.load(f)
        assert meta["expected_value"] == pytest.approx(0.3)

    def test_no_tmp_file_left_on_disk(self, tmp_path, feature_order):
        matrix_path = str(tmp_path / "shap_matrix.npy")
        tmp_matrix_path = str(tmp_path / "shap_matrix_tmp.npy")
        meta_path = str(tmp_path / "shap_meta.json")
        fake_df = pd.DataFrame(np.zeros((1, 3)), columns=feature_order)

        mock_model = MagicMock()
        mock_model.get_booster.return_value.feature_names = feature_order
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.zeros((1, 3))
        mock_explainer.expected_value = 0.0

        with (
            patch("analytics.tasks.SHAP_MATRIX_PATH", matrix_path),
            patch("analytics.tasks.SHAP_MATRIX_TMP_PATH", tmp_matrix_path),
            patch("analytics.tasks.SHAP_META_PATH", meta_path),
            patch("analytics.tasks.pd.read_csv", return_value=fake_df),
            patch("analytics.tasks.xgb.XGBClassifier", return_value=mock_model),
            patch("analytics.tasks.shap.TreeExplainer", return_value=mock_explainer),
        ):
            from analytics.tasks import precompute_shap_artifacts

            precompute_shap_artifacts()

        assert not os.path.exists(tmp_matrix_path)


# ─── on_worker_ready signal ───────────────────────────────────────────────────


class TestWorkerReadySignal:
    def test_queues_task_when_matrix_file_missing(self, tmp_path):
        matrix_path = str(tmp_path / "shap_matrix.npy")
        with (
            patch("analytics.tasks.SHAP_MATRIX_PATH", matrix_path),
            patch("analytics.tasks.precompute_shap_artifacts") as mock_task,
        ):
            from analytics.tasks import on_worker_ready

            on_worker_ready()
        mock_task.delay.assert_called_once()

    def test_skips_task_when_matrix_file_exists(self, tmp_path):
        matrix_path = str(tmp_path / "shap_matrix.npy")
        np.save(matrix_path, np.zeros((2, 3)))
        with (
            patch("analytics.tasks.SHAP_MATRIX_PATH", matrix_path),
            patch("analytics.tasks.precompute_shap_artifacts") as mock_task,
        ):
            from analytics.tasks import on_worker_ready

            on_worker_ready()
        mock_task.delay.assert_not_called()


# ─── Status View ──────────────────────────────────────────────────────────────


class TestStatusView:
    @pytest.mark.django_db
    def test_not_ready_when_both_files_missing(self, client, tmp_path):
        with (
            patch("analytics.services.SHAP_MATRIX_PATH", str(tmp_path / "a.npy")),
            patch("analytics.services.SHAP_META_PATH", str(tmp_path / "b.json")),
        ):
            response = client.get("/analytics/status/")
        assert response.json() == {"ready": False}

    @pytest.mark.django_db
    def test_not_ready_when_only_matrix_file_exists(self, client, tmp_path):
        matrix_path = tmp_path / "shap_matrix.npy"
        np.save(str(matrix_path), np.zeros((2, 2)))
        with (
            patch("analytics.services.SHAP_MATRIX_PATH", str(matrix_path)),
            patch("analytics.services.SHAP_META_PATH", str(tmp_path / "missing.json")),
        ):
            response = client.get("/analytics/status/")
        assert response.json() == {"ready": False}

    @pytest.mark.django_db
    def test_ready_when_both_files_exist(self, client, tmp_path):
        matrix_path = tmp_path / "shap_matrix.npy"
        meta_path = tmp_path / "shap_meta.json"
        np.save(str(matrix_path), np.zeros((2, 2)))
        meta_path.write_text("{}")
        with (
            patch("analytics.services.SHAP_MATRIX_PATH", str(matrix_path)),
            patch("analytics.services.SHAP_META_PATH", str(meta_path)),
        ):
            response = client.get("/analytics/status/")
        assert response.json() == {"ready": True}

    @pytest.mark.django_db
    def test_ready_when_already_loaded_in_memory(self, client, tmp_path):
        import analytics.services as svc

        svc._loaded = True
        with (
            patch("analytics.services.SHAP_MATRIX_PATH", str(tmp_path / "missing.npy")),
            patch("analytics.services.SHAP_META_PATH", str(tmp_path / "missing.json")),
        ):
            response = client.get("/analytics/status/")
        assert response.json() == {"ready": True}


# ─── Index View ───────────────────────────────────────────────────────────────


class TestIndexView:
    @pytest.mark.django_db
    def test_shows_loading_state_when_files_absent(self, client, tmp_path):
        with (
            patch("analytics.services.SHAP_MATRIX_PATH", str(tmp_path / "missing.npy")),
            patch("analytics.services.SHAP_META_PATH", str(tmp_path / "missing.json")),
            patch("analytics.tasks.precompute_shap_artifacts"),
        ):
            response = client.get("/analytics/")
        assert response.status_code == 200
        assert response.context["computing"] is True

    @pytest.mark.django_db
    def test_queues_task_on_first_request_when_not_ready(self, client, tmp_path):
        with (
            patch("analytics.services.SHAP_MATRIX_PATH", str(tmp_path / "missing.npy")),
            patch("analytics.services.SHAP_META_PATH", str(tmp_path / "missing.json")),
            patch("analytics.tasks.precompute_shap_artifacts") as mock_task,
        ):
            client.get("/analytics/")
        mock_task.delay.assert_called_once()

    @pytest.mark.django_db
    def test_does_not_queue_task_twice(self, client, tmp_path):
        import analytics.services as svc

        svc._task_sent = True  # simulate task already queued
        with (
            patch("analytics.services.SHAP_MATRIX_PATH", str(tmp_path / "missing.npy")),
            patch("analytics.services.SHAP_META_PATH", str(tmp_path / "missing.json")),
            patch("analytics.tasks.precompute_shap_artifacts") as mock_task,
        ):
            client.get("/analytics/")
            client.get("/analytics/")
        mock_task.delay.assert_not_called()

    @pytest.mark.django_db
    def test_renders_dashboard_when_artifacts_loaded(self, client, loaded_analytics):
        response = client.get("/analytics/")
        assert response.status_code == 200
        assert response.context["computing"] is False
        assert "shap_box_json" in response.context
        assert "shap_waterfall_json" in response.context
        assert "avg_adr" in response.context

    @pytest.mark.django_db
    def test_waterfall_row_clamped_to_valid_range(self, client, loaded_analytics):
        response = client.get("/analytics/?row=99999")
        assert response.status_code == 200
        data = json.loads(response.context["shap_waterfall_json"])
        assert data["row_index"] == 99  # SHAP matrix has 100 rows → max index 99

    @pytest.mark.django_db
    def test_waterfall_default_row_is_79(self, client, loaded_analytics):
        response = client.get("/analytics/")
        data = json.loads(response.context["shap_waterfall_json"])
        assert data["row_index"] == 79

    @pytest.mark.django_db
    def test_waterfall_prediction_equals_base_plus_shap_sum(
        self, client, loaded_analytics
    ):
        response = client.get("/analytics/?row=0")
        data = json.loads(response.context["shap_waterfall_json"])
        shap_sum = sum(f["shap"] for f in data["features"])
        assert data["prediction"] == pytest.approx(
            data["base_value"] + shap_sum, abs=1e-4
        )
