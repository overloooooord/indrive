import os
import json
import numpy as np
from typing import Dict, Any, List
import shap
from config import STRUCTURED_FEATURES, SLPI_FEATURES, ESSAY_FEATURES, FEATURE_DESCRIPTIONS, FEATURE_GROUPS, LABEL_NAMES, SHAP_PLOTS_DIR
_ALL_FEATURE_NAMES = list(STRUCTURED_FEATURES) + ["fp_" + f for f in SLPI_FEATURES] + list(ESSAY_FEATURES)
class CandidateExplainer:
    def __init__(self, model, X_background: np.ndarray = None):
        self.model         = model
        self.feature_names = _ALL_FEATURE_NAMES
        self.X_background  = X_background
        bg = X_background
        if bg is not None and len(bg) > 200:
            idx = np.random.RandomState(42).choice(len(bg), 200, replace=False)
            bg  = bg[idx]
        self.explainer = shap.TreeExplainer(model, data=bg)
    def explain(
        self, feature_vector: np.ndarray, predicted_class: int = None, top_k: int = 5
    ) -> Dict[str, Any]:
        X = feature_vector.reshape(1, -1)
        if predicted_class is None:
            predicted_class = int(self.model.predict(X)[0])
        if self.explainer is not None:
            return self._explain_shap(feature_vector, predicted_class, top_k)
        return self._explain_fallback(feature_vector, predicted_class, top_k)
    def _explain_shap(self, feature_vector, predicted_class, top_k):
        X = feature_vector.reshape(1, -1)
        shap_values = self.explainer.shap_values(X)
        if isinstance(shap_values, list):
            sv = shap_values[predicted_class][0]
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            sv = shap_values[0, :, predicted_class]
        else:
            sv = shap_values[0]
        return self._format_explanation(sv, feature_vector, predicted_class, top_k)
    def _explain_fallback(self, feature_vector, predicted_class, top_k):
        importances = (
            self.model.feature_importances_
            if hasattr(self.model, "feature_importances_")
            else np.ones(len(feature_vector)) / len(feature_vector)
        )
        means = self.X_background.mean(axis=0) if self.X_background is not None else np.zeros(len(feature_vector))
        stds  = self.X_background.std(axis=0)  if self.X_background is not None else np.ones(len(feature_vector))
        stds  = np.where(stds == 0, 1, stds)
        sv    = importances * (feature_vector - means) / stds
        return self._format_explanation(sv, feature_vector, predicted_class, top_k)
    def _format_explanation(self, sv, feature_vector, predicted_class, top_k):
        impacts = [
            {
                "feature":       name,
                "description":   FEATURE_DESCRIPTIONS.get(name, name),
                "shap_value":    float(sv[i]),
                "feature_value": float(feature_vector[i]),
                "impact":        "positive" if sv[i] > 0 else "negative",
            }
            for i, name in enumerate(self.feature_names)
        ]
        impacts.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return {
            "predicted_class":      LABEL_NAMES[predicted_class],
            "top_positive_factors": [f for f in impacts if f["shap_value"] > 0][:top_k],
            "top_negative_factors": [f for f in impacts if f["shap_value"] < 0][:top_k],
            "all_shap_values":      dict(zip(self.feature_names, sv.tolist())),
            "method":               "shap" if self.explainer is not None else "feature_importance_fallback",
        }
    def explain_readable(self, feature_vector: np.ndarray, predicted_class: int = None) -> str:
        exp   = self.explain(feature_vector, predicted_class)
        lines = [f"Рекомендация: {exp['predicted_class'].upper()}", ""]
        if exp["top_positive_factors"]:
            lines.append("Сильные стороны:")
            for f in exp["top_positive_factors"]:
                lines.append(
                    f"  ✅ {f['description']} "
                    f"(значение: {f['feature_value']:.2f}, вклад: +{f['shap_value']:.3f})"
                )
        if exp["top_negative_factors"]:
            lines.append("\nСлабые стороны:")
            for f in exp["top_negative_factors"]:
                lines.append(
                    f"  ⚠️  {f['description']} "
                    f"(значение: {f['feature_value']:.2f}, вклад: {f['shap_value']:.3f})"
                )
        return "\n".join(lines)
    def global_importance(self, X: np.ndarray) -> List[Dict[str, Any]]:
        if self.explainer is not None:
            shap_values = self.explainer.shap_values(X)
            if isinstance(shap_values, list):
                mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                mean_abs = np.abs(shap_values).mean(axis=(0, 2))
            else:
                mean_abs = np.abs(shap_values).mean(axis=0)
        else:
            mean_abs = (
                self.model.feature_importances_
                if hasattr(self.model, "feature_importances_")
                else np.ones(len(self.feature_names)) / len(self.feature_names)
            )
        result = [
            {
                "feature":       name,
                "description":   FEATURE_DESCRIPTIONS.get(name, name),
                "mean_abs_shap": float(mean_abs[i]),
            }
            for i, name in enumerate(self.feature_names)
        ]
        result.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
        return result
    def save_explanation(self, explanation: dict, candidate_id: str, path: str = None):
        path = path or os.path.join(SHAP_PLOTS_DIR, f"explanation_{candidate_id}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(explanation, f, indent=2, ensure_ascii=False)
def ablation_study(
    model_class, model_params: dict,
    X_train: np.ndarray, y_train: np.ndarray,
    X_test: np.ndarray,  y_test: np.ndarray,
) -> Dict[str, float]:
    from sklearn.metrics import f1_score as sk_f1
    full_model = model_class(**model_params)
    full_model.fit(X_train, y_train)
    full_f1 = sk_f1(y_test, full_model.predict(X_test), average="macro")
    results = {"Full model": float(full_f1)}
    print(f"\n=== Ablation Study ===\nFull model F1: {full_f1:.4f}\n")
    for group_name, indices in FEATURE_GROUPS.items():
        remaining  = [i for i in range(X_train.shape[1]) if i not in indices]
        ablated    = model_class(**model_params)
        ablated.fit(X_train[:, remaining], y_train)
        ablated_f1 = sk_f1(y_test, ablated.predict(X_test[:, remaining]), average="macro")
        drop       = full_f1 - ablated_f1
        results[f"Without {group_name}"] = float(ablated_f1)
        print(f"  Without {group_name:15s}: F1 = {ablated_f1:.4f}  (drop: {drop:+.4f})")
    return results
if __name__ == "__main__":
    import sys
    from trainer import train
    from feature_extractor import extract_features
    if len(sys.argv) < 2:
        print("Usage: python explainer.py <dataset.json> [candidate.json]")
        sys.exit(1)
    results = train(sys.argv[1])
    explainer = CandidateExplainer(results["model"], results["X_train"])
    if len(sys.argv) >= 3:
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            candidate = json.load(f)
        vector = extract_features(candidate)
        print("\n" + explainer.explain_readable(vector))
    else:
        importance = explainer.global_importance(results["X_train"])
        print("\n=== Global Feature Importance ===")
        for i, feat in enumerate(importance):
            bar = "█" * int(feat["mean_abs_shap"] * 50)
            print(f"  {i+1:2d}. {feat['description']:45s} {bar} ({feat['mean_abs_shap']:.4f})")
