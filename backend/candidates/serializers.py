"""
serializers.py — Сериалайзеры для валидации входных данных.

Упрощённая версия: только Candidate (ML pipeline), Application (бот-данные).
MBTI и LanguageTest удалены — не используются ботом.
"""

from rest_framework import serializers
from .models import Candidate, ScoringResult, Application
from .kz_regions import (
    CITY_REGION_MAP, LANGUAGES_CHOICES,
    validate_city_region, get_regions_for_city,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. ML pipeline serializers (Candidate model)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ScoringResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoringResult
        fields = ['prediction', 'confidence', 'probabilities', 'full_result', 'scored_at']


class CandidateListSerializer(serializers.ModelSerializer):
    prediction = serializers.SerializerMethodField()
    confidence = serializers.SerializerMethodField()
    gpa = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'age', 'city', 'region', 'school_type',
            'gpa', 'project_count', 'prediction', 'confidence', 'created_at',
        ]

    def get_prediction(self, obj):
        try:
            return obj.scoring.prediction
        except ScoringResult.DoesNotExist:
            return None

    def get_confidence(self, obj):
        try:
            return obj.scoring.confidence
        except ScoringResult.DoesNotExist:
            return None

    def get_gpa(self, obj):
        return obj.profile_data.get('education', {}).get('gpa', None)

    def get_project_count(self, obj):
        return len(obj.profile_data.get('experience', {}).get('projects', []))


class CandidateDetailSerializer(serializers.ModelSerializer):
    scoring = ScoringResultSerializer(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'age', 'city', 'region', 'school_type',
            'has_mentor', 'profile_data', 'scoring', 'created_at',
        ]


class CandidateRegisterSerializer(serializers.Serializer):
    """Accepts the full candidate JSON (matching candidate_scheme.json)."""
    personal = serializers.DictField(required=True)
    education = serializers.DictField(required=True)
    experience = serializers.DictField(required=False, default=dict)
    essay = serializers.DictField(required=False, default=dict)
    motivation = serializers.DictField(required=False, default=dict)
    self_assessment = serializers.DictField(required=False, default=dict)
    bot_metadata = serializers.DictField(required=False, default=dict)

    def validate_personal(self, value):
        if 'name' not in value:
            raise serializers.ValidationError("Поле 'name' обязательно")
        if 'age' not in value:
            raise serializers.ValidationError("Поле 'age' обязательно")
        return value

    def create(self, validated_data):
        personal = validated_data['personal']
        candidate = Candidate.objects.create(
            name=personal.get('name', ''),
            age=personal.get('age', 0),
            city=personal.get('city', ''),
            region=personal.get('region', ''),
            school_type=personal.get('school_type', ''),
            has_mentor=personal.get('has_mentor', False),
            profile_data=validated_data,
        )
        return candidate


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Application serializers (бот-формат)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ApplicationSerializer(serializers.ModelSerializer):
    """
    CRUD сериалайзер для заявок (бот-формат).
    Включает все поля: personal, education (GPA, olympiads, courses),
    projects, essay, telegram_id.
    """

    class Meta:
        model = Application
        fields = [
            'id', 'telegram_id', 'telegram_username',
            'name', 'age', 'city', 'region', 'school_type', 'languages',
            'gpa', 'gpa_raw', 'olympiads', 'courses',
            'projects', 'essay',
            'scoring_result', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'scoring_result', 'created_at', 'updated_at']

    def validate_city(self, value):
        if not value:
            return value
        value = value.strip()
        if value not in CITY_REGION_MAP:
            # Allow free-text cities (bot doesn't validate against a list)
            pass
        return value

    def validate_telegram_username(self, value):
        if not value:
            return value
        value = value.strip()
        if value.startswith('@'):
            value = value[1:]
        return f"@{value}" if value else ''


class ApplicationListSerializer(serializers.ModelSerializer):
    """Compact serializer for list views."""

    class Meta:
        model = Application
        fields = [
            'id', 'name', 'city', 'region', 'telegram_username',
            'gpa', 'status', 'created_at',
        ]


class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100)
