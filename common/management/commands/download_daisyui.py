"""Fetch the pinned standalone CSS plugins before building Tailwind."""

import hashlib
import shutil
from pathlib import Path
from tempfile import mkdtemp

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Download and verify the pinned daisyUI standalone bundles."

    def handle(self, *args, **options):
        destination = Path(settings.BASE_DIR) / "theme/static_src/src"
        active = destination / "daisyui"
        verified = {}
        for filename, checksum in settings.DAISYUI_SHA256.items():
            target = active / filename
            if (
                target.exists()
                and hashlib.sha256(target.read_bytes()).hexdigest() == checksum
            ):
                verified[filename] = target.read_bytes()
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
            verified[filename] = response.content
        if all(
            (active / name).exists() and (active / name).read_bytes() == content
            for name, content in verified.items()
        ):
            self.stdout.write(self.style.SUCCESS("daisyUI bundles already verified."))
            return

        # Each invocation owns its staging directory and link. Publish the pair
        # with one atomic rename, keeping the previous pair intact on failure.
        staged = Path(mkdtemp(prefix=".daisyui-", dir=destination))
        link = staged.with_suffix(".link")
        published = False
        try:
            for name, content in verified.items():
                (staged / name).write_bytes(content)
            link.symlink_to(staged.name, target_is_directory=True)
            link.replace(active)
            published = True
        finally:
            link.unlink(missing_ok=True)
            if not published:
                shutil.rmtree(staged)
        # Retain old directories: a running build may still be reading them.
        self.stdout.write(
            self.style.SUCCESS(f"daisyUI {settings.DAISYUI_VERSION} bundles verified."),
        )
