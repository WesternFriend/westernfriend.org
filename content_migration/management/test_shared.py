from io import BytesIO
from unittest.mock import patch
from django.test import TestCase, SimpleTestCase
from wagtail.models import Page, Site
from wagtail.rich_text import RichText


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
from content_migration.management.errors import (
    BlockFactoryError,
    CouldNotFindMatchingContactError,
    CouldNotParseAuthorIdError,
    DuplicateContactError,
)

from content_migration.management.shared import (
    BlockFactory,
    GenericBlock,
    adapt_html_to_generic_blocks,
    construct_import_file_path,
    create_archive_issues_from_articles_dicts,
    create_document_link_block,
    create_group_by,
    create_image_block_from_url,
    create_image_block_from_file_bytes,
    create_media_from_file_bytes,
    create_media_block_from_file_bytes,
    ensure_absolute_url,
    extract_image_urls,
    extract_pullquotes,
    fetch_file_bytes,
    get_existing_magazine_author_from_db,
    parse_body_blocks,
    parse_csv_file,
    parse_media_blocks,
    parse_media_string_to_list,
    remove_pullquote_tags,
)


from home.models import HomePage

from content_migration.management.constants import (
    IMPORT_FILENAMES,
    LOCAL_MIGRATION_DATA_DIRECTORY,
    SITE_BASE_URL,
    WESTERN_FRIEND_LOGO_URL,
    WESTERN_FRIEND_LOGO_FILE_NAME,
)


# class CreateMediaEmbedBlockTestCase(TestCase):
#     def test_create_media_embed_block(self) -> None:
#         self.MaxDiff = None
#         input_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
#         output_media_embed_block = create_media_embed_block(input_url)

#         self.assertEqual(
#             output_media_embed_block[1].url,
#             input_url,
#         )


class TestExtractImages(SimpleTestCase):
    def test_extract_image_urls(self) -> None:
        input_html = (
            """<p>Some text<img src="https://www.example.com/image.jpg" /></p>"""
        )
        output_images = extract_image_urls(input_html)
        expected_images = ["https://www.example.com/image.jpg"]
        self.assertEqual(output_images, expected_images)


