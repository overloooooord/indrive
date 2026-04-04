import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('candidates', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Полное имя заявителя', max_length=200, verbose_name='ФИО')),
                ('city', models.CharField(help_text='Город из списка городов Казахстана', max_length=100, verbose_name='Город')),
                ('region', models.CharField(help_text='Регион — определяется автоматически по городу', max_length=100, verbose_name='Регион')),
                ('languages', models.JSONField(default=list, help_text='Массив языков: ["Казахский", "Русский", "Английский"]', verbose_name='Языки')),
                ('telegram_username', models.CharField(help_text='Username в Telegram, например @ivanov', max_length=100, verbose_name='Telegram')),
                ('hobbies', models.TextField(blank=True, default='', help_text='Хобби и увлечения (свободный текст)', verbose_name='Хобби')),
                ('sport', models.CharField(blank=True, default='', help_text='Вид спорта (пока без логики оценки)', max_length=200, verbose_name='Спорт')),
                ('status', models.CharField(choices=[('new', 'Новая'), ('in_review', 'На рассмотрении'), ('accepted', 'Принята'), ('rejected', 'Отклонена')], default='new', max_length=20, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата подачи')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
            ],
            options={
                'verbose_name': 'Заявка',
                'verbose_name_plural': 'Заявки',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LanguageTestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(help_text='Например: Английский, Казахский', max_length=50, verbose_name='Тестируемый язык')),
                ('answers', models.JSONField(help_text='{"q1": "A", "q2": "C", ...}', verbose_name='Ответы')),
                ('score', models.IntegerField(default=0, help_text='Количество правильных ответов', verbose_name='Баллы')),
                ('max_score', models.IntegerField(default=0, help_text='Общее количество вопросов', verbose_name='Максимум баллов')),
                ('time_spent_seconds', models.IntegerField(default=0, help_text='Сколько секунд потратил на тест', verbose_name='Время (сек)')),
                ('violation_count', models.IntegerField(default=0, help_text='Сколько раз пытался уйти из вкладки', verbose_name='Нарушения')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата прохождения')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='language_tests', to='candidates.application', verbose_name='Заявка')),
            ],
            options={
                'verbose_name': 'Результат языкового теста',
                'verbose_name_plural': 'Результаты языковых тестов',
            },
        ),
        migrations.CreateModel(
            name='MBTITestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answers', models.JSONField(help_text='{"q1": "A", "q2": "B", ...} — A или B для каждого вопроса', verbose_name='Ответы')),
                ('result_type', models.CharField(blank=True, default='', help_text='Например: INTJ, ENFP, ISTP', max_length=4, verbose_name='Тип MBTI')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата прохождения')),
                ('application', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='mbti_result', to='candidates.application', verbose_name='Заявка')),
            ],
            options={
                'verbose_name': 'Результат MBTI',
                'verbose_name_plural': 'Результаты MBTI',
            },
        ),
    ]
