import os
import json
from tqdm import tqdm
import requests
from generation_funcs import generate_image_openai, generate_audio_openai, generate_image_leonardo ,generate_audio_elevenlabs, transcribe_audio
from aux_funcs import sanitize_title, generate_video

def save_images_from_json(generated_json, img_dir, service, leonardo_model):
    """
    Function to save images based on the prompts in the JSON.

    Args:
    - generated_json (dict): JSON dictionary representing the TikTok video script.
    - img_dir (str): Directory where the images should be saved.

    Returns:
    - None
    """
    title = generated_json['title']
    title_safe = sanitize_title(title)
    title_img_dir = os.path.join(img_dir, title_safe)
    os.makedirs(title_img_dir, exist_ok=True)
    scenes = generated_json['scenes']

    for scene in tqdm(scenes, desc="Generating images", unit="image"):
        order = scene['order']
        image_path = os.path.join(title_img_dir, f"{order}.png")
        if not os.path.exists(image_path):
            prompt_text = scene['image_prompt']
            try:
                if service == "openai":
                    image_url = generate_image_openai(prompt_text)
                elif service == "leonardo":
                    image_url = generate_image_leonardo(prompt_text, leonardo_model)
                response = requests.get(image_url)
                with open(image_path, "wb") as file:
                    file.write(response.content)
            except Exception as e:
                print(f"Error generating image for scene {order}: {str(e)}")
        else:
            print(f"Image {order} already exists at '{image_path}'")

def save_audio_from_json(json_data, audio_dir, service, elevenlabs_voice):
    """
    Function to save a single audio file based on the combined scripts in the JSON.

    Args:
    - json_data (dict): JSON dictionary representing the TikTok video script.
    - audio_dir (str): Directory where the audio should be saved.

    Returns:
    - None
    """
    title = json_data['title']
    title_safe = sanitize_title(title)
    title_audio_dir = os.path.join(audio_dir, title_safe)
    os.makedirs(title_audio_dir, exist_ok=True)
    combined_script = " ".join(scene['script'] for scene in json_data['scenes'])
    output_filename = os.path.join(title_audio_dir, f"{title_safe}.mp3")
    if not os.path.exists(output_filename):
        if service == "openai":
            generate_audio_openai(combined_script, output_filename)
        elif service == "elevenlabs":
            generate_audio_elevenlabs(combined_script, output_filename, elevenlabs_voice)

def save_transcription_from_json(json_data, trans_dir, audio_dir):
    """
    Function to save transcription based on the audio generated from the scripts in the JSON.

    Args:
    - json_data (dict): JSON dictionary representing the TikTok video script.
    - trans_dir (str): Directory where the transcription should be saved.
    - audio_dir (str): Directory where the audio files are stored.

    Returns:
    - None
    """
    title = json_data['title']
    title_safe = sanitize_title(title)
    title_trans_dir = os.path.join(trans_dir, title_safe)
    os.makedirs(title_trans_dir, exist_ok=True)
    audio_filename = f"{title_safe}.mp3"
    audio_path = os.path.join(audio_dir, title_safe, audio_filename)
    transcript_path = os.path.join(title_trans_dir, f"{title_safe}.json")
    if not os.path.exists(transcript_path):
        transcription_data = transcribe_audio(audio_path)
        with open(transcript_path, 'w', encoding='utf-8') as file:
            json.dump(transcription_data, file, ensure_ascii=False, indent=4)

def save_video_from_json(json_data, img_dir, audio_dir, video_dir):
    """
    Function to save a video based on the images and audio from the JSON data.

    Args:
    - json_data (dict): JSON dictionary representing the TikTok video script.
    - img_dir (str): Directory where the images are stored.
    - audio_dir (str): Directory where the audio files are stored.
    - video_dir (str): Directory where the video will be saved.

    Returns:
    - str: Path to the saved video file.
    """
    title = json_data['title']
    title_safe = sanitize_title(title)
    video_output_dir = os.path.join(video_dir, title_safe)
    os.makedirs(video_output_dir, exist_ok=True)
    audio_filename = f"{title_safe}.mp3"
    audio_path = os.path.join(audio_dir, title_safe, audio_filename)
    video_output_path = os.path.join(video_output_dir, f"{title_safe}.mp4")
    scene_durations = [(scene['start'], scene['end']) for scene in json_data['scenes']]
    if not os.path.exists(video_output_path):
        generate_video(os.path.join(img_dir, title_safe), audio_path, video_output_path, scene_durations)
    return video_output_path
