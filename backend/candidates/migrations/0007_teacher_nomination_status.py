from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('candidates', '0006_teacher_nomination'),
    ]
    operations = [
        migrations.AddField(
            model_name='teachernomination',
            name='admin_note',
            field=models.TextField(blank=True, verbose_name='Комментарий администратора'),
        ),
        migrations.AddField(
            model_name='teachernomination',
            name='status',
            field=models.CharField(choices=[('pending', 'На рассмотрении'), ('accepted', 'Принято'), ('rejected', 'Отклонено')], db_index=True, default='pending', max_length=20, verbose_name='Статус'),
        ),
        migrations.AddField(
            model_name='teachernomination',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата обновления'),
        ),
        migrations.AlterField(
            model_name='teachernomination',
            name='achievements',
            field=models.TextField(blank=True, verbose_name='Достижения ученика'),
        ),
        migrations.AlterField(
            model_name='teachernomination',
            name='reason',
            field=models.TextField(verbose_name='Почему следует принять'),
        ),
        migrations.AlterField(
            model_name='teachernomination',
            name='student_contacts',
            field=models.CharField(max_length=300, verbose_name='Контакты ученика'),
        ),
    ]
