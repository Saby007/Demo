from openai import AzureOpenAI
import base64
import os
from dotenv import load_dotenv
load_dotenv()

def main():
    client = AzureOpenAI(
        azure_endpoint = os.getenv('AZURE_ENDPOINT'), 
        api_key= os.getenv('API_KEY'),  
        api_version= os.getenv('API_VERSION'),
    )

    while True:
        print("Please enter your chat or press 'bye' to exit:")
        chat = input("User: ")

        #Getting the image paths
        IMAGE_PATH1 = ""
        IMAGE_PATH2 = ""
        encoded_image1 = base64.b64encode(open(IMAGE_PATH1, 'rb').read()).decode('ascii')
        encoded_image2 = base64.b64encode(open(IMAGE_PATH2, 'rb').read()).decode('ascii')
               
        
        if chat == "bye":
            break
        chat_prompt = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an AI assistant that helps people find information."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": chat
                    },
                    { 
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image1}"
                        }
                    },
                    { 
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image2}"
                        }
                    }
                    
                ]
            }
        ]
        
        response = client.chat.completions.create(
            model=os.getenv('MODEL_GPT4o'), # model = "deployment_name".
            messages=chat_prompt
        )
        
        print("Response: "+response.choices[0].message.content)
        print("Completion_Tokens: "+ str(response.usage.completion_tokens))
        print("Prompt Toekns: "+ str(response.usage.prompt_tokens))
        print("Total Tokens: "+ str(response.usage.total_tokens))

if __name__ == "__main__":
    main()
