import re
import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple
from collections import Counter

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM


@dataclass
class DetectionResult:
    label: str
    confidence: float
    ai_probability: float
    flags: List[str]
    features: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "ai_probability": round(self.ai_probability, 3),
            "flags": self.flags,
            "features": {k: round(v, 4) for k, v in self.features.items()}
        }


def split_sentences(text: str) -> List[str]:
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


class BinocularsCalculator:
    OBSERVER_MODEL  = "mistralai/Mistral-7B-v0.1"
    PERFORMER_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
    MAX_TOKENS      = 512

    def __init__(self, observer_name: str = None, performer_name: str = None):
        self.observer_name  = observer_name  or self.OBSERVER_MODEL
        self.performer_name = performer_name or self.PERFORMER_MODEL
        self._observer      = None
        self._performer     = None
        self._tokenizer     = None

    def _load(self):
        if self._observer is not None:
            return

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype  = torch.float16 if device == "cuda" else torch.float32

        print(f"[Binoculars] Загружаю observer: {self.observer_name}")
        self._tokenizer = AutoTokenizer.from_pretrained(self.observer_name, trust_remote_code=True)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        self._observer = AutoModelForCausalLM.from_pretrained(
            self.observer_name,
            torch_dtype=dtype,
            device_map="auto",
            trust_remote_code=True,
        ).eval()

        self._performer = AutoModelForCausalLM.from_pretrained(
            self.performer_name,
            torch_dtype=dtype,
            device_map="auto",
            trust_remote_code=True,
        ).eval()

        print("[Binoculars] Обе модели загружены ✓")

    def _get_token_log_probs(self, model, input_ids) -> torch.Tensor:
        with torch.no_grad():
            outputs = model(input_ids)
            logits  = outputs.logits

        shift_logits = logits[:, :-1, :]
        shift_labels = input_ids[:, 1:]
        log_probs    = F.log_softmax(shift_logits, dim=-1)

        token_log_probs = log_probs.gather(
            dim=-1,
            index=shift_labels.unsqueeze(-1)
        ).squeeze(-1)

        return token_log_probs.squeeze(0)

    def calculate(self, text: str) -> Tuple[float, float, float]:
        self._load()

        enc = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.MAX_TOKENS
        )
        input_ids = enc.input_ids.to(next(self._observer.parameters()).device)

        if input_ids.shape[1] < 5:
            return 1.0, 1.0, 1.0

        obs_log_probs  = self._get_token_log_probs(self._observer,  input_ids)
        perf_log_probs = self._get_token_log_probs(self._performer, input_ids)

        ppl_observer = float(torch.exp(-obs_log_probs.mean()).item())

        cross_entropy = -(perf_log_probs).mean()
        cross_ppl     = float(torch.exp(cross_entropy).item())

        binoculars_score = ppl_observer / (cross_ppl + 1e-10)

        return binoculars_score, ppl_observer, cross_ppl


class ThresholdClassifier:
    BINO_AI_THRESHOLD   = 0.9
    BINO_GRAY_THRESHOLD = 1.0

    def classify(self, bino_score: float, ppl: float, features: dict) -> DetectionResult:
        flags = []

        if bino_score < self.BINO_AI_THRESHOLD:
            label = "LIKELY_AI"
            ai_probability = 1.0 - (bino_score / self.BINO_AI_THRESHOLD) * 0.35
            confidence = ai_probability
            flags.append(
                f"Binoculars score: {bino_score:.3f} (ниже порога 0.9) — "
                f"обе языковые модели уверенно предсказывают этот текст, "
                f"что характерно для AI-генерации. "
                f"Человеческий текст обычно менее предсказуем."
            )

        elif bino_score < self.BINO_GRAY_THRESHOLD:
            label = "POSSIBLE_AI"
            t = (bino_score - self.BINO_AI_THRESHOLD) / (self.BINO_GRAY_THRESHOLD - self.BINO_AI_THRESHOLD)
            ai_probability = 0.65 - t * 0.25
            confidence = max(0.0, 1.0 - abs(ai_probability - 0.525) * 4)
            flags.append(
                f"Binoculars score: {bino_score:.3f} (серая зона 0.9–1.0) — "
                f"модели частично согласны с текстом. "
                f"Текст может быть написан человеком с помощью AI, "
                f"либо отредактирован после генерации."
            )

        else:
            label = "LIKELY_HUMAN"
            ai_probability = max(0.0, 0.40 - (bino_score - 1.0) * 0.20)
            confidence = 1.0 - ai_probability
            flags.append(
                f"Binoculars score: {bino_score:.3f} (выше порога 1.0) — "
                f"языковые модели плохо предсказывают этот текст, "
                f"что типично для живого человеческого письма "
                f"с индивидуальным стилем и непредсказуемыми формулировками."
            )

        if ppl < 20:
            flags.append(
                f"Perplexity (сложность текста): {ppl:.1f} — очень низкая. "
                f"Текст крайне предсказуем и гладок, что редко встречается "
                f"у людей и типично для языковых моделей."
            )
        elif ppl < 50:
            flags.append(
                f"Perplexity (сложность текста): {ppl:.1f} — умеренная. "
                f"Текст достаточно предсказуем, но не критично."
            )
        else:
            flags.append(
                f"Perplexity (сложность текста): {ppl:.1f} — высокая. "
                f"Текст непредсказуем и разнообразен, что характерно для человека."
            )

        word_count = features.get("word_count", 0)
        if word_count < 100:
            flags.append(
                f"Длина текста: {word_count} слов — слишком мало для уверенного вывода. "
                f"Точность детектора растёт с объёмом текста."
            )

        return DetectionResult(
            label=label,
            confidence=round(min(max(confidence, 0.0), 1.0), 3),
            ai_probability=round(ai_probability, 3),
            flags=flags,
            features={
                "binoculars_score": round(bino_score, 4),
                "observer_ppl":     round(ppl, 2),
            }
        )


