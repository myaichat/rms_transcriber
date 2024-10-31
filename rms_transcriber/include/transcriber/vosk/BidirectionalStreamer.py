#!/usr/bin/env python3

import json
import os
import sys
import asyncio
import websockets
import logging
import sounddevice as sd
import argparse
from ...config import init_config
apc = init_config.apc
apc.audio_queue = asyncio.Queue()

SAMPLE_RATE = 16000

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status, loop):
    """This is called (from a separate thread) for each audio block."""
    loop.call_soon_threadsafe(apc.audio_queue.put_nowait, bytes(indata))

class BidirectionalStreamer:
    def __init__(self):
        self.loop = asyncio.get_event_loop()



    def StartStreaming(self):
        print('BidirectionalStreamer: StartStreaming')

        # Start the input stream, passing the main loop to the callback
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=4000, device=None, dtype='int16',
                               channels=1, callback=lambda *args: callback(*args, self.loop)):
            print('#' * 80)
            
            # Run your transcribe function in the main loop
            rid = 0
            self.loop.run_until_complete(apc.transcriber.transcribe())

