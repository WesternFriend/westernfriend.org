from wagtail.documents.blocks import DocumentChooserBlock


class DocumentEmbedBlock(DocumentChooserBlock):
    class Meta:
        template = "documents/blocks/document.html"
