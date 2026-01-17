import tempfile
import unittest
from pathlib import Path

from differ import Differ


def block(search: str, replace: str) -> str:
  return f"<<<<<<<< SEARCH\n{search}========\n{replace}>>>>>>>> REPLACE\n"


class DifferTest(unittest.TestCase):
  def setUp(self):
    self.dir = tempfile.TemporaryDirectory()
    self.file = Path(self.dir.name) / "a.py"

  def tearDown(self):
    self.dir.cleanup()

  def apply(self, diff: str) -> tuple[bool, str]:
    return Differ.apply_diff(self.file, Differ.parse_diff(diff))

  def test_replaces_lines(self):
    self.file.write_text("a\n  b\nc\n")
    self.assertTrue(self.apply(block("  b\n", "  B\n"))[0])
    self.assertEqual(self.file.read_text(), "a\n  B\nc\n")

  def test_ignores_text_outside_blocks(self):
    self.file.write_text("a\nb\n")
    self.assertTrue(self.apply("```\n" + block("a\n", "A\n") + "```\n")[0])
    self.assertEqual(self.file.read_text(), "A\nb\n")

  def test_needs_eight_character_markers(self):
    self.assertEqual(Differ.parse_diff("<<<<<<< SEARCH\na\n=======\nb\n>>>>>>> REPLACE\n"), [])

  def test_empty_replace_deletes_lines(self):
    self.file.write_text("a\nb\nc\n")
    self.assertTrue(self.apply(block("b\n", ""))[0])
    self.assertEqual(self.file.read_text(), "a\nc\n")

  def test_empty_replace_does_not_take_next_block(self):
    self.file.write_text("a\nb\nc\n")
    self.assertTrue(self.apply(block("a\n", "") + block("c\n", "C\n"))[0])
    self.assertEqual(self.file.read_text(), "b\nC\n")

  def test_blank_replace_leaves_blank_line(self):
    self.file.write_text("a\nb\nc\n")
    self.assertTrue(self.apply(block("b\n", "\n"))[0])
    self.assertEqual(self.file.read_text(), "a\n\nc\n")

  def test_search_can_contain_equals_rule(self):
    self.file.write_text("# ==========\nx = 1\n")
    self.assertTrue(self.apply(block("# ==========\nx = 1\n", "# ==========\nx = 2\n"))[0])
    self.assertEqual(self.file.read_text(), "# ==========\nx = 2\n")

  def test_keeps_blank_lines_at_section_edges(self):
    self.file.write_text("a\n\nb\n\nc\n")
    self.assertTrue(self.apply(block("\nb\n\n", "\nB\n\n\n"))[0])
    self.assertEqual(self.file.read_text(), "a\n\nB\n\n\nc\n")

  def test_matches_whole_lines_only(self):
    self.file.write_text("max = 10\n")
    ok, message = self.apply(block("x = 1\n", "x = 2\n"))
    self.assertFalse(ok)
    self.assertIn("not found", message)
    self.assertEqual(self.file.read_text(), "max = 10\n")

  def test_replaces_first_match_only(self):
    self.file.write_text("b\nb\n")
    self.assertTrue(self.apply(block("b\n", "B\n"))[0])
    self.assertEqual(self.file.read_text(), "B\nb\n")

  def test_failed_block_changes_nothing(self):
    self.file.write_text("a\nb\n")
    ok, message = self.apply(block("a\n", "A\n") + block("zzz\n", "q\n"))
    self.assertFalse(ok)
    self.assertIn("Block 2", message)
    self.assertEqual(self.file.read_text(), "a\nb\n")

  def test_keeps_missing_final_newline(self):
    self.file.write_text("a\nb")
    self.assertTrue(self.apply(block("b\n", "B\n"))[0])
    self.assertEqual(self.file.read_text(), "a\nB")

  def test_empty_search_creates_file_with_final_newline(self):
    self.file = Path(self.dir.name) / "new" / "b.py"
    ok, message = self.apply(block("", "x = 1\n"))
    self.assertTrue(ok)
    self.assertIn("Created", message)
    self.assertEqual(self.file.read_text(), "x = 1\n")

  def test_empty_search_reports_rewrite_of_existing_file(self):
    self.file.write_text("old\n")
    ok, message = self.apply(block("", "new\n"))
    self.assertTrue(ok)
    self.assertIn("Rewrote", message)
    self.assertEqual(self.file.read_text(), "new\n")

  def test_reports_unreadable_path(self):
    self.file.mkdir()
    ok, message = self.apply(block("a\n", "A\n"))
    self.assertFalse(ok)
    self.assertIn("Error", message)

  def test_reports_undecodable_file(self):
    self.file.write_bytes(b"\xff\xfe\n")
    ok, message = self.apply(block("a\n", "A\n"))
    self.assertFalse(ok)
    self.assertIn("Error", message)

  def test_empty_search_must_be_only_block(self):
    self.file.write_text("a\nb\n")
    ok, message = self.apply(block("", "TOP\n") + block("b\n", "B\n"))
    self.assertFalse(ok)
    self.assertIn("only block", message)
    self.assertEqual(self.file.read_text(), "a\nb\n")


if __name__ == "__main__":
  unittest.main()
