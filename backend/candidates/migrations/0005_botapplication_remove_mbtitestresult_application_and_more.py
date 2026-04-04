from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('candidates', '0004_add_scoring_result'),
    ]
    operations = [
        migrations.CreateModel(
            name='BotApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.BigIntegerField(unique=True)),
                ('telegram_username', models.CharField(blank=True, max_length=100, null=True)),
                ('funnel_stage', models.CharField(default='started', max_length=50)),
                ('start_timestamp', models.DateTimeField(null=True)),
                ('consent_given', models.BooleanField(blank=True, null=True)),
                ('consent_timestamp', models.DateTimeField(null=True)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('age', models.IntegerField(null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('region', models.CharField(blank=True, max_length=100, null=True)),
                ('school_type', models.CharField(blank=True, max_length=50, null=True)),
                ('gpa_raw', models.CharField(blank=True, max_length=50, null=True)),
                ('gpa', models.FloatField(null=True)),
                ('languages', models.JSONField(default=list, null=True)),
                ('ielts_score', models.CharField(blank=True, max_length=20, null=True)),
                ('ent_score', models.CharField(blank=True, max_length=20, null=True)),
                ('olympiads', models.JSONField(default=list, null=True)),
                ('courses', models.JSONField(default=list, null=True)),
                ('projects', models.JSONField(default=list, null=True)),
                ('essay_text', models.TextField(blank=True, null=True)),
                ('essay_word_count', models.IntegerField(null=True)),
                ('scenario_choices', models.JSONField(default=dict, null=True)),
                ('fingerprint_display', models.JSONField(null=True)),
                ('fingerprint_reliable', models.BooleanField(blank=True, null=True)),
                ('timer_violations', models.IntegerField(default=0)),
                ('uploaded_files', models.JSONField(default=list, null=True)),
                ('score_prediction', models.CharField(blank=True, max_length=20, null=True)),
                ('score_confidence', models.FloatField(null=True)),
                ('score_probabilities', models.JSONField(null=True)),
                ('score_explanation', models.JSONField(null=True)),
                ('score_radar', models.JSONField(null=True)),
                ('score_flags', models.JSONField(null=True)),
                ('scored_at', models.DateTimeField(null=True)),
                ('updated_at', models.DateTimeField(null=True)),
            ],
            options={
                'verbose_name': 'Заявка (бот)',
                'verbose_name_plural': 'Заявки (бот)',
                'db_table': 'applications',
                'ordering': ['-id'],
                'managed': False,
            },
        ),
        migrations.RemoveField(
            model_name='mbtitestresult',
            name='application',
        ),
        migrations.RemoveField(
            model_name='application',
            name='hobbies',
        ),
        migrations.RemoveField(
            model_name='application',
            name='motivation_letter',
        ),
        migrations.RemoveField(
            model_name='application',
            name='sport',
        ),
        migrations.AddField(
            model_name='application',
            name='age',
            field=models.IntegerField(blank=True, null=True, verbose_name='Возраст'),
        ),
        migrations.AddField(
            model_name='application',
            name='courses',
            field=models.JSONField(blank=True, default=list, help_text='[{name, platform, year, completed}, ...]', verbose_name='Курсы'),
        ),
        migrations.AddField(
            model_name='application',
            name='gpa',
            field=models.FloatField(blank=True, null=True, verbose_name='GPA'),
        ),
        migrations.AddField(
            model_name='application',
            name='gpa_raw',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='GPA (сырой ввод)'),
        ),
        migrations.AddField(
            model_name='application',
            name='olympiads',
            field=models.JSONField(blank=True, default=list, help_text='[{subject, year, level, prize}, ...]', verbose_name='Олимпиады'),
        ),
        migrations.AddField(
            model_name='application',
            name='projects',
            field=models.JSONField(blank=True, default=list, help_text='[{name, type, year, role, team_size, description}, ...]', verbose_name='Проекты'),
        ),
        migrations.AddField(
            model_name='application',
            name='school_type',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Тип школы'),
        ),
        migrations.AddField(
            model_name='application',
            name='telegram_id',
            field=models.BigIntegerField(blank=True, db_index=True, help_text='Telegram user ID для рассылки', null=True, verbose_name='Telegram ID'),
        ),
        migrations.AlterField(
            model_name='application',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Город'),
        ),
        migrations.AlterField(
            model_name='application',
            name='essay',
            field=models.TextField(blank=True, default='', verbose_name='Эссе'),
        ),
        migrations.AlterField(
            model_name='application',
            name='languages',
            field=models.JSONField(blank=True, default=list, verbose_name='Языки'),
        ),
        migrations.AlterField(
            model_name='application',
            name='name',
            field=models.CharField(max_length=200, verbose_name='ФИО'),
        ),
        migrations.AlterField(
            model_name='application',
            name='region',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Регион'),
        ),
        migrations.AlterField(
            model_name='application',
            name='scoring_result',
            field=models.JSONField(blank=True, default=None, help_text='prediction, confidence, probabilities, radar, flags', null=True, verbose_name='Результат ML оценки'),
        ),
        migrations.AlterField(
            model_name='application',
            name='telegram_username',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Telegram username'),
        ),
        migrations.DeleteModel(
            name='LanguageTestResult',
        ),
        migrations.DeleteModel(
            name='MBTITestResult',
        ),
    ]
