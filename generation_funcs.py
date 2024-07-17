import json
from openai import OpenAI
from pathlib import Path
import os
from aux_funcs import sanitize_title
import requests
import time
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

# Read the OpenAI API key from a file
openai_key_path = 'api_keys/openai_key.txt'
with open(openai_key_path, 'r') as file:
    openai_key = file.read().strip()

# Read the OpenAI API key from a file
leonardo_key_path = 'api_keys/leonardo_key.txt'
with open(leonardo_key_path, 'r') as file:
    leonardo_key = file.read().strip()

# Read the OpenAI API key from a file
elevenlabs_key_path = 'api_keys/elevenlabs_key.txt'
with open(elevenlabs_key_path, 'r') as file:
    api_key_el = file.read().strip()






authorization = "Bearer %s" % leonardo_key
client_el = ElevenLabs(api_key=api_key_el)
client = OpenAI(api_key=openai_key)

def generate_image_leonardo(prompt,leonardo_model):
    # Función para comprobar los créditos restantes
    def check_credits():
        headers = {
            "accept": "application/json",
            "authorization": authorization
        }
        response = requests.get("https://cloud.leonardo.ai/api/rest/v1/me", headers=headers)
        data = json.loads(response.text)
        credits_left = data["user_details"][0]["apiSubscriptionTokens"]
        return credits_left

    # Función para generar la imagen
    def generate_image_id(prompt, leonardo_model):
        payload = {
            "alchemy": True,
            "height": 1024,
            "modelId": leonardo_model, #anime e71a1c2f-4f80-4800-934f-2c68979d8cc8  realista 5c232a9e-9061-4777-980a-ddc8e65647c6
            "num_images": 1,
            "presetStyle": "CINEMATIC",
            "prompt": prompt,
            "width": 1024,
            "highResolution": False,
            #"photoReal": True,
            #"photoRealVersion": "v2",
            "negative_prompt": "Do not generate text or numbers in the image",
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": authorization
        }
        response = requests.post("https://cloud.leonardo.ai/api/rest/v1/generations", json=payload, headers=headers)
        data = json.loads(response.text)
        generation_id = data["sdGenerationJob"]["generationId"]
        return generation_id

    # Función para obtener la URL de la imagen generada
    def get_image_url(generation_id):
        headers = {
            "accept": "application/json",
            "authorization": authorization
        }
        time.sleep(30)  # Esperar 30 segundos para que la imagen se genere
        response = requests.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}", headers=headers)
        data = json.loads(response.text)
        image_url = data["generations_by_pk"]["generated_images"][0]["url"]
        return image_url

    # Ejecutar los pasos en orden
    initial_credits = check_credits()
    print(f"Créditos API restantes inicialmente: {initial_credits}")
    
    generation_id = generate_image_id(prompt, leonardo_model)
    print(f"ID de la generación: {generation_id}")

    image_url = get_image_url(generation_id)
    print(f"URL de la imagen generada: {image_url}")

    final_credits = check_credits()
    print(f"Créditos API restantes después de la generación: {final_credits}")

    generation_cost = initial_credits - final_credits
    print(f"Costo de generar la imagen: {generation_cost}")

    return image_url

def generate_image_openai(prompt_text):
    """
    Function to generate an image URL based on a given prompt.

    Args:
    - prompt_text (str): The text prompt for the image.

    Returns:
    - str: URL of the generated image.
    """
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt_text,
        n=1,
        quality="standard",
        size='1024x1024'
    )
    return response.data[0].url

