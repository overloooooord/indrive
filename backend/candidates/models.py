"""
models.py — Модели базы данных.

Что здесь:
  - Candidate — старая модель для ML pipeline (не трогаем)
  - ScoringResult — результат ML оценки (не трогаем)
  - Application — НОВАЯ модель для заявок пользователей
  - MBTITestResult — результаты MBTI теста
  - LanguageTestResult — результаты языкового теста (с таймером и violation_count)

Все модели используют Django ORM → полная защита от SQL-инъекций.
Пароли хранятся как bcrypt-хеши (не в этих моделях, а в settings).
"""

from django.db import models
import uuid


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Существующие модели (для ML pipeline — НЕ трогаем)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Candidate(models.Model):
    """Candidate profile for InVision U (ML pipeline)."""

    name = models.CharField('ФИО', max_length=200)
    age = models.IntegerField('Возраст')
    city = models.CharField('Город', max_length=100, blank=True, default='')
    region = models.CharField('Регион', max_length=100, blank=True, default='')
    school_type = models.CharField('Тип школы', max_length=50, blank=True, default='')
    has_mentor = models.BooleanField('Есть ментор', default=False)

    # Full candidate data as JSON (education, experience, essay, etc.)
    profile_data = models.JSONField('Полные данные профиля')

    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Кандидат'
        verbose_name_plural = 'Кандидаты'

    def __str__(self):
        return f"{self.name} ({self.city})"

    def to_pipeline_dict(self):
        """Convert to the dict format expected by pipeline/scorer.py

        Origin pipeline expects:
          - candidate["essay"]         → string or {"text": str} for NLP
          - candidate["bot_metadata"]  → dict for SLPI radar (optional)
          - candidate["personal"]      → personal info
          - candidate["education"]     → education data
          - candidate["experience"]    → experience data
        """
        data = self.profile_data.copy()
        data['id'] = str(self.id)
        data['personal'] = {
            'name': self.name,
            'age': self.age,
            'city': self.city,
            'region': self.region,
            'school_type': self.school_type,
            'has_mentor': self.has_mentor,
        }
        if 'personal' in self.profile_data and 'languages' in self.profile_data['personal']:
            data['personal']['languages'] = self.profile_data['personal']['languages']

        # Ensure essay is available for NLP module (origin scorer reads candidate["essay"])
        if 'essay' not in data:
            data['essay'] = ''

        # Ensure bot_metadata exists for SLPI radar (graceful fallback to "pending")
        if 'bot_metadata' not in data:
            data['bot_metadata'] = {}

        return data


