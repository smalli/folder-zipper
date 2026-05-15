"""Main application window — layout, toolbar, tree, and bottom controls."""

from __future__ import annotations

import os
import sys
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from scanner import (
    scan_directory,
    select_all,
    deselect_all,
    invert_selection,
    collect_checked_files,
)
from tree_view import CheckboxTreeview
from zipper import create_zip


class ZipPackerApp:
    def __init__(self, root_dir: str | None = None):
        self.root_dir = root_dir or os.path.dirname(os.path.abspath(sys.argv[0]))
        self.root = tk.Tk()
        self.root.title("Folder Zipper")
        self.root.geometry("1024x680")
        self.root.minsize(640, 440)

        style = ttk.Style()
        style.configure("Treeview", font=("", 11))
        style.configure("Treeview.Heading", font=("", 11))
        style.configure("TButton", font=("", 10))
        style.configure("TLabel", font=("", 10))

        self._build_ui()
        self._load_tree()

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self.root, padding=(10, 10, 10, 4))
        toolbar.pack(fill="x")

        btn_select_all = ttk.Button(toolbar, text="全选", command=self._on_select_all)
        btn_select_all.pack(side="left", padx=(0, 4))

        btn_deselect_all = ttk.Button(toolbar, text="取消全选", command=self._on_deselect_all)
        btn_deselect_all.pack(side="left", padx=(0, 4))

        btn_invert = ttk.Button(toolbar, text="反选", command=self._on_invert)
        btn_invert.pack(side="left", padx=(0, 12))

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

        btn_expand = ttk.Button(toolbar, text="展开全部", command=self._on_expand_all)
        btn_expand.pack(side="left", padx=(10, 4))

        btn_collapse = ttk.Button(toolbar, text="折叠全部", command=self._on_collapse_all)
        btn_collapse.pack(side="left")

        self.stats_label = ttk.Label(toolbar, text="")
        self.stats_label.pack(side="right", padx=(12, 0))

        # Tree
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(4, 8))

        self.tree = CheckboxTreeview(tree_frame, on_check_changed=self._on_check_changed)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Context menu
        self._build_context_menu()

        # Bottom
        bottom = ttk.Frame(self.root, padding=(10, 4, 10, 10))
        bottom.pack(fill="x")

        ttk.Label(bottom, text="输出文件名:").pack(side="left", padx=(0, 6))
        default_name = os.path.basename(self.root_dir.rstrip("/\\")) or "archive"
        self.output_var = tk.StringVar(value=default_name)
        ttk.Entry(bottom, textvariable=self.output_var, width=32).pack(side="left", padx=(0, 4))
        ttk.Label(bottom, text=".zip").pack(side="left", padx=(0, 16))

        self.pack_btn = ttk.Button(bottom, text="确定打包", command=self._on_pack)
        self.pack_btn.pack(side="right")

        browse_btn = ttk.Button(bottom, text="浏览...", command=self._on_browse_output)
        browse_btn.pack(side="right", padx=(0, 8))

        # Progress bar (hidden)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.root, variable=self.progress_var, maximum=100, mode="determinate"
        )
        self.progress_label = ttk.Label(self.root, text="")

    def _build_context_menu(self):
        self.ctx_menu = tk.Menu(self.root, tearoff=0)
        self.ctx_menu.add_command(label="全选", command=self._on_select_all)
        self.ctx_menu.add_command(label="取消全选", command=self._on_deselect_all)
        self.ctx_menu.add_command(label="反选", command=self._on_invert)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="展开全部", command=self._on_expand_all)
        self.ctx_menu.add_command(label="折叠全部", command=self._on_collapse_all)

        def show_ctx(event):
            self.ctx_menu.post(event.x_root, event.y_root)

        self.tree.bind("<Button-2>", show_ctx)
        self.tree.bind("<Button-3>", show_ctx)
        self.tree.bind("<Control-Button-1>", show_ctx)

    def _load_tree(self):
        try:
            self.nodes = scan_directory(self.root_dir)
        except Exception as e:
            messagebox.showerror("错误", f"无法扫描目录:\n{e}")
            self.root.destroy()
            return

        if not self.nodes:
            messagebox.showinfo("提示", "当前目录没有可打包的文件。")

        self.tree.populate(self.nodes)
        self._update_stats()

    def _on_select_all(self):
        select_all(self.nodes)
        self.tree.refresh_all(self.nodes)
        self._update_stats()

    def _on_deselect_all(self):
        deselect_all(self.nodes)
        self.tree.refresh_all(self.nodes)
        self._update_stats()

    def _on_invert(self):
        invert_selection(self.nodes)
        self.tree.refresh_all(self.nodes)
        self._update_stats()

    def _on_expand_all(self):
        _expand_all(self.tree)

    def _on_collapse_all(self):
        _collapse_all(self.tree)

    def _on_check_changed(self):
        self._update_stats()

    def _update_stats(self):
        files = collect_checked_files(self.nodes)
        count = len(files)
        total_size = sum(
            os.path.getsize(abs_path) for abs_path, _ in files
            if os.path.exists(abs_path)
        )
        self.stats_label.config(text=f"已选: {count} 个文件, {_human_size(total_size)}")

    def _on_browse_output(self):
        output_name = self.output_var.get().strip()
        if not output_name:
            output_name = os.path.basename(self.root_dir.rstrip("/\\")) or "archive"
        path = filedialog.asksaveasfilename(
            title="保存 ZIP 文件",
            initialdir=self.root_dir,
            initialfile=f"{output_name}.zip",
            defaultextension=".zip",
            filetypes=[("ZIP 文件", "*.zip")],
        )
        if path:
            self.output_var.set(os.path.splitext(os.path.basename(path))[0])

    def _on_pack(self):
        files = collect_checked_files(self.nodes)
        if not files:
            messagebox.showwarning("提示", "没有选中任何文件。")
            return

        output_name = self.output_var.get().strip()
        if not output_name:
            output_name = os.path.basename(self.root_dir.rstrip("/\\")) or "archive"

        output_path = filedialog.asksaveasfilename(
            title="保存 ZIP 文件",
            initialdir=self.root_dir,
            initialfile=f"{output_name}.zip",
            defaultextension=".zip",
            filetypes=[("ZIP 文件", "*.zip")],
        )
        if not output_path:
            return

        self.progress_bar.pack(fill="x", padx=10, pady=(0, 2))
        self.progress_label.pack(fill="x", padx=10, pady=(0, 4))
        self.pack_btn.config(state="disabled")

        def on_progress(completed, total, current_file):
            self.root.after(0, lambda: self._update_progress(completed, total, current_file))

        def on_complete(zip_path, zip_size):
            self.root.after(0, lambda: self._on_pack_done(zip_path, zip_size))

        def on_error(msg):
            self.root.after(0, lambda: self._on_pack_error(msg))

        create_zip(files, output_path, on_progress, on_complete, on_error)

    def _update_progress(self, completed: int, total: int, current_file: str):
        if total > 0:
            self.progress_var.set((completed / total) * 100)
        self.progress_label.config(text=f"打包中... ({completed}/{total}) {current_file}")

    def _on_pack_done(self, zip_path: str, zip_size: int):
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        self.pack_btn.config(state="normal")

        messagebox.showinfo(
            "完成",
            f"打包完成!\n\n文件: {os.path.basename(zip_path)}\n"
            f"大小: {_human_size(zip_size)}\n"
            f"位置: {os.path.dirname(zip_path)}",
        )

        if messagebox.askyesno("打开位置", "是否打开文件所在位置?"):
            _reveal_in_explorer(zip_path)

    def _on_pack_error(self, msg: str):
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        self.pack_btn.config(state="normal")
        messagebox.showerror("打包错误", msg)

    def run(self):
        self.root.mainloop()


# ── Helpers ─────────────────────────────────────────────────────

def _expand_all(tree: ttk.Treeview):
    def _expand(item):
        tree.item(item, open=True)
        for child in tree.get_children(item):
            _expand(child)
    for item in tree.get_children(""):
        _expand(item)


def _collapse_all(tree: ttk.Treeview):
    def _collapse(item):
        tree.item(item, open=False)
        for child in tree.get_children(item):
            _collapse(child)
    for item in tree.get_children(""):
        _collapse(item)


def _human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def _reveal_in_explorer(path: str):
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["explorer", "/select,", path])
        elif system == "Darwin":
            subprocess.run(["open", "-R", path])
        else:
            subprocess.run(["xdg-open", os.path.dirname(path)])
    except Exception:
        pass
