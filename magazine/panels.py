from wagtail.admin.panels import InlinePanel


class NestedInlinePanel(InlinePanel):
    """Temporary fix so that page chooser renders correctly in nested inline
    panels.

    Issue: https://github.com/wagtail/wagtail/issues/5126
    """

    def widget_overrides(self) -> dict:  # pragma: no cover
        widgets = {}
        child_edit_handler = self.get_child_edit_handler()  # type: ignore
        for handler_class in child_edit_handler.children:
            widgets.update(handler_class.widget_overrides())
        widget_overrides = {self.relation_name: widgets}
        return widget_overrides
