# Generated by Django 5.0.2 on 2025-06-24 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_invitationtoken'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminLoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('username', models.CharField(max_length=150)),
                ('attempted_at', models.DateTimeField(auto_now_add=True)),
                ('success', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'admin_login_attempts',
                'indexes': [models.Index(fields=['ip_address', 'attempted_at'], name='admin_login_ip_addr_0b45f6_idx'), models.Index(fields=['username', 'attempted_at'], name='admin_login_usernam_6499d5_idx')],
            },
        ),
    ]
