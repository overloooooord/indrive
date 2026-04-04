from __future__ import annotations
import math
from typing import Optional
SLPI_SLICES = {
    "model_the_way":      (0,   100),
    "inspire_vision":     (100, 200),
    "challenge_process":  (200, 300),
    "enable_others":      (300, 400),
    "encourage_heart":    (400, 500),
}
MTW = 0
ISV = 100
CTP = 200
EOA = 300
ETH = 400
VECTOR_SIZE = 500
WEIGHT_MAP: dict[str, dict] = {
    "Q1:A": {"primary": (CTP+0, 1.0), "secondary": [(MTW+0, 0.4)]},
    "Q1:B": {"primary": (EOA+0, 1.0), "secondary": [(EOA+1, 0.4)]},
    "Q1:C": {"primary": (ISV+0, 1.0), "secondary": [(EOA+4, 0.4)]},
    "Q1:D": {"primary": (MTW+3, 1.0), "secondary": [(MTW+4, 0.4)]},
    "Q1A:A": {"primary": (CTP+0, 1.0), "secondary": [(CTP+6, 0.4)]},
    "Q1A:B": {"primary": (EOA+2, 1.0), "secondary": [(MTW+2, 0.4)]},
    "Q1A:C": {"primary": (MTW+3, 1.0), "secondary": [(MTW+5, 0.4)]},
    "Q1A:D": {"primary": (CTP+3, 1.0), "secondary": [(CTP+7, 0.4)]},
    "Q1B:A": {"primary": (ETH+3, 1.0), "secondary": [(ETH+4, 0.4)]},
    "Q1B:B": {"primary": (CTP+5, 1.0), "secondary": [(CTP+3, 0.4)]},
    "Q1B:C": {"primary": (EOA+2, 1.0), "secondary": [(EOA+1, 0.4)]},
    "Q1B:D": {"primary": (EOA+3, 1.0), "secondary": [(EOA+0, 0.4)]},
    "Q1C:A": {"primary": (CTP+0, 1.0), "secondary": [(MTW+0, 0.4)]},
    "Q1C:B": {"primary": (MTW+4, 1.0), "secondary": [(MTW+7, 0.4)]},
    "Q1C:C": {"primary": (ISV+7, 1.0), "secondary": [(ISV+1, 0.4)]},
    "Q1C:D": {"primary": (EOA+0, 1.0), "secondary": [(ISV+2, 0.4)]},
    "Q1D:A": {"primary": (MTW+0, 1.0), "secondary": [(CTP+6, 0.4)]},
    "Q1D:B": {"primary": (ISV+6, 1.0), "secondary": [(MTW+3, 0.4)]},
    "Q1D:C": {"primary": (CTP+4, 1.0), "secondary": [(MTW+5, 0.4)]},
    "Q1D:D": {"primary": (EOA+4, 1.0), "secondary": [(EOA+7, 0.4)]},
    "Q2:A": {"primary": (EOA+3, 1.0), "secondary": [(EOA+7, 0.4)]},
    "Q2:B": {"primary": (ETH+7, 1.0), "secondary": [(ETH+5, 0.4)]},
    "Q2:C": {"primary": (ISV+2, 1.0), "secondary": [(ISV+1, 0.4)]},
    "Q2:D": {"primary": (CTP+7, 1.0), "secondary": [(CTP+3, 0.4)]},
    "Q2A:A": {"primary": (ETH+5, 1.0), "secondary": [(MTW+2, 0.4)]},
    "Q2A:B": {"primary": (CTP+5, 1.0), "secondary": [(MTW+6, 0.4)]},
    "Q2A:C": {"primary": (MTW+0, 1.0), "secondary": [(ETH+4, 0.4)]},
    "Q2A:D": {"primary": (MTW+3, 1.0), "secondary": [(MTW+2, 0.4)]},
    "Q2B:A": {"primary": (ETH+6, 1.0), "secondary": [(ETH+3, 0.4)]},
    "Q2B:B": {"primary": (ETH+5, 1.0), "secondary": [(ETH+2, 0.4)]},
    "Q2B:C": {"primary": (EOA+3, 1.0), "secondary": [(EOA+2, 0.4)]},
    "Q2B:D": {"primary": (ISV+4, 1.0), "secondary": [(ETH+0, 0.4)]},
    "Q2C:A": {"primary": (MTW+6, 1.0), "secondary": [(MTW+1, 0.4)]},
    "Q2C:B": {"primary": (ETH+7, 1.0), "secondary": [(ETH+4, 0.4)]},
    "Q2C:C": {"primary": (CTP+7, 1.0), "secondary": [(CTP+3, 0.4)]},
    "Q2C:D": {"primary": (EOA+2, 1.0), "secondary": [(ETH+7, 0.4)]},
    "Q2D:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+5, 0.4)]},
    "Q2D:B": {"primary": (ETH+2, 1.0), "secondary": [(ETH+5, 0.4)]},
    "Q2D:C": {"primary": (CTP+7, 1.0), "secondary": [(CTP+0, 0.4)]},
    "Q2D:D": {"primary": (MTW+2, 1.0), "secondary": [(MTW+0, 0.4)]},
    "Q3:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+1, 0.4)]},
    "Q3:B": {"primary": (ISV+1, 1.0), "secondary": [(ISV+2, 0.4)]},
    "Q3:C": {"primary": (CTP+2, 1.0), "secondary": [(CTP+4, 0.4)]},
    "Q3:D": {"primary": (CTP+0, 1.0), "secondary": [(CTP+6, 0.4)]},
    "Q3A:A": {"primary": (MTW+4, 0.2), "secondary": []},
    "Q3A:B": {"primary": (CTP+1, 1.0), "secondary": [(CTP+6, 0.4)]},
    "Q3A:C": {"primary": (CTP+2, 1.0), "secondary": [(CTP+0, 0.4)]},
    "Q3A:D": {"primary": (ISV+3, 1.0), "secondary": [(ISV+2, 0.4)]},
    "Q3B:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+1, 0.4)]},
    "Q3B:B": {"primary": (ISV+7, 1.0), "secondary": [(ISV+1, 0.4)]},
    "Q3B:C": {"primary": (CTP+4, 1.0), "secondary": [(CTP+1, 0.4)]},
    "Q3B:D": {"primary": (CTP+6, 1.0), "secondary": [(CTP+2, 0.4)]},
    "Q3C:A": {"primary": (EOA+1, 1.0), "secondary": [(EOA+5, 0.4)]},
    "Q3C:B": {"primary": (MTW+5, 1.0), "secondary": [(MTW+4, 0.4)]},
    "Q3C:C": {"primary": (CTP+7, 0.2), "secondary": []},
    "Q3C:D": {"primary": (ISV+3, 1.0), "secondary": [(EOA+6, 0.4)]},
    "Q3D:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+1, 0.4)]},
    "Q3D:B": {"primary": (ISV+1, 1.0), "secondary": [(ISV+6, 0.4)]},
    "Q3D:C": {"primary": (CTP+2, 1.0), "secondary": [(CTP+0, 0.4)]},
    "Q3D:D": {"primary": (ISV+3, 1.0), "secondary": [(ISV+5, 0.4)]},
    "Q4:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+5, 0.4)]},
    "Q4:B": {"primary": (ETH+7, 1.0), "secondary": [(ETH+5, 0.4)]},
    "Q4:C": {"primary": (EOA+3, 1.0), "secondary": [(EOA+0, 0.4)]},
    "Q4:D": {"primary": (ETH+0, 1.0), "secondary": [(ISV+4, 0.4)]},
    "Q4A:A": {"primary": (MTW+5, 1.0), "secondary": [(MTW+1, 0.4)]},
    "Q4A:B": {"primary": (ETH+2, 1.0), "secondary": [(ETH+5, 0.4)]},
    "Q4A:C": {"primary": (MTW+2, 1.0), "secondary": [(ETH+1, 0.4)]},
    "Q4A:D": {"primary": (CTP+7, 1.0), "secondary": [(CTP+3, 0.4)]},
    "Q4B:A": {"primary": (ETH+3, 1.0), "secondary": [(ETH+6, 0.4)]},
    "Q4B:B": {"primary": (EOA+3, 1.0), "secondary": [(EOA+5, 0.4)]},
    "Q4B:C": {"primary": (ETH+4, 1.0), "secondary": [(ETH+0, 0.4)]},
    "Q4B:D": {"primary": (EOA+4, 1.0), "secondary": [(EOA+7, 0.4)]},
    "Q4C:A": {"primary": (MTW+5, 1.0), "secondary": [(MTW+6, 0.4)]},
    "Q4C:B": {"primary": (CTP+5, 1.0), "secondary": [(MTW+6, 0.4)]},
    "Q4C:C": {"primary": (ISV+5, 1.0), "secondary": [(ETH+7, 0.4)]},
    "Q4C:D": {"primary": (ETH+0, 1.0), "secondary": [(ISV+4, 0.4)]},
    "Q4D:A": {"primary": (ETH+2, 1.0), "secondary": [(ETH+5, 0.4)]},
    "Q4D:B": {"primary": (EOA+3, 1.0), "secondary": [(EOA+5, 0.4)]},
    "Q4D:C": {"primary": (MTW+1, 1.0), "secondary": [(MTW+5, 0.4)]},
    "Q4D:D": {"primary": (EOA+7, 1.0), "secondary": [(EOA+4, 0.4)]},
    "Q5:A": {"primary": (CTP+3, 1.0), "secondary": [(CTP+7, 0.4)]},
    "Q5:B": {"primary": (MTW+1, 1.0), "secondary": [(MTW+0, 0.4)]},
    "Q5:C": {"primary": (EOA+0, 1.0), "secondary": [(EOA+6, 0.4)]},
    "Q5:D": {"primary": (ISV+6, 1.0), "secondary": [(MTW+5, 0.4)]},
    "Q5A:A": {"primary": (MTW+5, 1.0), "secondary": [(MTW+1, 0.4)]},
    "Q5A:B": {"primary": (ETH+2, 1.0), "secondary": [(ETH+3, 0.4)]},
    "Q5A:C": {"primary": (EOA+5, 1.0), "secondary": [(EOA+6, 0.4)]},
    "Q5A:D": {"primary": (MTW+2, 1.0), "secondary": [(MTW+0, 0.4)]},
    "Q5B:A": {"primary": (MTW+1, 1.0), "secondary": [(MTW+7, 0.4)]},
    "Q5B:B": {"primary": (CTP+1, 1.0), "secondary": [(MTW+2, 0.4)]},
    "Q5B:C": {"primary": (EOA+0, 1.0), "secondary": [(EOA+1, 0.4)]},
    "Q5B:D": {"primary": (MTW+3, 1.0), "secondary": [(MTW+5, 0.4)]},
    "Q5C:A": {"primary": (EOA+5, 1.0), "secondary": [(EOA+1, 0.4)]},
    "Q5C:B": {"primary": (ETH+3, 1.0), "secondary": [(ETH+6, 0.4)]},
    "Q5C:C": {"primary": (EOA+6, 1.0), "secondary": [(EOA+5, 0.4)]},
    "Q5C:D": {"primary": (CTP+7, 1.0), "secondary": [(CTP+5, 0.4)]},
    "Q5D:A": {"primary": (ISV+5, 1.0), "secondary": [(ISV+2, 0.4)]},
    "Q5D:B": {"primary": (MTW+7, 1.0), "secondary": [(MTW+1, 0.4)]},
    "Q5D:C": {"primary": (CTP+4, 1.0), "secondary": [(CTP+1, 0.4)]},
    "Q5D:D": {"primary": (MTW+5, 1.0), "secondary": [(MTW+3, 0.4)]},
}
BRANCH_MAP: dict[str, str] = {
    "Q1:A": "Q1A", "Q1:B": "Q1B", "Q1:C": "Q1C", "Q1:D": "Q1D",
    "Q2:A": "Q2A", "Q2:B": "Q2B", "Q2:C": "Q2C", "Q2:D": "Q2D",
    "Q3:A": "Q3A", "Q3:B": "Q3B", "Q3:C": "Q3C", "Q3:D": "Q3D",
    "Q4:A": "Q4A", "Q4:B": "Q4B", "Q4:C": "Q4C", "Q4:D": "Q4D",
    "Q5:A": "Q5A", "Q5:B": "Q5B", "Q5:C": "Q5C", "Q5:D": "Q5D",
}
ROOT_QUESTIONS = ["Q1", "Q2", "Q3", "Q4", "Q5"]
def _apply_weights(vector: list[float], key: str) -> None:
    entry = WEIGHT_MAP.get(key)
    if entry is None:
        return
    dim, w = entry["primary"]
    vector[dim] += w
    for (sec_dim, sec_w) in entry.get("secondary", []):
        vector[sec_dim] += sec_w
