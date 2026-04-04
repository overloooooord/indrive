

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

# Для читаемости — базовые индексы каждого кластера
MTW = 0    # Model the Way:          dims   0–99
ISV = 100  # Inspire a Shared Vision: dims 100–199
CTP = 200  # Challenge the Process:   dims 200–299
EOA = 300  # Enable Others to Act:    dims 300–399
ETH = 400  # Encourage the Heart:     dims 400–499

VECTOR_SIZE = 500


WEIGHT_MAP: dict[str, dict] = {

    # -----------------------------------------------------------------------
    # СЦЕНАРИЙ 1 — Организационный кризис
    # -----------------------------------------------------------------------

    # Q1 — входной
    "Q1:A": {"primary": (CTP+0, 1.0), "secondary": [(MTW+0, 0.4)]},
    "Q1:B": {"primary": (EOA+0, 1.0), "secondary": [(EOA+1, 0.4)]},
    "Q1:C": {"primary": (ISV+0, 1.0), "secondary": [(EOA+4, 0.4)]},
    "Q1:D": {"primary": (MTW+3, 1.0), "secondary": [(MTW+4, 0.4)]},

    # Q1A — ветвь «взял всё на себя»
    "Q1A:A": {"primary": (CTP+0, 1.0), "secondary": [(CTP+6, 0.4)]},
    "Q1A:B": {"primary": (EOA+2, 1.0), "secondary": [(MTW+2, 0.4)]},   # признаёт ошибку
    "Q1A:C": {"primary": (MTW+3, 1.0), "secondary": [(MTW+5, 0.4)]},   # сигнализирует честно
    "Q1A:D": {"primary": (CTP+3, 1.0), "secondary": [(CTP+7, 0.4)]},   # приоритизирует

    # Q1B — ветвь «собрал команду»
    "Q1B:A": {"primary": (ETH+3, 1.0), "secondary": [(ETH+4, 0.4)]},   # верит в людей
    "Q1B:B": {"primary": (CTP+5, 1.0), "secondary": [(CTP+3, 0.4)]},   # результат > чувства
    "Q1B:C": {"primary": (EOA+2, 1.0), "secondary": [(EOA+1, 0.4)]},   # ищет причину
    "Q1B:D": {"primary": (EOA+3, 1.0), "secondary": [(EOA+0, 0.4)]},   # решает незаметно

    # Q1C — ветвь «ищет замену»
    "Q1C:A": {"primary": (CTP+0, 1.0), "secondary": [(MTW+0, 0.4)]},   # берёт риск
    "Q1C:B": {"primary": (MTW+4, 1.0), "secondary": [(MTW+7, 0.4)]},   # не нарушает правила
    "Q1C:C": {"primary": (ISV+7, 1.0), "secondary": [(ISV+1, 0.4)]},   # взаимовыгода
    "Q1C:D": {"primary": (EOA+0, 1.0), "secondary": [(ISV+2, 0.4)]},   # возвращает команде

    # Q1D — ветвь «сообщил куратору»
    "Q1D:A": {"primary": (MTW+0, 1.0), "secondary": [(CTP+6, 0.4)]},   # принимает ответств.
    "Q1D:B": {"primary": (ISV+6, 1.0), "secondary": [(MTW+3, 0.4)]},   # честно об ограничениях
    "Q1D:C": {"primary": (CTP+4, 1.0), "secondary": [(MTW+5, 0.4)]},   # структурирует, план
    "Q1D:D": {"primary": (EOA+4, 1.0), "secondary": [(EOA+7, 0.4)]},   # ищет ресурсы

    # -----------------------------------------------------------------------
    # СЦЕНАРИЙ 2 — Конфликт в команде
    # -----------------------------------------------------------------------

    # Q2 — входной
    "Q2:A": {"primary": (EOA+3, 1.0), "secondary": [(EOA+7, 0.4)]},    # верит в самоорг.
    "Q2:B": {"primary": (ETH+7, 1.0), "secondary": [(ETH+5, 0.4)]},    # слушает первым
    "Q2:C": {"primary": (ISV+2, 1.0), "secondary": [(ISV+1, 0.4)]},    # собирает вместе
    "Q2:D": {"primary": (CTP+7, 1.0), "secondary": [(CTP+3, 0.4)]},    # системное решение

    # Q2A — ветвь «пусть решают сами»
    "Q2A:A": {"primary": (ETH+5, 1.0), "secondary": [(MTW+2, 0.4)]},   # меняет решение
    "Q2A:B": {"primary": (CTP+5, 1.0), "secondary": [(MTW+6, 0.4)]},   # жёсткая граница
    "Q2A:C": {"primary": (MTW+0, 1.0), "secondary": [(ETH+4, 0.4)]},   # берёт на себя
    "Q2A:D": {"primary": (MTW+3, 1.0), "secondary": [(MTW+2, 0.4)]},   # эскалирует честно

    # Q2B — ветвь «поговорил с каждым»
    "Q2B:A": {"primary": (ETH+6, 1.0), "secondary": [(ETH+3, 0.4)]},   # верит в восстановление
    "Q2B:B": {"primary": (ETH+5, 1.0), "secondary": [(ETH+2, 0.4)]},   # настойчив в поддержке
    "Q2B:C": {"primary": (EOA+3, 1.0), "secondary": [(EOA+2, 0.4)]},   # адаптирует структуру
    "Q2B:D": {"primary": (ISV+4, 1.0), "secondary": [(ETH+0, 0.4)]},   # публично легитимизирует

    # Q2C — ветвь «собрал всех троих»
    "Q2C:A": {"primary": (MTW+6, 1.0), "secondary": [(MTW+1, 0.4)]},   # держит стандарты
    "Q2C:B": {"primary": (ETH+7, 1.0), "secondary": [(ETH+4, 0.4)]},   # даёт выговориться
    "Q2C:C": {"primary": (CTP+7, 1.0), "secondary": [(CTP+3, 0.4)]},   # возвращает к цели
    "Q2C:D": {"primary": (EOA+2, 1.0), "secondary": [(ETH+7, 0.4)]},   # создаёт условия

    # Q2D — ветвь «перераспределил задачи»
    "Q2D:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+5, 0.4)]},   # уважает автономию
    "Q2D:B": {"primary": (ETH+2, 1.0), "secondary": [(ETH+5, 0.4)]},   # не сдаётся
    "Q2D:C": {"primary": (CTP+7, 1.0), "secondary": [(CTP+0, 0.4)]},   # прагматично вперёд
    "Q2D:D": {"primary": (MTW+2, 1.0), "secondary": [(MTW+0, 0.4)]},   # публично берёт ответств.

    # -----------------------------------------------------------------------
    # СЦЕНАРИЙ 3 — Новая идея против системы
    # -----------------------------------------------------------------------

    # Q3 — входной
    "Q3:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+1, 0.4)]},    # уважает иерархию
    "Q3:B": {"primary": (ISV+1, 1.0), "secondary": [(ISV+2, 0.4)]},    # ищет понимание
    "Q3:C": {"primary": (CTP+2, 1.0), "secondary": [(CTP+4, 0.4)]},    # путь внутри правил
    "Q3:D": {"primary": (CTP+0, 1.0), "secondary": [(CTP+6, 0.4)]},    # эскалирует

    # Q3A — ветвь «принял отказ»
    "Q3A:A": {"primary": (MTW+4, 0.2), "secondary": []},               # низкий сигнал
    "Q3A:B": {"primary": (CTP+1, 1.0), "secondary": [(CTP+6, 0.4)]},   # готовится
    "Q3A:C": {"primary": (CTP+2, 1.0), "secondary": [(CTP+0, 0.4)]},   # создаёт свой путь
    "Q3A:D": {"primary": (ISV+3, 1.0), "secondary": [(ISV+2, 0.4)]},   # строит коалицию

    # Q3B — ветвь «попросил объяснить»
    "Q3B:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+1, 0.4)]},   # доверяет опыту
    "Q3B:B": {"primary": (ISV+7, 1.0), "secondary": [(ISV+1, 0.4)]},   # компромисс
    "Q3B:C": {"primary": (CTP+4, 1.0), "secondary": [(CTP+1, 0.4)]},   # пилот
    "Q3B:D": {"primary": (CTP+6, 1.0), "secondary": [(CTP+2, 0.4)]},   # действие > слов

    # Q3C — ветвь «реализовал в рамках правил»
    "Q3C:A": {"primary": (EOA+1, 1.0), "secondary": [(EOA+5, 0.4)]},   # делится знанием
    "Q3C:B": {"primary": (MTW+5, 1.0), "secondary": [(MTW+4, 0.4)]},   # легитимизирует
    "Q3C:C": {"primary": (CTP+7, 0.2), "secondary": []},               # низкий сигнал
    "Q3C:D": {"primary": (ISV+3, 1.0), "secondary": [(EOA+6, 0.4)]},   # строит движение

    # Q3D — ветвь «пошёл выше»
    "Q3D:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+1, 0.4)]},   # уважает систему
    "Q3D:B": {"primary": (ISV+1, 1.0), "secondary": [(ISV+6, 0.4)]},   # диалог с аргументами
    "Q3D:C": {"primary": (CTP+2, 1.0), "secondary": [(CTP+0, 0.4)]},   # создаёт свой путь
    "Q3D:D": {"primary": (ISV+3, 1.0), "secondary": [(ISV+5, 0.4)]},   # низовая коалиция

    # -----------------------------------------------------------------------
    # СЦЕНАРИЙ 4 — Поддержка человека
    # -----------------------------------------------------------------------

    # Q4 — входной
    "Q4:A": {"primary": (MTW+4, 1.0), "secondary": [(MTW+5, 0.4)]},    # уважает автономию
    "Q4:B": {"primary": (ETH+7, 1.0), "secondary": [(ETH+5, 0.4)]},    # слушает прежде всего
    "Q4:C": {"primary": (EOA+3, 1.0), "secondary": [(EOA+0, 0.4)]},    # адаптирует структуру
    "Q4:D": {"primary": (ETH+0, 1.0), "secondary": [(ISV+4, 0.4)]},    # сила команды

    # Q4A — ветвь «принял уход»
    "Q4A:A": {"primary": (MTW+5, 1.0), "secondary": [(MTW+1, 0.4)]},   # объясняет логику
    "Q4A:B": {"primary": (ETH+2, 1.0), "secondary": [(ETH+5, 0.4)]},   # меняет решение
    "Q4A:C": {"primary": (MTW+2, 1.0), "secondary": [(ETH+1, 0.4)]},   # признаёт ошибку
    "Q4A:D": {"primary": (CTP+7, 1.0), "secondary": [(CTP+3, 0.4)]},   # прагматично вперёд

    # Q4B — ветвь «поговорил с ним»
    "Q4B:A": {"primary": (ETH+3, 1.0), "secondary": [(ETH+6, 0.4)]},   # уважает темп
    "Q4B:B": {"primary": (EOA+3, 1.0), "secondary": [(EOA+5, 0.4)]},   # создаёт условия
    "Q4B:C": {"primary": (ETH+4, 1.0), "secondary": [(ETH+0, 0.4)]},   # безусловная поддержка
    "Q4B:D": {"primary": (EOA+4, 1.0), "secondary": [(EOA+7, 0.4)]},   # привлекает ресурсы

    # Q4C — ветвь «снизил нагрузку»
    "Q4C:A": {"primary": (MTW+5, 1.0), "secondary": [(MTW+6, 0.4)]},   # прозрачен, держит приват.
    "Q4C:B": {"primary": (CTP+5, 1.0), "secondary": [(MTW+6, 0.4)]},   # жёсткий, справедливый
    "Q4C:C": {"primary": (ISV+5, 1.0), "secondary": [(ETH+7, 0.4)]},   # слушает коллектив
    "Q4C:D": {"primary": (ETH+0, 1.0), "secondary": [(ISV+4, 0.4)]},   # просит жертву ради чел.

    # Q4D — ветвь «попросил команду поддержать»
    "Q4D:A": {"primary": (ETH+2, 1.0), "secondary": [(ETH+5, 0.4)]},   # не сдаётся
    "Q4D:B": {"primary": (EOA+3, 1.0), "secondary": [(EOA+5, 0.4)]},   # правильный контекст
    "Q4D:C": {"primary": (MTW+1, 1.0), "secondary": [(MTW+5, 0.4)]},   # называет проблему прямо
    "Q4D:D": {"primary": (EOA+7, 1.0), "secondary": [(EOA+4, 0.4)]},   # знает границы роли

    # -----------------------------------------------------------------------
    # СЦЕНАРИЙ 5 — Ресурсный конфликт
    # -----------------------------------------------------------------------

    # Q5 — входной
    "Q5:A": {"primary": (CTP+3, 1.0), "secondary": [(CTP+7, 0.4)]},    # приоритизирует
    "Q5:B": {"primary": (MTW+1, 1.0), "secondary": [(MTW+0, 0.4)]},    # держит обязательства
    "Q5:C": {"primary": (EOA+0, 1.0), "secondary": [(EOA+6, 0.4)]},    # делегирует
    "Q5:D": {"primary": (ISV+6, 1.0), "secondary": [(MTW+5, 0.4)]},    # строит на доверии

    # Q5A — ветвь «выбрал один проект»
    "Q5A:A": {"primary": (MTW+5, 1.0), "secondary": [(MTW+1, 0.4)]},   # прозрачен в решении
    "Q5A:B": {"primary": (ETH+2, 1.0), "secondary": [(ETH+3, 0.4)]},   # не бросает полностью
    "Q5A:C": {"primary": (EOA+5, 1.0), "secondary": [(EOA+6, 0.4)]},   # выращивает лидера
    "Q5A:D": {"primary": (MTW+2, 1.0), "secondary": [(MTW+0, 0.4)]},   # публично берёт ответств.

    # Q5B — ветвь «ведёт оба»
    "Q5B:A": {"primary": (MTW+1, 1.0), "secondary": [(MTW+7, 0.4)]},   # держит слово любой ценой
    "Q5B:B": {"primary": (CTP+1, 1.0), "secondary": [(MTW+2, 0.4)]},   # признаёт, исправляет
    "Q5B:C": {"primary": (EOA+0, 1.0), "secondary": [(EOA+1, 0.4)]},   # распределяет ответств.
    "Q5B:D": {"primary": (MTW+3, 1.0), "secondary": [(MTW+5, 0.4)]},   # эскалирует честно

    # Q5C — ветвь «нашёл замену»
    "Q5C:A": {"primary": (EOA+5, 1.0), "secondary": [(EOA+1, 0.4)]},   # передаёт знание
    "Q5C:B": {"primary": (ETH+3, 1.0), "secondary": [(ETH+6, 0.4)]},   # доверяет росту
    "Q5C:C": {"primary": (EOA+6, 1.0), "secondary": [(EOA+5, 0.4)]},   # строит переходный период
    "Q5C:D": {"primary": (CTP+7, 1.0), "secondary": [(CTP+5, 0.4)]},   # прагматичен в ресурсах

    # Q5D — ветвь «честно поговорил с командами»
    "Q5D:A": {"primary": (ISV+5, 1.0), "secondary": [(ISV+2, 0.4)]},   # доверяет коллектив. реш.
    "Q5D:B": {"primary": (MTW+7, 1.0), "secondary": [(MTW+1, 0.4)]},   # условия без компромисса
    "Q5D:C": {"primary": (CTP+4, 1.0), "secondary": [(CTP+1, 0.4)]},   # пилот = минимум риска
    "Q5D:D": {"primary": (MTW+5, 1.0), "secondary": [(MTW+3, 0.4)]},   # прозрачен даже неудобно
}


