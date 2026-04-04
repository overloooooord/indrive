from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ('candidates', '0002_application_languagetestresult_mbtitestresult'),
    ]
    operations = [
        migrations.AddField(
            model_name='application',
            name='essay',
            field=models.TextField(blank=True, default='', help_text='Эссе кандидата', verbose_name='Эссе'),
        ),
        migrations.AddField(
            model_name='application',
            name='motivation_letter',
            field=models.TextField(blank=True, default='', help_text='Почему кандидат хочет учиться у нас', verbose_name='Мотивационное письмо'),
        ),
    ]