class ParseBodyBlocksSimpleTestCase(SimpleTestCase):
    def test_parse_body_blocks_with_pullquote(self) -> None:
        self.MaxDiff = None
        input_html = (
            """<p>Some text <span class="pullquote">with a pullquote</span></p>"""
        )
        expected_output_html = """<p>Some text with a pullquote</p>"""

        output_blocks = parse_body_blocks(input_html)
        expected_blocks = [
            (
                "pullquote",
                "with a pullquote",
            ),
            (
                "rich_text",
                RichText(expected_output_html),
            ),
        ]

        # Make sure first output block matches first expected block
        self.assertEqual(
            output_blocks[0],
            expected_blocks[0],
        )

        # Make sure second output block matches second expected block
        # by comparing the .source attribute on the RichText objects
        # and the block type is rich_text
        self.assertEqual(
            output_blocks[1][1].source,
            expected_blocks[1][1].source,
        )
        self.assertEqual(
            output_blocks[1][0],
            expected_blocks[1][0],
        )

    def test_parse_body_blocks_with_multiple_pullquotes(self) -> None:
        self.MaxDiff = None
        input_html = """<p>Some text <span class="pullquote">with a pullquote</span> and <span class="pullquote">another pullquote</span>.</p>"""  # noqa: E501
        output_blocks = parse_body_blocks(input_html)

        expected_blocks = [
            (
                "pullquote",
                "with a pullquote",
            ),
            (
                "pullquote",
                "another pullquote",
            ),
            (
                "rich_text",
                RichText(
                    """<p>Some text with a pullquote and another pullquote.</p>"""
                ),
            ),
        ]

        # Make sure first pullquote block matches the first expected pullquote block
        self.assertEqual(
            output_blocks[0][0],
            expected_blocks[0][0],
        )
        self.assertEqual(
            output_blocks[0][1],
            expected_blocks[0][1],
        )

        # Make sure second output block matches second expected block
        self.assertEqual(
            output_blocks[1][0],
            expected_blocks[1][0],
        )
        self.assertEqual(
            output_blocks[1][1],
            expected_blocks[1][1],
        )

        # Make sure third output block matches third expected block
        # by comparing the .source attribute on the RichText objects
        # and the block type is rich_text
        self.assertEqual(
            output_blocks[2][1].source,
            expected_blocks[2][1].source,
        )
        self.assertEqual(
            output_blocks[2][0],
            expected_blocks[2][0],
        )

    def test_parse_body_blocks_with_multiple_consecutive_paragraphs(self) -> None:
        self.MaxDiff = None
        input_html = """<p>One paragraph.</p><p>Another paragraph.</p>"""

        output_blocks = parse_body_blocks(input_html)
        expected_blocks = [
            (
                "rich_text",
                RichText("""<p>One paragraph.</p><p>Another paragraph.</p>"""),
            ),
        ]

        # assert that outblocks rich text source matches the input html
        self.assertEqual(
            output_blocks[0][1].source,
            expected_blocks[0][1].source,
        )
        # Assert that the block type is rich_text
        self.assertEqual(
            output_blocks[0][0],
            expected_blocks[0][0],
        )

    def test_parse_body_blocks_with_multiple_paragraphs_and_a_pullquote(self) -> None:
        self.MaxDiff = None
        input_html = """<p>One paragraph.</p><p>Another paragraph.</p><p><span class="pullquote">A pullquote</span> inside of a paragraph</p>"""  # noqa: E501

        output_blocks = parse_body_blocks(input_html)
        expected_blocks = [
            (
                "rich_text",
                RichText("""<p>One paragraph.</p><p>Another paragraph.</p>"""),
            ),
            (
                "pullquote",
                "A pullquote",
            ),
            (
                "rich_text",
                RichText("""<p>A pullquote inside of a paragraph</p>"""),
            ),
        ]

        # The first block should be a rich_text block
        self.assertEqual(
            output_blocks[0][0],
            expected_blocks[0][0],
        )
        # The first block should have a source that matches the input html
        self.assertEqual(
            output_blocks[0][1].source,
            expected_blocks[0][1].source,
        )

        # The second block should be a pullquote block
        self.assertEqual(
            output_blocks[1][0],
            expected_blocks[1][0],
        )
        # The second block should have a source that matches the input html
        self.assertEqual(
            output_blocks[1][1],
            expected_blocks[1][1],
        )

        # The third block should be a rich_text block
        self.assertEqual(
            output_blocks[2][0],
            expected_blocks[2][0],
        )
        # The third block should have a source that matches the input html
        self.assertEqual(
            output_blocks[2][1].source,
            expected_blocks[2][1].source,
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

        output_file_bytes = fetch_file_bytes(WESTERN_FRIEND_LOGO_URL)

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


class CreateImageBlockFromFileBytesTestCase(TestCase):
    def test_create_image_block_from_file_bytes(self) -> None:
        file_bytes = fetch_file_bytes(WESTERN_FRIEND_LOGO_URL)
        output_image_block = create_image_block_from_file_bytes(
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

    def test_get_existing_magazine_author_from_db_with_invalid_drupal_author_id(
        self,
    ) -> None:
        input_drupal_author_id = "invalid"

        with self.assertRaises(CouldNotParseAuthorIdError):
            get_existing_magazine_author_from_db(
                drupal_author_id=input_drupal_author_id,
            )

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
    # def test_parse_media_blocks_with_youtube_url(self) -> None:
    #     input_media_urls = ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    #     output_media_blocks = parse_media_blocks(input_media_urls)
    #     output_media_block_type = output_media_blocks[0][0]
    #     expected_media_block_type = "embed"

    #     self.assertEqual(
    #         output_media_block_type,
    #         expected_media_block_type,
    #     )

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

    def test_parse_media_blocks_with_invalid_url(self) -> None:
        input_media_urls = ["https://www.sadflasdoöifr.com/image.jpg"]

        output_media_blocks = parse_media_blocks(input_media_urls)
        expected_media_blocks: list = []

        self.assertEqual(
            output_media_blocks,
            expected_media_blocks,
        )

    def test_parse_media_blocks_with_empty_string_as_input(self) -> None:
        input_media_urls = [""]

        output_media_blocks = parse_media_blocks(input_media_urls)
        expected_media_blocks: list = []

        self.assertEqual(
            output_media_blocks,
            expected_media_blocks,
        )

    def test_parse_media_blocks_with_audio_url(self) -> None:
        input_media_urls = [
            "https://westernfriend.org/sites/default/files/library/EvilWhyTalkAboutItByBruceFolsom.mp3"
        ]
        output_media_blocks = parse_media_blocks(input_media_urls)
        output_media_block_type = output_media_blocks[0][0]
        expected_media_block_type = "media"

        self.assertEqual(
            output_media_block_type,
            expected_media_block_type,
        )


class ParseCsvFileSimpleTestCase(SimpleTestCase):
    def test_parse_csv_file(self) -> None:
        input_csv_file_path = "content_migration/management/test_parse_csv_file.csv"
        output_parsed_csv_file = parse_csv_file(input_csv_file_path)
        expected_parsed_csv_file = [
            {
                "column_one": "value one",
                "column_two": "value two",
            }
        ]

        self.assertEqual(
            output_parsed_csv_file,
            expected_parsed_csv_file,
        )


class CreateGroupBySimpleTestCase(SimpleTestCase):
    def test_create_group_by(self) -> None:
        input_list = [
            {
                "column_one": "value one",
                "column_two": "value two",
            },
            {
                "column_one": "value one",
                "column_two": "value two",
            },
            {
                "column_one": "value one",
                "column_two": "value two",
            },
        ]
        output_grouped_list = create_group_by("column_one", input_list)
        expected_grouped_list = {
            "value one": [
                {
                    "column_one": "value one",
                    "column_two": "value two",
                },
                {
                    "column_one": "value one",
                    "column_two": "value two",
                },
                {
                    "column_one": "value one",
                    "column_two": "value two",
                },
            ]
        }

        self.assertEqual(
            output_grouped_list,
            expected_grouped_list,
        )


class CreateArchiveIssuesFromArticlesDictsSimpleTest(SimpleTestCase):
    def test_create_archive_issues_from_articles_dicts(self) -> None:
        input_articles_dicts = [
            {
                "internet_archive_identifier": "friendsbulletinp525unse_2",
            },
            {
                "internet_archive_identifier": "friendsbulletinp525unse_2",
            },
        ]

        create_archive_issues_from_articles_dicts(input_articles_dicts)


class RemovePullquoteTagsSimpleTestCase(SimpleTestCase):
    def test_remove_pullquote_tags(self) -> None:
        input_html = (
            """<p>Some text <span class="pullquote">with a pullquote</span></p>"""
        )
        output_html = remove_pullquote_tags(input_html)

        expected_html = """<p>Some text with a pullquote</p>"""

        self.assertEqual(output_html, expected_html)

    def test_remove_pullquote_tags_with_multiple_pullquotes(self) -> None:
        input_html = """<p>Some text <span class="pullquote">with a pullquote</span> and another <span class="pullquote">with a pullquote</span></p>"""  # noqa: E501
        output_html = remove_pullquote_tags(input_html)
        expected_html = """<p>Some text with a pullquote and another with a pullquote</p>"""  # noqa: E501

        self.assertEqual(output_html, expected_html)


class ExtractPullquotesSimpleTestCase(SimpleTestCase):
    def test_extract_pullquotes(self) -> None:
        input_html = (
            """<p>Some text<span class="pullquote">with a pullquote</span></p>"""
        )
        output_pullquotes = extract_pullquotes(input_html)
        expected_pullquotes = ["with a pullquote"]
        self.assertEqual(output_pullquotes, expected_pullquotes)

    def test_extract_pullquotes_with_multiple_pullquotes(self) -> None:
        input_html = """<p>Some text<span class="pullquote">with a pullquote</span> and another <span class="pullquote">with a pullquote</span></p>"""  # noqa: E501
        output_pullquotes = extract_pullquotes(input_html)
        expected_pullquotes = ["with a pullquote", "with a pullquote"]
        self.assertEqual(output_pullquotes, expected_pullquotes)

    def test_extract_pullquotes_with_none_as_input(self) -> None:
        input_html = None

        with self.assertRaises(TypeError):
            extract_pullquotes(input_html)  # type: ignore

    def test_extract_pullquotes_with_sub_tag(self) -> None:
        input_html = """<p><span class="pullquote">a pullquote and 2<sup>nd</sup> tag</span></p>"""  # noqa: E501
        output_pullquotes = extract_pullquotes(input_html)

        expected_pullquotes = ["a pullquote and 2nd tag"]
        self.assertEqual(output_pullquotes, expected_pullquotes)


class AdaptHtmlToGenericBlockTest(SimpleTestCase):
    def test_adapt_html_to_generic_blocks(self) -> None:
        html_string = """<p>Some text</p><p>Some more text</p>"""

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 1)
        self.assertEqual(generic_blocks[0].block_type, "rich_text")
        self.assertEqual(generic_blocks[0].block_content, html_string)

    def test_adapt_html_to_generic_blocks_with_pullquote(self) -> None:
        html_string = """<p>Some text</p><p>Some more text</p><p>A paragraph with <span class="pullquote">a pullquote</span> that should be extracted</p>"""  # noqa: E501

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 3)
        self.assertEqual(generic_blocks[0].block_type, "rich_text")
        self.assertEqual(
            generic_blocks[0].block_content, """<p>Some text</p><p>Some more text</p>"""
        )
        self.assertEqual(generic_blocks[1].block_type, "pullquote")
        self.assertEqual(generic_blocks[1].block_content, "a pullquote")
        self.assertEqual(generic_blocks[2].block_type, "rich_text")
        self.assertEqual(
            generic_blocks[2].block_content,
            "<p>A paragraph with a pullquote that should be extracted</p>",
        )

    def test_adapt_html_to_generic_blocks_with_image(self) -> None:
        html_string = """<p>Some text</p><p><img src="https://westernfriend.org/image.jpg" /></p>"""  # noqa: E501

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 2)
        self.assertEqual(generic_blocks[0].block_type, "rich_text")
        self.assertEqual(generic_blocks[0].block_content, """<p>Some text</p>""")
        self.assertEqual(generic_blocks[1].block_type, "image")
        self.assertEqual(
            generic_blocks[1].block_content["image"],  # type: ignore
            "https://westernfriend.org/image.jpg",
        )

    def test_adapt_html_to_generic_blocks_with_image_wrapped_in_link(self) -> None:
        html_string = """<a href="https://example.com"><img src="https://westernfriend.org/image.jpg" /></a>"""  # noqa: E501

        generic_blocks = adapt_html_to_generic_blocks(html_string)

        self.assertEqual(len(generic_blocks), 1)
        self.assertEqual(generic_blocks[0].block_type, "image")
        self.assertEqual(
            generic_blocks[0].block_content["image"],  # type: ignore
            "https://westernfriend.org/image.jpg",
        )
        self.assertEqual(
            generic_blocks[0].block_content["link"],  # type: ignore
            "https://example.com",
        )


