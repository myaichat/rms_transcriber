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
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


def setup_whisper_model(model_id="openai/whisper-large-v3", cache_dir="cache"):
    # Set device and dtype
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    # Load processor first
    processor = AutoProcessor.from_pretrained(model_id)
    
    # Load the model with proper configuration
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        cache_dir=cache_dir,
    )
    model.config.pad_token_id = processor.tokenizer.pad_token_id  # Add this line
    model.to(device)
    
    # Create pipeline with modified settings
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
        model_kwargs={
            "use_flash_attention_2": False,
            "pad_token_id": processor.tokenizer.pad_token_id,  # Add this line
        },
        generate_kwargs={
            "task": "transcribe",
            "language": "en",
        }
    )
    
    return pipe, processor, model

# Usage

# Usage

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-name",
        required=False,
        default="openai/whisper-large-v3",
        type=str,
        help="Name of the pretrained model/ checkpoint to perform ASR. (default: openai/whisper-large-v3)",
    )
    parser.add_argument(
        "--energy_threshold",
        default=400,
        help="Energy level for mic to detect.",
        type=int,
    )
    parser.add_argument(
        "--record_timeout",
        default=2,
        help="How real time the recording is in seconds.",
        type=float,
    )
    parser.add_argument(
        "--phrase_timeout",
        default=4,
        help="How much empty space between recordings before we "
        "consider it a new line in the transcription.",
        type=float,
    )
    parser.add_argument(
        "--language",
        required=False,
        type=str,
        default="en",
        help='Language of the input audio. (default: "None" (Whisper auto-detects the language))',
    )
    parser.add_argument(
        "--batch-size",
        required=False,
        type=int,
        default=24,
        help="Number of parallel batches you want to compute. Reduce if you face OOMs. (default: 24)",
    )
    parser.add_argument(
        "--task",
        required=False,
        default="transcribe",
        type=str,
        choices=["transcribe", "translate"],
        help="Task to perform: transcribe or translate to another language. (default: transcribe)",
    )
    parser.add_argument(
        "--timestamp",
        required=False,
        type=str,
        default="chunk",
        choices=["chunk", "word"],
        help="Whisper supports both chunked as well as word level timestamps. (default: chunk)",
    )
    parser.add_argument(
        "--device-id",
        required=False,
        default="cpu",
        type=str,
        help='Device ID for your GPU. Just pass the device number when using CUDA, or "mps" for Macs with Apple Silicon. (default: "0")',
    )
    if "linux" in platform:
        parser.add_argument(
            "--default_microphone",
            default="pulse",
            help="Default microphone name for SpeechRecognition. "
            "Run this with 'list' to view available Microphones.",
            type=str,
        )
    args = parser.parse_args()

    transcription = [""]
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3"

    pipe, processor, model = setup_whisper_model()        
    sampling_rate = pipe.feature_extractor.sampling_rate

    ts = "word" if args.timestamp == "word" else True

    language = None if args.language == "None" else args.language

    # The last time a recording was retrieved from the queue.
    phrase_time = None
    phrase_timeout = args.phrase_timeout
    # Current raw audio bytes.
    last_sample = bytes()
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()

    from audio_streamer import set_recorder
    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    source=set_recorder(data_queue, sampling_rate, args)

    # Cue the user that we're ready to go.
    print("Model loaded.\n")

    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(
                    seconds=phrase_timeout
                ):
                    last_sample = bytes()
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now

                # Concatenate our current audio data with the latest audio data.
                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                # Use AudioData to convert the raw data to wav data.
                audio_data = sr.AudioData(
                    last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH
                )
                wav_data = io.BytesIO(audio_data.get_wav_data())

                # Convert the wav data to a numpy ndarray
                sample_rate, audio_array = wavfile.read(wav_data)
                # audio_array is the numpy ndarray containing the audio data

                # Read the transcription.
                with Progress(
                    TextColumn("🤗 [progress.description]{task.description}"),
                    BarColumn(style="yellow1", pulse_style="white"),
                    TimeElapsedColumn(),
                ) as progress:
                    progress.add_task("[yellow]Transcribing...", total=None)
                    outputs = pipe(
                        audio_array,
                        chunk_length_s=30,
                        batch_size=args.batch_size,
                        generate_kwargs={"task": args.task, "language": language},
                        return_timestamps=ts,
                    )
                    # result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
                    text = outputs["text"].strip()

                # If we detected a pause between recordings, add a new item to our transcription.
                # Otherwise edit the existing one.
                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text

                # Clear the console to reprint the updated transcription.
                os.system("cls" if os.name == "nt" else "clear")
                for line in transcription:
                    print(line)
                # Flush stdout.
                print("", end="", flush=True)

                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    print("\n\nTranscription:")
    for line in transcription:
        print(line)


if __name__ == "__main__":
    main()