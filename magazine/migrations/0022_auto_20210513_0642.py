# Generated by Django 3.2.2 on 2021-05-13 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magazine', '0021_auto_20210226_0920'),
    ]

    operations = [
        migrations.AlterField(
            model_name='magazinearticleauthor',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='magazinearticletag',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='magazineissuefeaturedarticle',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
