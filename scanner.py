"""File system scanner — builds the file tree structure."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TreeNode:
    name: str
    path: str          # relative path from scan root
    full_path: str     # absolute path
    is_dir: bool
    size: int = 0
    children: list["TreeNode"] = field(default_factory=list)
    checked: bool = True       # all files default checked
    partial: bool = False      # some (not all) children checked
    error: str | None = None   # permission error etc.


def scan_directory(root_dir: str | None = None) -> list[TreeNode]:
    """Recursively scan a directory and return the file tree.

    If root_dir is None, uses the directory containing the running executable.
    The executable itself is excluded from the tree.
    System junk files (.DS_Store, Thumbs.db) are skipped.
    """
    if root_dir is None:
        root_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    root = Path(root_dir).resolve()
    exe_path = _get_exe_path()

    def _scan(current: Path) -> list[TreeNode]:
        nodes: list[TreeNode] = []
        try:
            entries = sorted(
                current.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except (PermissionError, OSError):
            return nodes

        for entry in entries:
            if _should_skip(entry, exe_path):
                continue

            rel_path = str(entry.relative_to(root))
            node = TreeNode(
                name=entry.name,
                path=rel_path,
                full_path=str(entry),
                is_dir=entry.is_dir(),
            )

            if entry.is_dir():
                node.children = _scan(entry)
                node.size = sum(c.size for c in node.children)
                _sync_dir_state(node)
            elif entry.is_symlink():
                continue
            else:
                try:
                    node.size = entry.stat().st_size
                except (PermissionError, OSError):
                    node.error = "无法读取"

            nodes.append(node)

        return nodes

    return _scan(root)


def _get_exe_path() -> str | None:
    """Get the path of the running executable, if identifiable (frozen PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.abspath(sys.executable)
    return None


def _should_skip(entry: Path, exe_path: str | None) -> bool:
    """Check if a file should be excluded from the tree."""
    if exe_path and str(entry.resolve()) == exe_path:
        return True
    if entry.name in {'.DS_Store', 'Thumbs.db'}:
        return True
    return False


def _sync_dir_state(node: TreeNode):
    """Update a directory node's check state based on its children."""
    if not node.children:
        node.partial = False
        return

    checked_count = sum(1 for c in node.children if c.checked)
    partial_count = sum(1 for c in node.children if c.partial)

    if checked_count == len(node.children) and partial_count == 0:
        node.checked = True
        node.partial = False
    elif checked_count == 0 and partial_count == 0:
        node.checked = False
        node.partial = False
    else:
        node.checked = False
        node.partial = True


def set_node_checked(node: TreeNode, checked: bool):
    """Recursively set a node and all its children to checked/unchecked."""
    node.checked = checked
    node.partial = False
    for child in node.children:
        set_node_checked(child, checked)


def propagate_check_state(nodes: list[TreeNode]):
    """After changing leaf nodes, propagate states up through all levels."""
    for node in nodes:
        if node.is_dir:
            _propagate_up(node)


def _propagate_up(node: TreeNode):
    """Bottom-up sync of check states from children to parent."""
    for child in node.children:
        if child.is_dir:
            _propagate_up(child)
    _sync_dir_state(node)


def collect_checked_files(nodes: list[TreeNode]) -> list[tuple[str, str]]:
    """Collect all checked file paths for zipping.

    Returns list of (absolute_path, relative_path_in_zip).
    """
    result: list[tuple[str, str]] = []

    def _collect(n: TreeNode):
        if n.error:
            return
        if not n.is_dir and n.checked:
            result.append((n.full_path, n.path))
        for child in n.children:
            _collect(child)

    for node in nodes:
        _collect(node)

    return result


def invert_selection(nodes: list[TreeNode]):
    """Invert check state of all leaf (file) nodes, then propagate."""
    def _invert(n: TreeNode):
        if not n.is_dir:
            n.checked = not n.checked
        for child in n.children:
            _invert(child)

    for node in nodes:
        _invert(node)
    propagate_check_state(nodes)


def select_all(nodes: list[TreeNode]):
    for node in nodes:
        set_node_checked(node, True)


def deselect_all(nodes: list[TreeNode]):
    for node in nodes:
        set_node_checked(node, False)
