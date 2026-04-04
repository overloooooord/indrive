from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('candidates', '0005_botapplication_remove_mbtitestresult_application_and_more'),
    ]
    operations = [
        migrations.CreateModel(
            name='TeacherNomination',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teacher_login', models.CharField(db_index=True, max_length=50, verbose_name='Логин учителя')),
                ('teacher_name', models.CharField(blank=True, max_length=200, verbose_name='ФИО учителя')),
                ('student_name', models.CharField(max_length=200, verbose_name='ФИО ученика')),
                ('student_contacts', models.CharField(help_text='Телефон, email или Telegram', max_length=300, verbose_name='Контакты ученика')),
                ('reason', models.TextField(help_text='Обоснование рекомендации', verbose_name='Почему следует принять')),
                ('achievements', models.TextField(blank=True, help_text='Олимпиады, проекты, награды и т.д.', verbose_name='Достижения ученика')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата рекомендации')),
            ],
            options={
                'verbose_name': 'Рекомендация учителя',
                'verbose_name_plural': 'Рекомендации учителей',
                'ordering': ['-created_at'],
            },
        ),
    ]
