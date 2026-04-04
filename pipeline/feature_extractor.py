import numpy as np
from typing import Dict, List, Any
from config import (
    OLYMPIAD_LEVEL_MAP,
    PROJECT_ROLE_MAP,
    STRUCTURED_FEATURES,
    SLPI_FEATURES,
    CURRENT_YEAR,
)
def extract_features(candidate: Dict[str, Any]) -> np.ndarray:
    structural = extract_structural_features(candidate)
    slpi       = extract_slpi_features(candidate)
    essay      = extract_essay_features(candidate)
    return np.concatenate([structural, slpi, essay]).astype(np.float32)
def extract_features_dict(candidate: Dict[str, Any]) -> Dict[str, float]:
    return _build_feature_dict(candidate)
def extract_structural_features(candidate: Dict[str, Any]) -> np.ndarray:
    features = _build_feature_dict(candidate)
    return np.array([features[name] for name in STRUCTURED_FEATURES], dtype=np.float32)
def extract_slpi_features(candidate: Dict[str, Any]) -> np.ndarray:
    meta = candidate.get("bot_metadata", {})
    if not meta.get("fingerprint_reliable", False):
        return np.zeros(len(SLPI_FEATURES), dtype=np.float32)
    display = meta.get("fingerprint_display", {})
    return np.array(
        [float(display.get(k, 0.0)) for k in SLPI_FEATURES],
        dtype=np.float32,
    )
def extract_essay_features(candidate: Dict[str, Any]) -> np.ndarray:
    nlp = candidate.get("bot_metadata", {}).get("essay_nlp")
    if nlp is None:
        raise KeyError(
            f"candidate {candidate.get('user_id', '?')} has no bot_metadata.essay_nlp — "
            "NLP must be computed in the bot before scoring"
        )
    return np.array([
        nlp["model_the_way"]         / 10.0,
        nlp["inspire_shared_vision"] / 10.0,
        nlp["challenge_the_process"] / 10.0,
        nlp["enable_others_to_act"]  / 10.0,
        nlp["encourage_the_heart"]   / 10.0,
        nlp["overall"]               / 10.0,
    ], dtype=np.float32)
def extract_batch(candidates: List[Dict[str, Any]]) -> np.ndarray:
    return np.array([extract_features(c) for c in candidates], dtype=np.float32)
def _build_feature_dict(candidate: dict) -> Dict[str, float]:
    edu      = candidate.get("education", {})
    olympiads = edu.get("olympiads", [])
    courses   = edu.get("courses", [])
    projects  = candidate.get("experience", {}).get("projects", [])
    return {
        "f_gpa":                          _f_gpa(edu),
        "f_ent_score":                    _f_ent_score(edu),
        "f_ielts_score":                  _f_ielts_score(edu),
        "f_olympiad_count":               float(len(olympiads)),
        "f_olympiad_max_level":           _f_olympiad_max_level(olympiads),
        "f_olympiad_has_prize":           _f_olympiad_has_prize(olympiads),
        "f_courses_count":                float(len(courses)),
        "f_has_any_courses":              1.0 if courses else 0.0,
        "f_courses_completed_ratio":      _f_courses_completed_ratio(courses),
        "f_project_count":                float(len(projects)),
        "f_founder_ratio":                _f_founder_ratio(projects),
        "f_max_role":                     _f_max_role(projects),
        "f_project_diversity":            float(len({p.get("type", "other") for p in projects})),
        "f_max_team_size":                _f_max_team_size(projects),
        "f_role_progression":             _f_role_progression(projects),
        "f_scope_progression":            _f_scope_progression(projects, olympiads),
        "f_skill_diversity_growth":       float(_f_skill_diversity_growth(projects)),
        "f_activity_years_span":          float(_f_activity_years_span(projects, olympiads)),
        "f_persistence_signal":           _f_persistence_signal(projects),
        "f_failure_acknowledgment_ratio": _f_failure_acknowledgment_ratio(projects),
    }
def _f_gpa(edu: dict) -> float:
    return float(np.clip(edu.get("gpa", 0.0), 0.0, 5.0))
def _f_ent_score(edu: dict) -> float:
    score = edu.get("ent_score") or 0
    return float(np.clip(score, 0, 140) / 140)
def _f_ielts_score(edu: dict) -> float:
    score = edu.get("ielts_score") or 0
    return float(np.clip(score, 0, 9) / 9)
