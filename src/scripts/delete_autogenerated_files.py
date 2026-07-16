import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from build.output.site_output import delete_output_file_space
from core.logging_config import configure_logging
from core import utils

configure_logging()
utils.find_project_root()
delete_output_file_space()