class CreateImageBlockTestCase(TestCase):
    def test_create_image_block(self) -> None:
        # use existing WesternFriend logo URL
        input_html = (
            f"""<p><img src="{ WESTERN_FRIEND_LOGO_URL }" /></p>"""  # noqa: E501
        )

        image_urls = extract_image_urls(input_html)

        image_block = create_image_block_from_url(image_urls[0])

        # self.assertEqual(image_block.block_type, "image")  # type: ignore
        self.assertEqual(
            image_block["image"].title,
            WESTERN_FRIEND_LOGO_FILE_NAME,
        )  # type: ignore

    def test_create_image_block_with_none_as_input(self) -> None:
        input_html = None

        with self.assertRaises(requests.exceptions.MissingSchema):
            create_image_block_from_url(input_html)  # type: ignore

    def test_create_image_block_with_invalid_url(self) -> None:
        input_html = "/image.jpg"

        with self.assertRaises(requests.exceptions.MissingSchema):
            create_image_block_from_url(input_html)


class BlockFactorySimpleTestCase(SimpleTestCase):
    # it should raise a ValueError if the block type is not supported
    def test_block_factory_with_invalid_block_type(self) -> None:
        generic_block = GenericBlock(
            "invalid_block_type",
            "some content",
        )

        with self.assertRaises(ValueError):
            BlockFactory.create_block(
                generic_block=generic_block,
            )

    def test_create_block_invalid_image_url_missing_schema(self) -> None:
        invalid_url_block = GenericBlock(
            "image",
            {
                "image": "invalid_url",
                "link": None,
                "align": None,
            },
        )
        with patch(
            "content_migration.management.shared.create_image_block_from_url"
        ) as mock_create_image_block:
            mock_create_image_block.side_effect = requests.exceptions.MissingSchema
            with self.assertRaises(BlockFactoryError) as cm:
                BlockFactory.create_block(invalid_url_block)
            self.assertEqual(str(cm.exception), "Invalid image URL: missing schema")

    def test_create_block_invalid_image_url_invalid_schema(self) -> None:
        invalid_url_block = GenericBlock(
            "image",
            {
                "image": "invalid_url",
                "link": None,
                "align": None,
            },
        )
        with patch(
            "content_migration.management.shared.create_image_block_from_url"
        ) as mock_create_image_block:
            mock_create_image_block.side_effect = requests.exceptions.InvalidSchema
            with self.assertRaises(BlockFactoryError) as cm:
                BlockFactory.create_block(invalid_url_block)
            self.assertEqual(str(cm.exception), "Invalid image URL: invalid schema")


