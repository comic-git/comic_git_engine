import logging
from unittest import TestCase
from unittest.mock import patch

from core import logging_config


class TestConfigureLogging(TestCase):
    def setUp(self):
        self.root_logger = logging.getLogger()
        self.original_handlers = list(self.root_logger.handlers)
        self.original_level = self.root_logger.level
        self.addCleanup(self.restore_root_logger)

    def restore_root_logger(self):
        for handler in list(self.root_logger.handlers):
            self.root_logger.removeHandler(handler)
            if handler not in self.original_handlers:
                handler.close()
        for handler in self.original_handlers:
            self.root_logger.addHandler(handler)
        self.root_logger.setLevel(self.original_level)

    def test_configure_logging_defaults_to_info_with_human_readable_format(self):
        with patch.dict("os.environ", {}, clear=True):
            logging_config.configure_logging(force=True)

        self.assertEqual(logging.INFO, self.root_logger.level)
        self.assertEqual(logging_config.HUMAN_READABLE_FORMAT, self.root_logger.handlers[0].formatter._fmt)

    def test_configure_logging_uses_env_var_level(self):
        with patch.dict("os.environ", {logging_config.LOG_LEVEL_ENV_VAR: "DEBUG"}, clear=True):
            logging_config.configure_logging(force=True)

        self.assertEqual(logging.DEBUG, self.root_logger.level)

    def test_configure_logging_accepts_lowercase_level_with_whitespace(self):
        with patch.dict("os.environ", {logging_config.LOG_LEVEL_ENV_VAR: " warning "}, clear=True):
            logging_config.configure_logging(force=True)

        self.assertEqual(logging.WARNING, self.root_logger.level)

    def test_configure_logging_accepts_numeric_level(self):
        with patch.dict("os.environ", {logging_config.LOG_LEVEL_ENV_VAR: "10"}, clear=True):
            logging_config.configure_logging(force=True)

        self.assertEqual(logging.DEBUG, self.root_logger.level)

    def test_configure_logging_falls_back_to_info_for_invalid_level(self):
        with (
            patch.dict("os.environ", {logging_config.LOG_LEVEL_ENV_VAR: "LOUD"}, clear=True),
            patch("core.logging_config.logging.getLogger") as mock_get_logger,
        ):
            logging_config.configure_logging(force=True)

        self.assertEqual(logging.INFO, self.root_logger.level)
        mock_get_logger.return_value.warning.assert_called_once_with(
            "Invalid %s value %r; using %s",
            logging_config.LOG_LEVEL_ENV_VAR,
            "LOUD",
            logging_config.DEFAULT_LOG_LEVEL,
        )
