"""Build script — produces a distributable app via PyInstaller.

Usage:
    python build.py           # build for current platform
    python build.py clean     # remove build artifacts

Prerequisites:
    pip install pyinstaller

Output:
    dist/folder-zipper.app    (macOS)
    dist/folder-zipper.exe    (Windows)
    dist/folder-zipper        (Linux)
"""

import os
import shutil
import subprocess
import sys
import platform


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
NAME = "folder-zipper"


def clean():
    """Remove build artifacts."""
    targets = ["build", "dist"]
    for d in targets:
        path = os.path.join(PROJECT_DIR, d)
        if os.path.isdir(path):
            shutil.rmtree(path)
    for f in os.listdir(PROJECT_DIR):
        if f.endswith(".spec"):
            os.remove(os.path.join(PROJECT_DIR, f))
    for root, dirs, _ in os.walk(PROJECT_DIR):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))


def _validate_version():
    version_file = os.path.join(PROJECT_DIR, "VERSION")
    try:
        with open(version_file) as f:
            file_ver = f.read().strip()
    except (FileNotFoundError, OSError):
        print("[build] WARNING: VERSION file not found, skipping version check.")
        return

    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--exact-match", "HEAD"],
            cwd=PROJECT_DIR, stderr=subprocess.DEVNULL,
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"[build] WARNING: No tag on HEAD (VERSION={file_ver}), dev build.")
        return

    tag_ver = tag.lstrip("v")
    if tag_ver != file_ver:
        print(f"[build] ERROR: VERSION file ({file_ver}) does not match git tag ({tag}).")
        print("[build] Update the VERSION file before building, or tag the commit with the correct version.")
        sys.exit(1)

    print(f"[build] Version check: VERSION={file_ver}, tag={tag}  OK")


def build():
    _validate_version()

    system = platform.system()
    is_mac = system == "Darwin"

    if is_mac:
        mode = "--onedir"
        output_name = NAME + ".app"
    else:
        mode = "--onefile"
        output_name = NAME + (".exe" if system == "Windows" else "")

    sep = ";" if system == "Windows" else ":"
    version_file = os.path.join(PROJECT_DIR, "VERSION")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        mode,
        "--windowed",
        "--name", NAME,
        "--clean",
        "--add-data", f"{version_file}{sep}.",
        os.path.join(PROJECT_DIR, "main.py"),
    ]

    print(f"[build] Platform: {system}")
    print(f"[build] Output: dist/{output_name}")
    print()

    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode != 0:
        print("\n[build] Failed!")
        sys.exit(result.returncode)

    dist_path = os.path.join(PROJECT_DIR, "dist", output_name)
    if os.path.exists(dist_path):
        print(f"\n[build] Done! -> {dist_path}")
    else:
        print(f"\n[build] Done! Check dist/ directory.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean()
        print("[clean] Removed build/, dist/, .spec files.")
    else:
        build()
