import json
import os
import pickle
import numpy as np
from typing import Dict, Any, Optional
from config import (
    LABEL_NAMES, MODEL_PATH, FEATURE_DESCRIPTIONS,
    STAGE_WEIGHTS, THREE_STAGE_MODEL_PATH, XGBOOST_PARAMS,
)
from feature_extractor import (
    extract_features, extract_features_dict,
    extract_structural_features, extract_slpi_features,
    extract_essay_features,
)
from trainer import load_model
from explainer import CandidateExplainer
class CandidateScorer:
    def __init__(self, model_path: str = None, X_background: np.ndarray = None):
        self.model     = load_model(model_path or MODEL_PATH)
        self.explainer = CandidateExplainer(self.model, X_background)
    def score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        feature_vector = extract_features(candidate)
        feature_dict   = extract_features_dict(candidate)
        X             = feature_vector.reshape(1, -1)
        probabilities = self.model.predict_proba(X)[0]
        predicted_cls = int(np.argmax(probabilities))
        confidence    = float(probabilities[predicted_cls])
        essay_nlp = None
        essay_raw = candidate.get("essay", "")
        essay_text = essay_raw.get("text", "") if isinstance(essay_raw, dict) else (essay_raw or "")
        if essay_text and len(essay_text.split()) >= 50:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
                from nlp.nlp_model import get_essay_nlp_result
                essay_nlp = get_essay_nlp_result(candidate)
            except Exception:
                essay_nlp = None
        explanation = self.explainer.explain(feature_vector, predicted_cls)
        radar       = self._build_radar(candidate)
        flags       = self._build_flags(feature_dict, essay_nlp)
        trajectory  = self._build_trajectory(candidate)
        return {
            "candidate_id": candidate.get("id", "unknown"),
            "prediction":   LABEL_NAMES[predicted_cls],
            "confidence":   confidence,
            "probabilities": {LABEL_NAMES[i]: float(probabilities[i]) for i in range(3)},
            "explanation": {
                "top_positive_factors": [
                    {
                        "description": f["description"],
                        "value":       f["feature_value"],
                        "impact":      round(f["shap_value"], 4),
                    }
                    for f in explanation["top_positive_factors"]
                ],
                "top_negative_factors": [
                    {
                        "description": f["description"],
                        "value":       f["feature_value"],
                        "impact":      round(f["shap_value"], 4),
                    }
                    for f in explanation["top_negative_factors"]
                ],
            },
            "radar":      radar,
            "flags":      flags,
            "trajectory": trajectory,
            "feature_values": {
                FEATURE_DESCRIPTIONS.get(k, k): round(v, 4)
                for k, v in feature_dict.items()
            },
        }
    def score_batch(self, candidates: list) -> list:
        return [self.score(c) for c in candidates]
    def rank(self, candidates: list) -> list:
        scored = self.score_batch(candidates)
        scored.sort(key=lambda x: x["probabilities"]["shortlist"], reverse=True)
        for i, s in enumerate(scored):
            s["rank"]             = i + 1
            s["total_candidates"] = len(scored)
        return scored
    def _build_radar(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        meta     = candidate.get("bot_metadata", {})
        reliable = meta.get("fingerprint_reliable", False)
        display  = meta.get("fingerprint_display", {})
        if not reliable or not display:
            return {
                "model_the_way":     None,
                "inspire_vision":    None,
                "challenge_process": None,
                "enable_others":     None,
                "encourage_heart":   None,
                "status":            "pending — scenario_engine.py not yet deployed",
            }
        return {
            "model_the_way":     display.get("model_the_way"),
            "inspire_vision":    display.get("inspire_vision"),
            "challenge_process": display.get("challenge_process"),
            "enable_others":     display.get("enable_others"),
            "encourage_heart":   display.get("encourage_heart"),
            "status":            "ok",
        }
    def _build_flags(self, f: Dict[str, float], essay_nlp: Optional[dict] = None) -> Dict[str, Any]:
        if essay_nlp is not None:
            overall = essay_nlp["scores"]["overall"]
            if overall >= 6.5:
                coherence_status, coherence_detail = "ok", f"Высокая когерентность эссе (overall {overall}/10)"
            elif overall >= 4.0:
                coherence_status, coherence_detail = "warning", f"Средняя когерентность эссе (overall {overall}/10)"
            else:
                coherence_status, coherence_detail = "alert", f"Низкая когерентность эссе (overall {overall}/10)"
            coherence_flag = {"status": coherence_status, "label": "Когерентность профиля", "detail": coherence_detail}
        else:
            coherence_flag = {"status": "pending", "label": "Когерентность профиля", "detail": "Эссе не предоставлено"}
        flags: Dict[str, Any] = {
            "coherence": coherence_flag,
            "ai_detection": {
                "status": "pending",
                "label":  "AI-детекция эссе",
                "detail": "Будет рассчитано AI-детектором",
            },
        }
        if f["f_project_count"] == 0:
            flags["no_projects"] = {
                "status": "warning",
                "label":  "Нет проектов",
                "detail": "Кандидат не указал ни одного проекта",
            }
        if f["f_founder_ratio"] == 0 and f["f_project_count"] > 0:
            flags["low_initiative"] = {
                "status": "info",
                "label":  "Низкая инициативность",
                "detail": "Участвовал в проектах, но не основал ни одного",
            }
        if f["f_role_progression"] > 1 and f["f_skill_diversity_growth"] >= 3:
            flags["strong_trajectory"] = {
                "status": "positive",
                "label":  "Сильная траектория роста",
                "detail": "Выраженный рост ролей и навыков",
            }
        return flags
    def _build_trajectory(self, candidate: Dict[str, Any]) -> list:
        events = []
        for p in candidate.get("experience", {}).get("projects", []):
            events.append({
                "year":     p.get("year", 0),
                "type":     "project",
                "title":    p.get("name", "Без названия"),
                "role":     p.get("role", "participant"),
                "category": p.get("type", "other"),
            })
        for o in candidate.get("education", {}).get("olympiads", []):
            events.append({
                "year":  o.get("year", 0),
                "type":  "olympiad",
                "title": f"Олимпиада: {o.get('subject', '?')}",
                "level": o.get("level", "?"),
                "prize": o.get("prize", False),
            })
        events.sort(key=lambda e: e["year"])
        return events
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scorer.py <candidate.json> [model.pkl]")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        candidate = json.load(f)
    model_path = sys.argv[2] if len(sys.argv) > 2 else None
    scorer = CandidateScorer(model_path)
    result = scorer.score(candidate)
    print(f"\n{'=' * 60}")
    print(f"CANDIDATE: {candidate.get('personal', {}).get('name', 'Unknown')}")
    print(f"{'=' * 60}")
    print(f"\nПредсказание: {result['prediction'].upper()}")
    print(f"Уверенность:  {result['confidence']:.1%}")
    print("\nВероятности:")
    for label, prob in result["probabilities"].items():
        bar = "█" * int(prob * 30)
        print(f"  {label:12s} {bar} {prob:.1%}")
    print("\n✅ Сильные стороны:")
    for f in result["explanation"]["top_positive_factors"]:
        print(f"   {f['description']} (+{f['impact']:.4f})")
    print("\n⚠️  Слабые стороны:")
    for f in result["explanation"]["top_negative_factors"]:
        print(f"   {f['description']} ({f['impact']:.4f})")
    print("\nLeadership Fingerprint (SLPI):")
    radar = result["radar"]
    print(f"  Status: {radar.get('status')}")
    for dim in ("model_the_way", "inspire_vision", "challenge_process", "enable_others", "encourage_heart"):
        val = radar.get(dim)
        if val is not None:
            print(f"  {dim:25s} {'█' * int(val * 20)} {val:.2f}")
        else:
            print(f"  {dim:25s} pending")
    output_path = f"outputs/score_{result['candidate_id']}.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nFull result → {output_path}")
