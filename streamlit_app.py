import streamlit as st
import os
import json
import threading
import queue
import io
from main import main as main_pipeline
import sys

# Cargar los JSON para los modelos de Leonardo y las voces de ElevenLabs
leonardo_json_path = os.path.join(os.path.dirname(__file__), 'models', 'leonardo_models.json')
elevenlabs_json_path = os.path.join(os.path.dirname(__file__), 'models','elevenlabs_voices.json')

with open(leonardo_json_path, 'r', encoding='utf-8') as file:
    leonardo_models = json.load(file)['custom_models']

with open(elevenlabs_json_path, 'r', encoding='utf-8') as file:
    elevenlabs_voices = json.load(file)['voices']

# Mapear nombres y descripciones para los desplegables
leonardo_model_options = [f"{model['name']} - {model['description']}" for model in leonardo_models]
leonardo_model_ids = {f"{model['name']} - {model['description']}": model['id'] for model in leonardo_models}

elevenlabs_voice_options = [f"{voice['name']} - {voice['description']}" for voice in elevenlabs_voices]
elevenlabs_voice_ids = {f"{voice['name']} - {voice['description']}": voice['id'] for voice in elevenlabs_voices}

# Define a queue to communicate between threads
output_queue = queue.Queue()

class StreamToQueue(io.StringIO):
    def __init__(self, queue, *args, **kwargs):
        self.queue = queue
        super().__init__(*args, **kwargs)

    def write(self, msg):
        super().write(msg)
        self.queue.put(msg)

def run_pipeline(base_path, prompt_path, leonardo_model, elevenlabs_voice, images_service, audio_service, add_music, add_subtitles, input_json, output_queue):
    # Save input JSON to a file
    input_json_path = os.path.join(base_path, "input.json")
    with open(input_json_path, 'w', encoding='utf-8') as file:
        json.dump(input_json, file, ensure_ascii=False, indent=4)
    
    # Capture stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StreamToQueue(output_queue)
    sys.stderr = StreamToQueue(output_queue)
    
    try:
        main_pipeline(base_path, prompt_path, leonardo_model, elevenlabs_voice, images_service, audio_service, add_music, add_subtitles)
    finally:
        # Reset stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    output_queue.put(None)  # Sentinel to indicate the end of the process

def streamlit_app():
    st.title('Video Generator')
    st.header('Enter video details')

    # User inputs for video details
    title = st.text_input('Title:', placeholder='Introduce title', key="title_input")
    topic = st.text_input('Topic:', placeholder='Introduce topic', key="topic_input")
    description = st.text_area('Description:', placeholder='Introduce description', key="description_input")

    # User inputs for paths and models
    base_path = st.text_input('Base Path:', placeholder='path/to/your/folder', key="base_path_input")
    prompt_path = 'prompts/prompt.txt'
    # font_path is hardcoded in the auxiliary functions

    # User inputs for services and options
    images_service = st.selectbox('Service for generating images:', ['openai', 'leonardo'], key="images_service_input")
    if images_service == 'leonardo':
        leonardo_model_option = st.selectbox('Leonardo Model:', leonardo_model_options, key="leonardo_model_input")
        leonardo_model = leonardo_model_ids[leonardo_model_option]
    else:
        leonardo_model = None

    audio_service = st.selectbox('Service for generating audio:', ['openai', 'elevenlabs'], key="audio_service_input")
    if audio_service == 'elevenlabs':
        elevenlabs_voice_option = st.selectbox('ElevenLabs Voice ID:', elevenlabs_voice_options, key="elevenlabs_voice_input")
        elevenlabs_voice = elevenlabs_voice_ids[elevenlabs_voice_option]
    else:
        elevenlabs_voice = None

    add_music = st.checkbox('Add background music', value=False, key="add_music_input")
    add_subtitles = st.checkbox('Add subtitles', value=False, key="add_subtitles_input")

    if st.button('Generate Video'):
        input_json = {
            "title": title,
            "topic": topic,
            "description": description,
        }

        # Start a new thread to run the pipeline
        threading.Thread(target=run_pipeline, args=(base_path, prompt_path, leonardo_model, elevenlabs_voice, images_service, audio_service, add_music, add_subtitles, input_json, output_queue)).start()

        # Display the captured output after the process is done
        st.info('Generating video...')
        stdout_output = ""
        stderr_output = ""

        while True:
            msg = output_queue.get()
            if msg is None:
                break
            if "Error" in msg:
                stderr_output += msg
            else:
                stdout_output += msg

        st.success('Video generated successfully!')

        # Display the captured output
        if stdout_output:
            st.text_area('Process Output', stdout_output, height=300)
        if stderr_output:
            st.text_area('Errors', stderr_output, height=300)

        # Display the generated video
        video_dir = os.path.join(base_path, "data", "video", title.replace(" ", "_"))
        base_video_path = os.path.join(video_dir, title.replace(' ', '_'))

        video_path = None
        if add_subtitles and add_music:
            video_path = f"{base_video_path}_sub_music.mp4"
        elif add_subtitles:
            video_path = f"{base_video_path}_sub.mp4"
        elif add_music:
            video_path = f"{base_video_path}_music.mp4"
        else:
            video_path = f"{base_video_path}.mp4"

        st.write(f"Looking for video at: {video_path}")

        if video_path and os.path.exists(video_path):
            st.video(video_path)
        else:
            st.error('Generated video not found.')

if __name__ == '__main__':
    streamlit_app()
