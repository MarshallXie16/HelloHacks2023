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
OPENAI_API_KEY = ""
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# variables and settings
summarization_model = 'gpt-3.5-turbo'
feedback_model = 'gpt-3.5-turbo'
username = 'Marshall'

# mapping
emoji_mapping = {
    "happy": "😊",
    "sad": "😔",
    "angry": "😡",
    "anxious": "😰",
    "neutral": "😐",
}

# homepage; display all existing journal entries
@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        db = get_db()
        db.row_factory = dict_factory
        cursor = db.cursor()
        cursor.execute('SELECT id, title, entry_date, summary, feedback, mood FROM entries')
        entries = cursor.fetchall()
    
        # Augment map emoji to string
        for entry in entries:
            mood = entry['mood']
            print(mood)
            entry['emoji'] = emoji_mapping.get(mood, "😐")
            print(entry['emoji'])

        return render_template('index.html', entries=entries)

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
        return redirect(url_for('index'))
    else:
        return render_template('error.html')

@app.route('/delete_entry/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    try:
        delete_entry(entry_id) 
        return jsonify(success=True), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# delete a database entry, given its id
def delete_entry(entry_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM entries WHERE id=?', (entry_id,))
    db.commit()
    print(f'entry {entry_id} has been successfully deleted.')

# transcribe the audio at filepath using Whisper API
def transcribe(filepath):
    with open("uploads/recorded_audio.wav", "rb") as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file)
        transcript = transcription['text']
        print(f'User said {transcript}')
    return transcript

# organize and summarize the transcript into bullet-point form
def get_summary(transcript):
    prompt = f'''The following is a transcript of a spoken journal entry from { username }. 
    Organize and summarize the journal entry in bullet point form, while retaining the same tone and speaking style of the user. 
    Write from a first-person perspective, taking note of key events, insights, and feelings.
    The output must be based on the Journal Entry provided; do not make up any information.
    Journal Entry: {transcript}
    Output: '''

    system_prompt = [{"role": "user", "content": prompt}]

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
    prompt = f'''Context: You are a professional therapist with over a decade of experience. You are highly empathetic and converse with your patients in a personal and casual manner. 
    Your patient, {username}, is talking about their day. Below is a summary of their day, including what happened (events), what they learned about themselves/life (insights), and their feelings (mood). 
    
    Task: Provide feedback to them as a therapist would to his patient. Be empathetic but also offer personalized advice to help {username} overcome his struggles. 
    
    Format: The response should be a maximum of 200 words. Be concise and to the point. Strike a balance between empathy and practical advice. 
    
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

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# automatically closes db connection after a response is sent to client
@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)