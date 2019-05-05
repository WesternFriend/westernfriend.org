# Generated by Django 2.1.7 on 2019-05-05 22:17

from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0001_initial'),
        ('magazine', '0004_auto_20190505_2137'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='magazinearticleauthor',
            name='author',
        ),
        migrations.RemoveField(
            model_name='magazinearticleauthor',
            name='magazine_article',
        ),
        migrations.AddField(
            model_name='magazinearticle',
            name='authors',
            field=modelcluster.fields.ParentalManyToManyField(related_name='authors', to='contact.Contact'),
        ),
        migrations.DeleteModel(
            name='MagazineArticleAuthor',
        ),
    ]
