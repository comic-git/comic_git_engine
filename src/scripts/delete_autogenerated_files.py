import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build.output.site_output import delete_output_file_space
from core.utils import find_project_root

find_project_root()
delete_output_file_space()