def _normalize(vector: list[float]) -> list[float]:
    v_min = min(vector)
    v_max = max(vector)
    if math.isclose(v_max, v_min):
        return [0.0] * len(vector)
    span = v_max - v_min
    return [(x - v_min) / span for x in vector]
def encode_choices_to_vector(choice_path: list[str]) -> list[float]:
    if len(choice_path) != 10:
        raise ValueError(
            f"choice_path должен содержать ровно 10 элементов, получено {len(choice_path)}"
        )
    vector = [0.0] * VECTOR_SIZE
    for i, root_q in enumerate(ROOT_QUESTIONS):
        root_choice  = choice_path[i * 2]
        branch_choice = choice_path[i * 2 + 1]
        root_key   = f"{root_q}:{root_choice}"
        branch_id  = BRANCH_MAP.get(root_key)
        _apply_weights(vector, root_key)
        if branch_id:
            branch_key = f"{branch_id}:{branch_choice}"
            _apply_weights(vector, branch_key)
    return _normalize(vector)
def aggregate_to_slpi(vector: list[float]) -> dict[str, float]:
    result = {}
    for cluster_name, (start, end) in SLPI_SLICES.items():
        cluster_vals = vector[start:end]
        result[cluster_name] = round(sum(cluster_vals) / len(cluster_vals), 4)
    return result
