import sys
args = sys.argv
audio_file_path = args[1]

import requests
import os
import assemblyai as aai
import time
from pprint import pprint as pp

# Set the API key
aai.settings.api_key = os.getenv("ASSEMBLY_API_KEY")

# Upload the local audio file using requests

transcriber = aai.Transcriber()
transcript = transcriber.transcribe(audio_file_path)
#pp (dir(transcript))
print(transcript.text)    