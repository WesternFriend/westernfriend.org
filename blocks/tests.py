from unittest.mock import Mock
from django.test import TestCase

from .blocks import MediaBlock


class MediaBlockTest(TestCase):
    def setUp(self) -> None:
        self.block = MediaBlock()

    def test_render_basic_no_value(self) -> None:
        result = self.block.render_basic(None)
        self.assertEqual(result, "")

    def test_render_basic_video(self) -> None:
        # Create a mock media object with type == "video"
        mock_media = Mock()
        mock_media.type = "video"
        mock_media.width = 400
        mock_media.height = 300
        mock_media.sources = [{"src": "test_source.mp4", "type": "video/mp4"}]

        result = self.block.render_basic(mock_media)

        # Check that the result matches expectations
        self.assertIn('<video width="400" height="300" controls>', result)

    def test_render_basic_audio(self) -> None:
        # Create a mock media object with type == "audio"
        mock_media = Mock()
        mock_media.type = "audio"
        mock_media.sources = [{"src": "test_source.mp3", "type": "audio/mpeg"}]

        result = self.block.render_basic(mock_media)

        # Check that the result matches expectations
        self.assertIn("<audio controls>", result)
