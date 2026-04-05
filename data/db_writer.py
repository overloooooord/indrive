"""
Writes ML pipeline scoring results back to the database.

Usage from pipeline:
    from data.db_writer import save_score_to_db
    save_score_to_db(telegram_id=123456, score_result=scorer.score(candidate))
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))
from database import update_application


def save_score_to_db(telegram_id: int, score_result: dict) -> None:
    """
    Saves the output of CandidateScorer.score() or ThreeStageScorer.score()
    back to the candidate's row in the database.

    Parameters
    ----------
    telegram_id  : candidate's Telegram ID (used as the DB key)
    score_result : dict returned by scorer.score(candidate)
    """
    asyncio.run(update_application(
        telegram_id=telegram_id,
        score_prediction=score_result.get("prediction"),
        score_confidence=score_result.get("confidence"),
        score_probabilities=score_result.get("probabilities"),
        score_explanation=score_result.get("explanation"),
        score_radar=score_result.get("radar"),
        score_flags=score_result.get("flags"),
        scored_at=datetime.utcnow(),
    ))
