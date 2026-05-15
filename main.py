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

    # Determine the root directory to scan
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle → scan the exe's folder
        root_dir = os.path.dirname(os.path.abspath(sys.executable))
    elif len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()

    app = ZipPackerApp(root_dir)
    app.run()


if __name__ == "__main__":
    main()
