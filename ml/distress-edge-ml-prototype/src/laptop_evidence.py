import json
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from .config import ARTIFACT_DIR, FEATURES


def _emergency_score(sample):
    fall = 1.0 if sample[0] > 2.2 else 0.0
    hr_anom = 1.0 if (sample[3] > 125 or sample[3] < 48) else 0.0
    immobile = 1.0 if sample[7] > 25 else 0.0
    return 0.40 * fall + 0.35 * hr_anom + 0.25 * immobile


def run():
    model = joblib.load(ARTIFACT_DIR / "model.joblib")
    metrics = json.loads((ARTIFACT_DIR / "metrics.json").read_text(encoding="utf-8"))

    scenarios = [
        {
            "name": "normal_walk",
            "sample": [1.1, 70, 120, 82, 42, 98, 33.4, 4, 8, 1.3, 3.2, 0, 102],
        },
        {
            "name": "possible_fall_distress",
            "sample": [2.9, 260, 910, 146, 17, 92, 34.1, 34, 1, 0.05, 8.6, 1, 4],
        },
        {
            "name": "night_immobility_only",
            "sample": [0.9, 62, 95, 61, 38, 97, 33.2, 38, 1, 0.01, 2.8, 1, 0],
        },
    ]

    out = []
    for s in scenarios:
        arr = pd.DataFrame([s["sample"]], columns=FEATURES, dtype=float)
        t0 = time.perf_counter()
        prob = float(model.predict_proba(arr)[0, 1])
        dt_ms = (time.perf_counter() - t0) * 1000.0
        emergency = _emergency_score(s["sample"])
        out.append(
            {
                "scenario": s["name"],
                "distress_probability": round(prob, 4),
                "inference_latency_ms": round(dt_ms, 3),
                "emergency_score": round(emergency, 4),
                "emergency_trigger": emergency > 0.72,
            }
        )

    # Micro benchmark on laptop CPU
    bench = np.tile(np.array([scenarios[1]["sample"]], dtype=float), (1000, 1))
    bench_df = pd.DataFrame(bench, columns=FEATURES)
    t0 = time.perf_counter()
    _ = model.predict_proba(bench_df)
    avg_ms = ((time.perf_counter() - t0) * 1000.0) / len(bench)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_device": "Laptop/PC (Python local runtime)",
        "feature_order": FEATURES,
        "dataset_sources": metrics.get("dataset_sources", []),
        "training_rows_total": metrics.get("dataset_rows_total"),
        "personalized_false_positive_rate": metrics.get("personalized_week1_thresholds", {}).get("false_positive_rate"),
        "roc_auc": metrics.get("personalized_week1_thresholds", {}).get("roc_auc"),
        "scenario_results": out,
        "benchmark": {
            "samples": 1000,
            "average_inference_ms_per_sample": round(avg_ms, 4),
        },
    }

    out_json = ARTIFACT_DIR / "laptop_evidence.json"
    out_md = ARTIFACT_DIR / "laptop_evidence.md"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Laptop Execution Evidence",
        "",
        f"- Generated at (UTC): {report['generated_at_utc']}",
        f"- Execution device: {report['execution_device']}",
        f"- Dataset sources: {', '.join(report['dataset_sources'])}",
        f"- Total training rows: {report['training_rows_total']}",
        f"- ROC-AUC: {report['roc_auc']}",
        f"- Personalized false positive rate: {report['personalized_false_positive_rate']}",
        f"- Avg inference latency on laptop (ms/sample): {report['benchmark']['average_inference_ms_per_sample']}",
        "",
        "## Scenario Results",
        "",
    ]
    for row in out:
        lines.append(
            f"- {row['scenario']}: prob={row['distress_probability']}, "
            f"score={row['emergency_score']}, trigger={row['emergency_trigger']}, "
            f"latency_ms={row['inference_latency_ms']}"
        )

    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nSaved: {out_json}")
    print(f"Saved: {out_md}")


if __name__ == "__main__":
    run()
