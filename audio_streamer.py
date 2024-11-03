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
def set_recorder(data_queue, sampling_rate,args):
    

    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold #400
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False

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

    return source