def compute_fingerprint(
    choice_path: list[str],
    timer_compliant: Optional[list[bool]] = None,
) -> dict:
    """
    Главная функция модуля. Вызывается из scorer.py и feature_extractor.py.

    Параметры
    ----------
    choice_path     : список из 10 строк (A/B/C/D/timeout)
    timer_compliant : список из 10 bool (True = ответил вовремя).
                      Если None — считаем все шаги compliant.

    Возвращает
    ----------
    {
        "fingerprint_vector":   list[float],  # 500 значений → в XGBoost
        "fingerprint_display":  dict,          # 5 SLPI-кластеров → в дашборд + SHAP
        "fingerprint_reliable": bool,          # False если > 3 timeout
        "timeout_steps":        list[int],     # индексы шагов с истёкшим таймером
    }
    """
    if timer_compliant is None:
        timer_compliant = [True] * len(choice_path)
    cleaned_path = [
        ch if compliant else "TIMEOUT"
        for ch, compliant in zip(choice_path, timer_compliant)
    ]
    timeout_steps = [i for i, c in enumerate(timer_compliant) if not c]
    # Надёжность: если > 3 из 10 шагов — timeout, fingerprint ненадёжен
    fingerprint_reliable = len(timeout_steps) <= 3

    if not fingerprint_reliable:
        return {
            "fingerprint_vector":   None,
            "fingerprint_display":  None,
            "fingerprint_reliable": False,
            "timeout_steps":        timeout_steps,
        }
    fingerprint_vector  = encode_choices_to_vector(cleaned_path)
    fingerprint_display = aggregate_to_slpi(fingerprint_vector)
    return {
        "fingerprint_vector":   fingerprint_vector,
        "fingerprint_display":  fingerprint_display,
        "fingerprint_reliable": True,
        "timeout_steps":        timeout_steps,
    }
