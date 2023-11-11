from django.core.management.base import BaseCommand
from magazine.models import MagazineArticle
from django.db import transaction
from wagtail.blocks import StreamValue
from wagtail.rich_text import RichText


class Command(BaseCommand):
    help = 'Remove all occurrences of "[pullquote]" and "[/pullquote]" in the rich_text field of StreamField'

    def handle(self, *args, **options):
        with transaction.atomic():
            articles = MagazineArticle.objects.all()

            for article in articles:
                stream_value = article.body
                modified_blocks = []
                for block in stream_value:
                    if block.block_type == "rich_text":
                        # Convert RichText content to string and remove the pullquote tags
                        modified_value = block.value.source.replace(
                            "[pullquote]",
                            "",
                        ).replace("[/pullquote]", "")
                        # Create a new block with the modified value
                        block_tuple = (block.block_type, RichText(modified_value))
                        modified_blocks.append(block_tuple)
                    else:
                        # If not 'rich_text', append the block as is
                        modified_blocks.append((block.block_type, block.value))
                print(modified_blocks)
                stream_data = StreamValue(stream_value.stream_block, modified_blocks)
                article.body = stream_data
                article.save()

                self.stdout.write(self.style.SUCCESS(f"Updated article {article.pk}"))

        self.stdout.write(self.style.SUCCESS("All articles have been updated."))