def _f_olympiad_max_level(olympiads: list) -> float:
    if not olympiads:
        return 0.0
    return float(max(OLYMPIAD_LEVEL_MAP.get(o.get("level", ""), 0) for o in olympiads))
def _f_olympiad_has_prize(olympiads: list) -> float:
    for o in olympiads:
        prize = o.get("prize", None)
        if prize is True:
            return 1.0
        if prize is None and o.get("result", "") in ("prize", "honorable_mention"):
            return 1.0
    return 0.0
def _f_courses_completed_ratio(courses: list) -> float:
    if not courses:
        return 0.0
    return sum(1 for c in courses if c.get("completed", False)) / len(courses)
def _f_founder_ratio(projects: list) -> float:
    if not projects:
        return 0.0
    return sum(1 for p in projects if p.get("role", "") in ("founder", "co_founder")) / len(projects)
def _f_max_role(projects: list) -> float:
    if not projects:
        return 0.0
    return float(max(PROJECT_ROLE_MAP.get(p.get("role", "participant"), 0) for p in projects))
def _f_max_team_size(projects: list) -> float:
    if not projects:
        return 0.0
    return float(min(max(p.get("team_size", 1) for p in projects), 500))
def _f_role_progression(projects: list) -> float:
    if len(projects) < 2:
        return 0.0
    sorted_p = sorted(projects, key=lambda p: p.get("year", 0))
    roles = [PROJECT_ROLE_MAP.get(p.get("role", "participant"), 0) for p in sorted_p]
    mid = len(roles) // 2
    return float(np.mean(roles[mid:]) - np.mean(roles[:mid]))
def _f_scope_progression(projects: list, olympiads: list) -> float:
    progression = 0.0
    if len(projects) >= 2:
        sorted_p = sorted(projects, key=lambda p: p.get("year", 0))
        log_sizes = [np.log1p(min(p.get("team_size", 1), 500)) for p in sorted_p]
        mid = len(log_sizes) // 2
        early = float(np.mean(log_sizes[:mid]))
        late  = float(np.mean(log_sizes[mid:]))
        if early > 0:
            progression += (late - early) / early
    if len(olympiads) >= 2:
        sorted_o = sorted(olympiads, key=lambda o: o.get("year", 0))
        levels = [OLYMPIAD_LEVEL_MAP.get(o.get("level", ""), 0) for o in sorted_o]
        progression += levels[-1] - levels[0]
    return float(progression)
def _f_skill_diversity_growth(projects: list) -> int:
    if not projects:
        return 0
    types_by_year: Dict[int, set] = {}
    for p in projects:
        types_by_year.setdefault(p.get("year", 0), set()).add(p.get("type", "other"))
    seen: set = set()
    growth = 0
    for year in sorted(types_by_year):
        new = types_by_year[year] - seen
        growth += len(new)
        seen.update(new)
    return growth
def _f_activity_years_span(projects: list, olympiads: list) -> int:
    years = [p["year"] for p in projects if "year" in p] + \
            [o["year"] for o in olympiads if "year" in o]
    if len(years) < 2:
        return 0
    return max(years) - min(years)
def _f_persistence_signal(projects: list) -> float:
    for p in projects:
        if p.get("failure_note", "") and p.get("continued_after_failure", False) is True:
            return 1.0
    return 0.0
def _f_failure_acknowledgment_ratio(projects: list) -> float:
    if not projects:
        return 0.0
    return sum(1 for p in projects if p.get("failure_note", "")) / len(projects)
if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python feature_extractor.py <candidate.json>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        candidate = json.load(f)
    from config import SLPI_FEATURES, ESSAY_FEATURES
    features = extract_features_dict(candidate)
    print("\n=== Structural Features (18) ===")
    for name, value in features.items():
        print(f"  {name:40s} = {value:.4f}")
    slpi = extract_slpi_features(candidate)
    print("\n=== SLPI Features (5) ===")
    for name, value in zip(SLPI_FEATURES, slpi):
        print(f"  {name:40s} = {value:.4f}")
    essay = extract_essay_features(candidate)
    print("\n=== Essay Features (10) ===")
    for name, value in zip(ESSAY_FEATURES, essay):
        print(f"  {name:40s} = {value:.4f}")
    vec = extract_features(candidate)
    print(f"\nCombined vector (stage 1+2): {len(vec)} dims")
