# Generated by Django 2.1.3 on 2018-11-09 19:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('magazine', '0006_magazinedepartment'),
    ]

    operations = [
        migrations.AddField(
            model_name='magazinearticle',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='magazine.MagazineDepartment'),
        ),
    ]