class AIDetector:
    MIN_WORDS = 50

    def __init__(self, observer_model: str = None, performer_model: str = None):
        self.binoculars = BinocularsCalculator(observer_model, performer_model)
        self.classifier = ThresholdClassifier()

    def detect(self, text: str) -> DetectionResult:
        text = text.strip()

        word_count = len(re.findall(r'\b\w+\b', text))
        if word_count < self.MIN_WORDS:
            return DetectionResult(
                label="INSUFFICIENT_TEXT",
                confidence=0.0,
                ai_probability=0.0,
                flags=[f"Слишком короткий текст ({word_count} слов, минимум {self.MIN_WORDS})"],
            )

        bino_score, ppl, cross_ppl = self.binoculars.calculate(text)

        features = {
            "cross_ppl": round(cross_ppl, 2),
            "word_count": word_count,
        }

        return self.classifier.classify(bino_score, ppl, features)


# --- Запуск ---

detector = AIDetector()


ESSAY = """ayev University admission department, I hope this letter finds you well. I am writing to express 
my strong desire to study at Nazarbyev University.  
I am Alinur, a final-year student at the Innovation Technologies Lyceum. My aspiration to attend NU has 
evolved into a clear goal, driven by my passion for computer science and personal growth. In this essay, I 
will elaborate on the reasons behind my strong desire to study at NU and provide insight into my academic 
achievements, and briefly recount the accident that had a major impact on shaping my dream.  
My dream Is rooted in altruism, a desire to positively influence the world. I wholeheartedly believe that by 
continuously improving myself, I can share more love and make a meaningful difference in others’ lives. My 
dream is an ongoing journey, a commitment to personal growth and making a positive influence in the lives 
of others. Nazarbayev University plays essential role in this journey, offering the tools and knowledge that I 
need. The remarkable success of NU alumni, with 96% of them acknowledging the value of university, 
further motivates my choice. My goal is to leverage AI to benefit society, and the interdisciplinary program 
focusing on computer science and AI at NU aligns perfectly with my aim.  I believe that NU will equip me 
with the skills and knowledge necessary to make a meaningful impact. So I choose NU for its program, 
which will sustain me with knowledge to help people. 
Nevertheless, I came to this dream after realizing that I want to be a light in such a dark world, to let people 
warm near me. I had a grandpa, he is the person of bright smile and diligent hands. I always helped him with 
various kind of job. Once, when we finished work, he went home. By his way, his heart stopped beating. I 
was near, and saw him. I do not want to blame an ambulance, but at this moment I felt helplessness and 
despair near my grandpa’s body. By the time when ambulance came, my grandpa had passed away. It was a 
big misery for me. This experience led me to a commitment to help prevent others from feeling the same 
way, and I will do my best to help others avoid the same fate. This is where my programming skills come in. 
I have acquired proficiency in one programming language, validated by a certificate from the Samsung 
Innovation Campus program. This experience has deepened my understanding of this field, aligning 
perfectly with my desire to study at NU. My decision made my dream, and my achievements are bringing 
my goal closer.  
In conclusion, my dream of leveraging AI for the benefit of society and my personal commitment to 
continuous self-improvement align accurately with the program offered by NU. I choose Nazarbayev 
University, as I will be provided with resources to make a positive difference in others’ lives. I want to 
express my sincere gratitude to the admission department for considering my essay.
"""

result = detector.detect(HUMAN_ESSAY)
print("Лейбл        :", result.label)
print("AI вероятность:", result.ai_probability)
print("Уверенность  :", result.confidence)
print("\nФлаги:")
for flag in result.flags:
    print(" -", flag)