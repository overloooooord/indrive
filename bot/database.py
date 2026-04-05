from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import (
    String, Integer, Boolean, Float, Text, DateTime, JSON, BigInteger, ForeignKey, delete, select, update
)
from datetime import datetime
from config import DATABASE_URL
import json


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
    connect_args={"ssl": "require"},
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String(100))

    # bot_metadata
    funnel_stage: Mapped[str] = mapped_column(String(50), default="started")
    start_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    consent_given: Mapped[bool | None] = mapped_column(Boolean)
    consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime)

    # personal
    name: Mapped[str | None] = mapped_column(String(100))
    age: Mapped[int | None] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))

    # education
    school_type: Mapped[str | None] = mapped_column(String(50))
    gpa: Mapped[float | None] = mapped_column(Float)
    languages: Mapped[list[str] | None] = mapped_column(JSON, default=[])

    # IELTS / ENT
    ielts_score: Mapped[float | None] = mapped_column(Float)
    ent_score: Mapped[int | None] = mapped_column(Integer)

    # education arrays (JSON)
    olympiads: Mapped[dict | None] = mapped_column(JSON, default=list)
    courses: Mapped[dict | None] = mapped_column(JSON, default=list)

    # experience
    projects: Mapped[dict | None] = mapped_column(JSON, default=list)

    # essay
    essay_text: Mapped[str | None] = mapped_column(Text)
    essay_word_count: Mapped[int | None] = mapped_column(Integer)
    essay_nlp: Mapped[dict | None] = mapped_column(JSON)  # computed once by nlp_model after essay submission

    # scenarios / fingerprint
    scenario_choices: Mapped[dict | None] = mapped_column(JSON, default=dict)
    fingerprint_display: Mapped[dict | None] = mapped_column(JSON)
    fingerprint_reliable: Mapped[bool | None] = mapped_column(Boolean)
    timer_violations: Mapped[int] = mapped_column(Integer, default=0)

    # files
    uploaded_files: Mapped[dict | None] = mapped_column(JSON, default=list)

    # full candidate JSON snapshot for ML pipeline (replaces ephemeral file)
    candidate_json: Mapped[dict | None] = mapped_column(JSON)

    # pipeline scoring results (written back by the ML pipeline)
    score_prediction:    Mapped[str | None]   = mapped_column(String(20))
    score_confidence:    Mapped[float | None] = mapped_column(Float)
    score_probabilities: Mapped[dict | None]  = mapped_column(JSON)
    score_explanation:   Mapped[dict | None]  = mapped_column(JSON)
    score_radar:         Mapped[dict | None]  = mapped_column(JSON)
    score_flags:         Mapped[dict | None]  = mapped_column(JSON)
    scored_at:           Mapped[datetime | None] = mapped_column(DateTime)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_application(telegram_id: int, username: str | None = None) -> Application:
    async with async_session() as session:
        # 1. Сначала удаляем старую заявку, если она существует
        await session.execute(
            delete(Application).where(Application.telegram_id == telegram_id)
        )
        await session.commit() # Фиксируем удаление

        # 2. Создаем новую чистую заявку
        app = Application(
            telegram_id=telegram_id,
            telegram_username=username,
            olympiads=[],
            courses=[],
            projects=[],
            uploaded_files=[],
            scenario_choices={},
            funnel_stage="started" # Сбрасываем этап воронки
        )
        session.add(app)
        await session.commit()
        await session.refresh(app)
        return app


async def update_application(telegram_id: int, **fields):
    async with async_session() as session:
        from sqlalchemy import select, update
        fields["updated_at"] = datetime.utcnow()
        await session.execute(
            update(Application).where(Application.telegram_id == telegram_id).values(**fields)
        )
        await session.commit()


async def get_application(telegram_id: int) -> Application | None:
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Application).where(Application.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
