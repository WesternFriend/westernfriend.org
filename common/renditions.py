"""Bulk-load image renditions for Wagtail's image tags."""

from collections import defaultdict
from collections.abc import Iterable
from io import BytesIO

from wagtail.images.models import Filter

# Must match the filters in blocks/blocks/formatted_image_block.html.
BODY_IMAGE_RENDITION_SPEC = "width-800|jpegquality-80"


def _prefetch_streamfield_renditions(stream_value, *filter_specs: str) -> None:
    """Attach renditions to images already loaded on a StreamField."""
    images = []
    for child in stream_value:
        if child.block_type != "image":
            continue
        image = child.value.get("image") if child.value else None
        if image is not None:
            images.append(image)
    attach_renditions(images, *filter_specs)


def attach_renditions(images: Iterable, *filter_specs: str) -> None:
    """Load or create renditions and store them on each image.

    ``{% image %}`` and ``{% srcset_image %}`` read ``prefetched_renditions``.
    Existing rows are loaded in one query. Missing renditions are generated
    and inserted together, then loaded again, so a cold page does not query
    once per image.
    """
    specs = list(dict.fromkeys(filter_specs))
    images_by_pk = _images_by_pk(images)
    if not images_by_pk or not specs:
        return

    # select_related builds a separate image object per row, even when two
    # pages share a cover. Read and generate once per primary key, then
    # attach the renditions to every object that was passed in.
    representatives = [copies[0] for copies in images_by_pk.values()]
    rendition_model = representatives[0].get_rendition_model()
    image_ids = set(images_by_pk)
    grouped = _renditions_by_image(rendition_model, image_ids, specs)
    created = _missing_renditions(representatives, specs, grouped)
    if created:
        rendition_model.objects.bulk_create(created, ignore_conflicts=True)
        grouped = _renditions_by_image(rendition_model, image_ids, specs)

    for image_id, copies in images_by_pk.items():
        renditions = grouped.get(image_id, [])
        for rendition in renditions:
            # Keep alt text on an instance already loaded with the page.
            rendition.image = copies[0]
        for image in copies:
            image.prefetched_renditions = renditions


def _images_by_pk(images: Iterable) -> dict[int, list]:
    grouped: dict[int, list] = defaultdict(list)
    for image in images:
        if image is not None:
            grouped[image.pk].append(image)
    return grouped


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
        try:
            with image.open_file() as source_file:
                original = source_file.read()
        except OSError:
            # Let Wagtail's image tag supply its missing-image fallback.
            continue
        for spec in missing:
            rendition_filter = image.clean_filter_for_svg(Filter(spec=spec))
            to_create.append(
                image.generate_rendition_instance(
                    rendition_filter,
                    BytesIO(original),
                ),
            )
    return to_create
