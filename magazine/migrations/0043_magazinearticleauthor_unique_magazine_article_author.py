from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("magazine", "0042_remove_duplicate_magazine_article_authors"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="magazinearticleauthor",
            constraint=models.UniqueConstraint(
                fields=("article", "author"),
                name="unique_magazine_article_author",
                deferrable=models.Deferrable.DEFERRED,
            ),
        ),
    ]
