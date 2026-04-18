from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0002_sitesettings'),
    ]

    operations = [
        # About section
        migrations.AddField('SiteSettings', 'show_about',
            models.BooleanField(default=True, help_text='Show the About section on the home page')),
        migrations.AddField('SiteSettings', 'about_en',
            models.TextField(blank=True, default='', help_text='English description (HTML allowed)')),
        migrations.AddField('SiteSettings', 'about_it',
            models.TextField(blank=True, default='', help_text='Italian description (HTML allowed)')),

        # Key Information section
        migrations.AddField('SiteSettings', 'show_keyinfo',
            models.BooleanField(default=True)),
        migrations.AddField('SiteSettings', 'project_date',
            models.CharField(blank=True, default='2024 \u2013 ongoing', max_length=60)),
        migrations.AddField('SiteSettings', 'institution_name',
            models.CharField(blank=True, default='Universit\xe0 degli Studi Roma Tre', max_length=200)),
        migrations.AddField('SiteSettings', 'institution_dept',
            models.CharField(blank=True, default='Dipartimento di Studi Umanistici', max_length=200)),
        migrations.AddField('SiteSettings', 'lab_name',
            models.CharField(blank=True, default='Archeopaesaggi Roma Tre', max_length=200)),
        migrations.AddField('SiteSettings', 'lab_instagram',
            models.CharField(blank=True, default='archeopaesaggi_roma3',
                             help_text='Instagram handle without @', max_length=100)),
        migrations.AddField('SiteSettings', 'phd_title',
            models.CharField(blank=True,
                             default='Shared Archaeological Landscapes / Paesaggi Archeologici Condivisi',
                             max_length=400)),
        migrations.AddField('SiteSettings', 'phd_researcher',
            models.CharField(blank=True, default='Margherita Bottoni', max_length=200)),
        migrations.AddField('SiteSettings', 'phd_years',
            models.CharField(blank=True, default='2024\u20132027', max_length=20)),

        # Team section
        migrations.AddField('SiteSettings', 'show_team',
            models.BooleanField(default=True)),
        migrations.AddField('SiteSettings', 'team_coordinators',
            models.TextField(blank=True,
                             default='Emanuele Farinetti | Project Coordinator \u2014 Universit\xe0 Roma Tre\nMargherita Bottoni | Project Coordinator & PhD Researcher',
                             help_text='One member per line: "Name | Role"')),
        migrations.AddField('SiteSettings', 'team_technical',
            models.TextField(blank=True,
                             default='Emanuele Bellini | Technical Developer\nErgin Mehmeti | Technical Developer',
                             help_text='One member per line: "Name | Role"')),

        # Logos section
        migrations.AddField('SiteSettings', 'show_logos',
            models.BooleanField(default=True)),
        migrations.AddField('SiteSettings', 'logo_partner_1',
            models.ImageField(blank=True, null=True,
                              help_text='First partner logo (e.g. Universit\xe0 Roma Tre)',
                              upload_to='site/')),
        migrations.AddField('SiteSettings', 'logo_partner_1_name',
            models.CharField(blank=True, default='Universit\xe0 degli Studi Roma Tre', max_length=200)),
        migrations.AddField('SiteSettings', 'logo_partner_2',
            models.ImageField(blank=True, null=True,
                              help_text='Second partner logo (e.g. Archeopaesaggi)',
                              upload_to='site/')),
        migrations.AddField('SiteSettings', 'logo_partner_2_name',
            models.CharField(blank=True, default='Archeopaesaggi Roma Tre', max_length=200)),
        migrations.AddField('SiteSettings', 'logo_partner_3',
            models.ImageField(blank=True, null=True,
                              help_text='Third partner logo (optional)',
                              upload_to='site/')),
        migrations.AddField('SiteSettings', 'logo_partner_3_name',
            models.CharField(blank=True, default='', max_length=200)),
    ]
