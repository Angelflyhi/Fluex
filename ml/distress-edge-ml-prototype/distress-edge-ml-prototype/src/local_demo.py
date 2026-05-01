import json
from datetime import datetime, timezone

import joblib
import pandas as pd

from .config import ARTIFACT_DIR, FEATURES, PROJECT_ROOT


def _emergency_score(df: pd.DataFrame) -> pd.Series:
    fall = (df["fall_g"] > 2.2).astype(float)
    hr_anom = ((df["hr_bpm"] > 125) | (df["hr_bpm"] < 48)).astype(float)
    immobile = (df["immobility_min"] > 25).astype(float)
    return 0.40 * fall + 0.35 * hr_anom + 0.25 * immobile


def run():
    model = joblib.load(ARTIFACT_DIR / "model.joblib")
    data_path = PROJECT_ROOT / "data" / "demo_sensor_windows.csv"
    demo_df = pd.read_csv(data_path)

    probs = model.predict_proba(demo_df[FEATURES])[:, 1]
    emergency = _emergency_score(demo_df)
    trigger = (emergency > 0.72).astype(int)

    result = demo_df.copy()
    result["distress_probability"] = probs
    result["emergency_score"] = emergency
    result["predicted_alert"] = trigger
    result["match_expected"] = (result["predicted_alert"] == result["expected_alert"]).astype(int)

    accuracy = float(result["match_expected"].mean())
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "demo_dataset": str(data_path),
        "samples": int(len(result)),
        "alert_accuracy_vs_expected": accuracy,
        "predicted_alert_rate": float(result["predicted_alert"].mean()),
        "mean_distress_probability": float(result["distress_probability"].mean()),
    }

    ARTIFACT_DIR.mkdir(exist_ok=True)
    csv_out = ARTIFACT_DIR / "demo_results.csv"
    md_out = ARTIFACT_DIR / "demo_results.md"
    json_out = ARTIFACT_DIR / "demo_results.json"

    result.to_csv(csv_out, index=False)
    json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Local Demo Results",
        "",
        f"- Generated (UTC): {summary['generated_at_utc']}",
        f"- Demo samples: {summary['samples']}",
        f"- Alert accuracy vs expected labels: {summary['alert_accuracy_vs_expected']:.2%}",
        f"- Predicted alert rate: {summary['predicted_alert_rate']:.2%}",
        f"- Mean distress probability: {summary['mean_distress_probability']:.4f}",
        "",
        "## Top Cases",
        "",
    ]
    top = result.sort_values("distress_probability", ascending=False).head(5)
    for _, row in top.iterrows():
        lines.append(
            f"- {row['case_id']}: prob={row['distress_probability']:.4f}, "
            f"score={row['emergency_score']:.2f}, alert={int(row['predicted_alert'])}, "
            f"expected={int(row['expected_alert'])}"
        )
    md_out.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Saved: {csv_out}")
    print(f"Saved: {md_out}")
    print(f"Saved: {json_out}")


if __name__ == "__main__":
    run()
