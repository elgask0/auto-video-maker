import os
import json
import re
from pathlib import Path
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, CompositeAudioClip, TextClip, VideoFileClip
from pydub import AudioSegment
import random
from natsort import natsorted

def create_project_structure(base_path):
    """
    Creates the directory structure for a project given a base directory.

    Args:
    - base_path (str): Base path where project directories will be created.

    Returns:
    - tuple: Contains paths of created directories in the following order:
      (data_dir, video_dir, img_dir, audio_dir, JSON_dir, trans_dir)
    """
    data_dir = os.path.join(base_path, "data")
    video_dir = os.path.join(data_dir, "video")
    img_dir = os.path.join(data_dir, "image")
    audio_dir = os.path.join(data_dir, "audio")
    JSON_dir = os.path.join(data_dir, "JSON")
    trans_dir = os.path.join(data_dir, "transcription")
    music_dir = os.path.join(data_dir, "music")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(JSON_dir, exist_ok=True)
    os.makedirs(trans_dir, exist_ok=True)

    return data_dir, video_dir, img_dir, audio_dir, JSON_dir, trans_dir, music_dir

def sanitize_title(title):
    """
    Function to sanitize the title for use in filenames and directories.

    Args:
    - title (str): The title to sanitize.

    Returns:
    - str: Sanitized title.
    """
    return title.replace(" ", "_").replace(":", "").replace("/", "_")

def count_total_words(scenes):
    total_words = 0
    for scene in scenes:
        total_words += len(scene["script"].split())
    return total_words

def update_and_save_scene_times(input_json, audio_dir, json_dir):
    title = input_json['title']
    title_safe = sanitize_title(title)
    
    # Encontrar el archivo de audio
    audio_path = os.path.join(audio_dir, title_safe, f"{title_safe}.mp3")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Obtener la duración del audio
    audio = AudioSegment.from_file(audio_path)
    total_duration = len(audio) / 1000.0  # Convertir a segundos

    scenes = input_json["scenes"]
    # Contar el número total de palabras en todas las escenas
    total_words = count_total_words(scenes)
    # Calcular la duración de cada palabra
    duration_per_word = total_duration / total_words

    current_time = 0.0
    for scene in scenes:
        script_words = scene["script"].split()
        scene_word_count = len(script_words)
        scene_duration = scene_word_count * duration_per_word

        scene["start"] = current_time
        current_time += scene_duration
        scene["end"] = current_time

    title_json_dir = os.path.join(json_dir, title_safe)
    os.makedirs(title_json_dir, exist_ok=True)
    output_path = os.path.join(title_json_dir, f"{title_safe}.json")
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(input_json, file, ensure_ascii=False, indent=4)

    return input_json

def apply_movement_effect(clip, index, tiktok_width, tiktok_height):
    """
    Apply a left-to-right or right-to-left movement effect to a clip based on its index.

    Args:
    - clip (VideoClip): The clip to which the effect will be applied.
    - index (int): Index of the clip to determine the direction of the movement.
    - tiktok_width (int): Width of the TikTok format.
    - tiktok_height (int): Height of the TikTok format.

    Returns:
    - VideoClip: The clip with the applied movement effect.
    """
    def move_left_to_right(get_frame, t):
        x = int(t * (clip.w - tiktok_width) / clip.duration)
        x = max(0, min(x, clip.w - tiktok_width))
        return clip.crop(x1=x, y1=0, width=tiktok_width, height=tiktok_height).get_frame(t)

    def move_right_to_left(get_frame, t):
        x = int((clip.w - tiktok_width) - t * (clip.w - tiktok_width) / clip.duration)
        x = max(0, min(x, clip.w - tiktok_width))
        return clip.crop(x1=x, y1=0, width=tiktok_width, height=tiktok_height).get_frame(t)

    if index % 2 == 0:
        return clip.fl(move_left_to_right, apply_to=['mask'])
    else:
        return clip.fl(move_right_to_left, apply_to=['mask'])

def generate_video(images_dir, audio_file, output_file, scene_durations, transition_duration=1):
    """
    Function to generate a video from images and a single audio file using scene durations and crossfade transitions.

    Args:
    - images_dir (str): Directory where the images are stored.
    - audio_file (str): Path to the audio file.
    - output_file (str): Path where the output video will be saved.
    - scene_durations (list): List of durations for each scene in the format [(start, end), ...].
    - transition_duration (float): Duration of the crossfade transition effect.

    Returns:
    - None
    """
    audio_clip = AudioFileClip(audio_file)
    image_files = natsorted([os.path.join(images_dir, f) for f in os.listdir(images_dir) if f.endswith('.png')])
    adjusted_durations = [(end - start) for start, end in scene_durations]

    image_clips = []
    for i, (img, duration) in enumerate(zip(image_files, adjusted_durations)):
        clip = ImageClip(img).set_duration(duration)
        # Calcular dimensiones de TikTok dinámicamente
        tiktok_height = clip.h
        tiktok_width = int(tiktok_height * 9 / 16)
        clip = apply_movement_effect(clip, i, tiktok_width, tiktok_height)
        image_clips.append(clip)

    # Apply crossfade transitions
    clips = [image_clips[0].crossfadeout(transition_duration)]
    for i in range(1, len(image_clips)):
        clip = image_clips[i].crossfadein(transition_duration)
        clips.append(clip)

    # Concatenate image clips with the specified transitions
    video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)

    # Write the video file
    video.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=24)

