# speech_server.py
import sys
import json
import socket
from datetime import datetime, timedelta
from queue import Queue
import speech_recognition as sr
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import io
from scipy.io import wavfile
import signal
import os
#! python3.7
#https://gist.github.com/Oceanswave/32da596e8bb10c928f6c69c889c3c130
import argparse
import io
import os
import torch
from transformers import pipeline
import speech_recognition as sr

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform
from scipy.io import wavfile
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from rich import print as pp    


def setup_whisper_model(model_id="openai/whisper-large-v3", cache_dir="cache"):
    # Set device and dtype
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    # Load processor first
    processor = AutoProcessor.from_pretrained(model_id)
    
    # Load the model with proper configuration
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        cache_dir=cache_dir,
    )
    model.config.pad_token_id = processor.tokenizer.pad_token_id  # Add this line
    model.to(device)
    
    # Create pipeline with modified settings
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
        model_kwargs={
            "use_flash_attention_2": False,
            "pad_token_id": processor.tokenizer.pad_token_id,  # Add this line
        },
        generate_kwargs={
            "task": "transcribe",
            "language": "en",
        }
    )
    
    return pipe, processor, model

# Usage

# Usage
from argparse import Namespace
def transcribe():



    args = Namespace(
        model_name='openai/whisper-large-v3',
        energy_threshold=400,
        record_timeout=2,
        phrase_timeout=4,
        language='en',
        batch_size=24,
        task='transcribe',
        timestamp='chunk',
        device_id='cpu'
    )

    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Current raw audio bytes.
    last_sample = bytes()
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold #400
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3"

    pipe, processor, model = setup_whisper_model()        
    sampling_rate = pipe.feature_extractor.sampling_rate

    ts = "word" if args.timestamp == "word" else True

    language = None if args.language == "None" else args.language

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    if "linux" in platform:
        mic_name = args.default_microphone
        if not mic_name or mic_name == "list":
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f'Microphone with name "{name}" found')
            return
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(
                        sample_rate=sampling_rate, device_index=index
                    )
                    break
    else:
        source = sr.Microphone(sample_rate=sampling_rate)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    transcription = [""]

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(
        source, record_callback, phrase_time_limit=record_timeout
    )

    # Cue the user that we're ready to go.
    print("Model loaded.\n")

    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(
                    seconds=phrase_timeout
                ):
                    last_sample = bytes()
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now

                # Concatenate our current audio data with the latest audio data.
                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                # Use AudioData to convert the raw data to wav data.
                audio_data = sr.AudioData(
                    last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH
                )
                wav_data = io.BytesIO(audio_data.get_wav_data())

                # Convert the wav data to a numpy ndarray
                sample_rate, audio_array = wavfile.read(wav_data)
                # audio_array is the numpy ndarray containing the audio data

                # Read the transcription.
                with Progress(
                    TextColumn("🤗 [progress.description]{task.description}"),
                    BarColumn(style="yellow1", pulse_style="white"),
                    TimeElapsedColumn(),
                ) as progress:
                    progress.add_task("[yellow]Transcribing...", total=None)
                    outputs = pipe(
                        audio_array,
                        chunk_length_s=30,
                        batch_size=args.batch_size,
                        generate_kwargs={"task": args.task, "language": language},
                        return_timestamps=ts,
                    )
                    # result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
                    text = outputs["text"].strip()

                # If we detected a pause between recordings, add a new item to our transcription.
                # Otherwise edit the existing one.
                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text

                # Clear the console to reprint the updated transcription.
                os.system("cls" if os.name == "nt" else "clear")
                for line in transcription:
                    print(line)
                # Flush stdout.
                print("", end="", flush=True)

                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    print("\n\nTranscription:")
    for line in transcription:
        print(line)

class SpeechServer:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Add socket reuse option
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.running = True
        
        # Create a file to signify the server is running
        self.pid_file = os.path.join(os.path.dirname(__file__), "speech_server.pid")
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        self.data_queue = Queue()
        self.transcription = [""]
        self.phrase_time = None
        self.last_sample = bytes()
        
        # Initialize speech recognition
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = 400
        self.recorder.dynamic_energy_threshold = False
        
        print("Initializing Whisper model...")
        self.pipe, self.processor, self.model = setup_whisper_model()
        self.sampling_rate = self.pipe.feature_extractor.sampling_rate
        
        # Setup microphone
        self.source = sr.Microphone(sample_rate=self.sampling_rate)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)

    def record_callback(self, _, audio):
        if self.running:
            data = audio.get_raw_data()
            self.data_queue.put(data)

    def cleanup(self):
        print("\nCleaning up resources...")
        self.running = False
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            self.server_socket.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def start(self):
        def signal_handler(signum, frame):
            print("\nSignal received, shutting down...")
            self.cleanup()
            sys.exit(0)

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print(f"Server listening on {self.host}:{self.port}")
        
        try:
            client_socket, addr = self.server_socket.accept()
            print(f"Connected to client at {addr}")

            # Start background listening
            stop_listening = self.recorder.listen_in_background(
                self.source, 
                self.record_callback, 
                phrase_time_limit=2
            )

            while self.running:
                now = datetime.utcnow()
                if not self.data_queue.empty():
                    phrase_complete = False
                    if self.phrase_time and now - self.phrase_time > timedelta(seconds=4):
                        self.last_sample = bytes()
                        phrase_complete = True
                    
                    self.phrase_time = now

                    while not self.data_queue.empty():
                        data = self.data_queue.get()
                        self.last_sample += data

                    audio_data = sr.AudioData(
                        self.last_sample, 
                        self.source.SAMPLE_RATE, 
                        self.source.SAMPLE_WIDTH
                    )
                    wav_data = io.BytesIO(audio_data.get_wav_data())
                    sample_rate, audio_array = wavfile.read(wav_data)

                    outputs = self.pipe(
                        audio_array,
                        chunk_length_s=30,
                        batch_size=24,
                        return_timestamps=True
                    )
                    text = outputs["text"].strip()

                    if phrase_complete:
                        self.transcription.append(text)
                    else:
                        self.transcription[-1] = text

                    message = {
                        'type': 'transcription',
                        'text': text,
                        'complete': phrase_complete
                    }
                    try:
                        client_socket.send(json.dumps(message).encode() + b'\n')
                    except:
                        break

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()

if __name__ == '__main__':
    server = SpeechServer()
    server.start()