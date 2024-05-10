from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pydub import AudioSegment
import sqlite3
import os
import logging
from logging.handlers import RotatingFileHandler
from gtts import gTTS
from io import BytesIO
import speech_recognition as sr
import time
import spacy
from spacy import displacy
from joblib import load

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'verysecretkey')
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['OTHER_UPLOAD_FOLDER'] = 'other_upload/'

app.config['ALLOWED_EXTENSIONS'] = {'wav', 'mp3', 'ogg', 'flac', 'aac'}
nlp = spacy.load("models/1700smodel/")
# Path to the model and vectorizer
model_path = os.path.join('models', 'sentiment', 'model.joblib')
vectorizer_path = os.path.join('models', 'sentiment', 'vectorizer.joblib')

# Load the model and vectorizer
senti_model = load(model_path)
tfidf_vectorizer = load(vectorizer_path)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def convert_to_wav(original_path):
    """Converts an audio file to a mono 16-bit PCM WAV at 16000 Hz sample rate."""
    sound = AudioSegment.from_file(original_path)
    wav_path = original_path.rsplit('.', 1)[0] + '.wav'
    # Convert to mono, 16-bit PCM at 16000 Hz
    sound = sound.set_channels(1)
    sound = sound.set_frame_rate(16000)
    sound = sound.set_sample_width(2)  # Set to 2 bytes (16-bit)
    sound.export(wav_path, format='wav')
    return wav_path

def convert_audio_for_recognition(source_path):
    """Converts any audio file to a WAV file compatible with speech recognition libraries."""
    target_path = os.path.splitext(source_path)[0] + '.wav'
    audio = AudioSegment.from_file(source_path)
    audio = audio.set_channels(1)  # Mono channel
    audio = audio.set_frame_rate(16000)  # 16000 Hz sample rate
    audio = audio.set_sample_width(2)  # 2 bytes (16 bits) per sample
    audio.export(target_path, format='wav')  # Export as WAV
    return target_path




