
from __future__ import annotations

import gc
import math
import os
import threading
from pathlib import Path
from typing import Optional

import numpy as np
from deep_translator import GoogleTranslator

# Configuration

ONNX_MODEL_ID = "optimum/mobilebert-uncased-mnli"
CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", "/tmp/onnx_model_cache"))

# Logit index for "entailment" label (model-dependent; 0 for most MNLI models)
ENTAILMENT_IDX = 2  # MNLI label order: contradiction=0, neutral=1, entailment=2

MIN_LOG, MAX_LOG = 0.0, 5.0


# Competency definitions (unchanged from original)


COMPETENCY_PAIRS: dict[str, tuple[str, str]] = {
    "model_the_way": (
        "the author gives a concrete example where they personally demonstrated "
        "their values and served as a role model for others",
        "the author only lists abstract qualities without backing them up with "
        "real stories from their life",
    ),
    "inspire_shared_vision": (
        "the author describes how they convinced specific people to join their "
        "idea or project and inspired others toward a shared goal",
        "the author writes only about personal plans without mentioning how they "
        "involved other people",
    ),
    "challenge_the_process": (
        "the author describes a specific situation where they changed the usual "
        "way of doing something or proposed an unconventional solution",
        "the author followed a standard path and does not describe cases where "
        "they changed rules or experimented",
    ),
    "enable_others_to_act": (
        "the author describes a specific case where they helped another person "
        "grow take responsibility or achieve a result",
        "the author does not mention cases of helping others and writes only "
        "about personal achievements",
    ),
    "encourage_the_heart": (
        "the author describes a moment where they publicly recognized someone's "
        "contribution thanked the team or celebrated shared success",
        "the author does not mention recognizing others and does not describe "
        "shared achievements",
    ),
}


# Model singleton — thread-safe, lazy-loaded, unloadable


_lock = threading.Lock()
_session: Optional["onnxruntime.InferenceSession"] = None  # noqa: F821
_tokenizer = None


def _load_model() -> tuple:
    """
    Downloads (once) and loads:
      • HuggingFace tokenizer (CPU-only, no torch)
      • ONNX Runtime InferenceSession with INT8 quantized weights

    Returns (session, tokenizer).
    """
    global _session, _tokenizer


    import onnxruntime as ort
    from transformers import AutoTokenizer

    with _lock:
        if _session is not None:
            return _session, _tokenizer

        CACHE_DIR.mkdir(parents=True, exist_ok=True)




        try:
            from optimum.onnxruntime import ORTModelForSequenceClassification

            print(f"[essay_analyzer] Loading ONNX model: {ONNX_MODEL_ID}")
            # export=False (default): downloads pre-built ONNX directly from Hub,
            # no PyTorch required.
            ort_model = ORTModelForSequenceClassification.from_pretrained(
                ONNX_MODEL_ID,
                cache_dir=str(CACHE_DIR),
            )
            # ort_model.model is the raw InferenceSession
            _session = ort_model.model
            _tokenizer = AutoTokenizer.from_pretrained(
                ONNX_MODEL_ID, cache_dir=str(CACHE_DIR)
            )
        except Exception as exc:


            local_onnx = CACHE_DIR / "model_int8.onnx"
            if local_onnx.exists():
                print(f"[essay_analyzer] Falling back to local ONNX: {local_onnx}")
                sess_opts = ort.SessionOptions()
                sess_opts.graph_optimization_level = (
                    ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                )
                sess_opts.intra_op_num_threads = 2  # cap RAM/CPU on shared hosting
                _session = ort.InferenceSession(
                    str(local_onnx), sess_options=sess_opts
                )
                _tokenizer = AutoTokenizer.from_pretrained(
                    ONNX_MODEL_ID, cache_dir=str(CACHE_DIR)
                )
            else:
                raise RuntimeError(
                    f"Could not load ONNX model ({exc}). "
                    "Run export_model_to_onnx() once to create a local copy."
                ) from exc

        print("[essay_analyzer] Model ready (ONNX Runtime, no PyTorch).")
        return _session, _tokenizer


def unload_model() -> None:
    """
    Explicitly free the ONNX session from memory.
    Call after batch processing if RAM is critical.
    """
    global _session, _tokenizer
    with _lock:
        _session = None
        _tokenizer = None
    gc.collect()
    print("[essay_analyzer] Model unloaded from memory.")



# NLI inference 


