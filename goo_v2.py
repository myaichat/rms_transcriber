
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

# TODO(developer): Update and un-comment below line
# PROJECT_ID = "your-project-id"
PROJECT_ID = 'spatial-flag-427113-n0'

# Instantiates a client
client = SpeechClient()

# Reads a file as bytes
with open("audio_chunks/2.0.chunk_1.wav", "rb") as f:
    audio_content = f.read()

config = cloud_speech.RecognitionConfig(
    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
    language_codes=["en-US"],
    model="long",
)

request = cloud_speech.RecognizeRequest(
    recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
    config=config,
    content=audio_content,
)

# Transcribes the audio into text
response = client.recognize(request=request)

for result in response.results:
    print(f"Transcript: {result.alternatives[0].transcript}")