import os
import sys
from unittest import TestCase
from unittest.mock import MagicMock, patch

from integrations import hooks


MUT = "integrations.hooks."


class TestRunHook(TestCase):
    @patch(MUT + "import_module")
    @patch(MUT + "os.path.exists", return_value=False)
    def test_missing_hook_file_is_a_no_op(self, _mock_exists, mock_import_module):
        result = hooks.run_hook("default", "modify_comic_data", [{"title": "Page"}])

        self.assertIsNone(result)
        mock_import_module.assert_not_called()

    @patch(MUT + "import_module")
    @patch(MUT + "os.path.exists", return_value=True)
    def test_calls_named_theme_hook_with_supplied_arguments(self, _mock_exists, mock_import_module):
        hook_module = MagicMock()
        hook_module.modify_comic_data.return_value = {"title": "Modified"}
        mock_import_module.return_value = hook_module

        result = hooks.run_hook(
            "custom-theme",
            "modify_comic_data",
            [{"title": "Original"}, 7],
        )

        mock_import_module.assert_called_once_with(
            "your_content.themes.custom-theme.scripts.hooks"
        )
        hook_module.modify_comic_data.assert_called_once_with({"title": "Original"}, 7)
        self.assertEqual({"title": "Modified"}, result)

    @patch(MUT + "import_module")
    @patch(MUT + "os.path.exists", return_value=True)
    def test_missing_named_function_is_a_no_op(self, _mock_exists, mock_import_module):
        hook_module = MagicMock(spec=[])
        mock_import_module.return_value = hook_module

        self.assertIsNone(hooks.run_hook("custom-theme", "unknown_hook", []))

    @patch(MUT + "import_module")
    @patch(MUT + "os.path.exists", return_value=True)
    def test_adds_project_directory_to_import_path_only_once(self, _mock_exists, mock_import_module):
        hook_module = MagicMock(spec=[])
        mock_import_module.return_value = hook_module
        project_directory = os.path.abspath(".")
        original_path = sys.path.copy()
        sys.path = [path for path in sys.path if path != project_directory]
        try:
            hooks.run_hook("custom-theme", "unknown_hook", [])
            hooks.run_hook("custom-theme", "unknown_hook", [])
        finally:
            updated_path = sys.path.copy()
            sys.path = original_path

        self.assertEqual(1, updated_path.count(project_directory))
