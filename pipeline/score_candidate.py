"""
Score a single candidate from a JSON file and write results to DB.

Usage:
    cd pipeline
    python score_candidate.py ../bot/model_inputs/user_1262791177.json
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def main():
    if len(sys.argv) < 2:
        print("Usage: python score_candidate.py <path_to_candidate.json>")
        sys.exit(1)

    candidate_path = sys.argv[1]

    with open(candidate_path, "r", encoding="utf-8") as f:
        candidate = json.load(f)

    from scorer import CandidateScorer
    scorer = CandidateScorer()
    result = scorer.score(candidate)

    name = candidate.get("personal", {}).get("name", "Unknown")
    print(f"\n{'─' * 50}")
    print(f"  {name}")
    print(f"  Рекомендация:  {result['prediction'].upper()}")
    print(f"  Уверенность:   {result['confidence']:.1%}")
    print(f"\n  Вероятности:")
    for label, prob in result["probabilities"].items():
        bar = "█" * int(prob * 30)
        print(f"    {label:12s} {bar} {prob:.1%}")
    print(f"\n  Сильные стороны:")
    for f in result["explanation"]["top_positive_factors"]:
        print(f"    + {f['description']} ({f['impact']:+.4f})")
    print(f"\n  Слабые стороны:")
    for f in result["explanation"]["top_negative_factors"]:
        print(f"    - {f['description']} ({f['impact']:+.4f})")
    print(f"{'─' * 50}")

    # Save JSON output
    out_path = f"outputs/score_{result['candidate_id']}.json"
    os.makedirs("outputs", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON: {out_path}")

    # Write to DB
    telegram_id = candidate.get("user_id")
    if telegram_id:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from data.db_writer import save_score_to_db
            save_score_to_db(telegram_id=telegram_id, score_result=result)
            print(f"  БД:   записано (telegram_id={telegram_id})")
        except Exception as e:
            print(f"  [WARN] Не удалось записать в БД: {e}")
    else:
        print("  [WARN] user_id не найден в JSON — в БД не записано")


if __name__ == "__main__":
    main()
