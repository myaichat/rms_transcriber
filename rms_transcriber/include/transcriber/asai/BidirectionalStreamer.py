#!/usr/bin/env python3

import json
import os
import sys
import asyncio
import assemblyai as aai
import websockets
import logging
import sounddevice as sd
import argparse
from ...config import init_config
apc = init_config.apc
apc.audio_queue = asyncio.Queue()
import pyaudio
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)

class BidirectionalStreamer:
    def __init__(self):
        self.loop = asyncio.get_event_loop()



    def StartStreaming(self):
        print('BidirectionalStreamer: StartStreaming')
        if 0:

            microphone_stream = aai.extras.MicrophoneStream(sample_rate=16_000)
            self.loop.run_until_complete(apc.transcriber.transcribe(microphone_stream))

        p = pyaudio.PyAudio()
        microphone_stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )    
        self.loop.run_until_complete(apc.transcriber.transcribe(microphone_stream))