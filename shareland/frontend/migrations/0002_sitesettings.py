from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(default='SHAReLAND', max_length=100)),
                ('tagline', models.CharField(blank=True, default='Archaeological Research Database', max_length=200)),
                ('logo', models.ImageField(blank=True, help_text='Replaces the default SVG logo in the navbar', null=True, upload_to='site/')),
                ('favicon', models.ImageField(blank=True, help_text='Browser tab icon (recommended: 32×32 PNG)', null=True, upload_to='site/')),
                ('navbar_primary', models.CharField(default='#2c3e50', help_text='Navbar gradient – left colour', max_length=7)),
                ('navbar_secondary', models.CharField(default='#34495e', help_text='Navbar gradient – right colour', max_length=7)),
                ('navbar_accent', models.CharField(default='#3498db', help_text='Navbar bottom border & active link colour', max_length=7)),
                ('navbar_text', models.CharField(default='#ecf0f1', help_text='Navbar link / brand text colour', max_length=7)),
                ('page_bg', models.CharField(default='#f5f6fa', help_text='Main page background', max_length=7)),
                ('card_accent', models.CharField(default='#3498db', help_text='Buttons, links, highlights', max_length=7)),
                ('footer_text', models.TextField(blank=True, default='© SHAReLAND – Archaeological Research Database')),
            ],
            options={
                'verbose_name': 'Site Settings',
                'db_table': 'site_settings',
            },
        ),
    ]
