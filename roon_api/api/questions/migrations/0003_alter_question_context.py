# Generated by Django 4.0.10 on 2023-03-07 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='context',
            field=models.TextField(blank=True, db_index=True, max_length=256, null=True, verbose_name='Context'),
        ),
    ]
