import json
import os
import numpy as np
from typing import Dict, Any, List
from collections import defaultdict
from scipy import stats
from config import FAIRNESS_DIR
def run_fairness_audit(
    candidates: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    assert len(candidates) == len(predictions), "Candidates and predictions must match"
    print("=" * 60)
    print("InVision U — Fairness Audit")
    print("=" * 60)
    audit = {}
    audit["city"] = _audit_by_field(
        candidates, predictions,
        field_path=["personal", "city"],
        field_name="Город",
    )
    audit["school_type"] = _audit_by_field(
        candidates, predictions,
        field_path=["personal", "school_type"],
        field_name="Тип школы",
    )
    audit["has_mentor"] = _audit_by_field(
        candidates, predictions,
        field_path=["personal", "has_mentor"],
        field_name="Наличие ментора",
        transform=lambda x: "Есть ментор" if x else "Нет ментора",
    )
    audit["age_group"] = _audit_by_field(
        candidates, predictions,
        field_path=["personal", "age"],
        field_name="Возрастная группа",
        transform=lambda x: "14-16" if x <= 16 else ("17-18" if x <= 18 else "19+"),
    )
    audit["region"] = _audit_by_field(
        candidates, predictions,
        field_path=["personal", "region"],
        field_name="Регион",
    )
    audit["verdict"] = _overall_verdict(audit)
    print(f"\n{'=' * 60}")
    print(f"VERDICT: {audit['verdict']['status']}")
    print(f"  {audit['verdict']['summary']}")
    print(f"{'=' * 60}")
    return audit
def _audit_by_field(
    candidates: list,
    predictions: list,
    field_path: list,
    field_name: str,
    transform=None,
) -> Dict[str, Any]:
    groups = defaultdict(list)
    for cand, pred in zip(candidates, predictions):
        value = cand
        for key in field_path:
            value = value.get(key, None) if isinstance(value, dict) else None
            if value is None:
                break
        if value is None:
            value = "Unknown"
        elif transform:
            value = transform(value)
        shortlist_prob = pred["probabilities"]["shortlist"]
        groups[str(value)].append(shortlist_prob)
    group_stats = {}
    for group_name, probs in sorted(groups.items()):
        probs_arr = np.array(probs)
        group_stats[group_name] = {
            "count": len(probs),
            "mean_shortlist_prob": float(np.mean(probs_arr)),
            "std_shortlist_prob": float(np.std(probs_arr)),
            "median_shortlist_prob": float(np.median(probs_arr)),
            "shortlist_rate": float(np.mean(probs_arr > 0.5)),
        }
    group_arrays = [np.array(probs) for probs in groups.values() if len(probs) >= 3]
    stat_test = None
    if len(group_arrays) >= 2:
        f_stat, p_value = stats.f_oneway(*group_arrays)
        stat_test = {
            "test": "ANOVA (one-way)",
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
        }
    means = [s["mean_shortlist_prob"] for s in group_stats.values()]
    max_disparity = max(means) - min(means) if means else 0
    result = {
        "field": field_name,
        "groups": group_stats,
        "max_disparity": float(max_disparity),
        "statistical_test": stat_test,
        "has_bias": max_disparity > 0.15 or (stat_test and stat_test["significant"]),
    }
    print(f"\n--- {field_name} ---")
    print(f"{'Группа':<25} {'N':>5} {'Ср. скор':>10} {'% шортлист':>12}")
    print("-" * 55)
    for name, s in group_stats.items():
        print(
            f"{name:<25} {s['count']:>5} "
            f"{s['mean_shortlist_prob']:>10.3f} "
            f"{s['shortlist_rate']:>11.1%}"
        )
    print(f"\nМакс. разброс: {max_disparity:.3f}", end="")
    if stat_test:
        sig = "⚠️ ЗНАЧИМО" if stat_test["significant"] else "✅ не значимо"
        print(f" | ANOVA p={stat_test['p_value']:.4f} ({sig})")
    else:
        print(" | (недостаточно данных для теста)")
    if result["has_bias"]:
        print(f"  ⚠️ ОБНАРУЖЕН ПОТЕНЦИАЛЬНЫЙ BIAS по '{field_name}'")
    return result
def _overall_verdict(audit: Dict[str, Any]) -> Dict[str, str]:
    biased_fields = []
    for key, result in audit.items():
        if key == "verdict":
            continue
        if isinstance(result, dict) and result.get("has_bias"):
            biased_fields.append(result["field"])
    if not biased_fields:
        return {
            "status": "✅ PASSED",
            "summary": (
                "Модель не показывает статистически значимого bias "
                "по демографическим группам. Демографические данные "
                "успешно исключены из скоринговой формулы."
            ),
            "biased_fields": [],
        }
    else:
        return {
            "status": "⚠️ NEEDS REVIEW",
            "summary": (
                f"Обнаружен потенциальный bias по: {', '.join(biased_fields)}. "
                f"Необходимо исследовать косвенные корреляции между "
                f"исключёнными демографическими полями и используемыми фичами."
            ),
            "biased_fields": biased_fields,
        }
def save_fairness_report(audit: Dict[str, Any], path: str = None):
    path = path or os.path.join(FAIRNESS_DIR, "fairness_report.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    report = json.loads(json.dumps(audit, default=str))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nFairness report saved to {path}")
def check_proxy_correlations(
    candidates: List[Dict[str, Any]],
    feature_matrix: np.ndarray,
    feature_names: list,
) -> Dict[str, Any]:
    from config import STRUCTURED_FEATURES
    print(f"\n=== Proxy Correlation Check ===")
    cities = []
    school_types = []
    has_mentors = []
    for c in candidates:
        personal = c.get("personal", {})
        cities.append(personal.get("city", "Unknown"))
        school_types.append(personal.get("school_type", "other"))
        has_mentors.append(1 if personal.get("has_mentor", False) else 0)
    results = {}
    has_mentors = np.array(has_mentors)
    if len(np.unique(has_mentors)) > 1:
        print(f"\nКорреляция фичей с 'наличие ментора':")
        mentor_correlations = {}
        for i, fname in enumerate(feature_names):
            if i < feature_matrix.shape[1]:
                corr = np.corrcoef(feature_matrix[:, i], has_mentors)[0, 1]
                mentor_correlations[fname] = float(corr) if not np.isnan(corr) else 0.0
                if abs(corr) > 0.3:
                    print(f"  ⚠️ {STRUCTURED_FEATURES[i]:35s} r={corr:+.3f}")
        results["mentor_correlations"] = mentor_correlations
    school_groups = defaultdict(list)
    for i, st in enumerate(school_types):
        if i < len(feature_matrix):
            school_groups[st].append(i)
    if len(school_groups) >= 2:
        print(f"\nФичи с значимым различием по типу школы:")
        school_bias = {}
        for fi, fname in enumerate(feature_names):
            if fi < feature_matrix.shape[1]:
                arrays = [
                    feature_matrix[indices, fi]
                    for indices in school_groups.values()
                    if len(indices) >= 3
                ]
                if len(arrays) >= 2:
                    f_stat, p_val = stats.f_oneway(*arrays)
                    if p_val < 0.05:
                        school_bias[fname] = float(p_val)
                        print(f"  ⚠️ {fname:35s} p={p_val:.4f}")
        results["school_type_anova"] = school_bias
    if not results.get("mentor_correlations") and not results.get("school_type_anova"):
        print("  ✅ Нет значимых proxy-корреляций обнаружено")
    return results
if __name__ == "__main__":
    import sys
    from trainer import train
    from scorer import CandidateScorer
    from feature_extractor import extract_batch
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else "../data/synthetic_dataset.json"
    training_results = train(dataset_path)
    with open(dataset_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)
    scorer = CandidateScorer(X_background=training_results["X_train"])
    predictions = scorer.score_batch(candidates)
    audit = run_fairness_audit(candidates, predictions)
    save_fairness_report(audit)
    X = extract_batch(candidates)
    from config import STRUCTURED_FEATURES
    proxy = check_proxy_correlations(candidates, X, STRUCTURED_FEATURES)
