import subprocess

from dos33 import catalog_entries, catalog_entry_as_text, contents_of_entry, list_applesoft, open_file
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal, HorizontalScroll, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Markdown,
    Static,
    TabbedContent,
    TabPane,
    TextLog,
)


class FileScreen(Screen):
    """Screen with file contents"""

    def __init__(self, disk, entry):
        super().__init__()
        self.disk = disk
        self.entry = entry
        self.data = open_file(disk, entry)
        self.tab_data = []
        if entry["file_type"] == "A":
            self.tab_data.append(("Listing", list_applesoft(self.data)))
        stripped_data = bytes(_ & 0x7f for _ in self.data)
        self.tab_data.append(("Text", stripped_data.decode("ascii", "ignore").replace("\r", "\n")))
        hexdump_process = subprocess.run("/usr/bin/hexdump -C".split(), capture_output=True, input=stripped_data)
        self.tab_data.append(("Stripped hex dump", hexdump_process.stdout.decode()))
        hexdump_process = subprocess.run("/usr/bin/hexdump -C".split(), capture_output=True, input=self.data)
        self.tab_data.append(("Hex dump", hexdump_process.stdout.decode()))

    def compose(self) -> ComposeResult:
        with Header():
            yield Static(f"View of {self.entry['name'].strip()}")
        with TabbedContent():
            for _ in self.tab_data:
                with TabPane(_[0]):
                    yield Static(_[1], markup=False)
        with Footer():
            yield Static("Press any key to exit")

    def on_key(self, event: events.Key) -> None:
        self.app.pop_screen()


class AppleDiskBrowser(App):
    CSS_PATH = "apple_disk_browser.css"

    def compose(self) -> ComposeResult:
        with Header():
            yield Static("Apple Disk Image Browser")
        with Horizontal():
            yield DirectoryTree("/Users/kiss/tmp/autorm/apple-ii-disks/")
            self.static = DataTable()
            self.static.cursor_type = "row"
            self.file_contents = TextLog()
            self.file_contents.wrap = True
            with Vertical():
                yield self.static
        yield Footer()

    def on_directory_tree_file_selected(self, message):
        self.file_contents.clear()
        try:
            self.disk = open(message.path, "rb").read(143360)
            self.entries = list(catalog_entries(self.disk))
            output = [catalog_entry_as_text(_) for _ in self.entries]
        except Exception as ex:
            output = [f"error: {ex}"]
        self.static.clear()
        self.static.add_column("Catalog")
        self.static.add_rows([[_] for _ in output])

    def on_data_table_row_selected(self, message):
        entry = self.entries[message.cursor_row]
        self.push_screen(FileScreen(self.disk, entry))


if __name__ == "__main__":
    app = AppleDiskBrowser()
    app.run()
