from colorama import Fore, Style
import re
import sys
import time
from google.cloud import speech
from pubsub import pub
from ...config import init_config
apc = init_config.apc

# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"


def get_current_time() -> int:
    """Return Current Time in MS.

    Returns:
        int: Current Time in MS.
    """

    return int(round(time.time() * 1000))

class AsyncTranscriber:
    def __init__(self, queue):
        self.queue = queue
        
        

    async def listen_print_loop(self,rid, responses: object, stream: object) -> None:
        """Iterates through server responses and prints them.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.

        Arg:
            responses: The responses returned from the API.
            stream: The audio stream to be processed.
        """
        tid=0
        start_time=0
        for response in responses:
            if get_current_time() - stream.start_time > STREAMING_LIMIT:
                stream.start_time = get_current_time()
                break

            if not response.results:
                continue

            result = response.results[0]

            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            result_seconds = 0
            result_micros = 0

            if result.result_end_time.seconds:
                result_seconds = result.result_end_time.seconds

            if result.result_end_time.microseconds:
                result_micros = result.result_end_time.microseconds

            stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

            corrected_time = (
                stream.result_end_time
                - stream.bridging_offset
                + (STREAMING_LIMIT * stream.restart_counter)
            )
            # Display interim results, but with a carriage return at the end of the
            # line, so subsequent lines will overwrite them.

            if result.is_final:
                sys.stdout.write(GREEN)
                sys.stdout.write("\033[K")
                elapsed_time=stream.result_end_time -start_time
                sys.stdout.write(str(elapsed_time)+ ": "+str(tid)  + ": "+str(corrected_time) + ": " + transcript + "\n")
                pub.sendMessage("stream_closed2", data=(transcript, corrected_time, tid, rid))
                await apc.transcriber.queue.put([transcript,'stream_closed', tid, rid])
                #print("FINAL:",transcript)
                pub.sendMessage("stream_closed", data=(transcript, corrected_time, tid, rid))
                if len(result.alternatives) > 1:
                    transcript = result.alternatives[1].transcript
                    sys.stdout.write(str(elapsed_time)+ ": "+str(tid)  + ": "+str(corrected_time) + ": " + transcript + "\n")
                    #pub.sendMessage("stream_closed", data=(transcript, corrected_time, tid, rid))
                    if len(result.alternatives) > 2:
                        transcript = result.alternatives[2].transcript
                        sys.stdout.write(str(elapsed_time)+ ": "+str(tid)  + ": "+str(corrected_time) + ": " + transcript + "\n")
                        #pub.sendMessage("stream_closed", data=(transcript, corrected_time, tid, rid))
            
                stream.is_final_end_time = stream.result_end_time
                stream.last_transcript_was_final = True
                tid += 1
                start_time=stream.result_end_time 

                # Exit recognition if any of the transcribed phrases could be
                # one of our keywords.
                if re.search(r"\b(exit|quit)\b", transcript, re.I):
                    sys.stdout.write(YELLOW)
                    sys.stdout.write("Exiting...\n")
                    stream.closed = True

                    break
                #print("final")
            else:
                if 1:
                    sys.stdout.write(RED)
                    sys.stdout.write("\033[K")
                    sys.stdout.write(str(corrected_time) + ": " + transcript[-100:] + "\r")
                #pub.sendMessage("partial_stream", data=(transcript, corrected_time, tid, rid))
                await apc.transcriber.queue.put([transcript,'partial_stream', tid, rid])
                stream.last_transcript_was_final = False
