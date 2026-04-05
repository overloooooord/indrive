import math
import numpy as np
from deep_translator import GoogleTranslator
from transformers import pipeline as hf_pipeline

# Lazy-loaded classifier — loads once on first call
_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = hf_pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
            use_fast=False,
        )
    return _classifier


def translate_to_english(text: str) -> str:
    chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
    translated = [GoogleTranslator(source='ru', target='en').translate(chunk) for chunk in chunks]
    return " ".join(translated)


COMPETENCY_PAIRS = {
    "model_the_way": (
        "the author gives a concrete example where they personally demonstrated their values and served as a role model for others",
        "the author only lists abstract qualities without backing them up with real stories from their life"
    ),
    "inspire_shared_vision": (
        "the author describes how they convinced specific people to join their idea or project and inspired others toward a shared goal",
        "the author writes only about personal plans without mentioning how they involved other people"
    ),
    "challenge_the_process": (
        "the author describes a specific situation where they changed the usual way of doing something or proposed an unconventional solution",
        "the author followed a standard path and does not describe cases where they changed rules or experimented"
    ),
    "enable_others_to_act": (
        "the author describes a specific case where they helped another person grow take responsibility or achieve a result",
        "the author does not mention cases of helping others and writes only about personal achievements"
    ),
    "encourage_the_heart": (
        "the author describes a moment where they publicly recognized someone's contribution thanked the team or celebrated shared success",
        "the author does not mention recognizing others and does not describe shared achievements"
    ),
}

MIN_LOG, MAX_LOG = 0.0, 5.0


def calculate_scores_zeroshot(text: str) -> dict:
    text_en = translate_to_english(text)
    classifier = _get_classifier()
    scores = {}

    for comp, (positive, negative) in COMPETENCY_PAIRS.items():
        result = classifier(
            text_en,
            candidate_labels=[positive, negative],
            hypothesis_template="In this text: {}",
        )
        pos_idx = result["labels"].index(positive)
        pos_score = result["scores"][pos_idx]
        neg_score = result["scores"][1 - pos_idx]

        ratio = pos_score / max(neg_score, 0.001)
        log_score = math.log(ratio)
        normalized = max(0, min(1, (log_score - MIN_LOG) / (MAX_LOG - MIN_LOG)))
        scores[comp] = round(normalized * 10, 1)

    practices = list(COMPETENCY_PAIRS.keys())
    scores["overall"] = round(sum(scores[p] for p in practices) / len(practices), 1)
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

    scores = calculate_scores_zeroshot(text)
    feedback = generate_rule_based_feedback(scores)

    return {
        "scores": scores,
        "feedback": feedback,
        "meta": {"word_count": len(text.split())},
    }


def get_essay_nlp_result(candidate: dict) -> dict | None:
    """
    Returns analyze_essay() output for the candidate's essay, or None if no essay.
    Handles both candidate["essay"] as string and as {"text": str}.
    """
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
    """
    Returns 6-dim essay NLP feature vector matching ESSAY_FEATURES in config:
      [model_the_way, inspire_shared_vision, challenge_the_process,
       enable_others_to_act, encourage_the_heart, overall]
    All values normalized to 0–1 (raw scores are 0–10).
    Returns zeros if essay is absent or too short.
    """
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


if __name__ == "__main__":
    print("=== Essay Leadership Analyzer ===")
    text = input("Enter essay:\n")
    try:
        result = analyze_essay(text)
        print(f"\nOverall score: {result['scores']['overall']}/10")
        print(f"Leader type: {result['feedback']['leader_type']}")
        print(f"\nBy practice:")
        for k, v in result["scores"].items():
            if k != "overall":
                print(f"  {k}: {v}/10")
    except Exception as e:
        print(f"\nError: {e}")
