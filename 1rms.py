import wx
import asyncio
import wx.html
from wxasync import WxAsyncApp
from pubsub import pub
from pprint import pprint as pp
from rms_transcriber import AsyncTranscriber, AsyncProcessor
from rms_transcriber import BidirectionalStreamer
from rms_transcriber import RMSFrame    
from concurrent.futures import ThreadPoolExecutor
from rms_transcriber import apc

apc.processor   = None
apc.transcriber = None
streamer=BidirectionalStreamer( )

async def run_streaming_in_executor():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, streamer.StartStreaming)

async def main():
    apc.proc_queue = asyncio.Queue()
    apc.trans_queue = asyncio.Queue()
    app = WxAsyncApp()  # Use WxAsyncApp for async compatibility
    #Resumable Microphone Streaming 
    frame = RMSFrame(  title="RMS Transcribe for Google Speech", size=(1200, 1000))
    #frame.SetSize((1200, 1000)) 
    frame.Show()
    apc.processor = AsyncProcessor(apc.proc_queue)
    apc.transcriber = AsyncTranscriber(apc.trans_queue)
    # Start the queue consumer task

    asyncio.create_task(run_streaming_in_executor())

    asyncio.create_task(frame.left_panel.tree.consume_transcription_queue())
    asyncio.create_task(frame.left_panel.tree.update_tree_periodically())
    asyncio.create_task(frame.center_panel.processor_panel.update_webview_periodically())
    
    await app.MainLoop()  # Run the app's main loop asynchronously

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run() to start the main function   