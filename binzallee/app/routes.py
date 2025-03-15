from flask import render_template
from . import create_app
import json
import os

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event_log')
def event_log():
    with open('event_data.json') as f:
        data = json.load(f)
    return data

@app.route('/action', methods=['POST'])
def action():
    # Handle the POST request here
    print('Action received')
    os.system('aplay proud-fart-288263.wav')
    return 'Action received'
    