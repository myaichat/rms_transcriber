from colorama import Fore, Style
import re
import sys
import time
import wave
import os

from google.cloud import speech
from pubsub import pub
from ...config import init_config
apc = init_config.apc


import asyncio
import websockets
import sys
from pubsub import pub
from os.path import isfile
import wave
from ...config import init_config
apc = init_config.apc
from pprint import pprint as pp
import json

# Instantiates a client

SAMPLE_RATE = 16000

# Ensure a directory for audio chunks exists
os.makedirs("audio_chunks", exist_ok=True)

chunk_counter = 0  # Counter for unique file names

def save_audio_chunk(item_id, audio_data, chunk_counter):
    """Saves the audio data to a .wav file."""
    file_name = f"audio_chunks/{item_id}.chunk_{chunk_counter}.wav"
    if os.path.exists(file_name):
        os.remove(file_name)
        #print(f"Deleted existing file: {file_name}")

    with wave.open(file_name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # Assuming 16-bit audio (pyaudio.paInt16)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data)
       
    num_frames = len(audio_data) // (2 * 1)  # audio_data length in bytes, 2 bytes per sample, 1 channel
    duration = num_frames / SAMPLE_RATE  # Duration in seconds   
    print(f"Saved: {file_name}")
    print(f"Audio Duration: {duration:.2f} seconds")
    
    return file_name, duration
chunk_counter = 0
class AsyncTranscriber:
    def __init__(self, queue):
        self.queue = queue
        self.uri='ws://localhost:2700'
        self.websocket = websockets.connect(self.uri)
        self.audio_input = []
        self.last_saved_index=0



         
    async def transcribe(self):
        global chunk_counter 
     

        async with websockets.connect(self.uri) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % (SAMPLE_RATE))
            tid=0
            rid=0
            pid=0
            while True:
                data = await apc.audio_queue.get()
                self.audio_input.append(data)
                await websocket.send(data)
                #print (111, await websocket.recv())
                result= json.loads (await websocket.recv())
                if 'partial' in result:
                    transcription=result['partial']
                    if transcription:
                        #print(f"VOSK partial: {transcription}", rid, pid)
                        #pub.sendMessage("partial_stream", data=(transcript, corrected_time, tid, rid))
                        await apc.trans_queue.put([f'await {pid}:{transcription}','partial_stream', tid, rid])                       
                        pid += 1    
                elif 'result' in result:
                    transcription=result['text']
                    if transcription:
                        print(f"VOSK final: {transcription}", rid)
                        #await apc.trans_queue.put([f'await {tid}:{rid}: {transcription}','stream_closed', tid, rid])
                        pub.sendMessage("stream_closed2", data=(f'pub {tid}:{rid}: {transcription}', None, tid, rid)) 
                        item_id= f'{tid}.{rid}'
                        new_audio_data = b"".join(self.audio_input[self.last_saved_index:])
                        file_name, duration=save_audio_chunk(item_id, new_audio_data, chunk_counter) 
                        print(len(self.audio_input),len(self.audio_input[self.last_saved_index:]), self.last_saved_index)
                        self.last_saved_index = len(self.audio_input)
       
                        chunk_counter += 1  
                        if duration <60:
                            await apc.recog_queue.put([file_name,tid, rid])
                        else:
                            print(f"Audio duration too long: {duration:.2f} seconds")  
                        rid += 1       
                        pid=0                                                    
                elif 'text' in result:
                    
                    text=result['text'] 
                    if text:
                        pp(result)
                        print(f"VOSK TEXT: {text}", tid)
                        raise Exception('VOSK: Unexpected response from server')
        if 0:
            await websocket.send('{"eof" : 1}')
            #print (await websocket.recv())
            result= json.loads (await websocket.recv())
            #print(111, type(result))
            transcription=result['alternatives'][0]
            transcript=transcription['text']
            #if transcript:


            await asyncio.sleep(0.1)


