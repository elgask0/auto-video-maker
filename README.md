# Automated Video Generation Using AI

---

## 📋 Project Overview

This repository contains a comprehensive pipeline for generating TikTok videos from user inputs using APIs from OpenAI, Leonardo, and ElevenLabs. The project processes the inputs to create a script with associated image prompts, generates audio, images, compiles them into a video, and optionally adds subtitles and background music. Additionally, it includes a Streamlit application for a user-friendly frontend interface.

## 📂 Directory Structure

- **main.py**: Main script to execute the entire video generation pipeline.
- **aux_funcs.py**: Auxiliary functions for supporting tasks such as creating project structure, sanitizing titles, and adding subtitles.
- **build_funcs.py**: Functions to build and save images, audio, and video based on the generated script.
- **generation_funcs.py**: Functions for generating content (images, audio, JSON scripts) using OpenAI, Leonardo, and ElevenLabs APIs.
- **streamlit_app.py**: Streamlit application script to provide a web interface for user interaction.

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Required Python packages listed in `requirements.txt`
- API keys for OpenAI, Leonardo, and ElevenLabs

### Installation

1. **Clone the repository**:
   ```sh
   git clone <repository_url>
   cd <repository_name>
   ```

2. **Create and activate a Conda environment**:
   ```sh
   conda create --name auto_video_maker python=3.10 -y
   conda activate auto_video_maker
   ```

3. **Navigate to the repository directory**:
   ```sh
   cd path/to/repo
   ```

4. **Install the required packages**:
   ```sh
   pip install -r requirements.txt
   ```

5. **Install ffmpeg and ImageMagick**:

   Follow the instructions for your operating system:

   - **Windows**:
     - Download the latest ffmpeg release from the ffmpeg website.
     - Extract the files and add the `bin` folder to your system's PATH.
     - Download the latest ImageMagick release from the ImageMagick website.
     - Run the installer and ensure you check the option to add ImageMagick to your system's PATH.

   - **macOS**:
     ```sh
     brew install ffmpeg
     brew install imagemagick
     ```

   - **Linux**:
     ```sh
     sudo apt update
     sudo apt install ffmpeg imagemagick
     ```

6. **Set up API keys**:
   - Place your OpenAI API key in a file located at `openai_key.txt`.
   - Place your Leonardo API key in a file located at `leonardo_key.txt`.
   - Place your ElevenLabs API key in a file located at `elevenlabs_key.txt`.

## 🛠️ Running the Project

### Using the Streamlit App

1. **Activate the Conda environment and navigate to the repository directory**:
   ```sh
   conda activate auto_video_maker
   cd path/to/repo
   ```

2. **Launch the Streamlit App**:
   ```sh
   streamlit run streamlit_app.py
   ```

3. **Enter Video Details**:
   - **Title**: Enter the title of the video.
   - **Topic**: Specify the topic of the video.
   - **Description**: Provide a detailed description of the video content.

4. **Specify Paths and Models**:
   - **Base Path**: Directory where project data will be stored.
   - **Prompt Path**: Path to the prompt template file.
   - **Image Generation Service**: Choose between `openai` or `leonardo`.
   - **Audio Generation Service**: Choose between `openai` or `elevenlabs`.

5. **Optional Settings**:
   - **Add Background Music**: Place an `.mp3` file in the music folder if you want to use this function.
   - **Add Subtitles**: Option to add subtitles to the video.

6. **Generate Video**:
   - Click on "Generate Video" to start the pipeline.
   - Monitor the process output and errors in the Streamlit interface.
   - Once the video is generated, it will be displayed within the app.

## 📜 Pipeline Description

### Step-by-Step Process

1. **Creating Project Structure**:
   - Sets up necessary directories for storing data, images, audio, JSON files, transcriptions, and videos.

2. **Generating JSON from Input**:
   - Reads user inputs and uses the prompt template to generate a detailed JSON script for the video.

3. **Generating and Saving Images**:
   - Uses the selected image generation service (OpenAI or Leonardo) to create images based on prompts in the JSON script.

4. **Generating and Saving Audio**:
   - Uses the selected audio generation service (OpenAI or ElevenLabs) to create audio narration for the script.

5. **Generating and Saving Transcription**:
   - Transcribes the generated audio to create a detailed text transcription.

6. **Updating and Saving Scene Times**:
   - Analyzes audio duration and updates scene times in the JSON script to sync with the generated images and audio.

7. **Compiling and Saving Video**:
   - Combines images, audio, and scene times to create a cohesive video.
   - Optionally adds background music and subtitles if specified.

8. **Adding Subtitles**:
   - Creates and adds animated subtitles to the video based on the transcription data.

9. **Adding Background Music**:
   - Integrates background music into the video, adjusting volume levels to ensure clarity of the narration.

## 📄 License

This project is licensed under the GNU General Public License v3.0. See the LICENSE file for more details.