def generate_audio_elevenlabs(script_text: str, output_filepath: str, elevenlabs_voice):
    """
    Function to generate an audio file from a given script text.

    Args:
    - script_text (str): The script text to convert to audio.
    - output_filepath (str): The path where the audio file will be saved.

    Returns:
    - str: The path of the saved audio file.
    """

    # Function to check remaining characters (credits)
    def check_credits():
        headers = {
            'xi-api-key': api_key_el
        }
        response = requests.get('https://api.elevenlabs.io/v1/user/subscription', headers=headers)
        if response.status_code == 200:
            data = response.json()
            remaining_characters = data['character_limit'] - data['character_count']
            return remaining_characters
        else:
            print("Failed to retrieve data")
            return None

    # Calculate the cost in dollars for the given number of characters
    def calculate_cost(characters_used):
        monthly_characters = 30000
        monthly_cost = 50 / 12  # Annual cost of $50 spread over 12 months
        cost_per_character = monthly_cost / monthly_characters
        return characters_used * cost_per_character

    # Check initial credits
    initial_credits = check_credits()
    print(f"Initial remaining characters: {initial_credits}")

    # Generate the audio
    response = client_el.text_to_speech.convert(
        voice_id=elevenlabs_voice,  # choose the voice id 'yl2ZDV1MzN4HbQJbMihG'
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=script_text,
        model_id="eleven_turbo_v2",  # use the turbo model for low latency, for other languages
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=False,
        )
    )


    # Write the audio to a file
    with open(output_filepath, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"Output file saved at: {output_filepath}")

    # Check final credits
    final_credits = check_credits()
    print(f"Remaining characters after generation: {final_credits}")

    # Calculate and print the credits used
    if initial_credits is not None and final_credits is not None:
        characters_used = initial_credits - final_credits
        cost_in_dollars = calculate_cost(characters_used)
        print(f"Characters used for generation: {characters_used}")
        print(f"Cost to generate the audio: ${cost_in_dollars:.4f}")

def generate_audio_openai(script_text, output_filename):
    """
    Function to generate an audio file from a given script text.

    Args:
    - script_text (str): The script text to convert to audio.
    - output_filename (str): The filename where the audio will be saved.

    Returns:
    - None
    """
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=script_text,
    )
    with open(output_filename, "wb") as file:
        file.write(response.content)

def transcribe_audio(audio_path):
    """
    Function to transcribe audio and return the transcription data.

    Args:
    - audio_path (str): Path to the audio file to transcribe.

    Returns:
    - dict: Transcription data including text and segments.
    """
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["word"],
            language='en'
        )
    return {
        "text": transcript.text,
        "segments": transcript.words
    }

def generate_json(input_json, prompt_path, JSON_dir):
    """
    Function to generate a JSON dictionary for a viral TikTok video script, and save it to a file.

    Args:
    - input_json (dict): Input dictionary containing title, topic, and description.
    - prompt_path (str): Path to the file containing the prompt template.
    - JSON_dir (str): Directory where the JSON output should be saved.

    Returns:
    - dict: JSON dictionary representing the TikTok video script.
    """
    # Extract title from input_json and sanitize it for folder/file names
    title = input_json["title"]
    title_safe = sanitize_title(title)

    # Path to the output directory and file
    output_dir = os.path.join(JSON_dir, title_safe)
    output_file = os.path.join(output_dir, f"{title_safe}.json")

    # Check if the JSON already exists
    if os.path.exists(output_file):
        print(f"Loading existing JSON from {output_file}")
        with open(output_file, 'r', encoding='utf-8') as file:
            existing_json = json.load(file)
        return existing_json

    # Create the directory if it does not exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate the prompt
    with open(prompt_path, 'r', encoding='utf-8') as file:
        prompt_template = file.read()


    formatted_prompt = prompt_template.format(
        title=input_json["title"],
        topic=input_json["topic"],
        description=input_json["description"]
    )

    # Call the OpenAI API to generate the JSON output
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": formatted_prompt}
        ],
        max_tokens=1000,
        temperature=0.8
    )

    # Extract the JSON content from the response
    generated_json = json.loads(response.choices[0].message.content.strip())

    # Save the JSON content to a file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(generated_json, file, ensure_ascii=False, indent=4)
    
    print(f"Created new JSON and saved to {output_file}")
    return generated_json
