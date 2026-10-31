"""Fetch the pinned standalone CSS plugins before building Tailwind."""

import hashlib
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Download and verify the pinned daisyUI standalone bundles."

    def handle(self, *args, **options):
        destination = Path(settings.BASE_DIR) / "theme/static_src/src"
        verified = {}
        for filename, checksum in settings.DAISYUI_SHA256.items():
            target = destination / filename
            if (
                target.exists()
                and hashlib.sha256(target.read_bytes()).hexdigest() == checksum
            ):
                continue
            url = f"https://github.com/saadeghi/daisyui/releases/download/v{settings.DAISYUI_VERSION}/{filename}"
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
            except requests.RequestException as exc:
                raise CommandError(str(exc)) from exc
            if hashlib.sha256(response.content).hexdigest() != checksum:
                message = f"SHA-256 mismatch for {filename}; refusing to install."
                raise CommandError(message)
            verified[target] = response.content
        # Verify both downloads before replacing either installed bundle.
        for target, content in verified.items():
            temporary = target.with_suffix(".mjs.tmp")
            temporary.write_bytes(content)
            temporary.replace(target)
        self.stdout.write(
            self.style.SUCCESS(f"daisyUI {settings.DAISYUI_VERSION} bundles verified."),
        )