def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    if user:
        session['username'] = user['username']
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        flash('Please log in to view the dashboard')
        return redirect(url_for('index'))

    tts_filename = session.get('tts_file', None)  # Retrieve the filename from the session

    if request.method == 'POST':
        # Handling file uploads and conversion to WAV if necessary
        file = request.files.get('audio_file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(original_path)
            if filename.rsplit('.', 1)[1].lower() != 'wav':
                wav_filename = filename.rsplit('.', 1)[0] + '.wav'
                target_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
                convert_to_wav(original_path, target_path)
                os.remove(original_path)  # Clean up the original file
                filename = wav_filename  # Update the filename to the converted file's name
            flash('File successfully uploaded and converted if necessary')
            return redirect(url_for('dashboard'))

    # Pass the filename to the template if it exists to display the audio player and download link
    return render_template('dashboard.html', tts_filename=tts_filename)


import re

# Function to expand contractions
def expand_contractions(text):
    contractions = {
        "can't": "cannot", "won't": "will not", "n't": " not", "'re": " are",
        "'s": " is", "'d": " would", "'ll": " will", "'t": " not", "'ve": " have",
        "'m": " am"
    }
    regex = re.compile('(%s)' % '|'.join(contractions.keys()))
    return regex.sub(lambda x: contractions[x.group()], text)

# Simplified Text Preprocessing Function
def preprocess_text(text):
    text = text.lower()  # Lowercasing to maintain consistency
    text = expand_contractions(text)  # Expand contractions to simplify text
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters but preserve alphanumeric
    return text


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio_file' not in request.files:
        flash("No file part")
        return redirect(request.url)
    file = request.files['audio_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['OTHER_UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Convert to WAV if necessary
        if not filename.endswith('.wav'):
            file_path = convert_to_wav(file_path)
        
        # Transcribe the audio
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
        try:
            transcription = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            flash("Speech Recognition could not understand the audio")
            return redirect(url_for('dashboard'))
        except sr.RequestError as e:
            flash(f"Could not request results from Google Speech Recognition service; {e}")
            return redirect(url_for('dashboard'))

        # Apply the SpaCy model to analyze the transcription
        doc = nlp(transcription)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # Define icon map with the new date icon
        icon_map = {
            'WEAPON': 'fas fa-bomb',
            'LOCATION': 'fas fa-map-marker-alt',
            'OPERATION': 'fas fa-user-secret',
            'RANK': 'fas fa-chess-queen',
            'DATE': 'fas fa-calendar-alt'  # Added icon for date entities
        }

        # Sentiment Analysis
        processed_text = preprocess_text(transcription)
        vectorized_text = tfidf_vectorizer.transform([processed_text])
        prediction = senti_model.predict(vectorized_text)
        sentiment_label = {0: 'Neutral', 1: 'Anti-military', 2: 'Pro'}  # Adjust according to your model's setup
        sentiment = sentiment_label[prediction[0]]

        # Clean up audio file to save space
        os.remove(file_path)

        return render_template('entities.html', entities=entities, transcription=transcription, sentiment=sentiment, icon_map=icon_map)
    
    flash('Invalid file format')
    return redirect(url_for('dashboard'))




@app.route('/transcribe_audio')
def transcribe_audio():
    # Placeholder for your transcribe_audio implementation
    return "Transcription results"

@app.route('/analyze_audio')
def analyze_audio():
    # Placeholder for your audio analysis implementation
    return "Audio analysis results"

@app.route('/anti_military_detection')
def anti_military_detection():
    # Placeholder for your anti-military detection feature
    return "Anti-military detection results"

@app.route('/entity_extraction')
def entity_extraction():
    # Placeholder for your entity extraction from audio
    return "Entity extraction results"

@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    text = request.form.get('text')
    if not text:
        flash("No text provided for conversion.")
        return redirect(url_for('dashboard'))
    
    # Check if there is an existing TTS file and delete it
    old_filename = session.get('tts_file')
    if old_filename:
        old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
        if os.path.exists(old_filepath):
            try:
                os.remove(old_filepath)  # Attempt to delete the old file
                session.pop('tts_file', None)  # Remove the file name from session after deletion
            except OSError as e:
                flash(f"Error removing the old file: {e}", "error")
    
    # Create a new TTS file
    tts = gTTS(text=text, lang='en', slow=False)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    
    # Generate a unique filename for the new TTS file using the current timestamp
    filename = secure_filename(f"{int(time.time())}_output.mp3")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(filepath, 'wb') as audio_file:
        audio_file.write(mp3_fp.getvalue())
    
    session['tts_file'] = filename  # Update the session with the new file
    flash('Text-to-Speech conversion successful. File ready for download.')
    return redirect(url_for('dashboard'))



@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    if 'audio_file' not in request.files:
        flash("No audio file uploaded.")
        return redirect(url_for('dashboard'))

    audio_file = request.files['audio_file']
    if audio_file and allowed_file(audio_file.filename):
        filename = secure_filename(audio_file.filename)
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(original_path)

        # Determine the file extension and process accordingly
        file_extension = filename.rsplit('.', 1)[1].lower()
        if file_extension != 'wav':
            # Convert to WAV format if not already
            wav_path = convert_audio_for_recognition(original_path)
            os.remove(original_path)  # Optionally remove the original file after conversion
            original_path = wav_path

        # Perform speech recognition on the WAV file
        recognizer = sr.Recognizer()
        with sr.AudioFile(original_path) as source:
            audio_data = recognizer.record(source)
        try:
            transcription = recognizer.recognize_google(audio_data)
            os.remove(original_path)  # Clean up the WAV file after processing
            return render_template('transcription.html', transcription=transcription, filename=filename)
        except sr.UnknownValueError:
            flash("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            flash(f"Could not request results from Google Speech Recognition service; {e}")
        except Exception as e:
            flash(f"An error occurred: {e}")
    else:
        flash("Invalid file format.")
    return redirect(url_for('dashboard'))





@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404_not_found.html'), 404

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(debug=True)