class ScoringResult(models.Model):
    """ML scoring result for a candidate."""

    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name='scoring',
        verbose_name='Кандидат',
    )
    prediction = models.CharField('Рекомендация', max_length=20)
    confidence = models.FloatField('Уверенность')
    probabilities = models.JSONField('Вероятности')
    full_result = models.JSONField('Полный результат')
    scored_at = models.DateTimeField('Дата оценки', auto_now=True)

    class Meta:
        verbose_name = 'Результат оценки'
        verbose_name_plural = 'Результаты оценки'

    def __str__(self):
        return f"{self.candidate.name}: {self.prediction} ({self.confidence:.0%})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# НОВЫЕ модели — заявки и тесты
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Application(models.Model):
    """
    Заявка пользователя — схема совпадает с БД бота.

    Все поля зеркалируют bot/database.py → applications table.
    + scoring_result хранит результат ML pipeline.
    """

    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_review', 'На рассмотрении'),
        ('accepted', 'Принята'),
        ('rejected', 'Отклонена'),
    ]

    # ── Идентификация ──
    telegram_id = models.BigIntegerField(
        'Telegram ID', null=True, blank=True, db_index=True,
        help_text='Telegram user ID для рассылки',
    )
    telegram_username = models.CharField(
        'Telegram username', max_length=100, blank=True, default='',
    )

    # ── Личные данные ──
    name = models.CharField('ФИО', max_length=200)
    age = models.IntegerField('Возраст', null=True, blank=True)
    city = models.CharField('Город', max_length=100, blank=True, default='')
    region = models.CharField('Регион', max_length=100, blank=True, default='')
    school_type = models.CharField('Тип школы', max_length=50, blank=True, default='')
    languages = models.JSONField('Языки', default=list, blank=True)

    # ── Образование ──
    gpa = models.FloatField('GPA', null=True, blank=True)
    gpa_raw = models.CharField('GPA (сырой ввод)', max_length=30, blank=True, default='')
    olympiads = models.JSONField('Олимпиады', default=list, blank=True,
        help_text='[{subject, year, level, prize}, ...]')
    courses = models.JSONField('Курсы', default=list, blank=True,
        help_text='[{name, platform, year, completed}, ...]')

    # ── Проекты ──
    projects = models.JSONField('Проекты', default=list, blank=True,
        help_text='[{name, type, year, role, team_size, description}, ...]')

    # ── Эссе ──
    essay = models.TextField('Эссе', blank=True, default='')

    # ── ML scoring ──
    scoring_result = models.JSONField(
        'Результат ML оценки', null=True, blank=True, default=None,
        help_text='prediction, confidence, probabilities, radar, flags',
    )

    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('Дата подачи', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f"#{self.pk} {self.name} — {self.city}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Bot Database — unmanaged model reading from Supabase PostgreSQL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BotApplication(models.Model):
    """
    Unmanaged model mapped to the Telegram bot's `applications` table in Supabase.
    Django does NOT create/migrate this table — it already exists.
    """
    # identity
    telegram_id = models.BigIntegerField(unique=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)

    # bot_metadata
    funnel_stage = models.CharField(max_length=50, default='started')
    start_timestamp = models.DateTimeField(null=True)
    consent_given = models.BooleanField(null=True, blank=True)
    consent_timestamp = models.DateTimeField(null=True)

    # personal
    name = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)

    # education
    school_type = models.CharField(max_length=50, null=True, blank=True)
    gpa_raw = models.CharField(max_length=50, null=True, blank=True)
    gpa = models.FloatField(null=True)
    languages = models.JSONField(null=True, default=list)

    # IELTS / ENT
    ielts_score = models.CharField(max_length=20, null=True, blank=True)
    ent_score = models.CharField(max_length=20, null=True, blank=True)

    # education arrays (JSON)
    olympiads = models.JSONField(null=True, default=list)
    courses = models.JSONField(null=True, default=list)

    # experience
    projects = models.JSONField(null=True, default=list)

    # essay
    essay_text = models.TextField(null=True, blank=True)
    essay_word_count = models.IntegerField(null=True)

    # scenarios / fingerprint
    scenario_choices = models.JSONField(null=True, default=dict)
    fingerprint_display = models.JSONField(null=True)
    fingerprint_reliable = models.BooleanField(null=True, blank=True)
    timer_violations = models.IntegerField(default=0)

    # files
    uploaded_files = models.JSONField(null=True, default=list)

    # pipeline scoring results
    score_prediction = models.CharField(max_length=20, null=True, blank=True)
    score_confidence = models.FloatField(null=True)
    score_probabilities = models.JSONField(null=True)
    score_explanation = models.JSONField(null=True)
    score_radar = models.JSONField(null=True)
    score_flags = models.JSONField(null=True)
    scored_at = models.DateTimeField(null=True)

    updated_at = models.DateTimeField(null=True)

    class Meta:
        managed = False          # Django does NOT create/migrate this table
        db_table = 'applications'  # exact table name in Supabase
        verbose_name = 'Заявка (бот)'
        verbose_name_plural = 'Заявки (бот)'
        ordering = ['-id']

    def __str__(self):
        return f"{self.name or '—'} (tg:{self.telegram_id})"

    def to_pipeline_dict(self):
        """
        Convert to the dict format expected by pipeline/scorer.py.
        Matches data/candidate_scheme.json exactly.
        """
        olympiads = self.olympiads or []
        courses = self.courses or []
        projects = self.projects or []
        fp = self.fingerprint_display or {}

        return {
            'id': str(self.pk),
            'personal': {
                'name': self.name or '',
                'age': self.age or 18,
                'city': self.city or '',
                'region': self.region or '',
                'school_type': self.school_type or '',
                'has_mentor': False,
                'languages': self.languages or [],
            },
            'education': {
                'gpa': self.gpa or 0.0,
                'olympiads': olympiads,
                'courses': courses,
            },
            'experience': {
                'projects': projects,
            },
            'essay': {
                'text': self.essay_text or '',
                'word_count': self.essay_word_count or 0,
            },
            'motivation': {
                'text': '',
            },
            'self_assessment': {},
            'bot_metadata': {
                'fingerprint_display': fp,
                'fingerprint_reliable': bool(self.fingerprint_reliable),
                'scenario_choices': self.scenario_choices or {},
                'timer_violations': self.timer_violations or 0,
            },
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Teacher Cabinet — рекомендации учеников
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TeacherNomination(models.Model):
    STATUS_PENDING  = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES  = [
        (STATUS_PENDING,  'На рассмотрении'),
        (STATUS_ACCEPTED, 'Принято'),
        (STATUS_REJECTED, 'Отклонено'),
    ]

    teacher_login    = models.CharField('Логин учителя', max_length=50, db_index=True)
    teacher_name     = models.CharField('ФИО учителя', max_length=200, blank=True)
    student_name     = models.CharField('ФИО ученика', max_length=200)
    student_contacts = models.CharField('Контакты ученика', max_length=300)
    reason           = models.TextField('Почему следует принять')
    achievements     = models.TextField('Достижения ученика', blank=True)
    status           = models.CharField(
        'Статус', max_length=20,
        choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    admin_note       = models.TextField('Комментарий администратора', blank=True)
    created_at       = models.DateTimeField('Дата рекомендации', auto_now_add=True)
    updated_at       = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Рекомендация учителя'
        verbose_name_plural = 'Рекомендации учителей'

    def __str__(self):
        return f'{self.student_name} ← {self.teacher_name} [{self.status}]'
