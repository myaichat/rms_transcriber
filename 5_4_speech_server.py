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
import os
from time import sleep

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
        model_kwargs={"use_flash_attention_2": False},
        generate_kwargs={"task": "transcribe", "language": "en"},
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

        # Audio processing setup
        self.data_queue = Queue()
        self.last_sample = bytes()
        self.phrase_time = None  # Track time of last recording
        self.current_text = ""  # Store the latest phrase only
        self.silence_start = None  # Track silence duration
        
        # Recorder setup
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = 400
        self.recorder.dynamic_energy_threshold = False
        
        # Initialize model
        print("Initializing Whisper model...")
        self.pipe, self.processor, self.model = setup_whisper_model()
        self.sampling_rate = self.pipe.feature_extractor.sampling_rate
        
        # Microphone setup
        self.source = sr.Microphone(sample_rate=self.sampling_rate)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        
        # Timeout settings
        self.record_timeout = 2
        self.phrase_timeout = 3

    def record_callback(self, _, audio):
        if self.running:
            data = audio.get_raw_data()
            self.data_queue.put(data)
            # Reset silence tracking since we received audio
            self.silence_start = None

    def process_audio(self, audio_array):
        """Process audio and return transcription with timestamps if needed"""
        outputs = self.pipe(
            audio_array,
            chunk_length_s=30,
            batch_size=24,
            return_timestamps=True
        )
        return outputs["text"].strip()

    def start(self):
        print(f"Server listening on {self.host}:{self.port}")
        
        try:
            client_socket, addr = self.server_socket.accept()
            print(f"Connected to client at {addr}")

            stop_listening = self.recorder.listen_in_background(
                self.source, 
                self.record_callback, 
                phrase_time_limit=self.record_timeout
            )

            while self.running:
                now = datetime.utcnow()
                
                if not self.data_queue.empty():
                    phrase_complete = False
                    # If enough time has passed since last audio, consider the phrase complete
                    if self.phrase_time and (now - self.phrase_time).total_seconds() > self.phrase_timeout:
                        self.last_sample = bytes()
                        phrase_complete = True
                        self.silence_start = now  # Start tracking silence
                    
                    # Update the last time audio data was received
                    self.phrase_time = now

                    # Collect audio data
                    while not self.data_queue.empty():
                        data = self.data_queue.get()
                        self.last_sample += data

                    # Convert to audio array
                    audio_data = sr.AudioData(
                        self.last_sample, 
                        self.source.SAMPLE_RATE, 
                        self.source.SAMPLE_WIDTH
                    )
                    wav_data = io.BytesIO(audio_data.get_wav_data())
                    sample_rate, audio_array = wavfile.read(wav_data)

                    # Get transcription
                    text = self.process_audio(audio_array)
                    
                    # Update current text for this phrase
                    if phrase_complete:
                        # Send the last completed phrase only
                        result = {
                            'type': 'transcription',
                            'text': self.current_text.strip(),
                            'complete': True
                        }
                        print(result)
                        try:
                            client_socket.send(json.dumps(result).encode() + b'\n')
                        except:
                            break
                        
                        # Start a new phrase
                        self.current_text = text
                    else:
                        # Accumulate text within the ongoing phrase
                        self.current_text = text

                    # Send an incomplete result with the current transcription
                    result = {
                        'type': 'transcription',
                        'text': self.current_text.strip(),
                        'complete': phrase_complete
                    }
                    print(result)
                    try:
                        client_socket.send(json.dumps(result).encode() + b'\n')
                    except:
                        break

                    # Clear transcription buffer if phrase complete
                    if phrase_complete:
                        self.last_sample = bytes()
                        self.phrase_time = None
                else:
                    # If silence_start has passed, send the final "complete" transcription
                    if self.silence_start and (now - self.silence_start).total_seconds() >= self.phrase_timeout:
                        result = {
                            'type': 'transcription',
                            'text': self.current_text.strip(),
                            'complete': True
                        }
                        print(result)
                        try:
                            client_socket.send(json.dumps(result).encode() + b'\n')
                        except:
                            break
                        self.last_sample = bytes()  # Reset for the next phrase
                        self.current_text = ""     # Clear current text
                        self.silence_start = None  # Reset silence tracking
                    elif not self.silence_start:
                        self.silence_start = now  # Start silence tracking if no audio data

                sleep(0.25)  # Prevent CPU overload

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        print("\nCleaning up resources...")
        self.running = False
        try:
            if os.path.exists("speech_server.pid"):
                os.remove("speech_server.pid")
            self.server_socket.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")

def main():
    server = SpeechServer()
    server.start()

if __name__ == '__main__':
    main()
