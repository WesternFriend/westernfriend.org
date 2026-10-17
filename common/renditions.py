"""Bulk-load image renditions for Wagtail's image tags."""

from collections import defaultdict
from collections.abc import Iterable
from io import BytesIO

from wagtail.images.models import Filter


def attach_renditions(images: Iterable, *filter_specs: str) -> None:
    """Load or create renditions and store them on each image.

    ``{% image %}`` and ``{% srcset_image %}`` read ``prefetched_renditions``.
    Existing rows are loaded in one query. Missing renditions are generated
    and inserted together, then loaded again, so a cold page does not query
    once per image.
    """
    specs = list(dict.fromkeys(filter_specs))
    unique_images = _unique_images(images)
    if not unique_images or not specs:
        return

    rendition_model = unique_images[0].get_rendition_model()
    image_ids = {image.pk for image in unique_images}
    grouped = _renditions_by_image(rendition_model, image_ids, specs)
    created = _missing_renditions(unique_images, specs, grouped)
    if created:
        rendition_model.objects.bulk_create(created, ignore_conflicts=True)
        grouped = _renditions_by_image(rendition_model, image_ids, specs)

    for image in unique_images:
        renditions = grouped.get(image.pk, [])
        for rendition in renditions:
            # Keep alt text and other image fields from the instance already
            # loaded with the page, instead of querying the image per rendition.
            rendition.image = image
        image.prefetched_renditions = renditions


def _unique_images(images: Iterable) -> list:
    unique_images = []
    seen: set[int] = set()
    for image in images:
        if image is None or image.pk in seen:
            continue
        seen.add(image.pk)
        unique_images.append(image)
    return unique_images


def _renditions_by_image(rendition_model, image_ids: set[int], specs: list[str]):
    grouped: dict[int, list] = defaultdict(list)
    renditions = rendition_model.objects.filter(
        image_id__in=image_ids,
        filter_spec__in=specs,
    )
    for rendition in renditions:
        grouped[rendition.image_id].append(rendition)
    return grouped


def _missing_renditions(images, specs: list[str], grouped) -> list:
    to_create = []
    for image in images:
        have = {rendition.filter_spec for rendition in grouped[image.pk]}
        missing = [spec for spec in specs if spec not in have]
        if not missing:
            continue
        with image.open_file() as source_file:
            original = source_file.read()
        for spec in missing:
            rendition_filter = image.clean_filter_for_svg(Filter(spec=spec))
            to_create.append(
                image.generate_rendition_instance(
                    rendition_filter,
                    BytesIO(original),
                ),
            )
    return to_create
