from openai import AzureOpenAI
from PIL import Image
import json
import os
import requests
from dotenv import load_dotenv
load_dotenv()

def main():
    client = AzureOpenAI(
        azure_endpoint = os.getenv('DALLE_ENDPOINT'), 
        api_key= os.getenv('DALLE_KEY'),  
        api_version= "2024-05-01-preview",
    )

    while True:
        print("Please enter your chat or press 'bye' to exit:")
        chat = input("User: ")
        if chat == "bye":
            break
        

        result = client.images.generate(
            model="dall-e-3", # the name of your DALL-E 3 deployment
            prompt=chat,
            n=1
        )
        
        json_response = json.loads(result.model_dump_json())

        # Set the directory for the stored image
        image_dir = os.path.join(os.curdir, 'images')

        # If the directory doesn't exist, create it
        if not os.path.isdir(image_dir):
            os.mkdir(image_dir)

        # Initialize the image path (note the filetype should be png)
        image_path = os.path.join(image_dir, 'generated_image.png')

        # Retrieve the generated image
        image_url = json_response["data"][0]["url"]  # extract image URL from response
        generated_image = requests.get(image_url).content  # download the image
        with open(image_path, "wb") as image_file:
            image_file.write(generated_image)

        # Display the image in the default image viewer
        image = Image.open(image_path)
        image.show() 

if __name__ == "__main__":
    main()
