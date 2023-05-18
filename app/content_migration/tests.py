# noqa: E501
from django.test import SimpleTestCase
from content_migration.management.commands.shared import parse_body_blocks

test_data = [
    {
        "input_html": """<p><strong><span style="color:rgb(34, 34, 34); font-family:roboto,arial,sans-serif; font-size:small">~</span></strong></p>""",  # noqa: E501
        "expected_html": """<p><strong><span style="color:rgb(34, 34, 34); font-family:roboto,arial,sans-serif; font-size:small">~</span></strong></p>""",  # noqa: E501
    },
]


class TestParseBodyBlocks(SimpleTestCase):
    def test_parse_body_blocks_on_blog_post(self):
        for item in test_data:
            output_body_blocks = parse_body_blocks(item["input_html"])
            parsed_html = output_body_blocks[0][1].source

            self.assertHTMLEqual(
                parsed_html,
                item["expected_html"],
            )