def get_branch_question_id(root_question: str, choice: str) -> Optional[str]:
    key = f"{root_question}:{choice}"
    return BRANCH_MAP.get(key)
if __name__ == "__main__":
    import sys
    import json
    args = sys.argv[1:]
    if "--choices" in args:
        idx = args.index("--choices")
        choices = args[idx + 1:]
    else:
        choices = ["B", "C", "C", "B", "C", "C", "B", "C", "D", "C"]
    print(f"\n=== scenario_engine.py ===")
    print(f"choice_path: {choices}")
    result = compute_fingerprint(choices)
    print(f"\nfingerprint_reliable: {result['fingerprint_reliable']}")
    print(f"timeout_steps:        {result['timeout_steps']}")
    if result["fingerprint_reliable"]:
        print(f"\nfingerprint_display (5 SLPI-кластеров):")
        for k, v in result["fingerprint_display"].items():
            bar = "█" * int(v * 20)
            print(f"  {k:<22} {v:.4f}  {bar}")
        vec = result["fingerprint_vector"]
        print(f"\nfingerprint_vector: {len(vec)} dims")
        print(f"  min={min(vec):.4f}  max={max(vec):.4f}  mean={sum(vec)/len(vec):.4f}")
        print(f"  first 10 values: {[round(x, 4) for x in vec[:10]]}")
    else:
        print("\n⚠️  fingerprint ненадёжен (> 2 timeout) — fp-компоненты исключены из скоринга")
