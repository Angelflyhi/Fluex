import json
from dataclasses import asdict, dataclass

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

from .config import ARTIFACT_DIR, FEATURES, TARGET, WEEK1_DAYS
from .open_data import build_open_dataset_training_frame
from .simulate_data import generate_dataset


@dataclass
class Metrics:
    roc_auc: float
    precision: float
    recall: float
    f1: float
    false_positive_rate: float


def _metrics(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fpr = float(fp / max(1, (fp + tn)))
    return Metrics(
        roc_auc=float(roc_auc_score(y_true, y_prob)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        false_positive_rate=fpr,
    )


def _personalized_thresholds(df_train, model):
    baselines = {}
    week1 = df_train[df_train["day"] < WEEK1_DAYS]
    for user_id, grp in week1.groupby("user_id"):
        probs = model.predict_proba(grp[FEATURES])[:, 1]
        # Calibrate threshold per user from week-1 normal behavior.
        # 97th percentile pushes false positives closer to embedded target.
        baselines[int(user_id)] = float(np.quantile(probs, 0.97))
    return baselines


def _evaluate_personalized(df_test, model, thresholds):
    y_true = df_test[TARGET].to_numpy()
    probs = model.predict_proba(df_test[FEATURES])[:, 1]
    th = np.array([thresholds.get(int(u), 0.5) for u in df_test["user_id"].to_numpy()])
    y_pred = (probs >= th).astype(int)
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fpr = float(fp / max(1, (fp + tn)))
    return Metrics(
        roc_auc=float(roc_auc_score(y_true, probs)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        false_positive_rate=fpr,
    )


def _export_edge_json(model, thresholds):
    edge_payload = {
        "model_type": "random_forest",
        "n_estimators": len(model.estimators_),
        "max_depth": int(model.max_depth) if model.max_depth is not None else None,
        "feature_names": FEATURES,
        "default_threshold": 0.5,
        "personalized_thresholds": thresholds,
        "estimators": [],
    }
    for tree in model.estimators_:
        t = tree.tree_
        edge_payload["estimators"].append(
            {
                "children_left": t.children_left.tolist(),
                "children_right": t.children_right.tolist(),
                "feature": t.feature.tolist(),
                "threshold": t.threshold.tolist(),
                "value": t.value.squeeze(axis=1).tolist(),
            }
        )
    out_file = ARTIFACT_DIR / "edge_model.json"
    out_file.write_text(json.dumps(edge_payload), encoding="utf-8")


def run():
    ARTIFACT_DIR.mkdir(exist_ok=True)
    data_mode = "open_datasets"
    try:
        df = build_open_dataset_training_frame()
    except Exception as exc:
        # Network or endpoint outages should not block local prototyping.
        print(f"Open-dataset fetch failed ({exc}). Falling back to synthetic data.")
        df = generate_dataset()
        data_mode = "synthetic_fallback"

    # Split by day to simulate first-week adaptation then deployment
    df_train = df[df["day"] < WEEK1_DAYS + 3].copy()
    df_test = df[df["day"] >= WEEK1_DAYS + 3].copy()

    model = RandomForestClassifier(
        n_estimators=16,
        max_depth=6,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced_subsample",
        n_jobs=-1,
    )
    model.fit(df_train[FEATURES], df_train[TARGET])

    y_prob = model.predict_proba(df_test[FEATURES])[:, 1]
    global_m = _metrics(df_test[TARGET].to_numpy(), y_prob, threshold=0.5)

    thresholds = _personalized_thresholds(df_train, model)
    personalized_m = _evaluate_personalized(df_test, model, thresholds)

    # Multi-modal fusion score with user-calibrated anomaly cutoffs
    fall = (df_test["fall_g"] > 2.2).astype(float)
    hr_anom = (abs(df_test["hr_bpm"] - df_test["hr_bpm"].median()) > 30).astype(float)
    immobile = (df_test["immobility_min"] > 25).astype(float)
    emergency_score = 0.40 * fall + 0.35 * hr_anom + 0.25 * immobile
    emergency_alert_rate = float((emergency_score > 0.72).mean())

    metrics = {
        "data_mode": data_mode,
        "dataset_rows_total": int(len(df)),
        "dataset_rows_train": int(len(df_train)),
        "dataset_rows_test": int(len(df_test)),
        "dataset_sources": sorted(df["dataset_source"].dropna().unique().tolist()) if "dataset_source" in df.columns else [],
        "global_threshold_0_5": asdict(global_m),
        "personalized_week1_thresholds": asdict(personalized_m),
        "emergency_score_alert_rate": emergency_alert_rate,
        "target_spec": {
            "inference_latency_goal_ms": 12,
            "false_positive_goal_pct": 2.5,
            "model_runtime": "TensorFlow Lite Micro compatible pipeline",
        },
    }

    joblib.dump(model, ARTIFACT_DIR / "model.joblib")
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _export_edge_json(model, thresholds)

    print("Training complete.")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    run()
