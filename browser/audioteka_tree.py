from __future__ import annotations

import sys
import os
import json
from pathlib import Path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)


from asyncio import Queue
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, ClassVar, Iterable, Iterator, Optional

from textual.await_complete import AwaitComplete

if TYPE_CHECKING:
    from typing_extensions import Self

from rich.style import Style
from rich.text import Text, TextType

from textual import work
from textual.message import Message
from textual.reactive import var
from textual.worker import Worker, WorkerCancelled, WorkerFailed, get_current_worker
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

# Add the parent directory to sys.path
from audtekapi import AudiotekaAPI

TOGGLE_STYLE = Style.from_meta({"toggle": True})


AUDIOTEKA_STATIC_PATHS = ['shelf', 'favourites']


api: AudiotekaAPI = AudiotekaAPI(os.getenv('AUDIOTEKA_EMAIL'), os.getenv('AUDIOTEKA_PASSWORD'),
                                 os.getenv('AUDIOTEKA_DEVICE_ID'), save_session=True)


class AudiotekaPath:
    def __init__(self, path: AudiotekaPath | str, audioteka_obj_type: str | None = None,
                 audioteka_data: dict | None = None) -> None:
        self.path: AudiotekaPath | str = path if isinstance(path, str) else path.path
        self._audioteka_obj_type: str | None = audioteka_obj_type
        self._data: dict | None = audioteka_data

    def is_dir(self):
        if self.path in ['audioteka', 'shelf', 'favourites']:
            return True
        return False

    @property
    def name(self) -> str:
        return self.path

    @property
    def data(self) -> dict:
        book = self._load_audiobook_content()
        if book:
            return book
        return self._data or dict()

    @property
    def data_as_str(self) -> str:
        return json.dumps(self.data, indent=4)

    @property
    def audioteka_obj_type(self) -> str:
        return self._audioteka_obj_type or ""

    def _get_products_function(self) -> Callable or None:
        if self.path == 'shelf':
            return api.get_shelf
        elif self.path == 'favourites':
            return api.get_favourites
        return None

    def __str__(self):
        return self.path

    def iterdir(self) -> Iterator[AudiotekaPath]:
        if self.path == 'audioteka':
            for p in AUDIOTEKA_STATIC_PATHS:
                yield AudiotekaPath(p)
        if self.path in ['shelf', 'favourites']:
            for path, audioteka_obj_type, audioteka_obj_data in self._get_products_details(self._get_products_function()):
                yield AudiotekaPath(path, audioteka_obj_type, audioteka_obj_data)

    def _load_audiobook_content(self) -> dict | None:
        if self._audioteka_obj_type == 'app:product' and self._data:
            book_id = self._data.get('id', None)
            if not book_id:
                return None
            book = api.get_audiobook(book_id)
            return book
        return None

    def _get_products_details(self, products_func: Callable) -> Iterator[str]:
        item = 0
        page = 1
        shelf = products_func(page=page)
        items = int(shelf['total'])
        while item < items:
            if len(shelf['_embedded']['app:product']) == 0:
                page += 1
                shelf = products_func(page=page)
            p = shelf['_embedded']['app:product'].pop()
            item += 1
            yield p['name'], 'app:product', p


@dataclass
class DirEntry:
    """Attaches directory information to a [`DirectoryTree`][textual.widgets.DirectoryTree] node."""

    path: AudiotekaPath
    """The path of the directory entry."""
    loaded: bool = False
    """Has this been loaded?"""


