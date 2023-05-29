from django.test import TestCase, SimpleTestCase
from wagtail.models import Page, Site

from bs4 import BeautifulSoup
import requests
from community.models import CommunityPage
from contact.models import (
    Meeting,
    MeetingIndexPage,
    Organization,
    OrganizationIndexPage,
    Person,
    PersonIndexPage,
)
from content_migration.management.commands.errors import (
    CouldNotFindMatchingContactError,
    DuplicateContactError,
)

from content_migration.management.commands.shared import (
    create_document_link_block,
    create_image_block,
    extract_image_urls,
    fetch_file_bytes,
    get_existing_magazine_author_from_db,
    parse_body_blocks,
    parse_media_blocks,
    remove_pullquote_tags,
    create_media_embed_block,
    extract_pullquotes,
)
from home.models import HomePage


WESTERN_FRIEND_LOGO = "https://westernfriend.org/sites/default/files/logo-2020-%20transparency-120px_0.png"
WESTERN_FRIEND_LOGO_FILE_NAME = "logo-2020-%20transparency-120px_0.png"


class RemovePullquoteTagsSimpleTestCase(SimpleTestCase):
    def test_remove_pullquote_tags(self) -> None:
        soup_context = BeautifulSoup(
            """<p>Some text[pullquote]with a pullquote[/pullquote]</p>""",
            "html.parser",
        )  # noqa: E501
        input_bs4_tag = soup_context.find("p")
        output_bs4_tag = remove_pullquote_tags(input_bs4_tag)  # type: ignore
        expected_bs4_tag = BeautifulSoup(
            """<p>Some textwith a pullquote</p>""",
            "html.parser",
        ).find("p")

        self.assertEqual(output_bs4_tag, expected_bs4_tag)

    def test_remove_pullquote_tags_with_multiple_pullquotes(self) -> None:
        soup_context = BeautifulSoup(
            """<p>Some text [pullquote]with a pullquote[/pullquote] and another [pullquote]with a pullquote[/pullquote]</p>""",  # noqa: E501
            "html.parser",
        )
        input_bs4_tag = soup_context.find("p")
        output_bs4_tag = remove_pullquote_tags(input_bs4_tag)  # type: ignore
        expected_bs4_tag = BeautifulSoup(
            """<p>Some text with a pullquote and another with a pullquote</p>""",
            "html.parser",
        ).find("p")

        self.assertEqual(output_bs4_tag, expected_bs4_tag)


class ExtractPullquotesSimpleTestCase(SimpleTestCase):
    def test_extract_pullquotes(self) -> None:
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote]</p>"""
        output_pullquotes = extract_pullquotes(input_html)
        expected_pullquotes = ["with a pullquote"]
        self.assertEqual(output_pullquotes, expected_pullquotes)

    def test_extract_pullquotes_with_multiple_pullquotes(self) -> None:
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote] and another [pullquote]with a pullquote[/pullquote]</p>"""  # noqa: E501
        output_pullquotes = extract_pullquotes(input_html)
        expected_pullquotes = ["with a pullquote", "with a pullquote"]
        self.assertEqual(output_pullquotes, expected_pullquotes)

    def test_extract_pullquotes_with_none_as_input(self) -> None:
        input_html = None

        with self.assertRaises(TypeError):
            extract_pullquotes(input_html)  # type: ignore


class CreateMediaEmbedBlockTestCase(TestCase):
    def test_create_media_embed_block(self) -> None:
        self.MaxDiff = None
        input_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        output_media_embed_block = create_media_embed_block(input_url)

        self.assertEqual(
            output_media_embed_block[1].url,
            input_url,
        )


class TestExtractImages(SimpleTestCase):
    def test_extract_image_urls(self) -> None:
        input_html = (
            """<p>Some text<img src="https://www.example.com/image.jpg" /></p>"""
        )
        output_images = extract_image_urls(input_html)
        expected_images = ["https://www.example.com/image.jpg"]
        self.assertEqual(output_images, expected_images)


