from wagtail.core import blocks


class ArchiveArticleBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    authors = blocks.ListBlock(
        blocks.PageChooserBlock()
    )
    toc_page_number = blocks.IntegerBlock()
    pdf_page_number = blocks.IntegerBlock()

    class Meta:
        icon = "doc-full"
