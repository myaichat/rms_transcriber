
import requests
import os
from os.path import isfile  
import assemblyai as aai
import time
import json
import asyncio
from pubsub import pub  
from pprint import pprint as pp


from ..config import init_config
apc = init_config.apc

aai.settings.api_key = os.getenv("ASSEMBLY_API_KEY")


class AsyncRecognizer:
    def __init__(self, queue):
        self.queue = queue
        self.transcriber = aai.Transcriber()

    async def consume_recognizer_queue(self, queue):
        # Continuously consume the queue and update WebView
        while True:

            content = await queue.get()

            await  self.transcribe(content)    
            #queue.task_done()
         
    async def transcribe(self, content):
        file_name,tid, rid = content
        #websocket=self.websocket
        print(f"ASAI: AsyncRecognizer: Transcribing: {file_name}",tid, rid)
        assert isfile(file_name)

        transcription = self.transcriber.transcribe(file_name)
        #pp (dir(transcript))
        print(transcription.text)    
        if 1:
            transcript=transcription.text
            #if transcript:
            #await apc.transcriber.queue.put(['ASAI 1: '+transcript,'stream_recognized', tid, rid])
            pub.sendMessage("stream_recognized", data=('ASAI pub: '+transcript, tid, rid))

            await asyncio.sleep(0.1)


