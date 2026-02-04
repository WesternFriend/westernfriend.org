"""
Core utility functions for the Western Friend website.

This module contains reusable helper functions that are used across
multiple apps in the project.
"""

import logging

from wagtail.models import Site

logger = logging.getLogger(__name__)


def get_default_site() -> Site | None:
    """
    Get the default Wagtail site, falling back to the first site if needed.

    This function provides a consistent way to retrieve a site for context
    where a specific site is needed (e.g., for site settings).

    Returns:
        The default site if one exists, otherwise the first available site,
        or None if no sites exist.

    Note:
        In test environments, multiple sites may be marked as default, so
        we use filter().first() instead of get() to handle this gracefully.
    """
    try:
        # Use filter().first() instead of get() to handle edge cases
        # where multiple sites might be marked as default (e.g., in tests)
        site = Site.objects.filter(is_default_site=True).first()

        if site is None:
            # If no default site, try to get any site
            site = Site.objects.first()

            if site:
                logger.debug(
                    "No default site found, using first available site: %s",
                    site.hostname,
                )
    except Site.DoesNotExist:
        site = None

    if site is None:
        logger.warning("No Wagtail site found in database.")

    return site
