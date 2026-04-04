import math
import numpy as np
def calculate_scores_heuristic(text: str) -> dict:
    word_count = len(text.split())
    base_score = 4.0
    if word_count > 50:
        base_score = min(10.0, 4.0 + ((word_count - 50) / 30.0))
    scores = {
        "model_the_way": round(min(10.0, base_score + 0.5), 1),
        "inspire_shared_vision": round(min(10.0, base_score), 1),
        "challenge_the_process": round(min(10.0, base_score - 0.5), 1),
        "enable_others_to_act": round(min(10.0, base_score + 0.2), 1),
        "encourage_the_heart": round(min(10.0, base_score), 1)
    }
    scores["overall"] = round(sum(scores.values()) / len(scores), 1)
    return scores
def generate_rule_based_feedback(scores: dict) -> dict:
    overall = scores["overall"]
    if overall >= 8:
        leader_type = "Exemplary Leader (S-LPI)"
    elif overall >= 5:
        leader_type = "Developing Leader"
    else:
        leader_type = "Early Stage Leader"
    return {"leader_type": leader_type}
def analyze_essay(text: str) -> dict:
    if len(text.split()) < 50:
        raise ValueError("Эссе слишком короткое, минимум 50 слов")
    scores = calculate_scores_heuristic(text)
    feedback = generate_rule_based_feedback(scores)
    return {
        "scores": scores,
        "feedback": feedback,
        "meta": {"word_count": len(text.split())},
    }
def get_essay_nlp_result(candidate: dict) -> dict | None:
    essay = candidate.get("essay")
    if not essay:
        return None
    text = essay.get("text", "") if isinstance(essay, dict) else essay
    if not text or len(text.split()) < 50:
        return None
    try:
        return analyze_essay(text)
    except Exception:
        return None
def extract_essay_features(candidate: dict) -> np.ndarray:
    result = get_essay_nlp_result(candidate)
    if result is None:
        return np.zeros(6, dtype=np.float32)
    scores = result["scores"]
    return np.array([
        scores["model_the_way"]        / 10.0,
        scores["inspire_shared_vision"] / 10.0,
        scores["challenge_the_process"] / 10.0,
        scores["enable_others_to_act"]  / 10.0,
        scores["encourage_the_heart"]   / 10.0,
        scores["overall"]               / 10.0,
    ], dtype=np.float32)
