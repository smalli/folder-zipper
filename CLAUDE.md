# folder-zipper

可视化文件夹打包工具。拷贝到目标文件夹双击运行，勾选文件后一键打包 ZIP。

## 环境
- Python 3.9+，仅用标准库（tkinter + zipfile + dataclasses）
- 无第三方依赖
- macOS：系统 Python 的 tkinter 8.5 与 macOS 26 不兼容，需用 Homebrew Python（`/opt/homebrew/bin/python3`）

## 项目结构
```
main.py       # 入口，判断运行模式（python/frozen），确定扫描目录
scanner.py    # 文件树扫描、TreeNode 数据结构、勾选状态管理
tree_view.py  # ttk.Treeview 子类，三态 checkbox UI + 修改时间列
zipper.py     # 后台线程 zip 打包 + 进度回调
app.py        # 主窗口（工具栏、树、进度条、打包按钮）
build.py      # PyInstaller 一键构建（clean / build）
```

## 构建
```bash
python3 build.py       # macOS → dist/folder-zipper.app, Windows/Linux → dist/folder-zipper(.exe)
python3 build.py clean # 清理 build/ dist/ .spec
```

- macOS 用 `--onedir` 生成 .app bundle
- Windows/Linux 用 `--onefile` 生成单文件

## CI
GitHub Actions，推 tag（`v*`）自动构建三平台产物，也可手动触发。

## 验证
```bash
python3 main.py                    # 以当前目录运行（需 GUI）
python3 -c "from scanner import scan_directory; print(len(scan_directory()))"  # 扫描测试
```