class ThreeStageScorer:
    MIN_FINGERPRINT_SAMPLES = 10
    MIN_ESSAY_SAMPLES = 10
    def __init__(self):
        self.model_structural  = None
        self.model_fingerprint = None
        self.model_essay       = None
        self.explainer         = None
    def fit(self, candidates: list, labels: np.ndarray) -> "ThreeStageScorer":
        from xgboost import XGBClassifier
        X_struct = np.array(
            [extract_structural_features(c) for c in candidates], dtype=np.float32
        )
        self.model_structural = XGBClassifier(**XGBOOST_PARAMS)
        self.model_structural.fit(X_struct, labels, verbose=False)
        self.explainer = CandidateExplainer(self.model_structural, X_struct)
        reliable_mask = np.array([
            c.get("bot_metadata", {}).get("fingerprint_reliable", False)
            for c in candidates
        ])
        n_reliable = int(reliable_mask.sum())
        if n_reliable >= self.MIN_FINGERPRINT_SAMPLES:
            X_fp = np.array(
                [extract_slpi_features(c) for c, r in zip(candidates, reliable_mask) if r],
                dtype=np.float32,
            )
            y_fp = labels[reliable_mask]
            self.model_fingerprint = XGBClassifier(**XGBOOST_PARAMS)
            self.model_fingerprint.fit(X_fp, y_fp, verbose=False)
            print(f"  Stage 2 trained on {n_reliable} candidates with reliable fingerprint.")
        else:
            print(
                f"  [WARN] Stage 2 not trained — only {n_reliable} candidates with "
                f"reliable fingerprint (need ≥ {self.MIN_FINGERPRINT_SAMPLES})."
            )
        essay_mask = np.array([
            bool(c.get("essay", {}).get("text", "") if isinstance(c.get("essay"), dict) else c.get("essay"))
            for c in candidates
        ])
        n_essay = int(essay_mask.sum())
        if n_essay >= self.MIN_ESSAY_SAMPLES:
            X_essay = np.array(
                [extract_essay_features(c) for c, has_essay in zip(candidates, essay_mask) if has_essay],
                dtype=np.float32,
            )
            y_essay = labels[essay_mask]
            self.model_essay = XGBClassifier(**XGBOOST_PARAMS)
            self.model_essay.fit(X_essay, y_essay, verbose=False)
            print(f"  Stage 3 trained on {n_essay} candidates with essays.")
        else:
            print(
                f"  [WARN] Stage 3 not trained — only {n_essay} candidates with "
                f"essays (need ≥ {self.MIN_ESSAY_SAMPLES})."
            )
        return self
    def score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        struct_vec = extract_structural_features(candidate)
        feature_dict = extract_features_dict(candidate)
        prob_struct = self.model_structural.predict_proba(
            struct_vec.reshape(1, -1)
        )[0]
        stage_proba = {"structural": prob_struct}
        meta = candidate.get("bot_metadata", {})
        fingerprint_reliable = meta.get("fingerprint_reliable", False)
        if self.model_fingerprint is not None and fingerprint_reliable:
            X_fp = extract_slpi_features(candidate).reshape(1, -1)
            stage_proba["fingerprint"] = self.model_fingerprint.predict_proba(X_fp)[0]
        essay_nlp = None
        essay_raw = candidate.get("essay", "")
        essay_text = essay_raw.get("text", "") if isinstance(essay_raw, dict) else (essay_raw or "")
        if essay_text and len(essay_text.split()) >= 50:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
                from nlp.nlp_model import get_essay_nlp_result
                essay_nlp = get_essay_nlp_result(candidate)
            except Exception:
                essay_nlp = None
        if self.model_essay is not None and essay_nlp is not None:
            X_essay = extract_essay_features(candidate).reshape(1, -1)
            stage_proba["essay"] = self.model_essay.predict_proba(X_essay)[0]
        final_proba = self._combine_proba(stage_proba)
        predicted_cls = int(np.argmax(final_proba))
        confidence = float(final_proba[predicted_cls])
        explanation = self.explainer.explain(struct_vec, predicted_cls)
        return {
            "candidate_id": candidate.get("id", "unknown"),
            "prediction":   LABEL_NAMES[predicted_cls],
            "confidence":   confidence,
            "probabilities": {
                LABEL_NAMES[i]: float(final_proba[i]) for i in range(3)
            },
            "stage_scores": {
                stage: {LABEL_NAMES[i]: round(float(p[i]), 4) for i in range(3)}
                for stage, p in stage_proba.items()
            },
            "weights_used": {
                stage: round(STAGE_WEIGHTS.get(stage, 0.0) / sum(
                    STAGE_WEIGHTS[s] for s in stage_proba
                ), 4)
                for stage in stage_proba
            },
            "explanation": {
                "top_positive_factors": [
                    {
                        "description": f["description"],
                        "value":       f["feature_value"],
                        "impact":      round(f["shap_value"], 4),
                    }
                    for f in explanation["top_positive_factors"]
                ],
                "top_negative_factors": [
                    {
                        "description": f["description"],
                        "value":       f["feature_value"],
                        "impact":      round(f["shap_value"], 4),
                    }
                    for f in explanation["top_negative_factors"]
                ],
            },
            "radar":      self._build_radar(candidate),
            "flags":      self._build_flags(feature_dict, essay_nlp),
            "trajectory": self._build_trajectory(candidate),
            "feature_values": {
                FEATURE_DESCRIPTIONS.get(k, k): round(v, 4)
                for k, v in feature_dict.items()
            },
        }
    def score_batch(self, candidates: list) -> list:
        return [self.score(c) for c in candidates]
    def rank(self, candidates: list) -> list:
        scored = self.score_batch(candidates)
        scored.sort(key=lambda x: x["probabilities"]["shortlist"], reverse=True)
        for i, s in enumerate(scored):
            s["rank"]             = i + 1
            s["total_candidates"] = len(scored)
        return scored
    def save(self, path: str = None) -> None:
        path = path or THREE_STAGE_MODEL_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "model_structural":  self.model_structural,
            "model_fingerprint": self.model_fingerprint,
            "model_essay":       self.model_essay,
        }
        with open(path, "wb") as f:
            pickle.dump(payload, f)
        print(f"ThreeStageScorer saved to {path}")
    @classmethod
    def load(cls, path: str = None) -> "ThreeStageScorer":
        path = path or THREE_STAGE_MODEL_PATH
        with open(path, "rb") as f:
            payload = pickle.load(f)
        scorer = cls()
        scorer.model_structural  = payload["model_structural"]
        scorer.model_fingerprint = payload.get("model_fingerprint")
        scorer.model_essay       = payload.get("model_essay")
        if scorer.model_structural is not None:
            scorer.explainer = CandidateExplainer(scorer.model_structural)
        return scorer
    def _combine_proba(self, stage_proba: Dict[str, np.ndarray]) -> np.ndarray:
        total_weight = sum(STAGE_WEIGHTS[s] for s in stage_proba)
        combined = sum(
            (STAGE_WEIGHTS[s] / total_weight) * stage_proba[s]
            for s in stage_proba
        )
        return combined
    def _build_radar(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        meta     = candidate.get("bot_metadata", {})
        reliable = meta.get("fingerprint_reliable", False)
        display  = meta.get("fingerprint_display", {})
        if not reliable or not display:
            return {
                "model_the_way":     None,
                "inspire_vision":    None,
                "challenge_process": None,
                "enable_others":     None,
                "encourage_heart":   None,
                "status":            "pending — scenario_engine.py not yet deployed",
            }
        return {
            "model_the_way":     display.get("model_the_way"),
            "inspire_vision":    display.get("inspire_vision"),
            "challenge_process": display.get("challenge_process"),
            "enable_others":     display.get("enable_others"),
            "encourage_heart":   display.get("encourage_heart"),
            "status":            "ok",
        }
    def _build_flags(self, f: Dict[str, float], essay_nlp: Optional[dict] = None) -> Dict[str, Any]:
        if essay_nlp is not None:
            overall = essay_nlp["scores"]["overall"]
            if overall >= 6.5:
                coherence_status, coherence_detail = "ok", f"Высокая когерентность эссе (overall {overall}/10)"
            elif overall >= 4.0:
                coherence_status, coherence_detail = "warning", f"Средняя когерентность эссе (overall {overall}/10)"
            else:
                coherence_status, coherence_detail = "alert", f"Низкая когерентность эссе (overall {overall}/10)"
            coherence_flag = {"status": coherence_status, "label": "Когерентность профиля", "detail": coherence_detail}
        else:
            coherence_flag = {"status": "pending", "label": "Когерентность профиля", "detail": "Эссе не предоставлено"}
        flags: Dict[str, Any] = {
            "coherence": coherence_flag,
            "ai_detection": {
                "status": "pending",
                "label":  "AI-детекция эссе",
                "detail": "Будет рассчитано AI-детектором",
            },
        }
        if f["f_project_count"] == 0:
            flags["no_projects"] = {
                "status": "warning",
                "label":  "Нет проектов",
                "detail": "Кандидат не указал ни одного проекта",
            }
        if f["f_founder_ratio"] == 0 and f["f_project_count"] > 0:
            flags["low_initiative"] = {
                "status": "info",
                "label":  "Низкая инициативность",
                "detail": "Участвовал в проектах, но не основал ни одного",
            }
        if f["f_role_progression"] > 1 and f["f_skill_diversity_growth"] >= 3:
            flags["strong_trajectory"] = {
                "status": "positive",
                "label":  "Сильная траектория роста",
                "detail": "Выраженный рост ролей и навыков",
            }
        return flags
    def _build_trajectory(self, candidate: Dict[str, Any]) -> list:
        events = []
        for p in candidate.get("experience", {}).get("projects", []):
            events.append({
                "year":     p.get("year", 0),
                "type":     "project",
                "title":    p.get("name", "Без названия"),
                "role":     p.get("role", "participant"),
                "category": p.get("type", "other"),
            })
        for o in candidate.get("education", {}).get("olympiads", []):
            events.append({
                "year":  o.get("year", 0),
                "type":  "olympiad",
                "title": f"Олимпиада: {o.get('subject', '?')}",
                "level": o.get("level", "?"),
                "prize": o.get("prize", False),
            })
        events.sort(key=lambda e: e["year"])
        return events
