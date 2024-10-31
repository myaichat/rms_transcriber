
from os.path import isfile  
from pprint import pprint as pp
from pubsub import pub 
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from ..config import init_config
apc = init_config.apc
# TODO(developer): Update and un-comment below line
# PROJECT_ID = "your-project-id"
PROJECT_ID = 'spatial-flag-427113-n0'

# Instantiates a client



class AsyncRecognizer:
    def __init__(self, queue):
        self.queue = queue
        self.client = SpeechClient()
        self.config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="long",
        )



    async def consume_recognizer_queue(self, queue):
        # Continuously consume the queue and update WebView
        while True:

            content = await queue.get()
            #print('\n\tconsume_queue: ',content)
            #pub.sendMessage("display_response", response=content)  # Send the content to the WebView
            #wx.CallAfter(self.update_text, content)  # Update UI safely in the main thread
            #queue.task_done()
            #self.content_buffer += content  
            await  self.transcribe(content)  
            await  apc.vosk_recognizer.transcribe(content)  
            queue.task_done()  
         
    async def transcribe(self, content):
        file_name,tid, rid = content
        assert isfile(file_name)    
        print(f"AsyncRecognizer: Transcribing: {file_name}")
        # Reads a file as bytes
        with open(file_name, "rb") as f:
            audio_content = f.read()

        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
            config=self.config,
            content=audio_content,
        )

        # Transcribes the audio into text
        response = self.client.recognize(request=request)
        #pp(response)
        transcript=None
        for result in response.results:
            try:
                #pp(result)
                print(f">>>>>>>>>>>>>>> AsyncRecognizer: Transcript: {result.alternatives[0].transcript}")
                transcript=result.alternatives[0].transcript

            except Exception as e:
                print('ERROR: AsyncRecognizer: transcrribe:  %s: %s' % (type(e).__name__, str(e)))
                
        if transcript:
            await apc.transcriber.queue.put(['RECOG: '+transcript,'stream_recognized', tid, rid])
            pub.sendMessage("stream_recognized", data=('GOOG: '+transcript, tid, rid))