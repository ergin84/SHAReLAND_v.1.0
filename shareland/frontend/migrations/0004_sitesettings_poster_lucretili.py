from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0003_sitesettings_project_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='poster_lucretili',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='site/',
                help_text="Event poster – Sulle orme di un viaggiatore dell'800 (Monti Lucretili)",
            ),
        ),
    ]
