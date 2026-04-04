import re
import json
import os
from datetime import datetime
from config import ESSAY_MIN_WORDS, ESSAY_MAX_WORDS

def validate_name(text: str) -> bool:
    """2–60 chars, only letters (cyrillic/latin) and spaces"""
    if not (2 <= len(text.strip()) <= 60):
        return False
    return bool(re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", text.strip()))


def validate_age(text: str) -> int | None:
    """Integer 14–25"""
    try:
        age = int(text.strip())
        if 14 <= age <= 25:
            return age
    except ValueError:
        pass
    return None


def validate_city(text: str) -> bool:
    return 2 <= len(text.strip()) <= 60


def validate_year(text: str) -> int | None:
    try:
        year = int(text.strip())
        if 2018 <= year <= 2026:
            return year
    except ValueError:
        pass
    return None


def validate_team_size(text: str) -> int | None:
    try:
        size = int(text.strip())
        if 1 <= size <= 500:
            return size
    except ValueError:
        pass
    return None


def count_words(text: str) -> int:
    return len(text.strip().split())


def validate_essay(text: str) -> tuple[bool, int, str]:
    wc = count_words(text)
    if wc < ESSAY_MIN_WORDS:
        return False, wc, f"Слишком коротко — {wc} слов. Нужно минимум {ESSAY_MIN_WORDS}."
    if wc > ESSAY_MAX_WORDS:
        return False, wc, f"Слишком длинно — {wc} слов. Максимум {ESSAY_MAX_WORDS}."
    return True, wc, ""


def extract_gpa(raw: str) -> float | None:
    raw = raw.strip().replace(",", ".")
    try:
        val = float(raw)
        if 1.0 <= val <= 5.0:
            return round(val, 2)
    except ValueError:
        return None
    return None
# ---------------------------------------------------------------------------------------------------------------------
# БОТОВСКИЙ СЧЕТЧИК FINGERPRINT
# ---------------------------------------------------------------------------------------------------------------------
# SLPI_MAPPING = {
#     # step1 → Challenge the Process / Enable Others
#     "sc1_A": {"challenge_process": 0.3, "model_the_way": 0.7},
#     "sc1_B": {"enable_others": 0.8, "inspire_vision": 0.5},
#     "sc1_C": {"challenge_process": 0.6, "model_the_way": 0.4},
#     "sc1_D": {"model_the_way": 0.5, "encourage_heart": 0.3},
#     # step2 → Enable Others / Encourage the Heart
#     "sc2_A": {"encourage_heart": 0.8, "enable_others": 0.3},
#     "sc2_B": {"model_the_way": 0.7, "challenge_process": 0.3},
#     "sc2_C": {"encourage_heart": 0.6, "enable_others": 0.6},
#     "sc2_D": {"enable_others": 0.5, "model_the_way": 0.4},
#     # step3 → Challenge the Process
#     "sc3_A": {"model_the_way": 0.6},
#     "sc3_B": {"challenge_process": 0.8, "inspire_vision": 0.5},
#     "sc3_C": {"challenge_process": 0.7, "model_the_way": 0.4},
#     "sc3_D": {"model_the_way": 0.4, "challenge_process": 0.2},
#     # step4 → Enable Others / Model the Way
#     "sc4_A": {"model_the_way": 0.8, "challenge_process": 0.3},
#     "sc4_B": {"enable_others": 0.8, "inspire_vision": 0.5},
#     "sc4_C": {"challenge_process": 0.5, "model_the_way": 0.4},
#     "sc4_D": {"model_the_way": 0.6, "challenge_process": 0.4},
# }

# SLPI_DIMS = ["model_the_way", "inspire_vision", "challenge_process", "enable_others", "encourage_heart"]


# def compute_fingerprint(choices: list[str]) -> dict:
#     scores = {d: 0.0 for d in SLPI_DIMS}
#     counts = {d: 0 for d in SLPI_DIMS}
#     for choice in choices:
#         mapping = SLPI_MAPPING.get(choice, {})
#         for dim, val in mapping.items():
#             scores[dim] += val
#             counts[dim] += 1
#     display = {}
#     for dim in SLPI_DIMS:
#         display[dim] = round(scores[dim] / max(counts[dim], 1), 2)
#     return display
# ---------------------------------------------------------------------------------------------------------------------


def build_summary(app) -> str:
    """Build a text summary of the full application"""
    lines = [
        "📋 *Заявка InVision U*",
        "",
        f"*Имя:* {app.name or '—'}",
        f"*Возраст:* {app.age or '—'}",
        f"*Город:* {app.city or '—'}",
        f"*Регион:* {app.region or '—'}\n",
        f"*Тип школы:* {app.school_type or '—'}\n",
        f"*Языки:* {', '.join(app.languages) if app.languages else '—'}\n",
        f"*GPA:* {app.gpa or '—'}",
        f"*IELTS:* {app.ielts_score or '—'}",
        f"*ЕНТ:* {app.ent_score or '—'}",
        "",
        f"*Олимпиады:* {len(app.olympiads or [])} шт.",
        f"*Курсы:* {len(app.courses or [])} шт.",
        f"*Проекты:* {len(app.projects or [])} шт.",
        "",
    ]
    if app.essay_text:
        words = app.essay_word_count or count_words(app.essay_text)
        lines.append(f"*Эссе:* {words} слов ✅")
    # if app.fingerprint_display:
    #     lines.append("\n*Leadership Fingerprint:*")
    #     labels = {
    #         "model": "Model the Way",
    #         "inspire": "Inspire a Vision",
    #         "challenge": "Challenge the Process",
    #         "enable": "Enable Others",
    #         "encourage": "Encourage the Heart",
    #     }
    #     for k, v in app.fingerprint_display.items():
    #         bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
    #         lines.append(f"  {labels.get(k, k)}: {bar} {v:.1f}")
    if app.uploaded_files:
        lines.append(f"\n*Прикреплённые файлы:* {len(app.uploaded_files)} шт.")
    return "\n".join(lines)


def save_to_json(app_data):
    if not os.path.exists('model_inputs'):
        os.makedirs('model_inputs')

    result = {
        "user_id": app_data.telegram_id,
        "username": app_data.telegram_username,
        "personal": {
            "name": app_data.name,
            "age": app_data.age,
            "city": app_data.city,
            "region": app_data.region,
            "school_type": app_data.school_type,
            "languages": app_data.languages or [],
        },
        "education": {
            "gpa": app_data.gpa,
            "ielts_score": app_data.ielts_score,
            "ent_score": app_data.ent_score,
            "olympiads": app_data.olympiads or [],
            "courses": app_data.courses or [],
        },
        "experience": {
            "projects": app_data.projects or [],
        },
        "essay": {
            "text": app_data.essay_text,
            "word_count": app_data.essay_word_count,
        },
        "bot_metadata": {
            "fingerprint_display": app_data.fingerprint_display,
            "fingerprint_reliable": app_data.fingerprint_reliable or False,
            "timer_violations": app_data.timer_violations or 0,
            "funnel_stage": app_data.funnel_stage,
            "essay_nlp": app_data.essay_nlp,
        },
        "scenario_results": app_data.scenario_choices,
        "submitted_at": datetime.utcnow().isoformat(),
    }

    file_path = f"model_inputs/user_{app_data.telegram_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    return file_path