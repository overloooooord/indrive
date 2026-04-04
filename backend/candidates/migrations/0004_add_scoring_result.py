from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('candidates', '0003_application_essay_application_motivation_letter'),
    ]
    operations = [
        migrations.AddField(
            model_name='application',
            name='scoring_result',
            field=models.JSONField(blank=True, default=None, help_text='Результат pipeline/scorer.py — prediction, confidence, radar, flags', null=True, verbose_name='Результат ML оценки'),
        ),
    ]
