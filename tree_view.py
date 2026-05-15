"""Checkbox tree view widget — ttk.Treeview subclass with tri-state checkboxes."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from scanner import TreeNode, set_node_checked, propagate_check_state

CHECKED = "☑"
UNCHECKED = "☐"
PARTIAL = "☒"


class CheckboxTreeview(ttk.Treeview):
    """Treeview with tri-state checkboxes per row."""

    def __init__(
        self,
        parent: tk.Widget,
        on_check_changed: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(
            parent,
            columns=("size",),
            show="tree headings",
            selectmode="browse",
            **kwargs,
        )

        self.heading("#0", text="名称")
        self.heading("size", text="大小")
        self.column("#0", width=400, minwidth=200, stretch=True)
        self.column("size", width=120, minwidth=80, stretch=False, anchor="e")

        self._node_map: dict[str, TreeNode] = {}
        self._on_check_changed = on_check_changed

        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<space>", self._on_space)
        self.bind("<Return>", self._on_space)

        self.tag_configure("dir", foreground="#1a1a2e")
        self.tag_configure("file", foreground="#555555")
        self.tag_configure("error", foreground="#cc3333")

    def populate(self, nodes: list[TreeNode], parent_iid: str = ""):
        self._node_map.clear()
        for item in self.get_children(""):
            self.delete(item)
        self._populate_nodes(nodes, parent_iid)

    def _populate_nodes(self, nodes: list[TreeNode], parent_iid: str):
        for node in nodes:
            iid = self.insert(
                parent_iid,
                "end",
                text=self._format_label(node),
                values=(self._format_size(node),),
                open=False,
                tags=self._get_tags(node),
            )
            self._node_map[iid] = node
            if node.is_dir and node.children:
                self._populate_nodes(node.children, iid)

    def _format_label(self, node: TreeNode) -> str:
        if node.partial:
            icon = PARTIAL
        elif node.checked:
            icon = CHECKED
        else:
            icon = UNCHECKED
        return f"{icon} {node.name}"

    def _format_size(self, node: TreeNode) -> str:
        if node.error:
            return node.error
        if node.is_dir and not node.children:
            return "(空)"
        return _human_size(node.size)

    def _get_tags(self, node: TreeNode) -> tuple[str, ...]:
        if node.error:
            return ("error",)
        if node.is_dir:
            return ("dir",)
        return ("file",)

    def refresh_node(self, node: TreeNode):
        iid = self._find_iid(node)
        if iid:
            self.item(
                iid,
                text=self._format_label(node),
                values=(self._format_size(node),),
                tags=self._get_tags(node),
            )

    def refresh_all(self, nodes: list[TreeNode]):
        def _refresh(n: TreeNode):
            self.refresh_node(n)
            for c in n.children:
                _refresh(c)
        for n in nodes:
            _refresh(n)

    def _find_iid(self, node: TreeNode) -> str | None:
        for iid, n in self._node_map.items():
            if n is node:
                return iid
        return None

    def _on_click(self, event: tk.Event):
        region = self.identify_region(event.x, event.y)
        if region not in ("cell", "tree", "row"):
            return
        iid = self.identify_row(event.y)
        if not iid:
            return
        node = self._node_map.get(iid)
        if node is None:
            return
        self._toggle_node(node)

    def _on_space(self, event: tk.Event):
        selection = self.selection()
        if not selection:
            return
        node = self._node_map.get(selection[0])
        if node is None:
            return
        self._toggle_node(node)

    def _toggle_node(self, node: TreeNode):
        if node.checked and not node.partial:
            set_node_checked(node, False)
        else:
            set_node_checked(node, True)

        nodes = self._get_root_nodes()
        propagate_check_state(nodes)
        self.refresh_all(nodes)
        if self._on_check_changed:
            self._on_check_changed()

    def _get_root_nodes(self) -> list[TreeNode]:
        root_iids = self.get_children("")
        return [self._node_map[iid] for iid in root_iids if iid in self._node_map]

    def get_root_nodes(self) -> list[TreeNode]:
        return self._get_root_nodes()


def _human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"
