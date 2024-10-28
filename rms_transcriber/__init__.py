from .include.config import init_config

from .include.transcriber.goog.AsyncTranscriber import AsyncTranscriber
from .include.transcriber.goog.BidirectionalStreamer import BidirectionalStreamer
from .include.RMSFrame import RMSFrame

# Initialize apc globally
init_config.init(**{})  # Initialize the configuration
apc = init_config.apc  # Expose apc

__all__ = [ 'apc','AsyncTranscriber','BidirectionalStreamer','RMSFrame']
#pip install -e .