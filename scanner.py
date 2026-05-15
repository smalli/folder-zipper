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
    mtime: float = 0.0        # modification timestamp
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
    skip_paths = _get_skip_paths(exe_path)

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
            if _should_skip(entry, skip_paths):
                continue

            try:
                st = entry.stat()
                mtime = st.st_mtime
                fsize = st.st_size if not entry.is_dir() else 0
            except (PermissionError, OSError):
                mtime = 0.0
                fsize = 0

            rel_path = str(entry.relative_to(root))
            node = TreeNode(
                name=entry.name,
                path=rel_path,
                full_path=str(entry),
                is_dir=entry.is_dir(),
                mtime=mtime,
            )

            if entry.is_dir():
                node.children = _scan(entry)
                node.size = sum(c.size for c in node.children)
                node.mtime = max((c.mtime for c in node.children), default=mtime)
                _sync_dir_state(node)
            elif entry.is_symlink():
                continue
            else:
                node.size = fsize

            nodes.append(node)

        return nodes

    return _scan(root)


def _get_exe_path() -> str | None:
    """Get the path of the running executable, if identifiable (frozen PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.abspath(sys.executable)
    return None


def _get_skip_paths(exe_path: str | None) -> set[str]:
    """Collect paths to exclude from the tree (the app itself and its data)."""
    paths: set[str] = set()
    if exe_path is None:
        return paths

    paths.add(exe_path)

    # On macOS .app bundle, exclude the bundle and the PyInstaller data dir
    app_dir = _find_app_bundle_dir(exe_path)
    if app_dir:
        paths.add(app_dir)
        data_dir = os.path.join(os.path.dirname(app_dir), os.path.basename(app_dir).removesuffix(".app"))
        if os.path.isdir(data_dir):
            paths.add(data_dir)

    return paths


def _find_app_bundle_dir(exe_path: str) -> str | None:
    """If exe_path is inside a macOS .app bundle, return the .app directory."""
    path = exe_path
    while path != os.path.dirname(path):
        if os.path.basename(path).endswith(".app") and os.path.isdir(path):
            return path
        path = os.path.dirname(path)
    return None


def _should_skip(entry: Path, skip_paths: set[str]) -> bool:
    if str(entry.resolve()) in skip_paths:
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
