# Generated by Django 5.1.7 on 2025-04-30 18:35

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WebApp', '0003_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WindData',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source', models.CharField(choices=[('csv', 'CSV'), ('meteostat', 'Meteostat')], max_length=20)),
                ('csv_data', models.TextField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
