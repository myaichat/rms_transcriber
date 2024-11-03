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
  
        self.loop.run_until_complete(apc.transcriber.transcribe())