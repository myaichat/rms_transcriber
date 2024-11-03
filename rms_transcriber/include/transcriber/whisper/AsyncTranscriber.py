# read_transcriptions.py
import socket
import json
import sys
import time
from pubsub import pub
from pprint import pprint as pp
import asyncio
from ...config import init_config
apc = init_config.apc

class AsyncTranscriber:
    def __init__(self, queue=None, host='127.0.0.1', port=5000):
        self.queue=queue
        self.host = host
        self.port = port
        self.client_socket = None
        self.loop = asyncio.get_event_loop()
        
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print("Connected to transcription server")
            return True
        except ConnectionRefusedError:
            print("Could not connect to server. Make sure the server is running.")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def transcribe(self):
        if not self.client_socket:
            if not self.connect():
                return

        buffer = ""
        try:
            tid=0
            while True:
                data = self.client_socket.recv(4096).decode()
                if not data:
                    break

                buffer += data
                rid=0
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    message = json.loads(line)
                    
                    if message['type'] == 'transcription':
                        # You can modify this part to handle the transcription data
                        # as needed (e.g., save to file, process, etc.)
                        text = message['text']
                        is_complete = message['complete']
                        
                        # Print with different formatting based on whether it's complete
                        if is_complete:
                            print(f"\nComplete phrase: {text}")
                            print("-" * 50)
                            
                            if text.strip().lower() not in ['booom','thank you','thank you.','uh',"I'm sorry.".lower(),'i''m sorry','i''m sorry.','bang!','boom!', 'yeah!',
                                'Thank you. I''m sorry'.lower(),'you', 'the end','Thank you for watching.'.lower()]:
                                    print('\nstream_closed2', data)
                                    pub.sendMessage("stream_closed2", data=(f'{tid}:{rid}: pub :{text}', None, tid, rid))
                                                              
                        else:
                            # Use carriage return to update the current line
                            print(f"\rCurrent: {text}", end='', flush=True)
                            if text.strip().lower() not in ['booom','thank you','thank you.','uh',"I'm sorry.".lower(),'i''m sorry','i''m sorry.','bang!','boom!', 'yeah!',
                                'Thank you. I''m sorry'.lower(),'you', 'the end','Thank you for watching.'.lower()]:
                                    print('\npartial_stream', data)
                                    #pub.sendMessage("partial_stream", data=(text, None, tid, rid))
                                    self.loop.call_soon_threadsafe(lambda: asyncio.create_task(apc.trans_queue.put([f'{tid}:{rid}: await p :{text}', 'partial_stream', tid, rid])))
                    rid+=1
                tid+=1

                        
        except KeyboardInterrupt:
            print("\nStopping transcription reader...")
        except Exception as e:
            print(f"\nError reading transcriptions: {e}")
        finally:
            self.close()

    def close(self):
        if self.client_socket:
            self.client_socket.close()
            print("Connection closed")

def main():
    reader = AsynTranscriber()
    reader.read_transcriptions()

if __name__ == "__main__":
    main()