from .include.config import init_config
from .include.processor.openai.AsyncProcessor import AsyncProcessor
from .include.recognizer.goog_AsyncRecognizer import AsyncRecognizer as goog_AsyncRecognizer
from .include.recognizer.vosk_AsyncRecognizer import AsyncRecognizer as vosk_AsyncRecognizer
from .include.recognizer.asai_AsyncRecognizer import AsyncRecognizer as asai_AsyncRecognizer
#no recog for whisper
from .include.transcriber.goog.AsyncTranscriber import AsyncTranscriber as goog_AsyncTranscriber
from .include.transcriber.vosk.AsyncTranscriber import AsyncTranscriber as vosk_AsyncTranscriber
from .include.transcriber.asai.AsyncTranscriber import AsyncTranscriber as asai_AsyncTranscriber
from .include.transcriber.whisper.AsyncTranscriber import AsyncTranscriber as whisper_AsyncTranscriber

from .include.transcriber.goog.BidirectionalStreamer import BidirectionalStreamer as goog_BidirectionalStreamer
from .include.transcriber.vosk.BidirectionalStreamer import BidirectionalStreamer as vosk_BidirectionalStreamer
from .include.transcriber.asai.BidirectionalStreamer import BidirectionalStreamer as asai_BidirectionalStreamer
from .include.transcriber.whisper.BidirectionalStreamer import BidirectionalStreamer as whisper_BidirectionalStreamer
from .include.frame.goog_RMSFrame import RMSFrame as goog_RMSFrame
from .include.frame.vosk_RMSFrame import RMSFrame as vosk_RMSFrame
from .include.frame.asai_RMSFrame import RMSFrame as asai_RMSFrame
from .include.frame.whisper_RMSFrame import RMSFrame as whisper_RMSFrame

# Initialize apc globally
init_config.init(**{})  # Initialize the configuration
apc = init_config.apc  # Expose apc

__all__ = [ 'apc','AsyncTranscriber','goog_BidirectionalStreamer',
           'vosk_BidirectionalStreamer', 'goog_AsyncTranscriber', 'vosk_AsyncTranscriber',  
           'goog_RMSFrame', 'AsyncProcessor','goog_AsyncRecognizer',  'asai_AsyncRecognizer',
           'asai_AsyncTranscriber', 'asai_RMSFrame', 'asai_BidirectionalStreamer',
           'vosk_AsyncRecognizer', 'vosk_RMSFrame','asai_RMSFrame','whisper_RMSFrame',
           'whisper_BidirectionalStreamer', 'whisper_AsyncTranscriber']
#pip install -e .