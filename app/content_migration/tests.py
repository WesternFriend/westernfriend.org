from django.test import SimpleTestCase
from content_migration.management.commands.shared import parse_body_blocks

test_data = [
    {
        "input_html": """<p><strong><span style="color:rgb(34, 34, 34); font-family:roboto,arial,sans-serif; font-size:small">~</span></strong></p>""",
        "expected_blocks": [
            {
                "block_type": "rich_text",
                "source": "~",
            },
        ],
    },
    {
        "input_html": """<h4><strong>To Spank Or Not To Spank: Is this still a question?</strong></h4>""",
        "expected_blocks": [
            {
                "block_type": "rich_text",
                "source": "To Spank Or Not To Spank: Is this still a question?",
            },
        ],
    },
    {
        "input_html": """<p>To Spank Or Not To Spank: Is this still a question?</p>""",
        "expected_blocks": [
            {
                "block_type": "rich_text",
                "source": "To Spank Or Not To Spank: Is this still a question?",
            },
        ],
    },
    {
        "input_html": """<p><img alt="Spank or No" src="/sites/default/files/media/Spank%20or%20No.png" style="height:400px; width:400px" title="Spank or No" /></p>""",
        "expected_blocks": [
            {
                "block_type": "rich_text",
                "source": "May 6, 2016 by Molly Wingate",
            },
        ],
    },
]


class TestParseBodyBlocks(SimpleTestCase):
    def test_parse_body_blocks_on_blog_post(self):
        for test_item in test_data:
            output_body_blocks = parse_body_blocks(
                test_item["input_html"],
            )

            assert len(output_body_blocks) == len(test_item["expected_blocks"])

            for index, block in enumerate(output_body_blocks):
                print(block[0])
                self.assertEqual(
                    block[0],
                    test_item["expected_blocks"][index]["block_type"],
                )
                print(block[1].source)
                self.assertEqual(
                    block[1].source,
                    test_item["expected_blocks"][index]["source"],
                )
