
import os
import assemblyai as aai
from pprint import pprint as pp 
import asyncio
import wave
import concurrent.futures
from pubsub import pub
from ...config import init_config
apc = init_config.apc


aai.settings.api_key = os.getenv("ASSEMBLY_API_KEY")



# Instantiates a client

SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)
# Ensure a directory for audio chunks exists
os.makedirs("audio_chunks", exist_ok=True)



class AsyncTranscriber:
    def __init__(self, queue):
        self.queue = queue
        self.transcriber = aai.Transcriber()
        self.audio_input = []
        self.last_saved_index = 0
        self.chunk_counter = 0
        self.tid = 0
        self.rid = 0
        self.pid = 0
        self.loop = asyncio.get_event_loop()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        #config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        #language="en"
        
        self.transcriber = aai.RealtimeTranscriber(
            sample_rate=16_000,
            word_boost=["aws", "azure", "google cloud", 'PySpark'],
            #boost_param="high",
            #disable_partial_transcripts=True
            on_data=self.on_data,
            on_error=self.on_error,
            on_open=self.on_open,
            on_close=self.on_close,
        )

    async def save_audio_chunk(self, item_id, audio_data, chunk_counter, rid):
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
                    await asyncio.sleep(0.01)
        
            num_frames = len(audio_data) // (2 * 1)  # Calculate frames correctly
            duration = num_frames / SAMPLE_RATE  # Duration in seconds   
            print(f"Saved: {file_name}")
            print(f"Audio Duration: {duration:.2f} seconds")

            self.chunk_counter += 1 

            if duration < 60:
                print(apc.tanscribe_file_queue)
                print([item_id,file_name, self.tid, rid])
                apc.tanscribe_file_queue.put([item_id,file_name, self.tid, rid])
                #apc.save_audio_queue.put([item_id, new_audio_data, self.chunk_counter,  self.tid,current_rid])
            else:
                print(f"Audio duration too long: {duration:.2f} seconds")            
        
            return file_name, duration

        except Exception as e:
            print(f"Error 111 saving audio chunk: {e}")
            raise e
            return None, 0

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        print("Session ID:", session_opened.session_id)
        #self.transcriber.set_config(language_code="ru")

    def on_data(self, transcript: aai.RealtimeTranscript):
        if not transcript.text:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            print(777, transcript.text, end="\r\n")
            current_rid = self.rid
            pub.sendMessage("stream_closed2", data=(f'final pub {self.tid}:{self.rid}: {transcript.text}', None, self.tid, current_rid))

            self.loop.call_soon_threadsafe(lambda: asyncio.create_task(apc.trans_queue.put([f'Fin await {self.tid}:{self.rid}: {transcript.text}', 'stream_closed', self.tid, current_rid])))

            item_id = f'{self.tid}.{self.rid}'
            new_audio_data = self.audio_input[self.last_saved_index:]

            print(f"Attempting to save audio chunk with item_id: {item_id}")
            if 1:
                future = asyncio.run_coroutine_threadsafe(
                    self.save_audio_chunk(item_id, new_audio_data, self.chunk_counter, current_rid),
                    self.loop
                )
            else:
                apc.save_audio_queue.put([item_id, new_audio_data, self.chunk_counter,  self.tid,current_rid])
            self.last_saved_index = len(self.audio_input)
            self.rid += 1
            self.pid = 0

        else:
            print(transcript.text[-100:], end="\r")
            self.loop.call_soon_threadsafe(lambda: asyncio.create_task(apc.trans_queue.put([f'{self.tid}:{self.pid}: await p :{transcript.text}', 'partial_stream', self.tid, self.rid])))
            #pub.sendMessage("partial_stream", data=(f'{self.tid}:{self.pid}: await p :{transcript.text}', None, self.tid, self.rid))
            self.pid += 1


    def on_error(self, error: aai.RealtimeError):
        print("An error occured:", error)


    def on_close(self):
        print("Closing Session")





         
    async def transcribe(self, microphone_stream):
        global chunk_counter 
     


        self.transcriber.connect()

        if 0:
            self.transcriber.stream(microphone_stream)

            self.transcriber.close()

            await asyncio.sleep(0.1)


        while True:
                audio_data = microphone_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                self.audio_input.append(audio_data)
                # Send the audio data chunk to the transcriber
                self.transcriber.stream(audio_data)

                # Optionally, save each chunk to file for analysis or backup
                # self.save_audio_chunk("microphone_stream", audio_data, self.chunk_counter)
                # self.chunk_counter += 1
                

                await asyncio.sleep(0.01)          