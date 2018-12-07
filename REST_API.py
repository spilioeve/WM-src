from flask import Flask, request
from Main import SOFIA
import json

app = Flask(__name__)

sofia = SOFIA(CoreNLP='/Users/brandon/stanford-corenlp-full-2018-10-05')

@app.route('/process_text', methods=['POST'])
def process_text():
    obj = request.json
    text = obj['text']
    print(text)
    results = sofia.getOutputOnline(text)
    return json.dumps(results)

@app.route('/process_query', methods=['POST'])
def process_query():
    obj = request.json
    text = obj['text']
    query = obj['query']
    print(text)
    print(query)
    results = sofia.writeQueryBasedOutput(text, query)
    return json.dumps(results)    