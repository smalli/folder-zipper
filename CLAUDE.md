# folder-zipper

可视化文件夹打包工具。拷贝到目标文件夹根目录双击运行，勾选文件后生成 ZIP。

## 环境
- Python 3.9+，仅用标准库（tkinter + zipfile + dataclasses）
- 无第三方依赖

## 项目结构
```
main.py       # 入口，判断运行模式（python/frozen），确定扫描目录
scanner.py    # 文件树扫描、TreeNode 数据结构、勾选状态管理
tree_view.py  # ttk.Treeview 子类，三态 checkbox UI
zipper.py     # 后台线程 zip 打包 + 进度回调
app.py        # 主窗口（工具栏、树、进度条、打包按钮）
build.py      # PyInstaller 一键构建（clean / build）
```

## 验证
```bash
python3 main.py                    # 以当前目录运行（需 GUI）
python3 -c "..."                   # 见根目录测试脚本
```

## 构建产物
```bash
python3 build.py       # → dist/folder-zipper(.exe)
python3 build.py clean # 清理 build/ dist/
```
