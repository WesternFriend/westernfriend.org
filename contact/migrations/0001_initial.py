# Generated by Django 2.2.1 on 2019-06-07 21:22

from django.db import migrations, models
import django.db.models.deletion
import wagtail.core.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0041_group_collection_permissions_verbose_name_plural'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('meeting_type', models.CharField(choices=[('monthly_meeting', 'Monthly Meeting'), ('quarterly_meeting', 'Quarterly Meeting'), ('worship_group', 'Worship Group'), ('yearly_meeting', 'Yearly Meeting')], max_length=255)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('website', models.URLField(blank=True, null=True)),
            ],
            options={
                'db_table': 'meeting',
                'ordering': ['title'],
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='MeetingIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('website', models.URLField(blank=True, null=True)),
            ],
            options={
                'db_table': 'organization',
                'ordering': ['title'],
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='OrganizationIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('body', wagtail.core.fields.StreamField([('heading', wagtail.core.blocks.CharBlock(classname='full title')), ('paragraph', wagtail.core.blocks.RichTextBlock()), ('organizations', wagtail.core.blocks.StructBlock([]))], null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('given_name', models.CharField(default='', help_text='Enter the given name for a person.', max_length=255)),
                ('family_name', models.CharField(blank=True, default='', max_length=255)),
            ],
            options={
                'db_table': 'person',
                'ordering': ['title'],
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='PersonIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
