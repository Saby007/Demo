import time
import datetime 
from openai import AzureOpenAI
import json
import os
from dotenv import load_dotenv
load_dotenv()

client = AzureOpenAI(
        azure_endpoint = os.getenv('AZURE_ENDPOINT'), 
        api_key= os.getenv('API_KEY'),  
        api_version= '2024-12-01-preview',
    )

batch_id = "batch_137fbdac-2904-4f82-8ef5-f469d280b08c"

status = "validating"
while status not in ("completed", "failed", "canceled"):
    time.sleep(60)
    batch_response = client.batches.retrieve(batch_id)
    status = batch_response.status
    print(f"{datetime.datetime.now()} Batch Id: {batch_id},  Status: {status}")

if batch_response.status == "failed":
    for error in batch_response.errors.data:  
        print(f"Error code {error.code} Message {error.message}")



output_file_id = batch_response.output_file_id

if not output_file_id:
    output_file_id = batch_response.error_file_id

if output_file_id:
    file_response = client.files.content(output_file_id)
    raw_responses = file_response.text.strip().split('\n')  

    for raw_response in raw_responses:  
        json_response = json.loads(raw_response)  
        formatted_json = json.dumps(json_response, indent=2)  
        print(formatted_json)