import argparse
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
def main():
    parser = argparse.ArgumentParser(description="InVision U ML Pipeline")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to labeled dataset JSON (list of candidates with 'label' field)",
    )
    parser.add_argument(
        "--candidate",
        default=None,
        help="Path to single candidate JSON for demo scoring",
    )
    parser.add_argument(
        "--skip-fairness",
        action="store_true",
        help="Skip fairness audit",
    )
    parser.add_argument(
        "--skip-ablation",
        action="store_true",
        help="Skip ablation study",
    )
    args = parser.parse_args()
    print("\n" + "█" * 60)
    print("  STEP 1: TRAINING")
    print("█" * 60)
    from trainer import train
    training_results = train(args.dataset)
    print("\n" + "█" * 60)
    print("  STEP 2: EVALUATION")
    print("█" * 60)
    from evaluator import evaluate
    eval_results = evaluate(training_results)
    if not args.skip_ablation:
        print("\n" + "█" * 60)
        print("  STEP 3: ABLATION STUDY")
        print("█" * 60)
        from xgboost import XGBClassifier
        from config import XGBOOST_PARAMS
        from explainer import ablation_study
        ablation = ablation_study(
            XGBClassifier,
            XGBOOST_PARAMS,
            training_results["X_train"],
            training_results["y_train"],
            training_results["X_test"],
            training_results["y_test"],
        )
    print("\n" + "█" * 60)
    print("  STEP 4: FEATURE IMPORTANCE")
    print("█" * 60)
    from explainer import CandidateExplainer
    global_explainer = CandidateExplainer(
        training_results["model"],
        training_results["X_train"],
    )
    importance = global_explainer.global_importance(training_results["X_train"])
    print("\n=== Global Feature Importance (SHAP) ===\n")
    for i, feat in enumerate(importance[:10]):
        bar = "█" * int(feat["mean_abs_shap"] * 100)
        print(f"  {i + 1:2d}. {feat['description']:40s} {bar} ({feat['mean_abs_shap']:.4f})")
    if not args.skip_fairness:
        print("\n" + "█" * 60)
        print("  STEP 5: FAIRNESS AUDIT")
        print("█" * 60)
        from scorer import CandidateScorer
        from fairness_audit import run_fairness_audit, save_fairness_report, check_proxy_correlations
        from feature_extractor import extract_batch
        from config import STRUCTURED_FEATURES
        with open(args.dataset, "r", encoding="utf-8") as f:
            all_candidates = json.load(f)
        scorer = CandidateScorer(X_background=training_results["X_train"])
        all_predictions = scorer.score_batch(all_candidates)
        audit = run_fairness_audit(all_candidates, all_predictions)
        save_fairness_report(audit)
        X_all = extract_batch(all_candidates)
        check_proxy_correlations(all_candidates, X_all, STRUCTURED_FEATURES)
    if args.candidate:
        print("\n" + "█" * 60)
        print("  STEP 6: DEMO — SINGLE CANDIDATE SCORING")
        print("█" * 60)
        with open(args.candidate, "r", encoding="utf-8") as f:
            candidate = json.load(f)
        from scorer import CandidateScorer
        scorer = CandidateScorer(X_background=training_results["X_train"])
        result = scorer.score(candidate)
        name = candidate.get("personal", {}).get("name", "Unknown")
        print(f"\n{'─' * 50}")
        print(f"  {name}")
        print(f"  {candidate.get('personal', {}).get('city', '?')}, "
              f"{candidate.get('personal', {}).get('age', '?')} лет")
        print(f"{'─' * 50}")
        print(f"\n  Рекомендация:  {result['prediction'].upper()}")
        print(f"  Уверенность:   {result['confidence']:.1%}")
        print(f"\n  Вероятности:")
        for label, prob in result["probabilities"].items():
            bar = "█" * int(prob * 30)
            print(f"    {label:12s} {bar} {prob:.1%}")
        print(f"\n  ✅ Сильные стороны:")
        for f in result["explanation"]["top_positive_factors"]:
            print(f"     {f['description']} (вклад: +{f['impact']:.4f})")
        print(f"\n  ⚠️ Слабые стороны:")
        for f in result["explanation"]["top_negative_factors"]:
            print(f"     {f['description']} (вклад: {f['impact']:.4f})")
        print(f"\n  Leadership Fingerprint (SLPI):")
        radar = result["radar"]
        print(f"    Status: {radar.get('status')}")
        for dim in ("model_the_way", "inspire_vision", "challenge_process", "enable_others", "encourage_heart"):
            val = radar.get(dim)
            if val is not None:
                print(f"    {dim:25s} {'█' * int(val * 20)} {val:.2f}")
            else:
                print(f"    {dim:25s} pending")
        out_path = f"outputs/score_{result['candidate_id']}.json"
        os.makedirs("outputs", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n  Результат сохранён: {out_path}")
        telegram_id = candidate.get("user_id")
        if telegram_id:
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
                from data.db_writer import save_score_to_db
                save_score_to_db(telegram_id=telegram_id, score_result=result)
                print(f"  Результат записан в БД (telegram_id={telegram_id})")
            except Exception as e:
                print(f"  [WARN] Не удалось записать в БД: {e}")
    print("\n" + "█" * 60)
    print("  PIPELINE COMPLETE")
    print("█" * 60)
    print(f)
if __name__ == "__main__":
    main()
