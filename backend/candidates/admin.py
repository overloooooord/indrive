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
        'name', 'age', 'city', 'region', 'gpa',
        'telegram_username', 'status', 'created_at',
    )
    list_filter = ('city', 'status', 'region')
    search_fields = ('name', 'telegram_username', 'city')
    readonly_fields = ('created_at', 'updated_at')
    def get_languages(self, obj):
        if isinstance(obj.languages, list):
            return ', '.join(obj.languages)
        return str(obj.languages)
    get_languages.short_description = 'Языки'
