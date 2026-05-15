"""Folder Zipper — 可视化文件夹打包工具

拷贝到目标文件夹根目录，双击运行，勾选文件后一键打包为 ZIP。

用法:
    python main.py              # 扫描当前工作目录
    python main.py /path/dir    # 扫描指定目录
"""

import os
import sys


def main():
    from app import ZipPackerApp

    if getattr(sys, 'frozen', False):
        exe_path = os.path.abspath(sys.executable)
        # macOS .app bundle: exe lives inside .app/Contents/MacOS/, use the
        # directory that contains the .app bundle so the user can place it
        # alongside files they want to package.
        app_dir = _find_app_bundle_dir(exe_path)
        if app_dir:
            root_dir = os.path.dirname(app_dir)
        else:
            root_dir = os.path.dirname(exe_path)
    elif len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()

    app = ZipPackerApp(root_dir)
    app.run()


def _find_app_bundle_dir(exe_path: str) -> str | None:
    """If exe_path is inside a macOS .app bundle, return the .app directory."""
    path = exe_path
    while path != os.path.dirname(path):
        if os.path.basename(path).endswith(".app") and os.path.isdir(path):
            return path
        path = os.path.dirname(path)
    return None


if __name__ == "__main__":
    main()