def generate_word_by_word_clips(segments, video_size, fontsize=80, color='yellow', stroke_color='black', stroke_width=6):
    """
    Generate individual word clips for subtitles with animation effects.

    Args:
    - segments (list): List of segments containing words and their timestamps.
    - video_size (tuple): Size of the video (width, height).
    - font_path (str): Path to the font file to be used for the text.
    - fontsize (int): Font size of the text.
    - color (str): Color of the text.
    - stroke_color (str): Stroke color for the text.
    - stroke_width (int): Stroke width for the text.

    Returns:
    - list: List of TextClip objects representing each word with animation effects.
    """
    font_path = 'fonts/KOMIKAX_.ttf'
    clips = []

    for word_info in segments:
        word = word_info['word'].upper()  # Convert to uppercase
        word_start_time = word_info['start']
        word_end_time = word_info['end']
        word_duration = word_end_time - word_start_time

        y_pos = video_size[1] * 0.75  # Place text in the bottom third

        # Create the main word clip with a shadow effect
        word_clip = TextClip(word, font=font_path, fontsize=fontsize, color=color, stroke_color=stroke_color, stroke_width=stroke_width)
        word_clip = word_clip.set_start(word_start_time).set_duration(word_duration).set_position(('center', y_pos))

        # Create a shadow effect by adding a slight offset black text
        shadow_clip = TextClip(word, font=font_path, fontsize=fontsize, color='black', stroke_color=stroke_color, stroke_width=stroke_width)
        shadow_clip = shadow_clip.set_start(word_start_time).set_duration(word_duration).set_position(('center', y_pos + 5))  # Offset for shadow effect

        clips.append(shadow_clip)  # Add shadow first
        clips.append(word_clip)    # Add main word clip on top

    return clips

def generate_animated_subtitles(video_path, segments):
    """
    Generate animated subtitles for a video.

    Args:
    - video_path (str): Path to the video file.
    - segments (list): List of segments containing words and their timestamps.
    - font_path (str): Path to the font file to be used for the text.

    Returns:
    - CompositeVideoClip: Composite video with the original video and animated subtitles.
    """
    video = VideoFileClip(video_path)
    clips = generate_word_by_word_clips(segments, video.size)
    composite = CompositeVideoClip([video] + clips)
    return composite

def add_subtitles_to_video(input_json, video_dir, trans_dir):
    """
    Add animated subtitles to a video based on transcription JSON data.

    Args:
    - input_json (dict): JSON dictionary representing the TikTok video script.
    - video_dir (str): Directory where the video files are stored.
    - trans_dir (str): Directory where the transcription files are stored.
    - font_path (str): Path to the font file to be used for the text.

    Returns:
    - None
    """
    title = input_json['title']
    title_safe = sanitize_title(title)
    video_path = os.path.join(video_dir, title_safe, f"{title_safe}.mp4")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    transcript_path = os.path.join(trans_dir, title_safe, f"{title_safe}.json")
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcription file not found: {transcript_path}")

    output_path = os.path.splitext(video_path)[0] + '_sub.mp4'
    if os.path.exists(output_path):
        print(f"Output file already exists: {output_path}")
        return

    with open(transcript_path, 'r', encoding='utf-8') as file:
        transcript_json = json.load(file)

    segments = transcript_json["segments"]
    composite = generate_animated_subtitles(video_path, segments)
    composite.write_videofile(output_path, codec='libx264', audio_codec='aac')

    print(f"Subtitled video created successfully: {output_path}")

def add_background_music_to_video(video_path, music_dir):
    """
    Add background music to a video.

    Args:
    - video_path (str): Path to the video file.
    - music_dir (str): Directory containing the music files.

    Returns:
    - str: Path to the output video file with background music.
    """
    # Obtener la ruta del archivo de salida
    base, ext = os.path.splitext(video_path)
    output_path = f"{base}_music{ext}"

    if os.path.exists(output_path):
        print(f"Output file already exists: {output_path}")
        return output_path

    # Cargar el video
    video_clip = VideoFileClip(video_path)
    
    # Obtener el audio original del video
    original_audio = video_clip.audio

    # Seleccionar un archivo de música aleatorio
    music_files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.endswith('.mp3')]
    audio_path = random.choice(music_files)
    
    # Cargar el audio
    audio_clip = AudioFileClip(audio_path)
    
    # Reducir el volumen de la música al 25%
    audio_clip = audio_clip.volumex(0.2)
    
    # Ajustar la duración del audio para que coincida con la duración del video
    audio_clip = audio_clip.subclip(max(0, audio_clip.duration - video_clip.duration), audio_clip.duration)
    
    # Combinar el audio original con la música de fondo
    combined_audio = CompositeAudioClip([original_audio, audio_clip])
    
    # Añadir el audio combinado al video
    video_with_audio = video_clip.set_audio(combined_audio)
    
    # Guardar el video resultante
    video_with_audio.write_videofile(output_path, codec='libx264', audio_codec='aac')

    print(f"Video with background music created successfully: {output_path}")