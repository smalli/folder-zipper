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
app.py        # 主窗口（工具栏、树、进度条、打包按钮），版本号显示
build.py      # PyInstaller 一键构建（clean / build），含 VERSION 校验
VERSION       # 版本号文件，app.py 和 build.py 都从这里读
```

## 构建模式
- macOS：`--onedir` + `--windowed` → `dist/folder-zipper.app`
- Windows：`--onefile` + `--windowed` → `dist/folder-zipper.exe`
- Linux：`--onefile` + `--windowed` → `dist/folder-zipper`
- VERSION 文件通过 `--add-data` 打入包内，app 启动时多路径 fallback 查找

## 本地构建
```bash
python3 build.py           # 构建
python3 build.py clean     # 清理 build/ dist/ *.spec
```

构建前自动校验 VERSION 文件与当前 git tag 是否一致（见下）。

## 发版流程

VERSION 文件（如 `1.2.5`）和 git tag（如 `v1.2.5`）必须一致，build.py 会在构建前校验，不匹配则报错拦截。

```bash
# 1. 更新 VERSION 文件
echo "1.3.0" > VERSION

# 2. 提交
git add VERSION [其他改动的文件]
git commit -m "release v1.3.0"

# 3. 打 tag 并推送（tag 触发 CI 构建三平台产物）
git tag v1.3.0
git push origin main
git push origin v1.3.0
```

- CI 地址：https://github.com/smalli/folder-zipper/actions
- 用户下载：https://github.com/smalli/folder-zipper/releases（需手动从 CI Artifacts 上传）

## VERSION 查找逻辑
Frozen 模式下按以下顺序查找 VERSION 文件：
1. `sys._MEIPASS` — `--onefile` 临时解压目录（Win/Linux）
2. `.app/Contents/Resources/` — macOS `.app` bundle
3. `os.path.dirname(sys.executable)` — 兜底

开发模式下从 `app.py` 所在目录查找。

## 验证
```bash
python3 main.py                    # 以当前目录运行（需 GUI）
python3 -c "from app import VERSION; print(VERSION)"   # 版本号
python3 -c "from scanner import scan_directory; print(len(scan_directory()))"   # 扫描
```