# ---------------------------------------------------------------------------
# 3. МАППИНГ ВХОДНЫХ ВОПРОСОВ → ВЕТКИ
#
# Формат: "Q<N>:<choice>" → "Q<N><choice>"  (ключ ветки следующего вопроса)
# Нужен, чтобы бот знал, какой ветвевой вопрос задать следующим.
# ---------------------------------------------------------------------------

BRANCH_MAP: dict[str, str] = {
    "Q1:A": "Q1A", "Q1:B": "Q1B", "Q1:C": "Q1C", "Q1:D": "Q1D",
    "Q2:A": "Q2A", "Q2:B": "Q2B", "Q2:C": "Q2C", "Q2:D": "Q2D",
    "Q3:A": "Q3A", "Q3:B": "Q3B", "Q3:C": "Q3C", "Q3:D": "Q3D",
    "Q4:A": "Q4A", "Q4:B": "Q4B", "Q4:C": "Q4C", "Q4:D": "Q4D",
    "Q5:A": "Q5A", "Q5:B": "Q5B", "Q5:C": "Q5C", "Q5:D": "Q5D",
}

# Порядок входных вопросов
ROOT_QUESTIONS = ["Q1", "Q2", "Q3", "Q4", "Q5"]


# ---------------------------------------------------------------------------
# 4. ОСНОВНАЯ ЛОГИКА
# ---------------------------------------------------------------------------

