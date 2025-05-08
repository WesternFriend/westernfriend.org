from django.forms import CharField, TextInput
from django.forms.forms import Form
from django.test import TestCase

from common.templatetags.common_form_tags import add_class
from common.templatetags.common_tags import exclude_from_breadcrumbs, model_name


class MockModel:
    """Mock model class for testing template tags."""

    class _meta:
        model_name = "mockmodel"


class CommonFormTagsTests(TestCase):
    """Tests for common form tags template filters."""

    def setUp(self):
        """Set up test data."""

        # Create a simple form with a single field
        class TestForm(Form):
            test_field = CharField(
                widget=TextInput(attrs={"class": "existing-class"}),
            )
            no_class_field = CharField(widget=TextInput())

        self.form = TestForm()
        self.field_with_class = self.form["test_field"]
        self.field_without_class = self.form["no_class_field"]

    def test_add_class(self):
        """Test the add_class filter adds CSS classes correctly."""
        # Test adding a class to a field with existing class
        result = add_class(self.field_with_class, "new-class")
        self.assertIn('class="new-class existing-class"', result)

        # Test adding multiple classes
        result = add_class(self.field_with_class, "class1 class2")
        self.assertIn('class="class1 class2 existing-class"', result)

        # Test adding a class to a field without existing class
        result = add_class(self.field_without_class, "new-class")
        self.assertIn('class="new-class "', result)

        # Test with empty class string
        result = add_class(self.field_with_class, "")
        self.assertIn('class=" existing-class"', result)


class CommonTagsTests(TestCase):
    """Tests for common tags template filters."""

    def test_model_name(self):
        """Test the model_name filter returns the correct model name."""
        # Test with a valid model object
        mock_model = MockModel()
        self.assertEqual(model_name(mock_model), "mockmodel")

        # Test with None
        self.assertEqual(model_name(None), "")

        # Test with an object that has no _meta attribute
        class NoMetaObject:
            pass

        self.assertEqual(model_name(NoMetaObject()), "")

    def test_exclude_from_breadcrumbs(self):
        """Test the exclude_from_breadcrumbs filter."""

        # Test with a page that should be excluded
        class PersonIndexPage:
            class _meta:
                model_name = (
                    "personindexpage"  # This is a string attribute, not a function
                )

        mock_page = PersonIndexPage()
        self.assertTrue(exclude_from_breadcrumbs(mock_page))

        # Test with a page that should not be excluded
        class RegularPage:
            class _meta:
                model_name = "regularpage"

        self.assertFalse(exclude_from_breadcrumbs(RegularPage()))

        # Test with None
        self.assertFalse(exclude_from_breadcrumbs(None))

        # Test with an object that has no _meta attribute
        class NoMetaObject:
            pass

        self.assertFalse(exclude_from_breadcrumbs(NoMetaObject()))

        # Test with all excluded model types
        excluded_models = [
            "personindexpage",
            "meetingindexpage",
            "organizationindexpage",
            "facetindexpage",
            "audienceindexpage",
            "genreindexpage",
            "mediumindexpage",
            "timeperiodindexpage",
            "topicindexpage",
        ]

        for excluded_model in excluded_models:

            class ExcludedPage:
                class _meta:
                    model_name = excluded_model  # Using the string from the list

            self.assertTrue(exclude_from_breadcrumbs(ExcludedPage()))
