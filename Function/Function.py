"""Re-export bridge from core/ modules.

AVDC_Main_new.py and legacy modules import from Function.Function;
this module re-exports the relevant symbols from core/.
"""
from core.file_utils import getNumber, movie_lists, escapePath, check_pic
from core.config_io import save_config
from core.metadata import get_info
from core.scrape_pipeline import getDataFromJSON
