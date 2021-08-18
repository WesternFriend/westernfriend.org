# Generated by Django 3.2.6 on 2021-08-18 18:08

from django.db import migrations
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('magazine', '0032_auto_20210818_1601'),
    ]

    operations = [
        migrations.AlterField(
            model_name='magazinearticle',
            name='teaser',
            field=wagtail.core.fields.RichTextField(blank=True, help_text='Try to keep teaser to a couple dozen words.'),
        ),
    ]
