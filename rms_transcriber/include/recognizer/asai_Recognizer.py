import queue, time
import wave, os
import asyncio
from pubsub import pub
from ..config import init_config
apc = init_config.apc
import assemblyai as aai

SAMPLE_RATE=16000
def save_audio_chunk(loop, item_id, audio_data, chunk_counter, tid,rid):
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
                
    
        num_frames = len(b''.join(audio_data)) // (2 * 1)  # Calculate frames correctly
        duration = num_frames / SAMPLE_RATE  # Duration in seconds   
        print(f"Saved: {file_name}")
        print(f"Audio Duration: {duration:.2f} seconds")

        if 0:
            if duration < 60:
                #asyncio.create_task(apc.recog_queue.put([file_name, tid, rid]))
                print(f"RECOG QUEUE: {file_name}, {tid}, {rid}")
                asyncio.run_coroutine_threadsafe(apc.recog_queue.put([file_name, tid, rid]), loop)
            else:
                print(f"Audio duration too long: {duration:.2f} seconds")            
    
        return file_name, duration

    except Exception as e:
        print(f"Error saving audio chunk: {e}")
        raise   e
        return None, 0
        
def recognize(q):
    """start bidirectional streaming from microphone input to speech API"""
    chunk_counter = 0

    while True:
        try:
            # Try to get a message from the queue with a timeout
            message = q.get(timeout=1)  # Wait for 1 second for a message
            item_id, file_name,tid, rid = message
            if message == "STOP":  # A special message to exit the loop
                print("Stopping thread.")
                break
            

            if 1:
                import requests
                import os
                import assemblyai as aai
                import time
                from pprint import pprint as pp

                # Set the API key
                aai.settings.api_key = os.getenv("ASSEMBLY_API_KEY")

                # Upload the local audio file using requests
                assert os.path.isfile(file_name)
                print(apc.asai_lang)
                #e()
                config = aai.TranscriptionConfig(
                    language_code=apc.asai_lang, 
                    filter_profanity=False,
                    #speaker_labels=True,
                    #speech_threshold=0.1
                    )
                transcriber = aai.Transcriber(config=config)
                transcript = transcriber.transcribe(file_name)
                pp (transcript)
                if transcript.utterances:
                    for utterance in transcript.utterances:
                        print(f"Speaker {utterance.speaker}: {utterance.text}")
                print('THREAT RECOGNIZE:', transcript.text, tid, rid) 
                pub.sendMessage("stream_recognized", data=('ASAI pub: '+transcript.text, tid, rid))


            q.task_done()  # Mark the task as done
        except queue.Empty:
            # Handle the case where no message was received within the timeout
            continue