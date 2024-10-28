from .include.config import init_config
#from .include.utils import execute_pipeline
from .include.left.LeftPanel import LeftPanel
from .include.left.CustomHtmlListBox import CustomHtmlListBox
from .include.left.MultiLineHtmlTreeCtrl import MultiLineHtmlTreeCtrl
from .include.transcriber.goog.AsyncTranscriber import AsyncTranscriber
from .include.transcriber.goog.BiderectionalStreamer import BiderectionalStreamer
from .include.RMSFrame import RMSFrame







# Initialize apc globally
init_config.init(**{})  # Initialize the configuration
apc = init_config.apc  # Expose apc

__all__ = [ 'apc','CustomHtmlListBox','MultiLineHtmlTreeCtrl','AsyncTranscriber','BiderectionalStreamer','LeftPanel','RMSFrame']
#pip install -e .