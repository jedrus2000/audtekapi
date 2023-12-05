"""
Code browser example.

Run with:

    python code_browser.py PATH
"""
from __future__ import annotations

import sys
from copy import copy

from lxml import etree
from pathlib import Path
from urllib.parse import urlparse, unquote
from slugify import slugify

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widgets import Footer, Header, Static, Log
from textual import work
from audioteka_tree import DirectoryTree, AudiotekaPath

from audioteka_tree import api

categories = api.get_categories()


class CodeBrowser(App):
    """Textual code browser app."""

    CSS_PATH = "browser.tcss"
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("d", "download_content", "Download"),
        ("q", "quit", "Quit"),
    ]

    show_tree = var(True)

    selected_node: AudiotekaPath | None = None

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = "./" if len(sys.argv) < 2 else sys.argv[1]
        yield Header()
        with Container():
            yield DirectoryTree(path, id="tree-view")
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
            yield Log(id="log")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    def on_directory_tree_directory_selected(
            self, event: DirectoryTree.FileSelected):
        event.stop()
        self.selected_node = event.path

    def on_directory_tree_file_selected(
            self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        self.selected_node = event.path
        code_view = self.query_one("#code", Static)
        try:
            syntax = Syntax(
                event.path.data_as_str,
                'json',
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)

    def on_directory_tree_file_highlighted(
            self, event: DirectoryTree.FileHighlighted
    ) -> None:
        """Called when file is highlighted"""
        event.stop()
        self.selected_node = None
        code_view = self.query_one("#code", Static)
        code_view.update()
        self.sub_title = ""

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree

    async def _write_to_log(self, line):
        log: Log = self.query_one("#log", Log)
        log.write_line(line)

    @work(exclusive=False, thread=True)
    async def _download_book_from_selected_node(self, node: AudiotekaPath):
        def format_item_number(number: int, no_of_items: int) -> str:
            max_digits = len(str(no_of_items))
            return str(number).zfill(max_digits)
        book_data = node.data
        node_name = node.name
        await self._write_to_log(f"{node_name}: Downloading")
        # category
        category_id = book_data['main_category_id']
        book_data['category_name'] = ""
        if category_id:
            for category in categories['_embedded']['app:category']:
                if category['id'] == category_id:
                    book_data['category_name'] = category['name']
                    break
        # opf
        await self._write_to_log(f"{node_name}: Creating OPF file")
        author_name = book_data['_embedded']['app:author'][0]['name']
        tile = book_data['name']
        parts = author_name.split()
        if len(parts) >= 2:
            author_name = f"{' '.join(parts[1:])}, {parts[0]}"
        book_dir = Path("books", f"{author_name}", f"{tile}")
        book_dir.mkdir(parents=True, exist_ok=True)
        self._create_opf_file(book_data, book_dir)
        # cover
        await self._write_to_log(f"{node_name} Downloading cover.")
        r = api._session.get(book_data['image_url'])
        Path(book_dir, 'cover.jpg').write_bytes(r.content)
        # book content
        audiobook_id = book_data['id']
        tracks_list = api.get_audiobook_track_list(audiobook_id)
        tracks_number = len(tracks_list['_embedded']['app:track'])
        add_number_in_front = False
        for idx, track in enumerate(tracks_list['_embedded']['app:track']):
            await self._write_to_log(f"{node_name}: Downloading track {idx+1} of of {tracks_number}")
            file_info = api.get_track(track['_links']['app:file']['href'])
            # filename = Path(book_dir, f"{track['title']}.mp3")
            # filename = Path(book_dir, unquote(urlparse(file_info['url']).path).split('/')[-1])
            slug_track_name = slugify(track['title'], allow_unicode=True)
            if idx == 0 and slug_track_name[0].isdigit():
                add_number_in_front = False
            elif idx == 0:
                add_number_in_front = True
            if not add_number_in_front:
                track_number_str = ''
            else:
                track_number_str = f"{format_item_number(idx+1, tracks_number)}-"
            filename = Path(book_dir, f"{track_number_str}{slug_track_name}.mp3")
            response = api._session.get(file_info['url'], stream=True, timeout=(90, 180))
            with open(filename, "wb") as f:
                # Iterate over the chunks of the response content
                for chunk in response.iter_content(chunk_size=8192):
                    # Write the chunk to the file
                    f.write(chunk)
        #
        await self._write_to_log(f"{node_name} Done !")

    async def action_download_content(self) -> None:
        """Called in response to key binding."""
        if self.selected_node and self.selected_node.audioteka_obj_type == 'app:product':
            node = copy(self.selected_node)
            self._download_book_from_selected_node(node)

    def _create_opf_file(self, book_data: dict, file_path: Path):
        title = book_data['name']
        authors = book_data['_embedded']['app:author']
        narrator = book_data['_embedded']['app:lector'][0]['name']
        publish_year = book_data['published_at'].split('-')[0]
        publisher = book_data['_embedded']['app:publisher'][0]['name']
        isbn = ""
        description = book_data['description']
        genres = book_data['category_name']
        language = book_data['_embedded']['app:context']['country'].lower()
        series = ''
        volume_number = '1'
        NSMAP = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf'
        }

        # Create the root element with namespaces
        package = etree.Element('package', nsmap=NSMAP, attrib={
            '{http://www.w3.org/XML/1998/namespace}lang': 'en',
            'version': '3.0',
            'unique-identifier': 'bookid'
        })

        # Create the metadata element
        metadata = etree.SubElement(package, 'metadata')

        # Add fields to metadata with proper namespace
        etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}title').text = title
        for author in authors:
            etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}creator', attrib={'{http://www.idpf.org/2007/opf}role': 'aut'}).text = author['name']
        etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}creator', attrib={'{http://www.idpf.org/2007/opf}role': 'nrt'}).text = narrator
        etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}date').text = publish_year
        etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}publisher').text = publisher
        etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}identifier', attrib={'id': 'bookid'}).text = isbn
        etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}description').text = description
        etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}language').text = language
        etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}relation').text = f'{series} - Volume {volume_number}'

        # Adding genres
        for genre in genres.split(','):
            etree.SubElement(metadata, '{http://purl.org/dc/elements/1.1/}subject').text = genre.strip()

        # Create a string from the ElementTree
        opf_string = etree.tostring(package, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        # Write to file
        with open(Path(file_path, 'book.opf'), 'wb') as file:
            file.write(opf_string)


if __name__ == "__main__":
    CodeBrowser().run()