class ParseBodyBlocksTestCase(TestCase):
    def test_parse_body_blocks(self) -> None:
        self.MaxDiff = None
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote]</p>"""
        output_blocks = parse_body_blocks(input_html)
        expected_blocks = [
            (
                "pullquote",
                "with a pullquote",
            ),
            (
                "rich_text",
                """<p>Some textwith a pullquote</p>""",
            ),
        ]

        self.assertEqual(
            output_blocks,
            expected_blocks,
        )

    def test_parse_body_blocks_with_multiple_pullquotes(self) -> None:
        self.MaxDiff = None
        input_html = """<p>Some text[pullquote]with a pullquote[/pullquote] and [pullquote]another pullquote[/pullquote].</p>"""  # noqa: E501
        parse_body_blocks(input_html)

    def test_parse_body_blocks_with_multiple_consecutive_paragraphs(self) -> None:
        self.MaxDiff = None
        input_html = """<p>One paragraph.</p><p>Another paragraph.</p>"""

        output_blocks = parse_body_blocks(input_html)
        expected_blocks = [
            (
                "rich_text",
                """<p>One paragraph.</p><p>Another paragraph.</p>""",
            ),
        ]

        self.assertEqual(
            output_blocks,
            expected_blocks,
        )

    def test_parse_body_blocks_with_multiple_paragraphs_and_a_pullquote(self) -> None:
        self.MaxDiff = None
        input_html = """<p>One paragraph.</p><p>Another paragraph.</p><p>[pullquote]A pullquote[/pullquote] inside of a paragraph</p>"""  # noqa: E501

        output_blocks = parse_body_blocks(input_html)
        expected_blocks = [
            (
                "rich_text",
                """<p>One paragraph.</p><p>Another paragraph.</p>""",  # noqa: E501
            ),
            (
                "pullquote",
                "A pullquote",
            ),
            (
                "rich_text",
                """<p>A pullquote inside of a paragraph</p>""",
            ),
        ]

        self.assertEqual(
            output_blocks,
            expected_blocks,
        )

    def test_parse_body_blocks_witn_none_as_input(self) -> None:
        input_html = ""

        ouptut_blocks = parse_body_blocks(input_html)
        expected_blocks: list = []

        self.assertEqual(
            ouptut_blocks,
            expected_blocks,
        )


class FetchFileBytesTestCase(TestCase):
    def test_fetch_file_bytes(self) -> None:
        self.MaxDiff = None

        output_file_bytes = fetch_file_bytes(WESTERN_FRIEND_LOGO)

        self.assertEqual(
            output_file_bytes.file_name,
            WESTERN_FRIEND_LOGO_FILE_NAME,
        )

    def test_fetch_file_bytes_raises_exception(self) -> None:
        input_url = (
            "https://doesntexistyetbutmaybesomedaypleasedontbreakmytest.com/image.jpg"
        )

        with self.assertRaises(requests.exceptions.RequestException):
            fetch_file_bytes(input_url)


class TestCreateDocumentLinkBlock(TestCase):
    def test_create_document_link_block(self) -> None:
        input_url = "https://ia600400.us.archive.org/33/items/friendsbulletinp525unse_2/friendsbulletinp525unse_2.pdf"
        input_file_name = "friendsbulletinp525unse_2.pdf"

        file_bytes = fetch_file_bytes(input_url)

        output_document_link_block = create_document_link_block(
            input_file_name,
            file_bytes.file_bytes,
        )
        output_file_name = output_document_link_block[1].title

        self.assertEqual(
            output_file_name,
            input_file_name,
        )


class CreateImageBlockTestCase(TestCase):
    def test_create_image_block(self) -> None:
        file_bytes = fetch_file_bytes(WESTERN_FRIEND_LOGO)
        output_image_block = create_image_block(
            file_name=file_bytes.file_name,
            file_bytes=file_bytes.file_bytes,
        )
        output_filename_start = output_image_block[1]["image"].filename[:5]
        expected_filename_start = WESTERN_FRIEND_LOGO_FILE_NAME[:5]

        self.assertEqual(
            output_filename_start,
            expected_filename_start,
        )


class GetExistingContactFromDbTestCase(TestCase):
    def setUp(self) -> None:
        self.site = Site.objects.get(is_default_site=True)

        try:
            self.root_page = Page.objects.get(id=1)
        except Page.DoesNotExist:
            self.root_page = Page(
                id=1,
                title="Root",
            )

        self.site.root_page = self.root_page

        self.home_page = HomePage(
            title="Welcome",
        )

        self.root_page.add_child(
            instance=self.home_page,
        )
        self.root_page.save()

        self.community_page = CommunityPage(
            title="Community",
            show_in_menus=True,
        )
        self.home_page.add_child(
            instance=self.community_page,
        )
        self.home_page.save()

        self.organization_index_page = OrganizationIndexPage(
            title="Organizations",
        )
        self.person_index_page = PersonIndexPage(
            title="People",
        )
        self.meeting_index_page = MeetingIndexPage(
            title="Meetings",
        )
        self.community_page.add_child(
            instance=self.meeting_index_page,
        )
        self.community_page.add_child(
            instance=self.organization_index_page,
        )
        self.community_page.add_child(
            instance=self.person_index_page,
        )
        self.community_page.save()

        self.person_drupal_author_id = "1"
        self.organization_drupal_author_id = "2"
        self.meeting_drupal_author_id = "3"

        self.person = Person(
            drupal_author_id=self.person_drupal_author_id,
            given_name="Test",
            family_name="Person",
        )
        self.person_index_page.add_child(
            instance=self.person,
        )
        self.organization = Organization(
            drupal_author_id=self.organization_drupal_author_id,
            title="Test Organization",
        )
        self.organization_index_page.add_child(
            instance=self.organization,
        )
        self.meeting = Meeting(
            drupal_author_id=self.meeting_drupal_author_id,
            title="Test Meeting",
        )
        self.meeting_index_page.add_child(
            instance=self.meeting,
        )

    def test_get_existing_person_from_db(self) -> None:
        output_person = get_existing_magazine_author_from_db(
            drupal_author_id=self.person_drupal_author_id,
        )

        self.assertEqual(
            output_person,
            self.person,
        )

    def test_get_existing_organization_from_db(self) -> None:
        output_organization = get_existing_magazine_author_from_db(
            drupal_author_id=self.organization_drupal_author_id,
        )

        self.assertEqual(
            output_organization,
            self.organization,
        )

    def test_get_existing_meeting_from_db(self) -> None:
        output_meeting = get_existing_magazine_author_from_db(
            drupal_author_id=self.meeting_drupal_author_id,
        )

        self.assertEqual(
            output_meeting,
            self.meeting,
        )

    def test_get_existing_magazine_author_from_db_raises_exception(self) -> None:
        input_drupal_author_id = "4"

        with self.assertRaises(CouldNotFindMatchingContactError):
            get_existing_magazine_author_from_db(
                drupal_author_id=input_drupal_author_id,
            )

    def test_duplicate_raises_exception(self) -> None:
        meeting_with_duplicate_person_id = Meeting(
            drupal_author_id=self.person_drupal_author_id,
            title="Test Meeting",
        )
        self.meeting_index_page.add_child(instance=meeting_with_duplicate_person_id)

        with self.assertRaises(DuplicateContactError):
            get_existing_magazine_author_from_db(
                drupal_author_id=self.person_drupal_author_id,
            )

        meeting_with_duplicate_person_id.delete()

    def tearDown(self) -> None:
        self.person.delete()
        self.organization.delete()
        self.meeting.delete()

        self.person_index_page.delete()
        self.organization_index_page.delete()
        self.meeting_index_page.delete()

        self.community_page.delete()
        self.home_page.delete()

        self.root_page.delete()


class ParseMediaBlocksTestCase(TestCase):
    def test_parse_media_blocks_with_youtube_url(self) -> None:
        input_media_urls = ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
        output_media_blocks = parse_media_blocks(input_media_urls)
        output_media_block_type = output_media_blocks[0][0]
        expected_media_block_type = "embed"

        self.assertEqual(
            output_media_block_type,
            expected_media_block_type,
        )

    def test_parse_media_blocks_with_pdf_url(self) -> None:
        input_media_urls = [
            "https://ia600400.us.archive.org/33/items/friendsbulletinp525unse_2/friendsbulletinp525unse_2.pdf"
        ]
        output_media_blocks = parse_media_blocks(input_media_urls)
        output_media_block_type = output_media_blocks[0][0]
        expected_media_block_type = "document"

        self.assertEqual(
            output_media_block_type,
            expected_media_block_type,
        )

    def test_parse_media_blocks_with_image_url(self) -> None:
        input_media_urls = [
            "https://westernfriend.org/sites/default/files/logo-2020-%20transparency-120px_0.png"
        ]
        output_media_blocks = parse_media_blocks(input_media_urls)
        output_media_block_type = output_media_blocks[0][0]
        expected_media_block_type = "image"

        self.assertEqual(
            output_media_block_type,
            expected_media_block_type,
        )


# TODO: add command tests
# from django.core.management import call_command
# from django.test import TestCase

# class CommandTest(TestCase):
#     def test_my_command(self):
#         call_command('my_command', 'arg1', 'arg2')
#         # Now assert that the command has done what it's supposed to do
