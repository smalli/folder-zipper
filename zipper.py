"""Zip creation with progress callback. Runs in background thread."""

from __future__ import annotations

import os
import threading
import zipfile
from typing import Callable


def create_zip(
    file_list: list[tuple[str, str]],
    output_path: str,
    on_progress: Callable[[int, int, str], None] | None = None,
    on_complete: Callable[[str, int], None] | None = None,
    on_error: Callable[[str], None] | None = None,
):
    """Create a zip archive from a list of (abs_path, rel_path) tuples.

    Runs in a background thread to avoid blocking the UI.
    Uses ZIP_DEFLATED compression and automatic ZIP64 for large files.
    """

    def _run():
        try:
            total = len(file_list)
            completed = 0
            total_bytes = 0

            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for abs_path, rel_path in file_list:
                    try:
                        zf.write(abs_path, rel_path)
                    except (PermissionError, OSError) as e:
                        if on_error:
                            on_error(f"跳过 {rel_path}: {e}")
                        continue

                    completed += 1
                    try:
                        total_bytes += os.path.getsize(abs_path)
                    except OSError:
                        pass

                    if on_progress:
                        on_progress(completed, total, rel_path)

            try:
                zip_size = os.path.getsize(output_path)
            except OSError:
                zip_size = total_bytes

            if on_complete:
                on_complete(output_path, zip_size)

        except Exception as e:
            if on_error:
                on_error(str(e))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
