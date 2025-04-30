import base64
import pyaudio
import azure.cognitiveservices.speech as speechsdk
from azure.core.credentials import AzureKeyCredential
from rtclient import (
    ResponseCreateMessage,
    RTLowLevelClient,
    ResponseCreateParams
)
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=28000,
                output=True)

api_key = os.getenv('REALTIME_KEY')
endpoint = os.getenv('REALTIME_ENDPOINT')
deployment = os.getenv('MODEL_REALTIME')
speech_key = os.getenv('SPEECH_KEY')
service_region = "eastus2"

# Initialize the speech recognizer
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

async def text_in_audio_out():
    while True:
        print("Please speak your chat or say 'bye' to exit:")
        
        # Capture audio from the microphone and recognize speech
        result = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            chat = result.text
            print(f"User: {chat}")
            
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized")
            continue
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech Recognition canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
            continue
        
        print(chat.lower())
        if chat.lower() == "bye" or chat.lower() == "bye.":
            print("Exiting the chat...")
            break
        
        else:
            async with RTLowLevelClient(
                url=endpoint,
                azure_deployment=deployment,
                key_credential=AzureKeyCredential(api_key) 
            ) as client:
                await client.send(
                    ResponseCreateMessage(
                        response=ResponseCreateParams(
                            modalities={"audio", "text"}, 
                            instructions=chat
                        )
                    )
                )
                done = False
                while not done:
                    message = await client.recv()
                    match message.type:
                        case "response.done":
                            done = True
                        case "error":
                            done = True
                            print(message.error)
                        case "response.audio_transcript.delta":
                            print(message.delta,end="", flush=True)
                        case "response.audio.delta":
                            buffer = base64.b64decode(message.delta)
                            stream.write(buffer)
                            #print(f"Received {len(buffer)} bytes of audio data.")
                        case _:
                            pass

async def main():
    await text_in_audio_out()
    # Close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
