# read_transcriptions.py
import socket
import json
import sys
import time

class TranscriptionReader:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.client_socket = None
        
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

    def read_transcriptions(self):
        if not self.client_socket:
            if not self.connect():
                return

        buffer = ""
        try:
            while True:
                data = self.client_socket.recv(4096).decode()
                if not data:
                    break

                buffer += data
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
                        else:
                            # Use carriage return to update the current line
                            print(f"\rCurrent: {text}", end='', flush=True)
                        
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
    reader = TranscriptionReader()
    reader.read_transcriptions()

if __name__ == "__main__":
    main()