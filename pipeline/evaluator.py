import json
import os
import numpy as np
from typing import Dict, Any
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize
from config import LABEL_NAMES, METRICS_DIR
from trainer import (
    train_baseline_gpa,
    train_baseline_rules,
    train_baseline_logreg,
)
def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    metrics = _compute_metrics(y_test, y_pred, y_proba, "XGBoost")
    return metrics
def evaluate_baselines(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> Dict[str, Dict[str, Any]]:
    results = {}
    print("\n--- Baseline 1: GPA Ranking ---")
    y_pred_gpa = train_baseline_gpa(X_test, y_test)
    results["GPA Ranking"] = _compute_metrics(y_test, y_pred_gpa, None, "GPA Ranking")
    print("\n--- Baseline 2: Rule-Based ---")
    y_pred_rules = train_baseline_rules(X_test, y_test)
    results["Rule-Based"] = _compute_metrics(y_test, y_pred_rules, None, "Rule-Based")
    print("\n--- Baseline 3: Logistic Regression ---")
    y_pred_lr = train_baseline_logreg(X_train, y_train, X_test)
    results["Logistic Regression"] = _compute_metrics(
        y_test, y_pred_lr, None, "Logistic Regression"
    )
    return results
def comparison_table(
    model_metrics: Dict[str, Any],
    baseline_metrics: Dict[str, Dict[str, Any]],
) -> str:
    lines = []
    lines.append("")
    lines.append("=" * 75)
    lines.append("MODEL COMPARISON")
    lines.append("=" * 75)
    header = f"{'Model':<25} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}"
    lines.append(header)
    lines.append("-" * 75)
    for name, metrics in baseline_metrics.items():
        line = (
            f"{name:<25} "
            f"{metrics['accuracy']:>10.4f} "
            f"{metrics['precision_macro']:>10.4f} "
            f"{metrics['recall_macro']:>10.4f} "
            f"{metrics['f1_macro']:>10.4f}"
        )
        lines.append(line)
    lines.append("-" * 75)
    line = (
        f"{'XGBoost (Ours)':<25} "
        f"{model_metrics['accuracy']:>10.4f} "
        f"{model_metrics['precision_macro']:>10.4f} "
        f"{model_metrics['recall_macro']:>10.4f} "
        f"{model_metrics['f1_macro']:>10.4f}"
    )
    lines.append(line)
    lines.append("=" * 75)
    if "auc_roc" in model_metrics:
        lines.append(f"\nXGBoost AUC-ROC (one-vs-rest): {model_metrics['auc_roc']:.4f}")
    table = "\n".join(lines)
    print(table)
    return table
def format_confusion_matrix(y_test: np.ndarray, y_pred: np.ndarray, title: str = "") -> str:
    cm = confusion_matrix(y_test, y_pred)
    lines = []
    if title:
        lines.append(f"\n--- Confusion Matrix: {title} ---")
    lines.append(f"\n{'':>15} {'Pred reject':>13} {'Pred maybe':>13} {'Pred shortlist':>15}")
    for i, label in enumerate(LABEL_NAMES):
        row = f"  True {label:<10}"
        for j in range(3):
            row += f"{cm[i][j]:>13}"
        lines.append(row)
    result = "\n".join(lines)
    print(result)
    return result
def error_analysis(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    raw_candidates: list = None,
    test_indices: list = None,
) -> Dict[str, Any]:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    errors = []
    for i in range(len(y_test)):
        if y_pred[i] != y_test[i]:
            error = {
                "index": i,
                "true_label": LABEL_NAMES[y_test[i]],
                "predicted_label": LABEL_NAMES[y_pred[i]],
                "confidence": float(np.max(y_proba[i])),
                "probabilities": {
                    LABEL_NAMES[j]: float(y_proba[i][j]) for j in range(3)
                },
            }
            if raw_candidates and test_indices:
                cand = raw_candidates[test_indices[i]]
                error["candidate_id"] = cand.get("id", "unknown")
                error["candidate_name"] = cand.get("personal", {}).get("name", "unknown")
            errors.append(error)
    error_types = {}
    for e in errors:
        key = f"{e['true_label']} → {e['predicted_label']}"
        error_types[key] = error_types.get(key, 0) + 1
    total_errors = len(errors)
    total_samples = len(y_test)
    print(f"\n=== Error Analysis ===")
    print(f"Total errors: {total_errors}/{total_samples} ({total_errors / total_samples:.1%})")
    print(f"\nError breakdown:")
    for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
        print(f"  {error_type}: {count}")
    correct_mask = y_pred == y_test
    if correct_mask.any():
        correct_confidence = np.max(y_proba[correct_mask], axis=1)
        low_confidence_idx = np.argsort(correct_confidence)[:5]
        print(f"\nMost uncertain correct predictions (borderline cases):")
        for idx in low_confidence_idx:
            real_idx = np.where(correct_mask)[0][idx]
            print(
                f"  True: {LABEL_NAMES[y_test[real_idx]]}, "
                f"Confidence: {np.max(y_proba[real_idx]):.3f}, "
                f"Probs: {dict(zip(LABEL_NAMES, y_proba[real_idx].round(3)))}"
            )
    return {
        "total_errors": total_errors,
        "total_samples": total_samples,
        "error_rate": total_errors / total_samples,
        "error_types": error_types,
        "errors": errors[:10],
    }
def save_evaluation_report(
    model_metrics: dict,
    baseline_metrics: dict,
    cv_results: dict,
    error_report: dict,
    path: str = None,
):
    path = path or os.path.join(METRICS_DIR, "evaluation_report.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    report = {
        "model_metrics": model_metrics,
        "baseline_metrics": baseline_metrics,
        "cross_validation": cv_results,
        "error_analysis": {
            "total_errors": error_report["total_errors"],
            "total_samples": error_report["total_samples"],
            "error_rate": error_report["error_rate"],
            "error_types": error_report["error_types"],
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nEvaluation report saved to {path}")
def _compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray = None,
    model_name: str = "",
) -> Dict[str, Any]:
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    metrics = {
        "model": model_name,
        "accuracy": float(acc),
        "precision_macro": float(prec),
        "recall_macro": float(rec),
        "f1_macro": float(f1),
    }
    if y_proba is not None and len(np.unique(y_true)) > 1:
        try:
            y_bin = label_binarize(y_true, classes=[0, 1, 2])
            auc = roc_auc_score(y_bin, y_proba, multi_class="ovr", average="macro")
            metrics["auc_roc"] = float(auc)
        except ValueError:
            metrics["auc_roc"] = None
    report = classification_report(
        y_true, y_pred,
        target_names=LABEL_NAMES,
        output_dict=True,
        zero_division=0,
    )
    metrics["per_class"] = {
        label: {
            "precision": report[label]["precision"],
            "recall": report[label]["recall"],
            "f1": report[label]["f1-score"],
            "support": report[label]["support"],
        }
        for label in LABEL_NAMES
    }
    print(f"\n[{model_name}] Acc={acc:.4f} | P={prec:.4f} | R={rec:.4f} | F1={f1:.4f}")
    return metrics
def evaluate(training_results: dict) -> dict:
    model = training_results["model"]
    X_train = training_results["X_train"]
    X_test = training_results["X_test"]
    y_train = training_results["y_train"]
    y_test = training_results["y_test"]
    cv_results = training_results["cv_results"]
    print("\n" + "=" * 60)
    print("InVision U — Model Evaluation")
    print("=" * 60)
    print("\n--- Our Model: XGBoost ---")
    model_metrics = evaluate_model(model, X_test, y_test)
    y_pred = model.predict(X_test)
    format_confusion_matrix(y_test, y_pred, "XGBoost")
    baseline_metrics = evaluate_baselines(X_train, y_train, X_test, y_test)
    comparison_table(model_metrics, baseline_metrics)
    error_report = error_analysis(model, X_test, y_test)
    save_evaluation_report(model_metrics, baseline_metrics, cv_results, error_report)
    return {
        "model_metrics": model_metrics,
        "baseline_metrics": baseline_metrics,
        "error_report": error_report,
    }
if __name__ == "__main__":
    from trainer import train
    import sys
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else "../data/synthetic_dataset.json"
    training_results = train(dataset_path)
    evaluate(training_results)
