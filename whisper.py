from openai import AzureOpenAI
import os
from dotenv import load_dotenv 

load_dotenv()

def main():
    client = AzureOpenAI(
        azure_endpoint = os.getenv('REALTIME_ENDPOINT'), 
        api_key= os.getenv('REALTIME_KEY'),  
        api_version= '2024-05-01-preview',
    )
    deployment_id = "whisper" #This will correspond to the custom name you chose for your deployment when you deployed a model."
    audio_test_file = "./audio.wav"    
    print("Processing the Audio......")
    result = client.audio.transcriptions.create(
        file=open(audio_test_file, "rb"),            
        model=deployment_id
    )
    print(result)

if __name__ == "__main__":
    main()