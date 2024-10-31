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
from rms_transcriber import  asai_AsyncRecognizer #goog_AsyncRecognizer , vosk_AsyncRecognizer,
from rms_transcriber import asai_AsyncTranscriber as    AsyncTranscriber
from rms_transcriber import asai_BidirectionalStreamer as BidirectionalStreamer
from rms_transcriber import apc

apc.processor   = None
apc.transcriber = None
streamer=BidirectionalStreamer( )

async def run_streaming_in_executor():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, streamer.StartStreaming)
        
from rms_transcriber.include.center.CenterPanel import CenterPanel

from rms_transcriber.include.left.asai.LeftPanel import LeftPanel        

class _RMSFrame(wx.Frame):
    def __init__(self, title, size):
        super(RMSFrame, self).__init__(None, title=title, 
                                           size=size)
        #panel= wx.Panel(self)
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left_panel = LeftPanel(splitter)
        #self.tree = MultiLineHtmlTreeCtrl(panel, size=(380, 480))

        self.center_panel = CenterPanel(splitter)   

        # Split the main splitter window vertically between the left and right notebooks
        splitter.SplitVertically(self.left_panel, self.center_panel)
        splitter.SetSashGravity(0.5)  # Set initial split at 50% width for each side
        splitter.SetMinimumPaneSize(400)  # Minimum pane width to prevent collapsing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        #sizer.Add(self.button, 0, wx.CENTER | wx.ALL, 5)
        #sizer.Add(self.abutton, 0, wx.CENTER | wx.ALL, 5)
        #panel.SetSizer(sizer)
        self.content_buffer = ""
        self.Layout()
        
from rms_transcriber.include.frame.asai_RMSFrame import RMSFrame     
apc.mock=False
apc.processor_model_name=None
class SelectionDialog(wx.Dialog):
    def __init__(self, parent, title="Select Option"):
        super().__init__(parent, title=title, size=(300, 200))
        self.panel = wx.Panel(self)

        # Create radio buttons for selection
        self.radio_option1 = wx.RadioButton(self.panel, label="en-US", style=wx.RB_GROUP)
        self.radio_option2 = wx.RadioButton(self.panel, label="uk-UA")
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

    def on_ok(self, event):
        # Determine which radio button is selected
        if self.radio_option1.GetValue():
            self.selected_option = "en-US"
        elif self.radio_option2.GetValue():
            self.selected_option = "uk-UA"

        
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
import queue, time
import wave, os
SAMPLE_RATE=16000
def save_audio_chunk(loop, item_id, audio_data, chunk_counter, tid,rid):
    """Saves the audio data to a .wav file."""
    if not audio_data:  # Check if there's audio data
        print("No audio data to save.")
        return None, 0

    file_name = f"audio_chunks/{item_id}.chunk_{chunk_counter}.wav"
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"Deleted existing file: {file_name}")

    try:
        with wave.open(file_name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # Assuming 16-bit audio
            wf.setframerate(SAMPLE_RATE)

            for chunk in audio_data:
                wf.writeframes(chunk)
                
    
        num_frames = len(b''.join(audio_data)) // (2 * 1)  # Calculate frames correctly
        duration = num_frames / SAMPLE_RATE  # Duration in seconds   
        print(f"Saved: {file_name}")
        print(f"Audio Duration: {duration:.2f} seconds")

        if 0:
            if duration < 60:
                #asyncio.create_task(apc.recog_queue.put([file_name, tid, rid]))
                print(f"RECOG QUEUE: {file_name}, {tid}, {rid}")
                asyncio.run_coroutine_threadsafe(apc.recog_queue.put([file_name, tid, rid]), loop)
            else:
                print(f"Audio duration too long: {duration:.2f} seconds")            
    
        return file_name, duration

    except Exception as e:
        print(f"Error saving audio chunk: {e}")
        raise   e
        return None, 0
        
def _long_running_process(q):
    """start bidirectional streaming from microphone input to speech API"""
    chunk_counter = 0

    while True:
        try:
            # Try to get a message from the queue with a timeout
            message = q.get(timeout=1)  # Wait for 1 second for a message
            item_id, file_name,tid, rid = message
            if message == "STOP":  # A special message to exit the loop
                print("Stopping thread.")
                break
            

            if 1:
                import requests
                import os
                import assemblyai as aai
                import time
                from pprint import pprint as pp

                # Set the API key
                aai.settings.api_key = os.getenv("ASSEMBLY_API_KEY")

                # Upload the local audio file using requests
                assert os.path.isfile(file_name)
                transcriber = aai.Transcriber()
                transcript = transcriber.transcribe(file_name)
                #pp (dir(transcript))
                print('THREAT RECOGNIZE:', transcript.text, tid, rid) 
                pub.sendMessage("stream_recognized", data=('ASAI pub: '+transcript.text, tid, rid))


            q.task_done()  # Mark the task as done
        except queue.Empty:
            # Handle the case where no message was received within the timeout
            continue

async def main():
    app = WxAsyncApp() 
    frame = RMSFrame( title="RMS Transcribe for Google Speech", size=(1200, 1000))
    frame.Show()
    await app.MainLoop()
async def main():
    apc.askmodel_queue = asyncio.Queue()
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
    frame = RMSFrame(  title="RMS Transcribe for Google Speech", size=(1200, 1000))
    #frame.SetSize((1200, 1000)) 
    frame.Show()
    frame.CenterOnScreen()
    
    apc.processor = AsyncProcessor(apc.askmodel_queue)
    
    apc.transcriber = AsyncTranscriber(apc.trans_queue)
    
    #apc.goog_recognizer = goog_AsyncRecognizer(apc.recog_queue)
    apc.asai_recognizer = asai_AsyncRecognizer(apc.recog_queue)
    #apc.vosk_recognizer = vosk_AsyncRecognizer(apc.recog_queue)
    # Start the queue consumer task
    if 1:
        asyncio.create_task(run_streaming_in_executor())
        asyncio.create_task(frame.center_panel.processor_panel.consume_askmodel_queue(apc.askmodel_queue))
        #asyncio.create_task(apc.goog_recognizer.consume_recognizer_queue(apc.recog_queue))
        #asyncio.create_task(apc.vosk_recognizer.consume_recognizer_queue(apc.recog_queue))
        asyncio.create_task(apc.asai_recognizer.consume_recognizer_queue(apc.recog_queue))
        if 1:
            asyncio.create_task(frame.left_panel.tree.consume_transcription_queue())
            asyncio.create_task(frame.left_panel.tree.update_tree_periodically())
        if 0:
            asyncio.create_task(frame.left_panel.tree_2.consume_transcription_queue())
            asyncio.create_task(frame.left_panel.tree_2.update_tree_periodically())        
        asyncio.create_task(frame.center_panel.processor_panel.update_webview_periodically())

    if 1:        
        import threading
        apc.tanscribe_file_queue = queue.Queue()
        long_running_thread = threading.Thread(target=_long_running_process, args=(apc.tanscribe_file_queue,))
        long_running_thread.start()     
        if 0: 
            for i in range(5):
                apc.tanscribe_file_queue.put(f"Message {i + 1}")
                #time.sleep(0.5)
          
    await app.MainLoop()  # Run the app's main loop asynchronously
if __name__ == "__main__":
    asyncio.run(main())