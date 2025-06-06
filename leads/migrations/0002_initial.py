# Generated by Django 5.0.2 on 2025-05-20 13:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('leads', '0001_initial'),
        ('properties', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='agent',
            field=models.ForeignKey(blank=True, limit_choices_to={'role': 'Agent'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='handled_leads', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='lead',
            name='property',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leads', to='properties.property'),
        ),
        migrations.AddField(
            model_name='lead',
            name='spotter',
            field=models.ForeignKey(limit_choices_to={'role': 'Spotter'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='spotted_leads', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='leadnote',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='leadnote',
            name='lead',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='leads.lead'),
        ),
    ]
