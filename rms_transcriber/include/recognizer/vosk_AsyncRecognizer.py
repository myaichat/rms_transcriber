
import asyncio
import websockets
import sys
from pubsub import pub
from os.path import isfile
import wave
from ..config import init_config
apc = init_config.apc
from pprint import pprint as pp
import json

# Instantiates a client



class AsyncRecognizer:
    def __init__(self, queue):
        self.queue = queue
        self.uri='ws://localhost:2700'
        self.websocket = websockets.connect(self.uri)



    async def consume_recognizer_queue(self, queue):
        # Continuously consume the queue and update WebView
        while True:

            content = await queue.get()

            await  self.transcribe(content)    
            queue.task_done()
         
    async def transcribe(self, content):
        file_name,tid, rid = content
        #websocket=self.websocket
        print(f"VOSK: AsyncRecognizer: Transcribing: {file_name}")
        assert isfile(file_name)
        async with websockets.connect(self.uri) as websocket:

            wf = wave.open(file_name, "rb")
            await websocket.send('{ "config" : { "max_alternatives" : 1, "sample_rate" : %d } }' % (wf.getframerate()))
            buffer_size = int(wf.getframerate() * 0.2) # 0.2 seconds of audio
            while True:
                data = wf.readframes(buffer_size)

                if len(data) == 0:
                    break

                await websocket.send(data)
                result=await websocket.recv()
                print(111, result)

            await websocket.send('{"eof" : 1}')
            result= json.loads (await websocket.recv())
            #print(111, type(result))
            transcription=result['alternatives'][0]
            transcript=transcription['text']
            #if transcript:
            await apc.transcriber.queue.put(['VOSK2: '+transcript,'stream_recognized', tid, rid])
            pub.sendMessage("stream_recognized", data=('VOSK: '+transcript, tid, rid))

            await asyncio.sleep(0.1)


