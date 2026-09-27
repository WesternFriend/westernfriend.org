from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Site


class DrupalFields(models.Model):
    drupal_node_id = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True


DEFAULT_LLMS_TXT_SUMMARY = (
    "Western Friend is a Quaker nonprofit that publishes a magazine, "
    "books, and other resources exploring the spiritual lives of Friends "
    "(Quakers) in the western United States and beyond."
)


@register_setting(icon="globe")
class CrawlerPolicySetting(BaseSiteSetting):
    """How search engines and AI systems may use the site's content.

    The defaults follow ADR 0006: Quaker perspectives are open to search
    engines, AI answers, and AI training alike. Private and transactional
    paths are always disallowed in robots.txt, so they are not settings.
    """

    allow_search = models.BooleanField(
        "Search engines",
        default=True,
        help_text="Allow search engines to index pages and link to them.",
    )
    allow_ai_input = models.BooleanField(
        "AI answers",
        default=True,
        help_text=(
            "Allow AI systems to read pages to answer questions, "
            "for example in AI search results and chat assistants."
        ),
    )
    allow_ai_train = models.BooleanField(
        "AI training",
        default=True,
        help_text="Allow AI systems to learn from pages when building AI models.",
    )
    publish_llms_txt = models.BooleanField(
        "Publish llms.txt",
        default=True,
        help_text=(
            "Publish a guide to the site for AI systems at /llms.txt, "
            "built from the navigation menu."
        ),
    )
    llms_txt_summary = models.TextField(
        "Site summary",
        blank=True,
        default=DEFAULT_LLMS_TXT_SUMMARY,
        help_text="One paragraph describing the site, shown at the top of llms.txt.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("allow_search"),
                FieldPanel("allow_ai_input"),
                FieldPanel("allow_ai_train"),
            ],
            heading="Content signals",
            help_text=(
                "Tell crawlers how they may use the site's content, through robots.txt."
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("publish_llms_txt"),
                FieldPanel("llms_txt_summary"),
            ],
            heading="llms.txt",
        ),
    ]

    class Meta:
        verbose_name = "Crawlers and AI"

    @classmethod
    def for_request_or_default(cls, request):
        """Return the site's setting, or the defaults if none has been saved.

        Unlike ``for_request``, this never saves a row, so serving a page
        costs at most one query. The result is cached on the request.
        """
        attr_name = "crawler_policy_setting"
        if not hasattr(request, attr_name):
            site = Site.find_for_request(request)
            saved = cls.objects.filter(site=site).first() if site else None
            setattr(request, attr_name, saved or cls(site=site))
        return getattr(request, attr_name)

    @property
    def content_signal(self):
        """Format the choices as a robots.txt Content-Signal value.

        See https://contentsignals.org/
        """
        signals = [
            ("search", self.allow_search),
            ("ai-input", self.allow_ai_input),
            ("ai-train", self.allow_ai_train),
        ]
        return ", ".join(
            f"{name}={'yes' if allowed else 'no'}" for name, allowed in signals
        )

    @property
    def excluded_content_usage(self):
        """Format the preference for pages excluded from AI use.

        Excluded pages opt out of AI training and AI use but follow the
        site's search choice. The value uses the IETF AI preferences
        vocabulary (draft-ietf-aipref-vocab), which, unlike Content Signals,
        can be scoped to a path in robots.txt and sent as a Content-Usage
        header (draft-ietf-aipref-attach).
        """
        return f"train-ai=n, ai-use=n, search={'y' if self.allow_search else 'n'}"
