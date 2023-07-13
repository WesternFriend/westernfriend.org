from wagtail.admin.panels import InlinePanel


class NestedInlinePanel(InlinePanel):
    """Temporary fix so that page chooser renders correctly in nested inline
    panels.

    Issue: https://github.com/wagtail/wagtail/issues/5126
    """

    def widget_overrides(self) -> dict:
        widgets = {}  # pragma: no cover
        child_edit_handler = self.get_child_edit_handler()  # pragma: no cover
        for handler_class in child_edit_handler.children:  # pragma: no cover
            widgets.update(handler_class.widget_overrides())  # pragma: no cover
        widget_overrides = {self.relation_name: widgets}  # pragma: no cover
        return widget_overrides  # pragma: no cover
