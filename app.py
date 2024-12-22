from flask import Flask, request, render_template, send_from_directory
import os
import whisper
from gtts import gTTS
from uuid import uuid4
import subprocess
from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Load Whisper model
whisper_model = whisper.load_model("base")

# Function to load the translation model
def load_translation_model(target_language="fr"):
    language_models = {
        "English": "Helsinki-NLP/opus-mt-en-en",  # Placeholder for no translation
        "Hindi": "Helsinki-NLP/opus-mt-en-hi",
        "French": "Helsinki-NLP/opus-mt-en-fr",
        "Spanish": "Helsinki-NLP/opus-mt-en-es",
        "German": "Helsinki-NLP/opus-mt-en-de",
        "Italian": "Helsinki-NLP/opus-mt-en-it",
        "Dutch": "Helsinki-NLP/opus-mt-en-nl",
        "Portuguese": "Helsinki-NLP/opus-mt-en-pt",
        "Russian": "Helsinki-NLP/opus-mt-en-ru",
        "Swedish": "Helsinki-NLP/opus-mt-en-sv",
        "Chinese (Simplified)": "Helsinki-NLP/opus-mt-en-zh",
        "Arabic": "Helsinki-NLP/opus-mt-en-ar",
    }
    model_name = language_models.get(target_language, "Helsinki-NLP/opus-mt-en-en")
    llm_pipeline = HuggingFacePipeline.from_model_id(model_id=model_name, task="translation")
    return llm_pipeline

# Function to get video duration
def get_video_duration(video_path):
    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0 or not result.stdout.strip():
            raise ValueError(f"FFprobe error: {result.stderr.strip()}")
        return float(result.stdout.strip())
    except Exception as e:
        raise ValueError(f"Could not extract video duration. Please check the video file format. Error: {str(e)}")

# Helper function to segment video
def split_video(video_path, segment_length=15):
    output_files = []
    output_pattern = os.path.join(app.config['UPLOAD_FOLDER'], f"segment_%03d.mp4")
    split_command = f"ffmpeg -i {video_path} -c copy -map 0 -segment_time {segment_length} -f segment {output_pattern}"
    subprocess.run(split_command, shell=True, check=True)
    segment_files = [os.path.join(app.config['UPLOAD_FOLDER'], f) for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith("segment_")]
    output_files.extend(segment_files)
    return output_files

# Route to handle index
@app.route('/')
def index():
    supported_languages = [
        "English", "Hindi", "French", "Spanish", "German", "Italian",
        "Dutch", "Portuguese", "Russian", "Swedish", "Chinese (Simplified)", "Arabic"
    ]
    return render_template('index.html', languages=supported_languages)

# Route to handle upload
@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return "No video file uploaded", 400
    if 'language' not in request.form or not request.form['language']:
        return "No target language selected", 400

    video_file = request.files['video']
    target_language = request.form['language']
    video_filename = f"{uuid4().hex}_{video_file.filename}"
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    video_file.save(video_path)

    try:
        video_duration = get_video_duration(video_path)
        segments = [video_path] if video_duration <= 15 else split_video(video_path)
        transcriptions = []
        translations = []

        for segment in segments:
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"audio_{uuid4().hex}.wav")
            extract_audio_command = f"ffmpeg -i {segment} -q:a 0 -map a {audio_path}"
            subprocess.run(extract_audio_command, shell=True, check=True)

            transcription_result = whisper_model.transcribe(audio_path)
            transcribed_text = transcription_result['text']
            transcriptions.append(transcribed_text)

            if target_language == "English":
                translated_text = transcribed_text
            else:
                translation_model = load_translation_model(target_language)
                translation_prompt = PromptTemplate(
                    template="Translate the following text to {target_language}: {text}",
                    input_variables=["text", "target_language"]
                )
                prompt = translation_prompt.format(text=transcribed_text, target_language=target_language)
                translated_text = translation_model(prompt)
            translations.append(translated_text)

            os.remove(audio_path)

        final_transcription = " ".join(transcriptions)
        final_translation = " ".join(translations)

        tts_lang = 'hi' if target_language == "Hindi" else 'en'
        tts_output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"new_audio_{uuid4().hex}.mp3")
        tts = gTTS(text=final_translation, lang=tts_lang)
        tts.save(tts_output_path)

        final_output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"final_{uuid4().hex}.mp4")
        replace_audio_command = f"ffmpeg -i {video_path} -i {tts_output_path} -c:v copy -map 0:v:0 -map 1:a:0 {final_output_path}"
        subprocess.run(replace_audio_command, shell=True, check=True)

        return render_template(
            'output.html',
            transcribed_text=final_transcription,
            translated_text=final_translation,
            video_url=f"/output/{os.path.basename(final_output_path)}"
        )

    except Exception as e:
        return f"Error processing video: {str(e)}", 500

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        for segment in segments:
            if os.path.exists(segment):
                os.remove(segment)

@app.route('/output/<filename>')
def serve_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