def _nli_score(session, tokenizer, premise: str, hypothesis: str) -> float:
    """
    Runs one NLI forward pass and returns P(entailment).

    The hypothesis_template mirrors the original:
        "In this text: {label}"
    """
    import onnxruntime as ort

    full_hypothesis = f"In this text: {hypothesis}"

    enc = tokenizer(
        premise,
        full_hypothesis,
        truncation=True,
        max_length=512,
        padding="max_length",
        return_tensors="np",
    )

    inputs = {k: v.astype(np.int64) for k, v in enc.items()}
    logits = session.run(None, inputs)[0][0]  # shape: (num_labels,)

    # Softmax
    e = np.exp(logits - logits.max())
    probs = e / e.sum()

    return float(probs[ENTAILMENT_IDX])



# Translation


def translate_to_english(text: str) -> str:
    chunks = [text[i : i + 4500] for i in range(0, len(text), 4500)]
    translated = [
        GoogleTranslator(source="ru", target="en").translate(chunk)
        for chunk in chunks
    ]
    return " ".join(translated)



# Scoring 


def calculate_scores_zeroshot(text: str) -> dict:
    text_en = translate_to_english(text)
    session, tokenizer = _load_model()
    scores: dict[str, float] = {}

    for comp, (positive, negative) in COMPETENCY_PAIRS.items():
        pos_score = _nli_score(session, tokenizer, text_en, positive)
        neg_score = _nli_score(session, tokenizer, text_en, negative)

        ratio = pos_score / max(neg_score, 0.001)
        log_score = math.log(ratio)
        normalized = max(0.0, min(1.0, (log_score - MIN_LOG) / (MAX_LOG - MIN_LOG)))
        scores[comp] = round(normalized * 10, 1)

    practices = list(COMPETENCY_PAIRS.keys())
    scores["overall"] = round(
        sum(scores[p] for p in practices) / len(practices), 1
    )
    return scores



# Feedback & public API 


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
    """6-dim feature vector [0..1], matches ESSAY_FEATURES in config."""
    result = get_essay_nlp_result(candidate)
    if result is None:
        return np.zeros(6, dtype=np.float32)

    s = result["scores"]
    return np.array(
        [
            s["model_the_way"] / 10.0,
            s["inspire_shared_vision"] / 10.0,
            s["challenge_the_process"] / 10.0,
            s["enable_others_to_act"] / 10.0,
            s["encourage_the_heart"] / 10.0,
            s["overall"] / 10.0,
            ],
        dtype=np.float32,
    )



def export_model_to_onnx(
        model_id: str = ONNX_MODEL_ID,
        output_dir: Path = CACHE_DIR,
) -> Path:
    """
    Exports a HuggingFace sequence-classification model to ONNX and
    applies dynamic INT8 quantization.

    Requires: pip install optimum[onnxruntime] onnxruntime-tools
    Does NOT require GPU.

    Usage:
        python -c "from essay_analyzer_onnx import export_model_to_onnx; export_model_to_onnx()"
    """
    from optimum.onnxruntime import ORTModelForSequenceClassification
    from optimum.onnxruntime.configuration import AutoQuantizationConfig
    from optimum.onnxruntime import ORTQuantizer

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fp32_dir = output_dir / "fp32"

    print(f"[export] Exporting {model_id} to ONNX FP32 …")
    model = ORTModelForSequenceClassification.from_pretrained(
        model_id, export=True
    )
    model.save_pretrained(fp32_dir)

    print("[export] Quantizing to INT8 (dynamic) …")
    quantizer = ORTQuantizer.from_pretrained(fp32_dir)
    qconfig = AutoQuantizationConfig.avx512_vnni(
        is_static=False, per_channel=False
    )
    quantizer.quantize(
        save_dir=output_dir,
        quantization_config=qconfig,
    )

    out_file = output_dir / "model_quantized.onnx"
    print(f"[export] Done → {out_file}  ({out_file.stat().st_size // 1024} KB)")
    return out_file



if __name__ == "__main__":
    print("=== Essay Leadership Analyzer [ONNX Lightweight] ===")
    text = input("Enter essay:\n")
    try:
        result = analyze_essay(text)
        print(f"\nOverall score: {result['scores']['overall']}/10")
        print(f"Leader type:   {result['feedback']['leader_type']}")
        print("\nBy practice:")
        for k, v in result["scores"].items():
            if k != "overall":
                print(f"  {k}: {v}/10")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Optional: free RAM after CLI use
        unload_model()