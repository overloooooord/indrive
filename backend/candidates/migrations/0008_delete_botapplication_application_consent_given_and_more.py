from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('candidates', '0007_teacher_nomination_status'),
    ]
    operations = [
        migrations.DeleteModel(
            name='BotApplication',
        ),
        migrations.AddField(
            model_name='application',
            name='consent_given',
            field=models.BooleanField(blank=True, null=True, verbose_name='Согласие дано'),
        ),
        migrations.AddField(
            model_name='application',
            name='consent_timestamp',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время согласия'),
        ),
        migrations.AddField(
            model_name='application',
            name='essay_nlp',
            field=models.JSONField(blank=True, default=dict, null=True, verbose_name='Анализ NLP'),
        ),
        migrations.AddField(
            model_name='application',
            name='essay_text',
            field=models.TextField(blank=True, default='', verbose_name='Эссе (бот)'),
        ),
        migrations.AddField(
            model_name='application',
            name='essay_word_count',
            field=models.IntegerField(blank=True, null=True, verbose_name='Кол-во слов эссе'),
        ),
        migrations.AddField(
            model_name='application',
            name='fingerprint_display',
            field=models.JSONField(blank=True, default=dict, verbose_name='Fingerprint'),
        ),
        migrations.AddField(
            model_name='application',
            name='fingerprint_reliable',
            field=models.BooleanField(blank=True, null=True, verbose_name='Fingerprint надежен'),
        ),
        migrations.AddField(
            model_name='application',
            name='funnel_stage',
            field=models.CharField(blank=True, default='started', max_length=50, verbose_name='Этап воронки'),
        ),
        migrations.AddField(
            model_name='application',
            name='scenario_choices',
            field=models.JSONField(blank=True, default=dict, verbose_name='Сценарии SLPI'),
        ),
        migrations.AddField(
            model_name='application',
            name='score_confidence',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='score_explanation',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='score_flags',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='score_prediction',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='score_probabilities',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='score_radar',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='scored_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='start_timestamp',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время начала бота'),
        ),
        migrations.AddField(
            model_name='application',
            name='timer_violations',
            field=models.IntegerField(default=0, verbose_name='Нарушения таймера'),
        ),
        migrations.AddField(
            model_name='application',
            name='uploaded_files',
            field=models.JSONField(blank=True, default=list, verbose_name='Файлы'),
        ),
        migrations.AlterField(
            model_name='application',
            name='name',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='ФИО'),
        ),
    ]
