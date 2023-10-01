from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import openai
import os
import sqlite3
from datetime import datetime
import pytz
from flask import g

# initialization
app = Flask(__name__, static_folder='static')
app.secret_key = 'hello'
DATABASE = 'database.db'
pst = pytz.timezone('America/Los_Angeles')

# keys and credentials
OPENAI_API_KEY = "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"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# variables and settings
summarization_model = 'gpt-3.5-turbo'
feedback_model = 'gpt-3.5-turbo'
username = 'Marshall'

# homepage; display all existing journal entries
@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT title, entry_date, summary, feedback, mood FROM entries')
        results = cursor.fetchall()
        print(results)
        return render_template('index.html')

# processes audio input
@app.route('/upload', methods=['POST'])
def upload():
    # no audio file uploaded
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file"}), 400
    
    # retrieve and save audio
    audio_file = request.files['audio']
    filename = "uploads/recorded_audio.wav"
    audio_file.save(filename)
    
    transcript = transcribe(filename)

    summary = get_summary(transcript)
    feedback = get_feedback(transcript)
    
    current_time = datetime.now(pst)
    current_time_string = current_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    print(f'Time saved: {current_time}')

    return jsonify({'summary': summary, 'feedback': feedback, 'title': current_time_string})

# submits journal entry
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # retrieve form information
        title = request.form.get('title')
        summary = request.form.get('summary')
        feedback = request.form.get('feedback')
        mood = request.form.get('selectedMood')
        print(mood)
        # attempt to add to database
        try: 
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO entries (title, summary, feedback, mood) VALUES(?, ?, ?, ?)", (title, summary, feedback, mood))
            db.commit()
        except Exception as e:
            print("Error inserting into database", e)
        return render_template('index.html')
    else:
        return render_template('error.html')
    

# transcribe the audio at filepath using Whisper API
def transcribe(filepath):
    with open("uploads/recorded_audio.wav", "rb") as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file)
        transcript = transcription['text']
        print(f'User said {transcript}')
    return transcript

# organize and summarize the transcript into bullet-point form
def get_summary(transcript):
    prompt = f'''The following is a journal entry from {{ user }}. 
    Organize and summarize the journal entry in bullet point form, from the perspective of {{ user }}, taking note of key events, insights, and feelings.
    Journal Entry: ---
    {transcript}.

    Summary: '''

    system_prompt = [{"role": "system", "content": prompt}]

    # make openAI API call
    response = openai.ChatCompletion.create(
        model=summarization_model,
        messages=system_prompt,
    )

    # parse response
    summary = response["choices"][0]["message"]["content"]
    print(f'Tokens used (summarize): {response["usage"]["total_tokens"]}')
    print(f'Summary: {summary}')
    return summary

# based on the transcript, provide personalized feedback and advice
def get_feedback(transcript):
    prompt = f'''You are a professional therapist with over a decade of experience. 
    You are highly empathetic and converses with your patients in a personal and casual manner. 
    Your patient, {username}, is talking about their day. Below is a summary of their day, including what happened (events), 
    what they learned about themselves/life (insights), and their feelings (mood). 
    Provide feedback to them as a therapist would to his patient. Be empathetic but also offer personalized advice for help {username} overcome his struggles. 
    The response should be a maximum of 300 words.
    {username}'s summary of their day: {transcript}'''

    system_prompt = [{"role": "system", "content": prompt}]

    # make openAI API call
    response = openai.ChatCompletion.create(
        model=feedback_model,
        messages=system_prompt,
    )

    # parse response
    feedback = response["choices"][0]["message"]["content"]
    print(f'Tokens used (feedback): {response["usage"]["total_tokens"]}')
    print(f'AI Therapist Feedback: {feedback}')
    return feedback

# create a new db connection for every thread
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

# automatically closes db connection after a response is sent to client
@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)