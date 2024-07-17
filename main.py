import argparse
import json
import os
import time
import traceback

from aux_funcs import (
    add_background_music_to_video,
    add_subtitles_to_video,
    create_project_structure,
    sanitize_title,
    update_and_save_scene_times,
)
from build_funcs import (
    save_audio_from_json,
    save_images_from_json,
    save_transcription_from_json,
    save_video_from_json,
)
from generation_funcs import generate_json


def main(
    base_path,
    prompt_path,
    leonardo_model,
    elevenlabs_voice,
    generate_images_with,
    generate_audio_with,
    add_music,
    add_subtitles,
):
    """
    Main function to execute the full pipeline for creating a TikTok video script, generating images, audio, transcription, and compiling them into a video with subtitles.

    Args:
    - base_path (str): Base path for project directories.
    - prompt_path (str): Path to the prompt template file.
    - leonardo_model (str): Model ID for Leonardo image generation.
    - elevenlabs_voice (str): Voice ID for ElevenLabs audio generation.
    - generate_images_with (str): Service to use for generating images ("openai" or "leonardo").
    - generate_audio_with (str): Service to use for generating audio ("openai" or "elevenlabs").
    - add_music (bool): Flag to indicate if music should be added.
    - add_subtitles (bool): Flag to indicate if subtitles should be added.

    Returns:
    - None
    """
    print("Starting the project pipeline...")
    start_time = time.time()

    # Load input JSON
    input_json_path = os.path.join(base_path, "input.json")
    with open(input_json_path, "r", encoding="utf-8") as file:
        input_json = json.load(file)

    # Step 1: Create project structure
    try:
        print("Step 1: Creating project structure...")
        step_start_time = time.time()
        data_dir, video_dir, img_dir, audio_dir, JSON_dir, trans_dir, music_dir = (
            create_project_structure(base_path)
        )
        music_dir = os.path.join(data_dir, "music")
        step_end_time = time.time()
        print(f"Project directories created under base path: {base_path}")
        print(f"Step 1 completed in {step_end_time - step_start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error in Step 1: {e}")
        traceback.print_exc()

    # Step 2: Generate JSON from input
    try:
        print("Step 2: Generating JSON from input...")
        step_start_time = time.time()
        generated_json = generate_json(input_json, prompt_path, JSON_dir)
        step_end_time = time.time()
        print("JSON generated and saved.")
        print(f"Step 2 completed in {step_end_time - step_start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error in Step 2: {e}")
        traceback.print_exc()

    # Step 3: Save images from JSON
    try:
        print("Step 3: Generating and saving images...")
        step_start_time = time.time()
        save_images_from_json(
            generated_json, img_dir, generate_images_with, leonardo_model
        )
        step_end_time = time.time()
        print(f"Step 3 completed in {step_end_time - step_start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error in Step 3: {e}")
        traceback.print_exc()

    # Step 4: Save audio from JSON
    try:
        print("Step 4: Generating and saving audio...")
        step_start_time = time.time()
        save_audio_from_json(
            generated_json, audio_dir, generate_audio_with, elevenlabs_voice
        )
        step_end_time = time.time()
        print(f"Step 4 completed in {step_end_time - step_start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error in Step 4: {e}")
        traceback.print_exc()

    # Step 5: Save transcription from JSON
    try:
        print("Step 5: Generating and saving transcription...")
        step_start_time = time.time()
        save_transcription_from_json(generated_json, trans_dir, audio_dir)
        step_end_time = time.time()
        print("Transcription generated and saved.")
        print(f"Step 5 completed in {step_end_time - step_start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error in Step 5: {e}")
        traceback.print_exc()

    # Step 6: Update and save scene times in JSON
    try:
        print("Step 6: Updating and saving scene times in JSON...")
        step_start_time = time.time()
        generated_json = update_and_save_scene_times(
            generated_json, audio_dir, JSON_dir
        )
        step_end_time = time.time()
        print("Scene times updated in JSON and saved.")
        print(f"Step 6 completed in {step_end_time - step_start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error in Step 6: {e}")
        traceback.print_exc()

    # Step 7: Save video from JSON
    try:
        print("Step 7: Compiling and saving video...")
        step_start_time = time.time()
        video_path = save_video_from_json(generated_json, img_dir, audio_dir, video_dir)
        step_end_time = time.time()
        print("Video compiled and saved.")
        print(f"Step 7 completed in {step_end_time - step_start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error in Step 7: {e}")
        traceback.print_exc()

    # Step 8: Add subtitles to video
    if add_subtitles:
        try:
            print("Step 8: Adding subtitles to video...")
            step_start_time = time.time()
            add_subtitles_to_video(generated_json, video_dir, trans_dir)
            video_path_with_subtitles = os.path.join(
                video_dir,
                sanitize_title(generated_json["title"]),
                sanitize_title(generated_json["title"]) + "_sub.mp4",
            )
            step_end_time = time.time()
            print("Subtitles added to video.")
            print(f"Step 8 completed in {step_end_time - step_start_time:.2f} seconds.")
        except Exception as e:
            print(f"Error in Step 8: {e}")
            traceback.print_exc()

    # Step 9: Add music to video
    if add_music:
        try:
            print("Step 9: Adding music to video...")
            step_start_time = time.time()
            add_background_music_to_video(
                video_path_with_subtitles if add_subtitles else video_path, music_dir
            )
            step_end_time = time.time()
            print(f"Step 9 completed in {step_end_time - step_start_time:.2f} seconds.")
        except Exception as e:
            print(f"Error in Step 9: {e}")
            traceback.print_exc()

    end_time = time.time()
    print(
        f"Project pipeline completed successfully in {end_time - start_time:.2f} seconds."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a TikTok video with specified options."
    )
    parser.add_argument(
        "--base_path",
        type=str,
        required=True,
        help="Base path for project directories.",
    )
    parser.add_argument(
        "--prompt_path",
        type=str,
        required=True,
        help="Path to the prompt template file.",
    )
    parser.add_argument(
        "--leonardo_model",
        type=str,
        required=True,
        help="Model ID for Leonardo image generation.",
    )
    parser.add_argument(
        "--elevenlabs_voice",
        type=str,
        required=True,
        help="Voice ID for ElevenLabs audio generation.",
    )
    parser.add_argument(
        "--images",
        type=str,
        choices=["openai", "leonardo"],
        help="Service to use for generating images.",
    )
    parser.add_argument(
        "--audio",
        type=str,
        choices=["openai", "elevenlabs"],
        help="Service to use for generating audio.",
    )
    parser.add_argument(
        "--music",
        action="store_true",
        default=True,
        help="Flag to add music to the video.",
    )
    parser.add_argument(
        "--subtitles",
        action="store_true",
        default=True,
        help="Flag to add subtitles to the video.",
    )
    args = parser.parse_args()