def _apply_weights(vector: list[float], key: str) -> None:
    """
    Применяет веса из WEIGHT_MAP для одного выбора кандидата.
    Модифицирует vector на месте.
    """
    entry = WEIGHT_MAP.get(key)
    if entry is None:
        return  # неизвестный ключ — пропускаем, не падаем

    dim, w = entry["primary"]
    vector[dim] += w

    for (sec_dim, sec_w) in entry.get("secondary", []):
        vector[sec_dim] += sec_w


def _normalize(vector: list[float]) -> list[float]:
    """
    Min-max нормализация → все значения в [0.0, 1.0].
    Если все нули (пустой путь) — возвращаем нулевой вектор.
    """
    v_min = min(vector)
    v_max = max(vector)
    if math.isclose(v_max, v_min):
        return [0.0] * len(vector)
    span = v_max - v_min
    return [(x - v_min) / span for x in vector]


def encode_choices_to_vector(choice_path: list[str]) -> list[float]:
    """
    Принимает choice_path из бота:
      ["B", "C",   "C", "B",   "C", "C",   "B", "C",   "D", "C"]
       ←Q1→ ←Q1B→  ←Q2→ ←Q2C→  ←Q3→ ←Q3C→  ←Q4→ ←Q4B→  ←Q5→ ←Q5D→

    choice_path — плоский список из 10 строк.
    Пары: (входной, ветка) × 5 сценариев.

    Возвращает нормализованный вектор из 500 float.
    """
    if len(choice_path) != 10:
        raise ValueError(
            f"choice_path должен содержать ровно 10 элементов, получено {len(choice_path)}"
        )

    vector = [0.0] * VECTOR_SIZE

    for i, root_q in enumerate(ROOT_QUESTIONS):
        root_choice  = choice_path[i * 2]       # 0, 2, 4, 6, 8
        branch_choice = choice_path[i * 2 + 1]  # 1, 3, 5, 7, 9

        root_key   = f"{root_q}:{root_choice}"
        branch_id  = BRANCH_MAP.get(root_key)

        _apply_weights(vector, root_key)

        if branch_id:
            branch_key = f"{branch_id}:{branch_choice}"
            _apply_weights(vector, branch_key)

    return _normalize(vector)


