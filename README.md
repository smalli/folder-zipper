# Folder Zipper

可视化文件夹打包工具 —— 放到目标文件夹双击运行，勾选文件，一键生成 ZIP。

## 使用方式

1. 将 `folder-zipper.app`（macOS）或 `folder-zipper.exe`（Windows）拷贝到目标文件夹
2. 双击运行，勾选需要打包的文件和文件夹
3. 输入 ZIP 文件名，点击「确定打包」

## 下载

在 [Releases](https://github.com/smalli/folder-zipper/releases) 页面下载对应平台的包：

| 平台 | 文件 |
|------|------|
| macOS | `folder-zipper.app` |
| Windows | `folder-zipper.exe` |
| Linux | `folder-zipper` |

也可以从 [Actions](https://github.com/smalli/folder-zipper/actions) 的最新成功 run 的 Artifacts 中下载。

## 运行环境

- macOS 10.15+
- Windows 10+
- Linux（需桌面环境）

## 开发

```bash
# 运行
python3 main.py

# 构建
pip install pyinstaller
python3 build.py         # macOS → .app, Windows → .exe, Linux → 二进制

# 清理
python3 build.py clean
```

Python 3.9+，仅用标准库，无第三方依赖。macOS 需用 Homebrew Python（系统自带 tkinter 8.5 不兼容 macOS 26）。

## 发版

VERSION 文件与 git tag 必须一致，构建脚本会自动校验：

```bash
echo "1.3.0" > VERSION
git add VERSION
git commit -m "release v1.3.0"
git tag v1.3.0
git push origin main
git push origin v1.3.0   # 推送 tag 触发 CI 构建三平台产物
```

## 功能

- 三态复选框（全选 / 部分选中 / 全不选）
- 多层级文件夹展开/折叠
- 显示文件大小和最后修改时间
- 后台线程打包，不阻塞界面，带进度条
- 打包完成后一键打开文件所在位置（Windows / macOS / Linux 均支持）
- 自动排除 `.DS_Store`、`Thumbs.db` 等系统文件
