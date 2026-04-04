OLYMPIAD_LEVEL_MAP = {
    "school": 1,
    "regional": 2,
    "city": 2,
    "republican": 3,
    "national": 4,
    "international": 4,
}
PROJECT_ROLE_MAP = {
    "participant": 0,
    "key_member": 1,
    "co_founder": 2,
    "founder": 3,
}
PROJECT_TYPES = ["technical", "social", "creative", "business", "educational", "other"]
LABEL_MAP = {
    "reject": 0,
    "maybe": 1,
    "shortlist": 2,
}
LABEL_NAMES = ["reject", "maybe", "shortlist"]
FINGERPRINT_SIZE = 500
STRUCTURED_FEATURES = [
    "f_gpa",
    "f_ent_score",
    "f_ielts_score",
    "f_olympiad_count",
    "f_olympiad_max_level",
    "f_olympiad_has_prize",
    "f_courses_count",
    "f_has_any_courses",
    "f_courses_completed_ratio",
    "f_project_count",
    "f_founder_ratio",
    "f_max_role",
    "f_project_diversity",
    "f_max_team_size",
    "f_role_progression",
    "f_scope_progression",
    "f_skill_diversity_growth",
    "f_activity_years_span",
    "f_persistence_signal",
    "f_failure_acknowledgment_ratio",
]
FEATURE_GROUPS = {
    "Education":  [0, 1, 2, 3, 4, 5, 6, 7, 8],
    "Experience": [9, 10, 11, 12, 13],
    "Trajectory": [14, 15, 16, 17, 18, 19],
    "SLPI":       [20, 21, 22, 23, 24],
    "Essay":      [25, 26, 27, 28, 29, 30],
}
FEATURE_DESCRIPTIONS = {
    "f_gpa":                          "Средний балл (GPA)",
    "f_ent_score":                    "Балл ЕНТ (0–140, норм. 0–1)",
    "f_ielts_score":                  "Балл IELTS (0–9, норм. 0–1)",
    "f_olympiad_count":               "Количество олимпиад",
    "f_olympiad_max_level":           "Максимальный уровень олимпиады",
    "f_olympiad_has_prize":           "Наличие призового места",
    "f_courses_count":                "Количество онлайн-курсов",
    "f_has_any_courses":              "Проходил(а) хоть один курс",
    "f_courses_completed_ratio":      "Доля завершённых курсов",
    "f_project_count":                "Количество проектов",
    "f_founder_ratio":                "Доля проектов как основатель",
    "f_max_role":                     "Максимальная роль в проектах",
    "f_project_diversity":            "Разнообразие типов проектов",
    "f_max_team_size":                "Макс. размер команды (до 500)",
    "f_role_progression":             "Рост ролей (участник → лидер)",
    "f_scope_progression":            "Рост масштаба деятельности",
    "f_skill_diversity_growth":       "Рост разнообразия навыков",
    "f_activity_years_span":          "Период активности (лет)",
    "f_persistence_signal":           "Упорство (продолжил после неудачи)",
    "f_failure_acknowledgment_ratio": "Доля проектов с признанием трудностей",
    "fp_model_the_way":     "SLPI: Пример для других (Model the Way)",
    "fp_inspire_vision":    "SLPI: Вдохновляет на общее видение",
    "fp_challenge_process": "SLPI: Бросает вызов процессу",
    "fp_enable_others":     "SLPI: Развивает других",
    "fp_encourage_heart":   "SLPI: Поддерживает команду",
    "essay_model_the_way":         "Эссе SLPI: Пример для других",
    "essay_inspire_shared_vision": "Эссе SLPI: Вдохновляет на общее видение",
    "essay_challenge_the_process": "Эссе SLPI: Бросает вызов процессу",
    "essay_enable_others_to_act":  "Эссе SLPI: Развивает других",
    "essay_encourage_the_heart":   "Эссе SLPI: Поддерживает команду",
    "essay_overall":               "Эссе SLPI: Общий балл лидерства",
}
SLPI_FEATURES = [
    "model_the_way",
    "inspire_vision",
    "challenge_process",
    "enable_others",
    "encourage_heart",
]
ESSAY_FEATURES = [
    "essay_model_the_way",
    "essay_inspire_shared_vision",
    "essay_challenge_the_process",
    "essay_enable_others_to_act",
    "essay_encourage_the_heart",
    "essay_overall",
]
STAGE_WEIGHTS = {
    "structural":  0.5,
    "fingerprint": 0.25,
    "essay":       0.25,
}
THREE_STAGE_MODEL_PATH = "models/three_stage_model.pkl"
XGBOOST_PARAMS = {
    "n_estimators": 200,
    "max_depth": 5,
    "learning_rate": 0.1,
    "min_child_weight": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "multi:softprob",
    "num_class": 3,
    "eval_metric": "mlogloss",
    "random_state": 42,
}
MODEL_PATH = "models/model.pkl"
SHAP_PLOTS_DIR = "outputs/shap_plots"
METRICS_DIR = "outputs/metrics"
FAIRNESS_DIR = "outputs/fairness"
CURRENT_YEAR = 2025
