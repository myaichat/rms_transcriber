import re
import sys
import asyncio
import wx
import wx.html2
from urllib.parse import unquote
from pubsub import pub
from wxasync import WxAsyncApp, AsyncBind, StartCoroutine
import markdown2
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from concurrent.futures import ThreadPoolExecutor
from rms_transcriber import  AsyncProcessor
#from rms_transcriber import  whisper_AsyncRecognizer #goog_AsyncRecognizer , vosk_AsyncRecognizer,
from rms_transcriber.include.transcriber.whisper._AsyncTranscriber import   AsyncTranscriber
from rms_transcriber import whisper_BidirectionalStreamer as BidirectionalStreamer
from rms_transcriber import apc

apc.processor   = None
apc.transcriber = None
streamer=BidirectionalStreamer( )

async def run_streaming_in_executor():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, streamer.StartStreaming)
        
from rms_transcriber.include.center.CenterPanel import CenterPanel

from rms_transcriber.include.left.whisper.LeftPanel import LeftPanel        


        
from rms_transcriber import whisper_RMSFrame as RMSFrame
apc.mock=False
apc.processor_model_name=None
apc.whisper_lang = "en"

class SelectionDialog(wx.Dialog):
    def __init__(self, parent, title="Select Option"):
        super().__init__(parent, title=title, size=(300, 200))
        self.panel = wx.Panel(self)

        # Create radio buttons for selection
        self.radio_option1 = wx.RadioButton(self.panel, label="en-US", style=wx.RB_GROUP)
        self.radio_option2 = wx.RadioButton(self.panel, label="uk-UA")
        self.radio_option3 = wx.RadioButton(self.panel, label="ru-RU")
        # OK and Cancel buttons
        ok_button = wx.Button(self.panel, label="OK")
        cancel_button = wx.Button(self.panel, label="Cancel")
        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        # Set OK button as the default to enable Enter key functionality
        ok_button.SetDefault()

        # Layout for radio buttons
        radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        radio_sizer.Add(self.radio_option1, 0, wx.ALL, 5)
        radio_sizer.Add(self.radio_option2, 0, wx.ALL, 5)
        radio_sizer.Add(self.radio_option3, 0, wx.ALL, 5)
        

        # Layout for buttons, aligned to the bottom-right corner
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer(1)  # Adds space to push buttons to the right
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)
        button_sizer.Add(ok_button, 0, wx.ALL, 5)

        # Main vertical sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(radio_sizer, 1, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.BOTTOM | wx.RIGHT, 10)

        self.panel.SetSizer(main_sizer)

        # Center the dialog on the screen
        self.CenterOnScreen()
        self.selected_option = "en-US"

    def on_ok(self, event):
        # Determine which radio button is selected
        if self.radio_option1.GetValue():
            self.selected_option = "en-US"
            apc.whisper_lang = "en"
        elif self.radio_option2.GetValue():
            self.selected_option = "uk-UA"
            apc.whisper_lang = "uk"
        elif self.radio_option3.GetValue():
            self.selected_option = "ru-RU"
            apc.whisper_lang = "ru"
        
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
async def show_selection_dialog():
    """Function to show the selection dialog and wait for the user response."""
    dialog = SelectionDialog(None, "Choose an option")
    if dialog.ShowModal() == wx.ID_OK:
        print("User selected:", dialog.selected_option)
        return dialog.selected_option
    else:
        print("User canceled the dialog.")
        return None


async def main():
    app = WxAsyncApp() 
    frame = RMSFrame( title="RMS Transcriber for OpenAI Whisper", size=(1200, 1000))
    frame.Show()
    await app.MainLoop()
async def main():
    apc.askmodel_queue = asyncio.Queue()
    apc.question_queue = asyncio.Queue()
    apc.trans_queue = asyncio.Queue()
    apc.recog_queue = asyncio.Queue()
    app = WxAsyncApp()  # Use WxAsyncApp for async compatibility
    if 1:
        user_selection = await show_selection_dialog()
        apc.transcription_lang = user_selection
        if user_selection is None:
            print("Exiting app as dialog was canceled.")
            return  # Exit if the dialog is canceled    
        #Resumable Microphone Streaming 
    frame = RMSFrame(  title="RMS Transcribe for Assembly AI", size=(1600, 1000))
    #frame.SetSize((1200, 1000)) 
    frame.Show()
    frame.CenterOnScreen()
    
    apc.processor = AsyncProcessor(apc.askmodel_queue)
    apc.question_processor = AsyncProcessor(apc.question_queue)
    
    apc.transcriber = AsyncTranscriber(apc.trans_queue)
    
    #apc.goog_recognizer = goog_AsyncRecognizer(apc.recog_queue)
    #apc.asai_recognizer = asai_AsyncRecognizer(apc.recog_queue)
    #apc.vosk_recognizer = vosk_AsyncRecognizer(apc.recog_queue)
    # Start the queue consumer task
    if 1:
        asyncio.create_task(run_streaming_in_executor())
        asyncio.create_task(frame.processor_panel.left_panel.processor_panel.consume_askmodel_queue(apc.askmodel_queue))
        asyncio.create_task(frame.processor_panel.right_panel.processor_panel.consume_question_queue(apc.question_queue))
        #asyncio.create_task(apc.goog_recognizer.consume_recognizer_queue(apc.recog_queue))
        #asyncio.create_task(apc.vosk_recognizer.consume_recognizer_queue(apc.recog_queue))
        #asyncio.create_task(apc.asai_recognizer.consume_recognizer_queue(apc.recog_queue))
        if 1:
            asyncio.create_task(frame.left_panel.tree.consume_transcription_queue())
            asyncio.create_task(frame.left_panel.tree.update_tree_periodically())
        if 0:
            asyncio.create_task(frame.left_panel.tree_2.consume_transcription_queue())
            asyncio.create_task(frame.left_panel.tree_2.update_tree_periodically())        
        asyncio.create_task(frame.processor_panel.left_panel.processor_panel.update_webview_periodically())
        asyncio.create_task(frame.processor_panel.right_panel.processor_panel.update_webview_periodically())


    await app.MainLoop()  # Run the app's main loop asynchronously
if __name__ == "__main__":
    asyncio.run(main())