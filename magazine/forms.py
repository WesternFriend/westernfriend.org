from wagtail.admin.forms import WagtailAdminPageForm

DUPLICATE_AUTHOR_MESSAGE = "{author} is already an author of this article."


class MagazineArticleForm(WagtailAdminPageForm):
    """Page form that names a repeated author on the row that repeats it.

    The database forbids the same contact twice on one article. modelcluster
    would catch that too, but only with a generic "duplicate values" message.
    """

    def clean(self):
        cleaned_data = super().clean()
        self._reject_duplicate_authors()
        return cleaned_data

    def _reject_duplicate_authors(self) -> None:
        formset = self.formsets["authors"]
        seen = set()
        for form in formset.forms:
            # Rows the editor removed, or left blank or invalid, don't count.
            author = form.cleaned_data.get("author") if form.is_valid() else None
            if author is None or formset._should_delete_form(form):  # noqa: SLF001
                continue
            if author.pk in seen:
                form.add_error(
                    "author",
                    DUPLICATE_AUTHOR_MESSAGE.format(author=author),
                )
            seen.add(author.pk)