class DirectoryTree(Tree[DirEntry]):
    """A Tree widget that presents files and directories."""

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "directory-tree--extension",
        "directory-tree--file",
        "directory-tree--folder",
        "directory-tree--hidden",
    }
    """
    | Class | Description |
    | :- | :- |
    | `directory-tree--extension` | Target the extension of a file name. |
    | `directory-tree--file` | Target files in the directory structure. |
    | `directory-tree--folder` | Target folders in the directory structure. |
    | `directory-tree--hidden` | Target hidden items in the directory structure. |

    See also the [component classes for `Tree`][textual.widgets.Tree.COMPONENT_CLASSES].
    """

    DEFAULT_CSS = """
    DirectoryTree > .directory-tree--folder {
        text-style: bold;
    }

    DirectoryTree > .directory-tree--extension {
        text-style: italic;
    }

    DirectoryTree > .directory-tree--hidden {
        color: $text 50%;
    }
    """

    PATH: Callable[[str | AudiotekaPath], AudiotekaPath] = AudiotekaPath
    """Callable that returns a fresh path object."""

    class FileSelected(Message):
        """Posted when a file is selected.

        Can be handled using `on_directory_tree_file_selected` in a subclass of
        `DirectoryTree` or in a parent widget in the DOM.
        """

        def __init__(self, node: TreeNode[DirEntry], path: AudiotekaPath) -> None:
            """Initialise the FileSelected object.

            Args:
                node: The tree node for the file that was selected.
                path: The path of the file that was selected.
            """
            super().__init__()
            self.node: TreeNode[DirEntry] = node
            """The tree node of the file that was selected."""
            self.path: AudiotekaPath = path
            """The path of the file that was selected."""

        @property
        def control(self) -> Tree[DirEntry]:
            """The `Tree` that had a file selected."""
            return self.node.tree

    class FileHighlighted(Message):
        """Posted when a file is highlighted.

        Can be handled using `on_directory_tree_file_highlighted` in a subclass of
        `DirectoryTree` or in a parent widget in the DOM.
        """

        def __init__(self, node: TreeNode[DirEntry], path: AudiotekaPath) -> None:
            """Initialise the FileSelected object.

            Args:
                node: The tree node for the file that was highlighted.
                path: The path of the file that was highlighted.
            """
            super().__init__()
            self.node: TreeNode[DirEntry] = node
            """The tree node of the file that was highlighted."""
            self.path: AudiotekaPath = path
            """The path of the file that was highlighted."""

        @property
        def control(self) -> Tree[DirEntry]:
            """The `Tree` that had a file highlighted."""
            return self.node.tree

    class DirectorySelected(Message):
        """Posted when a directory is selected.

        Can be handled using `on_directory_tree_directory_selected` in a
        subclass of `DirectoryTree` or in a parent widget in the DOM.
        """

        def __init__(self, node: TreeNode[DirEntry], path: AudiotekaPath) -> None:
            """Initialise the DirectorySelected object.

            Args:
                node: The tree node for the directory that was selected.
                path: The path of the directory that was selected.
            """
            super().__init__()
            self.node: TreeNode[DirEntry] = node
            """The tree node of the directory that was selected."""
            self.path: AudiotekaPath = path
            """The path of the directory that was selected."""

        @property
        def control(self) -> Tree[DirEntry]:
            """The `Tree` that had a directory selected."""
            return self.node.tree

    path: var[str | AudiotekaPath] = var["str | AudiotekaPath"](PATH("audioteka"), init=False, always_update=True)
    """The path that is the root of the directory tree.

    Note:
        This can be set to either a `str` or a `pathlib.AudiotekaPath` object, but
        the value will always be a `pathlib.AudiotekaPath` object.
    """

    def __init__(
            self,
            path: str | AudiotekaPath,
            *,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False,
    ) -> None:
        """Initialise the directory tree.

        Args:
            path: AudiotekaPath to directory.
            name: The name of the widget, or None for no name.
            id: The ID of the widget in the DOM, or None for no ID.
            classes: A space-separated list of classes, or None for no classes.
            disabled: Whether the directory tree is disabled or not.
        """
        path = 'audioteka'
        self._load_queue: Queue[TreeNode[DirEntry]] = Queue()
        super().__init__(
            str(path),
            data=DirEntry(self.PATH(path)),
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.path: str | AudiotekaPath = path

    def _add_to_load_queue(self, node: TreeNode[DirEntry]) -> AwaitComplete:
        """Add the given node to the load queue.

        The return value can optionally be awaited until the queue is empty.

        Args:
            node: The node to add to the load queue.

        Returns:
            An optionally awaitable object that can be awaited until the
            load queue has finished processing.
        """
        assert node.data is not None
        if not node.data.loaded:
            node.data.loaded = True
            self._load_queue.put_nowait(node)

        return AwaitComplete(self._load_queue.join())

    def reload(self) -> AwaitComplete:
        """Reload the `DirectoryTree` contents."""
        self.reset(str(self.path), DirEntry(self.PATH(self.path)))
        # Orphan the old queue...
        self._load_queue = Queue()
        # ...and replace the old load with a new one.
        self._loader()
        # We have a fresh queue, we have a fresh loader, get the fresh root
        # loading up.
        queue_processed = self._add_to_load_queue(self.root)
        return queue_processed

    def clear_node(self, node: TreeNode[DirEntry]) -> Self:
        """Clear all nodes under the given node.

        Returns:
            The `Tree` instance.
        """
        self._clear_line_cache()
        node_label = node._label
        node_data = node.data
        node_parent = node.parent
        node = TreeNode(
            self,
            node_parent,
            self._new_id(),
            node_label,
            node_data,
            expanded=True,
        )
        self._updates += 1
        self.refresh()
        return self

    def reset_node(
            self, node: TreeNode[DirEntry], label: TextType, data: DirEntry | None = None
    ) -> Self:
        """Clear the subtree and reset the given node.

        Args:
            node: The node to reset.
            label: The label for the node.
            data: Optional data for the node.

        Returns:
            The `Tree` instance.
        """
        self.clear_node(node)
        node.label = label
        node.data = data
        return self

    def reload_node(self, node: TreeNode[DirEntry]) -> AwaitComplete:
        """Reload the given node's contents.

        The return value may be awaited to ensure the DirectoryTree has reached
        a stable state and is no longer performing any node reloading (of this node
        or any other nodes).

        Args:
            node: The node to reload.
        """
        self.reset_node(
            node, str(node.data.path.name), DirEntry(self.PATH(node.data.path))
        )
        return self._add_to_load_queue(node)

    def validate_path(self, path: str | AudiotekaPath) -> AudiotekaPath:
        """Ensure that the path is of the `AudiotekaPath` type.

        Args:
            path: The path to validate.

        Returns:
            The validated AudiotekaPath value.

        Note:
            The result will always be a Python `AudiotekaPath` object, regardless of
            the value given.
        """
        return self.PATH(path)

    async def watch_path(self) -> None:
        """Watch for changes to the `path` of the directory tree.

        If the path is changed the directory tree will be repopulated using
        the new value as the root.
        """
        await self.reload()

    def process_label(self, label: TextType) -> Text:
        """Process a str or Text into a label. Maybe overridden in a subclass to modify how labels are rendered.

        Args:
            label: Label.

        Returns:
            A Rich Text object.
        """
        if isinstance(label, str):
            text_label = Text(label)
        else:
            text_label = label
        first_line = text_label.split()[0]
        return first_line

    def render_label(
            self, node: TreeNode[DirEntry], base_style: Style, style: Style
    ) -> Text:
        """Render a label for the given node.

        Args:
            node: A tree node.
            base_style: The base style of the widget.
            style: The additional style for the label.

        Returns:
            A Rich Text object containing the label.
        """
        node_label = node._label.copy()
        node_label.stylize(style)

        if node._allow_expand:
            prefix = ("📂 " if node.is_expanded else "📁 ", base_style + TOGGLE_STYLE)
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--folder", partial=True)
            )
        else:
            prefix = (
                "📄 ",
                base_style,
            )
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--file", partial=True),
            )
            node_label.highlight_regex(
                r"\..+$",
                self.get_component_rich_style(
                    "directory-tree--extension", partial=True
                ),
            )

        if node_label.plain.startswith("."):
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--hidden")
            )

        text = Text.assemble(prefix, node_label)
        return text

    def filter_paths(self, paths: Iterable[AudiotekaPath]) -> Iterable[AudiotekaPath]:
        """Filter the paths before adding them to the tree.

        Args:
            paths: The paths to be filtered.

        Returns:
            The filtered paths.

        By default this method returns all of the paths provided. To create
        a filtered `DirectoryTree` inherit from it and implement your own
        version of this method.
        """
        return paths

    @staticmethod
    def _safe_is_dir(path: AudiotekaPath) -> bool:
        """Safely check if a path is a directory.

        Args:
            path: The path to check.

        Returns:
            `True` if the path is for a directory, `False` if not.
        """
        try:
            return path.is_dir()
        except PermissionError:
            # We may or may not have been looking at a directory, but we
            # don't have the rights or permissions to even know that. Best
            # we can do, short of letting the error blow up, is assume it's
            # not a directory. A possible improvement in here could be to
            # have a third state which is "unknown", and reflect that in the
            # tree.
            return False

    def _populate_node(self, node: TreeNode[DirEntry], content: Iterable[AudiotekaPath]) -> None:
        """Populate the given tree node with the given directory content.

        Args:
            node: The Tree node to populate.
            content: The collection of `AudiotekaPath` objects to populate the node with.
        """
        node.remove_children()
        for path in content:
            node.add(
                path.name,
                data=DirEntry(path),
                allow_expand=self._safe_is_dir(path),
            )
        node.expand()

    def _directory_content(self, location: AudiotekaPath, worker: Worker) -> Iterator[AudiotekaPath]:
        """Load the content of a given directory.

        Args:
            location: The location to load from.
            worker: The worker that the loading is taking place in.

        Yields:
            AudiotekaPath: An entry within the location.
        """
        try:
            for entry in location.iterdir():
                if worker.is_cancelled:
                    break
                yield entry
        except PermissionError:
            pass

    @work(thread=True)
    def _load_directory(self, node: TreeNode[DirEntry]) -> list[AudiotekaPath]:
        """Load the directory contents for a given node.

        Args:
            node: The node to load the directory contents for.

        Returns:
            The list of entries within the directory associated with the node.
        """
        assert node.data is not None
        return sorted(
            self.filter_paths(
                self._directory_content(node.data.path, get_current_worker())
            ),
            key=lambda path: (not self._safe_is_dir(path), path.name.lower()),
        )

    @work(exclusive=True)
    async def _loader(self) -> None:
        """Background loading queue processor."""
        worker = get_current_worker()
        while not worker.is_cancelled:
            # Get the next node that needs loading off the queue. Note that
            # this blocks if the queue is empty.
            node = await self._load_queue.get()
            content: list[AudiotekaPath] = []
            try:
                # Spin up a short-lived thread that will load the content of
                # the directory associated with that node.
                content = await self._load_directory(node).wait()
            except WorkerCancelled:
                # The worker was cancelled, that would suggest we're all
                # done here and we should get out of the loader in general.
                break
            except WorkerFailed:
                # This particular worker failed to start. We don't know the
                # reason so let's no-op that (for now anyway).
                pass
            else:
                # We're still here and we have directory content, get it into
                # the tree.
                if content:
                    self._populate_node(node, content)
            finally:
                # Mark this iteration as done.
                self._load_queue.task_done()

    async def _on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        event.stop()
        dir_entry = event.node.data
        if dir_entry is None:
            return
        if self._safe_is_dir(dir_entry.path):
            await self._add_to_load_queue(event.node)
        else:
            self.post_message(self.FileSelected(event.node, dir_entry.path))

    async def _on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        event.stop()
        dir_entry = event.node.data
        if dir_entry is None:
            return
        if not self._safe_is_dir(dir_entry.path):
            self.post_message(self.FileHighlighted(event.node, dir_entry.path))

    def _on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        event.stop()
        dir_entry = event.node.data
        if dir_entry is None:
            return
        if self._safe_is_dir(dir_entry.path):
            self.post_message(self.DirectorySelected(event.node, dir_entry.path))
        else:
            self.post_message(self.FileSelected(event.node, dir_entry.path))
