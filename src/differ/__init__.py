import re
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Input, Label, Static, TextArea


class Differ:
  """Handles parsing and applying diff blocks."""

  @staticmethod
  def parse_diff(diff_content: str) -> list[tuple[str, str]]:
    """Parse diff content into (search, replace) pairs.

    Markers must be whole lines. Each line in a pair ends with a newline,
    so an empty section has zero lines.
    """
    blocks = []
    search: list[str] | None = None
    replace: list[str] | None = None
    for line in diff_content.split("\n"):
      if search is None:
        if re.fullmatch(r"<{8}\s*SEARCH\s*", line):
          search = []
      elif replace is None:
        if re.fullmatch(r"={8}\s*", line):
          replace = []
        else:
          search.append(line + "\n")
      elif re.fullmatch(r">{8}\s*REPLACE\s*", line):
        blocks.append(("".join(search), "".join(replace)))
        search = replace = None
      else:
        replace.append(line + "\n")
    return blocks

  @staticmethod
  def apply_diff(file_path: Path, diff_blocks: list[tuple[str, str]]) -> tuple[bool, str]:
    """Apply diff blocks to a file. Returns (success, message)."""
    try:
      # check if this is a new file creation (single block with empty search)
      if len(diff_blocks) == 1 and diff_blocks[0][0] == "":
        existed = file_path.exists()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(diff_blocks[0][1])
        return True, f"{'Rewrote' if existed else 'Created new'} file: {file_path}"

      if any(search == "" for search, _ in diff_blocks):
        return False, "Empty SEARCH (new file or full rewrite) must be the only block"

      if not file_path.exists():
        return False, f"File not found: {file_path}"

      content = file_path.read_text()
      # match whole lines: every line, the last one too, must end with a newline
      missing_final_newline = not content.endswith("\n")
      if missing_final_newline:
        content += "\n"

      for i, (search, replace) in enumerate(diff_blocks, 1):
        # first match that starts at a line start
        match = re.search("^" + re.escape(search), content, re.MULTILINE)
        if not match:
          return False, f"Block {i}: Search text not found in file"

        content = content[: match.start()] + replace + content[match.end() :]

      if missing_final_newline:
        content = content.removesuffix("\n")

      file_path.write_text(content)

      changes = len(diff_blocks)
      return True, f"Successfully applied {changes} change(s) to {file_path}"

    except (OSError, UnicodeError) as e:
      return False, f"Error: {e!s}"


class DifferApp(App):
  """A TUI app for applying SEARCH/REPLACE diffs."""

  CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        padding: 1;
    }

    #input-container {
        height: auto;
        margin-bottom: 1;
    }

    #file-input {
        margin-bottom: 1;
    }

    #diff-container {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }

    #diff-area {
        height: 100%;
    }

    #button-container {
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }

    #status {
        height: auto;
        margin-top: 1;
        padding: 1;
        background: $boost;
        color: $text;
    }

    .success {
        background: $success;
        color: $text;
    }

    .error {
        background: $error;
        color: $text;
    }

    Label {
        margin-bottom: 1;
    }
    """

  BINDINGS: ClassVar[list[BindingType]] = [
    Binding("ctrl+s", "apply_diff", "Apply"),
    Binding("ctrl+r", "clear", "Clear"),
  ]

  def compose(self) -> ComposeResult:
    """Compose the UI."""
    yield Header()

    with Container(id="main-container"):
      yield Label(f"CWD: {Path.cwd()}", id="cwd-label")

      with Vertical(id="input-container"):
        yield Label("File Path (relative to current directory):")
        yield Input(placeholder="e.g., src/main.py", id="file-input")

      with Container(id="diff-container"):
        yield Label("Diff Content:")
        yield TextArea("", id="diff-area", language="python", theme="monokai", show_line_numbers=True)

      yield Static("Ready", id="status")

    yield Footer()

  def on_mount(self) -> None:
    """Set focus when app starts."""
    self.query_one("#file-input").focus()

  def _timestamp(self) -> str:
    return datetime.now().strftime("%H:%M:%S")

  def action_apply_diff(self) -> None:
    """Apply the diff (keyboard shortcut)."""
    self.apply_diff()

  def action_clear(self) -> None:
    """Clear fields (keyboard shortcut)."""
    self.clear_fields()

  def apply_diff(self) -> None:
    """Parse and apply the diff to the file."""
    file_input = self.query_one("#file-input", Input)
    diff_area = self.query_one("#diff-area", TextArea)
    status = self.query_one("#status", Static)

    file_path_str = file_input.value.strip()
    diff_content = diff_area.text

    # Validation
    if not file_path_str:
      status.update(f"[{self._timestamp()}] Error: Please enter a file path")
      status.remove_class("success")
      status.add_class("error")
      return

    if not diff_content.strip():
      status.update(f"[{self._timestamp()}] Error: Please enter diff content")
      status.remove_class("success")
      status.add_class("error")
      return

    diff_blocks = Differ.parse_diff(diff_content)

    if not diff_blocks:
      status.update(f"[{self._timestamp()}] Error: No valid diff blocks found. Check format.")
      status.remove_class("success")
      status.add_class("error")
      return

    file_path = Path.cwd() / file_path_str
    success, message = Differ.apply_diff(file_path, diff_blocks)

    status.update(f"[{self._timestamp()}] {message}")
    if success:
      status.remove_class("error")
      status.add_class("success")
    else:
      status.remove_class("success")
      status.add_class("error")

  def clear_fields(self) -> None:
    """Clear diff content first, then file path if diff is empty."""
    diff_area = self.query_one("#diff-area", TextArea)
    file_input = self.query_one("#file-input", Input)
    if diff_area.text.strip():
      diff_area.text = ""
      diff_area.focus()
    else:
      file_input.value = ""
      file_input.focus()
    status = self.query_one("#status", Static)
    status.update(f"[{self._timestamp()}] Ready")
    status.remove_class("success", "error")


def main():
  """Run the application."""
  app = DifferApp()
  app.run()
