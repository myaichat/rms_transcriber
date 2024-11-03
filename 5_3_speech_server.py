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
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn
from rich import print as pp
from time import sleep
from sys import platform

def setup_whisper_model(model_id="openai/whisper-large-v3", cache_dir="cache"):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    processor = AutoProcessor.from_pretrained(model_id)
    
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        cache_dir=cache_dir,
    )
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.to(device)
    
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
        model_kwargs={
            "use_flash_attention_2": False,
            "pad_token_id": processor.tokenizer.pad_token_id,
        },
        generate_kwargs={
            "task": "transcribe",
            "language": "en",
        }
    )
    
    return pipe, processor, model

class SpeechServer:
    def __init__(self, host='127.0.0.1', port=5000):
        # Network setup
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.running = True
        
        # PID file management
        self.pid_file = os.path.join(os.path.dirname(__file__), "speech_server.pid")
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        # Speech recognition setup
        self.data_queue = Queue()
        self.transcription = [""]
        self.phrase_time = None
        self.last_sample = bytes()
        
        # Recorder configuration
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = 400
        self.recorder.dynamic_energy_threshold = False
        
        # Initialize Whisper model
        print("Initializing Whisper model...")
        self.pipe, self.processor, self.model = setup_whisper_model()
        self.sampling_rate = self.pipe.feature_extractor.sampling_rate
        
        # Microphone setup
        self.source = sr.Microphone(sample_rate=self.sampling_rate)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
            
        # Transcription state management
        self.current_phrase = ""
        self.silence_start = None
        self.min_phrase_length = 10
        self.max_silence_duration = 1.5
        self.last_transcription_time = None
        self.confidence_threshold = 0.8
        
        # Processing parameters
        self.record_timeout = 2
        self.phrase_timeout = 4
        self.batch_size = 24

    def record_callback(self, _, audio):
        if self.running:
            data = audio.get_raw_data()
            self.data_queue.put(data)

    def is_phrase_complete(self, text, silence_duration):
        """Determine if a phrase is complete based on multiple factors"""
        if not text:
            return False
            
        # Check various completion indicators
        has_ending_punctuation = text[-1] in '.!?'
        is_long_enough = len(text) >= self.min_phrase_length
        sufficient_silence = silence_duration >= self.max_silence_duration
        
        # Natural language heuristics
        words = text.split()
        has_complete_structure = len(words) >= 3
        
        return (has_ending_punctuation and is_long_enough) or \
               (sufficient_silence and is_long_enough and has_complete_structure)

    def process_transcription(self, audio_array, tid):
        """Process audio and determine transcription completeness"""
        outputs = self.pipe(
            audio_array,
            chunk_length_s=30,
            batch_size=self.batch_size,
            return_timestamps=True
        )
        
        text = outputs["text"].strip()
        current_time = datetime.utcnow()
        
        silence_duration = 0
        if self.last_transcription_time:
            silence_duration = (current_time - self.last_transcription_time).total_seconds()
        
        self.last_transcription_time = current_time
        
        if not self.current_phrase:
            self.current_phrase = text
        else:
            if len(text) > len(self.current_phrase):
                self.current_phrase = text

        is_complete = self.is_phrase_complete(self.current_phrase, silence_duration)
        
        if is_complete:
            result_text = self.current_phrase
            self.current_phrase = ""
        else:
            result_text = self.current_phrase
            
        return {
            'type': 'transcription',
            'text': result_text,
            'complete': is_complete,
            'confidence': outputs.get('confidence', 1.0),
            'tid':tid
        }

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
                phrase_time_limit=self.record_timeout
            )
            tid=0
            while self.running:
                now = datetime.utcnow()
                if not self.data_queue.empty():
                    phrase_complete = False
                    
                    if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.phrase_timeout):
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

                    # Process transcription
                    result = self.process_transcription(audio_array, tid)
                    tid+=1
                    # Only send if we have meaningful content
                    if result['text']:
                        pp(result)  # Pretty print the result
                        try:
                            client_socket.send(json.dumps(result).encode() + b'\n')
                        except:
                            break

                    # Reset audio buffer if phrase was complete
                    if result['complete']:
                        self.last_sample = bytes()

                # Add a small sleep to prevent CPU overload
                sleep(0.1)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()

def main():
    server = SpeechServer()
    server.start()

if __name__ == '__main__':
    main()