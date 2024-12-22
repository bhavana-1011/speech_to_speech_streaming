# Speech-to-Speech Streaming Application

This web application allows users to upload an audio file and a video file. The audio is transcribed using OpenAI's Whisper model, then translated to the selected language using the LLM models. The translated text is converted to speech and used to replace the original audio in the video.

## Features:
- Upload video files
- Select a language for translation
- Transcribe audio using Whisper
- Translate transcribed text to the selected language
- Generate translated speech and replace the original video audio

## Requirements:
1. Flask
2. Whisper (for audio transcription)
3. Langchain (for translation)
4. Transformers (for TTS)
5. ffmpeg-python (for audio replacement in video)
6. gTTS (for TTS)

## Installation:
1. Clone this repository:
    ```bash
    git clone https://github.com/yourusername/speech_to_speech.git
    cd speech_to_speech
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Install `ffmpeg` on your system (it is required for audio replacement):
    - **Linux**: `sudo apt-get install ffmpeg`
    - **Windows**: Download and install from [ffmpeg.org](https://ffmpeg.org/download.html)
    - **macOS**: `brew install ffmpeg`

4. Run the Flask application:
    ```bash
    python app.py
    ```

5. Open your browser and go to `http://127.0.0.1:5000/`.

## License:
MIT License
