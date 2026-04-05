import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Bilingual RU+EN keyword descriptions for each SLPI competency
COMPETENCY_PAIRS = {
    "model_the_way": (
        "личный пример ценности принципы показал сам лидер образец поведение конкретный случай демонстрировал "
        "personal example values role model demonstrated principles showed own behavior led by example",
        "абстрактные качества общие слова нет примеров только теория без доказательств расплывчато "
        "abstract vague no examples only theory no evidence general words"
    ),
    "inspire_shared_vision": (
        "убедил людей вдохновил команду привлёк единомышленников общая цель мотивировал других присоединились идея проект "
        "inspired team convinced people shared goal motivated others joined vision project common purpose",
        "только личные планы не упомянул других нет команды нет вовлечения один без партнёров "
        "only personal plans no others no team no involvement solo no partners"
    ),
    "challenge_the_process": (
        "изменил привычный способ нестандартное решение эксперимент инновация предложил новый подход сломал правила улучшил "
        "changed usual way unconventional solution experiment innovation new approach questioned rules improved process",
        "стандартный путь не менял ничего следовал правилам традиционный подход без изменений "
        "standard path no change followed rules traditional approach no improvement no innovation"
    ),
    "enable_others_to_act": (
        "помог другому вырасти поддержал делегировал доверил ответственность помог достичь наставник развитие команды "
        "helped person grow supported delegated trusted responsibility mentor team development empowered",
        "только личные достижения не помогал другим нет поддержки сольная работа нет упоминания помощи "
        "only personal achievements no helping others no support solo work no mentoring"
    ),
    "encourage_the_heart": (
        "отметил вклад поблагодарил команду праздновал успех признал заслуги похвалил публично ценил людей "
        "recognized contribution thanked team celebrated success acknowledged praised publicly appreciated people",
        "нет признания нет благодарности нет праздника нет упоминания других только про себя "
        "no recognition no thanks no celebration no acknowledgment only about self"
    ),
}

_vectorizer = None
_pos_vectors = None
_neg_vectors = None
_competencies = None


def _build_vectors():
    global _vectorizer, _pos_vectors, _neg_vectors, _competencies
    if _vectorizer is not None:
        return
    _competencies = list(COMPETENCY_PAIRS.keys())
    pos_texts = [COMPETENCY_PAIRS[c][0] for c in _competencies]
    neg_texts = [COMPETENCY_PAIRS[c][1] for c in _competencies]
    # char n-grams (3-5) handle Russian morphology: помог/помогли/помогать → shared substrings
    _vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=8000)
    _vectorizer.fit(pos_texts + neg_texts)
    _pos_vectors = _vectorizer.transform(pos_texts)
    _neg_vectors = _vectorizer.transform(neg_texts)


def calculate_scores(text: str) -> dict:
    _build_vectors()
    text_vec = _vectorizer.transform([text])
    scores = {}
    for i, comp in enumerate(_competencies):
        pos_sim = float(cosine_similarity(text_vec, _pos_vectors[i])[0][0])
        neg_sim = float(cosine_similarity(text_vec, _neg_vectors[i])[0][0])
        total = pos_sim + neg_sim
        normalized = round((pos_sim / total) * 10, 1) if total > 1e-9 else 5.0
        scores[comp] = normalized
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
    scores = calculate_scores(text)
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
        scores["model_the_way"]         / 10.0,
        scores["inspire_shared_vision"] / 10.0,
        scores["challenge_the_process"] / 10.0,
        scores["enable_others_to_act"]  / 10.0,
        scores["encourage_the_heart"]   / 10.0,
        scores["overall"]               / 10.0,
    ], dtype=np.float32)


if __name__ == "__main__":
    text = input("Enter essay:\n")
    try:
        result = analyze_essay(text)
        print(f"\nOverall: {result['scores']['overall']}/10  ({result['feedback']['leader_type']})")
        for k, v in result["scores"].items():
            if k != "overall":
                print(f"  {k}: {v}/10")
    except Exception as e:
        print(f"Error: {e}")