class ConvertRelativeImageUrlToAbsoluteSimpleTestCase(SimpleTestCase):
    def test_ensure_absolute_url(self) -> None:
        relative_image_url = (
            "/sites/default/files/logo-2020-%20transparency-120px_0.png"
        )
        absolute_image_url = ensure_absolute_url(relative_image_url)
        # without double slashes
        expected_absolute_image_url = (
            f"{ SITE_BASE_URL }{ relative_image_url.lstrip('/') }"
        )
        self.assertEqual(
            absolute_image_url,
            expected_absolute_image_url,
        )


class ParseMediaStringToListSimpleTest(SimpleTestCase):
    def test_parse_media_string_to_list(self) -> None:
        # create a media string with several URLs
        media_string = f"{ WESTERN_FRIEND_LOGO_URL }, { WESTERN_FRIEND_LOGO_URL }, { WESTERN_FRIEND_LOGO_URL }"  # noqa: E501

        media_urls = parse_media_string_to_list(media_string)
        expected_media_urls = [
            WESTERN_FRIEND_LOGO_URL,
            WESTERN_FRIEND_LOGO_URL,
            WESTERN_FRIEND_LOGO_URL,
        ]

        self.assertEqual(media_urls, expected_media_urls)


class ConstructImportFilePathSimpleTest(SimpleTestCase):
    def test_construct_import_file_path(self) -> None:
        # construct a file path for a file in the test data directory
        file_key = "extra_extra"
        import_file_path = construct_import_file_path(file_key)
        expected_import_file_path = (
            f"{LOCAL_MIGRATION_DATA_DIRECTORY}{IMPORT_FILENAMES[file_key]}"
        )

        self.assertEqual(import_file_path, expected_import_file_path)


# TODO: add command tests
# from django.core.management import call_command
# from django.test import TestCase

# class CommandTest(TestCase):
#     def test_my_command(self):
#         call_command('my_command', 'arg1', 'arg2')
#         # Now assert that the command has done what it's supposed to do


class CreateMediaFromFileBytesTestCase(TestCase):
    def test_create_media_from_file_bytes(self) -> None:
        # create a media file from a file in the test data directory
        file_path = "test_data/test.mp3"
        with open(file_path, "rb") as f:
            file_bytes = BytesIO(f.read())

            media = create_media_from_file_bytes(
                file_name="test.mp3",
                file_bytes=file_bytes,
                file_type="audio",
            )

            self.assertEqual(media.file_extension, "mp3")

    def test_create_media_block_from_file_bytes(self) -> None:
        # create a media file from a file in the test data directory
        file_path = "test_data/test.mp3"
        with open(file_path, "rb") as f:
            file_bytes = BytesIO(f.read())

            media_block = create_media_block_from_file_bytes(
                file_name="test.mp3",
                file_bytes=file_bytes,
                file_type="audio",
            )

            self.assertEqual(media_block[0], "media")
