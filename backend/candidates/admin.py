from django.contrib import admin
from .models import Candidate, ScoringResult, Application


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'city', 'school_type', 'get_prediction', 'created_at')
    list_filter = ('city', 'school_type', 'has_mentor')
    search_fields = ('name', 'city', 'region')
    readonly_fields = ('created_at', 'updated_at')

    def get_prediction(self, obj):
        try:
            return obj.scoring.prediction
        except ScoringResult.DoesNotExist:
            return '—'
    get_prediction.short_description = 'Рекомендация'


@admin.register(ScoringResult)
class ScoringResultAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'prediction', 'confidence', 'scored_at')
    list_filter = ('prediction',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'age', 'city', 'region',
        'gpa', 'ielts_score', 'ent_score',
        'source', 'telegram_username', 'get_ml_result', 'status', 'created_at',
    )
    list_filter = ('source', 'status', 'city', 'region')
    search_fields = ('name', 'telegram_username', 'city')
    readonly_fields = ('created_at', 'updated_at')

    def get_ml_result(self, obj):
        if obj.scoring_result and obj.scoring_result.get('prediction'):
            p = obj.scoring_result['prediction']
            c = obj.scoring_result.get('confidence', 0)
            icons = {'shortlist': '✅', 'maybe': '🟡', 'reject': '❌'}
            return f"{icons.get(p, '')} {p} ({c:.0%})"
        return '—'
    get_ml_result.short_description = 'ML оценка'

    def get_languages(self, obj):
        if isinstance(obj.languages, list):
            return ', '.join(obj.languages)
        return str(obj.languages)
    get_languages.short_description = 'Языки'
