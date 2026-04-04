import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    initial = True
    dependencies = [
    ]
    operations = [
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='ФИО')),
                ('age', models.IntegerField(verbose_name='Возраст')),
                ('city', models.CharField(blank=True, default='', max_length=100, verbose_name='Город')),
                ('region', models.CharField(blank=True, default='', max_length=100, verbose_name='Регион')),
                ('school_type', models.CharField(blank=True, default='', max_length=50, verbose_name='Тип школы')),
                ('has_mentor', models.BooleanField(default=False, verbose_name='Есть ментор')),
                ('profile_data', models.JSONField(verbose_name='Полные данные профиля')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Кандидат',
                'verbose_name_plural': 'Кандидаты',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ScoringResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prediction', models.CharField(max_length=20, verbose_name='Рекомендация')),
                ('confidence', models.FloatField(verbose_name='Уверенность')),
                ('probabilities', models.JSONField(verbose_name='Вероятности')),
                ('full_result', models.JSONField(verbose_name='Полный результат')),
                ('scored_at', models.DateTimeField(auto_now=True, verbose_name='Дата оценки')),
                ('candidate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scoring', to='candidates.candidate', verbose_name='Кандидат')),
            ],
            options={
                'verbose_name': 'Результат оценки',
                'verbose_name_plural': 'Результаты оценки',
            },
        ),
    ]
