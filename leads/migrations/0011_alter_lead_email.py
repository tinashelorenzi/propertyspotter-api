# Generated by Django 5.0.2 on 2025-06-10 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0010_lead_preferred_agent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lead',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
