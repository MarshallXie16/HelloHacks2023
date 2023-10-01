from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import openai
import os
import sqlite3

# initialization
app = Flask(__name__, static_folder='static')
app.secret_key = 'hello'
DATABASE = 'database.db'
connection = sqlite3.connect('database.db')
cursor = connection.cursor()

# keys and credentials
OPENAI_API_KEY = ""
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# variables and settings
summarization_model = 'gpt-3.5-turbo'
feedback_model = 'gpt-3.5-turbo'
username = 'Marshall'

# homepage
@app.route('/', methods=['GET'])
def index():
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

    return jsonify({'summary': summary, 'feedback': feedback})

# submits journal entry
@app.route('/submit')
def submit():
    if request.method == 'POST':
        # retrieve form information
        title = request.form.get('title')
        summary = request.form.get('summary')
        feedback = request.form.get('feedback')
        print(title, summary, feedback)
        cursor.execute("INSERT INTO entries (title, summary, feedback) VALUES(?, ?, ?)", (title, summary, feedback))
        connection.commit()
        test_database()
    return render_template('index.html')

def test_database():
    cursor.execute('SELECT * FROM entries')
    all_entries = cursor.fetchall()
    print(all_entries)

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# click record button -> JS starts recording
# clicks record button again -> JS stops recording and sends recorded data to backend + display loading circle
# In the backend: parse the recorded data and save as audio file
    # transcribe audio file with whisper
    # get summary
    # get feedback
    # return render with summary and feedback,


# CREATE TABLE entries (id INTEGER PRIMARY KEY, entry_date DATE DEFAULT (CURRENT_DATE), title TEXT NOT NULL, summary TEXT NOT NULL, feedback TEXT NOT NULL, mood TEXT NOT NULL);