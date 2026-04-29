"""
TUI Application Module — fully wired to real backend

Features:
- Full-screen terminal UI with curses
- Real data loading (CSV/JSON/JSONL/TXT)
- Real semantic search with sentence-transformers + FAISS
- Knowledge base shows loaded documents
- Export results to JSON/Markdown/CSV
- Settings that actually toggle
- Graceful error handling
"""

import curses
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

KEY_ESCAPE = 27
KEY_ENTER = 10
KEY_BACKSPACE = 127


class CursesTUI:
    """Interactive terminal UI — connected to real backend"""

    def __init__(self, system=None):
        self.system = system  # MiniWikiIntegratedSystem instance
        self.running = False
        self.screen = None
        self.current_menu = "main"
        self.prev_menu: List[str] = []
        self.menu_index = 0
        self.search_query = ""
        self.search_results: List[Dict] = []
        self.message = ""
        self.message_timer = 0
        self.results_index = 0
        self.kb_index = 0
        self.settings_index = 0
        self.doc_scroll = 0
        self.doc_content = ""
        self.doc_source = ""
        self.theme = "dark"
        self.results_per_page = 10
        self.load_path = ""  # for the load screen
        self.export_format = "json"

        self.menus = {
            "main": [
                ("Load Data", "load_data"),
                ("Search Documents", "search_input"),
                ("View Knowledge Base", "knowledge_base"),
                ("Recent Searches", "results"),
                ("Export Results", "export"),
                ("Settings", "settings"),
                ("Help", "help"),
                ("Exit", "exit"),
            ],
            "settings": [
                ("Theme: Dark", "toggle_theme"),
                ("Results per page: 10", None),
                ("Back to Menu", "main"),
            ],
            "export": [
                ("Export as JSON", "export_json"),
                ("Export as Markdown", "export_md"),
                ("Export as CSV", "export_csv"),
                ("Back to Menu", "main"),
            ],
        }

        # Knowledge base items — populated from loaded data
        self.kb_items: List[str] = []
        self.kb_details: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Safe drawing
    # ------------------------------------------------------------------

    def _safe_addstr(self, y, x, text, attr=curses.A_NORMAL):
        try:
            max_y, max_x = self.screen.getmaxyx()
            if y < 0 or y >= max_y or x < 0 or x >= max_x:
                return
            available = max_x - x - 1
            if available <= 0:
                return
            self.screen.addstr(y, x, text[:available], attr)
        except curses.error:
            pass

    def _safe_hline(self, y, x, ch, n, attr=curses.A_NORMAL):
        try:
            max_y, max_x = self.screen.getmaxyx()
            if y < 0 or y >= max_y:
                return
            n = min(n, max_x - x - 1)
            if n <= 0:
                return
            self.screen.addstr(y, x, ch * n, attr)
        except curses.error:
            pass

    def _go_to(self, target: str):
        self.prev_menu.append(self.current_menu)
        self.current_menu = target
        self.menu_index = 0
        self.results_index = 0
        self.kb_index = 0
        self.settings_index = 0
        self.doc_scroll = 0

    def _go_back(self):
        if self.prev_menu:
            self.current_menu = self.prev_menu.pop()
        else:
            self.current_menu = "main"

    def _show_message(self, msg: str, duration: int = 40):
        self.message = msg
        self.message_timer = duration

    # ------------------------------------------------------------------
    # Start / main loop
    # ------------------------------------------------------------------

    def start(self):
        try:
            curses.wrapper(self._main_loop)
        except Exception as e:
            logger.error(f"TUI error: {e}")
            print(f"\nError: {e}\n")

    def _main_loop(self, stdscr):
        self.screen = stdscr
        self.running = True
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        stdscr.keypad(True)
        stdscr.nodelay(False)

        # Show loaded docs count on start
        if self.system and self.system.documents:
            self._show_message(f"{len(self.system.documents)} documents loaded")

        while self.running:
            try:
                self._render()
                stdscr.refresh()
                key = stdscr.getch()
                self._handle_input(key)
                if self.message_timer > 0:
                    self.message_timer -= 1
                    if self.message_timer == 0:
                        self.message = ""
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                logger.debug(f"Render error: {e}")
                self._show_message(f"Error: {str(e)[:60]}")

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self):
        try:
            self.screen.clear()
        except curses.error:
            pass
        height, width = self.screen.getmaxyx()
        if height < 5 or width < 20:
            self._safe_addstr(0, 0, "Terminal too small", curses.A_BOLD)
            return

        dispatch = {
            "main": self._render_main,
            "load_data": self._render_load_data,
            "search_input": self._render_search_input,
            "results": self._render_results,
            "knowledge_base": self._render_knowledge_base,
            "settings": self._render_settings,
            "help": self._render_help,
            "doc_viewer": self._render_doc_viewer,
            "export": self._render_export,
        }
        renderer = dispatch.get(self.current_menu, self._render_main)
        renderer(width, height)

    def _render_main(self, width, height):
        title = "mini_wiki - Universal Research Assistant"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        # Show document count
        if self.system and self.system.documents:
            doc_info = f"[ {len(self.system.documents)} documents loaded ]"
            self._safe_addstr(3, width - len(doc_info) - 4, doc_info, curses.A_DIM)

        items = self.menus["main"]
        for i, (label, _) in enumerate(items):
            y = 5 + i
            if y >= height - 3:
                break
            if i == self.menu_index:
                self._safe_addstr(y, 4, f" > {label}", curses.A_REVERSE | curses.A_BOLD)
            else:
                self._safe_addstr(y, 4, f"   {label}")

        self._safe_addstr(height - 2, 2, "Up/Down: Navigate  Enter: Select  Q: Quit", curses.A_DIM)
        if self.message:
            self._safe_addstr(height - 4, 4, self.message[:width - 6], curses.A_BOLD)

    def _render_load_data(self, width, height):
        title = "Load Data"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        self._safe_addstr(5, 4, "Enter path to data file (CSV, JSON, JSONL, TXT):")
        self._safe_addstr(7, 4, "> ", curses.A_BOLD)
        self._safe_addstr(7, 6, self.load_path + "_")

        if self.system and self.system.documents:
            self._safe_addstr(9, 4, f"Currently loaded: {len(self.system.documents)} documents", curses.A_BOLD)

        self._safe_addstr(height - 2, 2, "Type path  Enter: Load  Esc: Back", curses.A_DIM)

    def _render_search_input(self, width, height):
        title = "Search Documents"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        if not self.system or not self.system.documents:
            self._safe_addstr(5, 4, "No documents loaded. Go to 'Load Data' first.", curses.A_BOLD)
            self._safe_addstr(7, 4, "Press Esc to go back.")
        else:
            self._safe_addstr(5, 4, f"Search across {len(self.system.documents)} documents:")
            self._safe_addstr(7, 4, "> ", curses.A_BOLD)
            self._safe_addstr(7, 6, self.search_query + "_")

            if self.search_results:
                self._safe_addstr(9, 4, f"Found {len(self.search_results)} results:", curses.A_BOLD)
                for i, result in enumerate(self.search_results):
                    y = 11 + i
                    if y >= height - 3:
                        break
                    t = result.get("title", "Untitled")[:width - 14]
                    s = result.get("relevance", 0)
                    self._safe_addstr(y, 6, f"{i+1}. {t} ({s:.3f})")

        self._safe_addstr(height - 2, 2, "Type: Search  Enter: Execute  Esc: Back", curses.A_DIM)

    def _render_results(self, width, height):
        title = "Search Results"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        if not self.search_results:
            self._safe_addstr(5, 4, "No results yet. Search first (Esc to go back).")
        else:
            self._safe_addstr(5, 4, f"  #  {'Document':<30} {'Score':<8} {'Level':<8}", curses.A_BOLD)
            self._safe_hline(6, 4, "-", width - 8)

            for i, result in enumerate(self.search_results):
                y = 7 + i
                if y >= height - 3:
                    break
                t = result.get("title", "Untitled")[:28]
                s = result.get("relevance", 0)
                level = "High" if s >= 0.7 else "Med" if s >= 0.5 else "Low"
                line = f"  {i+1:<3} {t:<30} {s:<8.3f} {level:<8}"
                if i == self.results_index:
                    self._safe_addstr(y, 4, line, curses.A_REVERSE)
                else:
                    self._safe_addstr(y, 4, line)

        self._safe_addstr(height - 2, 2, "Up/Down: Navigate  Enter: View  Esc: Back", curses.A_DIM)

    def _render_knowledge_base(self, width, height):
        title = "Knowledge Base"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        if not self.system or not self.system.documents:
            self._safe_addstr(5, 4, "No documents loaded. Go to 'Load Data' first.", curses.A_BOLD)
        else:
            self._safe_addstr(5, 4, f"Loaded documents ({len(self.system.documents)}):", curses.A_BOLD)

            for i, doc in enumerate(self.system.documents[:height - 9]):
                y = 7 + i
                if y >= height - 3:
                    self._safe_addstr(y, 4, f"  ... and {len(self.system.documents) - i} more")
                    break
                title_text = doc.get("title", f"Doc {i+1}")[:width - 10]
                if i == self.kb_index:
                    self._safe_addstr(y, 4, f" > {i+1}. {title_text}", curses.A_REVERSE)
                else:
                    self._safe_addstr(y, 4, f"   {i+1}. {title_text}")

        self._safe_addstr(height - 2, 2, "Up/Down: Navigate  Enter: View  Esc: Back", curses.A_DIM)

    def _render_settings(self, width, height):
        title = "Settings"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        # Dynamic settings
        items = [
            (f"Theme: {self.theme.capitalize()}", "toggle_theme"),
            (f"Results per page: {self.results_per_page}", None),
            (f"Documents loaded: {len(self.system.documents) if self.system else 0}", None),
            ("Back to Menu", "main"),
        ]
        for i, (label, _) in enumerate(items):
            y = 5 + i
            if y >= height - 3:
                break
            if i == self.settings_index:
                self._safe_addstr(y, 4, f" > {label}", curses.A_REVERSE)
            else:
                self._safe_addstr(y, 4, f"   {label}")

        self._safe_addstr(height - 2, 2, "Up/Down: Navigate  Enter: Select  Esc: Back", curses.A_DIM)

    def _render_export(self, width, height):
        title = "Export Results"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        if not self.search_results:
            self._safe_addstr(5, 4, "No results to export. Search first.")
        else:
            self._safe_addstr(5, 4, f"Export {len(self.search_results)} results as:", curses.A_BOLD)

            items = self.menus["export"]
            for i, (label, _) in enumerate(items):
                y = 7 + i
                if y >= height - 3:
                    break
                if i == self.menu_index:
                    self._safe_addstr(y, 4, f" > {label}", curses.A_REVERSE)
                else:
                    self._safe_addstr(y, 4, f"   {label}")

        self._safe_addstr(height - 2, 2, "Up/Down: Navigate  Enter: Select  Esc: Back", curses.A_DIM)

    def _render_help(self, width, height):
        title = "Help"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        lines = [
            ("mini_wiki - Universal Research Assistant", curses.A_BOLD),
            ("", None),
            ("WORKFLOW:", curses.A_BOLD),
            ("  1. Load Data    Load a CSV/JSON/JSONL/TXT file", None),
            ("  2. Search       Type a query, get semantic results", None),
            ("  3. View         Browse results, view documents", None),
            ("  4. Export       Save results as JSON/Markdown/CSV", None),
            ("", None),
            ("KEYBOARD:", curses.A_BOLD),
            ("  Up/Down    Navigate", None),
            ("  Enter      Select / Confirm", None),
            ("  Esc        Go back", None),
            ("  Q          Quit (main menu)", None),
            ("", None),
            ("SEARCH:", curses.A_BOLD),
            ("  Uses sentence-transformers for semantic search", None),
            ("  Results ranked by relevance score (0-1)", None),
        ]

        for i, (line, attr) in enumerate(lines):
            y = 5 + i
            if y >= height - 3:
                break
            self._safe_addstr(y, 4, line[:width - 6], attr if attr else curses.A_NORMAL)

        self._safe_addstr(height - 2, 2, "Esc: Back", curses.A_DIM)

    def _render_doc_viewer(self, width, height):
        title = "Document Viewer"
        self._safe_addstr(1, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self._safe_hline(3, 2, "-", width - 4)

        lines = self.doc_content.split("\n")
        visible = lines[self.doc_scroll : self.doc_scroll + max(1, height - 6)]
        for i, line in enumerate(visible):
            y = 5 + i
            if y >= height - 3:
                break
            self._safe_addstr(y, 4, line[:width - 6])

        self._safe_addstr(height - 2, 2, "Up/Down: Scroll  Esc: Back", curses.A_DIM)

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _handle_input(self, key):
        dispatch = {
            "main": self._handle_main_input,
            "load_data": self._handle_load_input,
            "search_input": self._handle_search_input,
            "results": self._handle_results_input,
            "knowledge_base": self._handle_kb_input,
            "settings": self._handle_settings_input,
            "help": self._handle_help_input,
            "doc_viewer": self._handle_doc_viewer_input,
            "export": self._handle_export_input,
        }
        handler = dispatch.get(self.current_menu)
        if handler:
            handler(key)

    def _handle_main_input(self, key):
        items = self.menus["main"]
        if key == curses.KEY_UP:
            self.menu_index = max(0, self.menu_index - 1)
        elif key == curses.KEY_DOWN:
            self.menu_index = min(len(items) - 1, self.menu_index + 1)
        elif key in (KEY_ENTER, 10, 13):
            _, target = items[self.menu_index]
            if target == "exit":
                self.running = False
            elif target:
                self._go_to(target)
        elif key == ord("q") or key == ord("Q"):
            self.running = False

    def _handle_load_input(self, key):
        if key == KEY_ESCAPE:
            self._go_back()
        elif key in (KEY_ENTER, 10, 13):
            if self.load_path.strip():
                self._do_load()
        elif key in (KEY_BACKSPACE, 8, 127):
            self.load_path = self.load_path[:-1]
        elif 32 <= key <= 126:
            self.load_path += chr(key)

    def _do_load(self):
        path = self.load_path.strip()
        # Expand ~ to home directory
        path = os.path.expanduser(path)
        if not self.system:
            self._show_message("System not initialized")
            return
        ok = self.system.load_data(path, "auto")
        if ok:
            n = len(self.system.documents)
            self._show_message(f"Loaded {n} documents from {Path(path).name}")
            # Update KB items
            self.kb_items = [d.get("title", f"Doc {i+1}") for i, d in enumerate(self.system.documents)]
        else:
            self._show_message(f"Failed to load: {path}")

    def _handle_search_input(self, key):
        if key == KEY_ESCAPE:
            self._go_back()
        elif key in (KEY_ENTER, 10, 13):
            if self.search_query.strip():
                self._do_search()
                self._go_to("results")
        elif key in (KEY_BACKSPACE, 8, 127):
            self.search_query = self.search_query[:-1]
        elif 32 <= key <= 126:
            self.search_query += chr(key)

    def _do_search(self):
        if not self.system or not self.system.documents:
            self.search_results = [
                {"id": f"doc_{i}", "title": "No documents loaded — use Load Data first",
                 "content": "Go to Load Data from the main menu to load a file.",
                 "relevance": 0.5, "importance": 0.5, "source": "system", "date": ""}
                for i in range(3)
            ]
            self._show_message("No documents loaded")
            return

        try:
            self.search_results = self.system.search(self.search_query, limit=self.results_per_page)
            self._show_message(f"Found {len(self.search_results)} results")
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.search_results = []
            self._show_message(f"Search error: {str(e)[:50]}")

    def _handle_results_input(self, key):
        if key == KEY_ESCAPE:
            self._go_back()
        elif not self.search_results:
            if key in (KEY_ENTER, 10, 13):
                self._go_to("search_input")
        else:
            if key == curses.KEY_UP:
                self.results_index = max(0, self.results_index - 1)
            elif key == curses.KEY_DOWN:
                self.results_index = min(len(self.search_results) - 1, self.results_index + 1)
            elif key in (KEY_ENTER, 10, 13):
                result = self.search_results[self.results_index]
                self.doc_content = (
                    f"Document: {result.get('title', 'Untitled')}\n"
                    f"Source: {result.get('source', 'Unknown')}\n"
                    f"Relevance: {result.get('relevance', 0):.3f}\n"
                    f"Importance: {result.get('importance', 0):.3f}\n"
                    f"\n{result.get('content', 'No content available.')}\n"
                )
                self.doc_source = "results"
                self.doc_scroll = 0
                self._go_to("doc_viewer")

    def _handle_kb_input(self, key):
        if key == KEY_ESCAPE:
            self._go_back()
        elif key == curses.KEY_UP:
            self.kb_index = max(0, self.kb_index - 1)
        elif key == curses.KEY_DOWN:
            n = len(self.system.documents) if self.system else len(self.kb_items)
            self.kb_index = min(n - 1, self.kb_index + 1) if n > 0 else 0
        elif key in (KEY_ENTER, 10, 13):
            if self.system and self.system.documents:
                idx = min(self.kb_index, len(self.system.documents) - 1)
                doc = self.system.documents[idx]
                self.doc_content = (
                    f"Document: {doc.get('title', 'Untitled')}\n"
                    f"Source: {doc.get('source', 'Unknown')}\n"
                    f"\n{doc.get('content', 'No content available.')}\n"
                )
            else:
                topic = self.kb_items[self.kb_index] if self.kb_index < len(self.kb_items) else "Unknown"
                self.doc_content = f"Topic: {topic}\n\nNo documents loaded."
            self.doc_source = "knowledge_base"
            self.doc_scroll = 0
            self._go_to("doc_viewer")

    def _handle_settings_input(self, key):
        if key == KEY_ESCAPE:
            self._go_back()
        elif key == curses.KEY_UP:
            self.settings_index = max(0, self.settings_index - 1)
        elif key == curses.KEY_DOWN:
            self.settings_index = min(3, self.settings_index + 1)  # 4 items
        elif key in (KEY_ENTER, 10, 13):
            if self.settings_index == 0:
                # Toggle theme
                self.theme = "light" if self.theme == "dark" else "dark"
                self._show_message(f"Theme: {self.theme}")
            elif self.settings_index == 3:
                self._go_to("main")

    def _handle_export_input(self, key):
        if key == KEY_ESCAPE:
            self._go_back()
        elif key == curses.KEY_UP:
            self.menu_index = max(0, self.menu_index - 1)
        elif key == curses.KEY_DOWN:
            self.menu_index = min(len(self.menus["export"]) - 1, self.menu_index + 1)
        elif key in (KEY_ENTER, 10, 13):
            items = self.menus["export"]
            _, action = items[self.menu_index]
            if action == "export_json":
                self._do_export("json")
            elif action == "export_md":
                self._do_export("markdown")
            elif action == "export_csv":
                self._do_export("csv")
            elif action == "main":
                self._go_to("main")

    def _do_export(self, fmt: str):
        if not self.search_results:
            self._show_message("No results to export")
            return
        ext = "json" if fmt == "json" else ("md" if fmt == "markdown" else "csv")
        path = f"/tmp/mini_wiki_results.{ext}"
        if self.system:
            ok = self.system.export_results(self.search_results, fmt, path)
            if ok:
                self._show_message(f"Exported to {path}")
            else:
                self._show_message("Export failed")
        else:
            self._show_message("System not initialized")

    def _handle_help_input(self, key):
        if key == KEY_ESCAPE:
            self._go_back()

    def _handle_doc_viewer_input(self, key):
        if key == KEY_ESCAPE:
            self._go_back()
        elif key == curses.KEY_UP:
            self.doc_scroll = max(0, self.doc_scroll - 1)
        elif key == curses.KEY_DOWN:
            self.doc_scroll += 1


def run_tui(system=None):
    """Run the TUI application with optional system instance."""
    tui = CursesTUI(system=system)
    tui.start()


if __name__ == "__main__":
    run_tui()