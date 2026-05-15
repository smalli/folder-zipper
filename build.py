"""Build script — produces a single-file executable via PyInstaller.

Usage:
    python build.py           # build for current platform
    python build.py clean     # remove build artifacts

Prerequisites:
    pip install pyinstaller

Output:
    dist/folder-zipper       (macOS / Linux)
    dist/folder-zipper.exe   (Windows)
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


def build():
    system = platform.system()
    ext = ".exe" if system == "Windows" else ""
    output_name = NAME + ext

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", NAME,
        "--clean",
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
        size_mb = os.path.getsize(dist_path) / (1024 * 1024)
        print(f"\n[build] Done! -> {dist_path} ({size_mb:.1f} MB)")
    else:
        print(f"\n[build] Done! Check dist/ directory.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean()
        print("[clean] Removed build/, dist/, .spec files.")
    else:
        build()