def aggregate_to_slpi(vector: list[float]) -> dict[str, float]:
    """
    500-мерный вектор → 5 SLPI-кластеров (среднее по 100 dims каждого).
    Используется для дашборда и SHAP-объяснений.
    """
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

    # Заменяем timeout-шаги на специальный маркер, чтобы они не влияли на веса
    cleaned_path = [
        ch if compliant else "TIMEOUT"
        for ch, compliant in zip(choice_path, timer_compliant)
    ]

    timeout_steps = [i for i, c in enumerate(timer_compliant) if not c]
    # Надёжность: если > 3 из 10 шагов — timeout, fingerprint ненадёжен
    fingerprint_reliable = len(timeout_steps) <= 3

    if not fingerprint_reliable:
        # Возвращаем None-значения — scorer.py исключит fp-компоненты из модели
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


# ---------------------------------------------------------------------------
# 5. УТИЛИТЫ ДЛЯ БОТА (какую ветку показать следующей)
# ---------------------------------------------------------------------------

def get_branch_question_id(root_question: str, choice: str) -> Optional[str]:
    """
    Возвращает ID ветвевого вопроса по входному вопросу и выбору.

    Пример:
        get_branch_question_id("Q1", "B") → "Q1B"
        get_branch_question_id("Q3", "C") → "Q3C"
    """
    key = f"{root_question}:{choice}"
    return BRANCH_MAP.get(key)


# ---------------------------------------------------------------------------
# 6. CLI ДЛЯ ТЕСТИРОВАНИЯ
#    python scenario_engine.py --choices B C C B C C B C D C
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import json

    args = sys.argv[1:]

    # --choices A B C D ...
    if "--choices" in args:
        idx = args.index("--choices")
        choices = args[idx + 1:]
    else:
        # дефолтный пример из документации
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
