import os
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pages.TestSave import TestSave
from state import history_state


class TestSavePageTests(unittest.TestCase):
    def setUp(self):
        history_state["saved"] = False
        history_state["history_id"] = None

    def test_back_goes_to_masking(self):
        page = object.__new__(TestSave)
        page.controller = Mock()

        TestSave._on_back(page)

        page.controller.show_page.assert_called_once_with("Masking")

    def test_next_saves_history_once_and_goes_to_session_end(self):
        page = object.__new__(TestSave)
        page.controller = Mock()
        page.next_button = Mock()

        with patch("pages.TestSave.save_upload_step1", return_value={"id": 42}) as save_mock:
            with patch("pages.TestSave.messagebox.showinfo") as info_mock:
                TestSave._on_next(page)

        save_mock.assert_called_once()
        page.controller.show_page.assert_called_once_with("SessionEnd")
        info_mock.assert_called_once()
        self.assertTrue(history_state["saved"])
        self.assertEqual(history_state["history_id"], 42)


if __name__ == "__main__":
    unittest.main()
