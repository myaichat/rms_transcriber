
import sys
import asyncio
from google.cloud import speech
from .ResumableMicrophoneStream import ResumableMicrophoneStream
from ...config import init_config
apc = init_config.apc
# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"

class BidirectionalStreamer:
    def __init__(self):
        pass

    def StartStreaming(self):
        """start bidirectional streaming from microphone input to speech API"""
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="en-US",
            max_alternatives=1,
            model='latest_long',
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
        print(mic_manager.chunk_size)
        sys.stdout.write(YELLOW)
        sys.stdout.write('\nListening, say "Quit" or "Exit" to stop.\n\n')
        sys.stdout.write("End (ms)       Transcript Results/Status\n")
        sys.stdout.write("=====================================================\n")
        rid=0
        #loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)
        with mic_manager as stream:
            

            while not stream.closed:

                sys.stdout.write(YELLOW)
                sys.stdout.write(
                    "\n" + str(STREAMING_LIMIT * stream.restart_counter) + ": NEW REQUEST\n"
                )

                stream.audio_input = []
                #print("NEW STREAM")
                #stream.start_stream()
                audio_generator = stream.generator()

                requests = (
                    speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator
                )

                #responses = client.streaming_recognize(streaming_config, requests)
                responses = client.streaming_recognize(streaming_config, requests)


                asyncio.run( apc.transcriber.listen_print_loop(rid,responses, stream))

                if stream.result_end_time > 0:
                    stream.final_request_end_time = stream.is_final_end_time
                stream.result_end_time = 0
                stream.last_audio_input = []
                stream.last_audio_input = stream.audio_input
                stream.audio_input = []
                stream.restart_counter = stream.restart_counter + 1

                if not stream.last_transcript_was_final:
                    sys.stdout.write("\n")
                stream.new_stream = True
                
                rid += 1