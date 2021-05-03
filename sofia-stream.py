#!/usr/bin/env python3

import json
import os
from sofia import *
import faust
import ssl
import requests
from requests.auth import HTTPBasicAuth
from os.path import exists, basename
from os import makedirs
import re
from nltk.tokenize import sent_tokenize
import enchant
d = enchant.Dict("en_US")

def create_kafka_app(broker, user, pwd):
    credentials = None
    if user is not None and pwd is not None:
        credentials = faust.SASLCredentials(
            username=user,
            password=pwd,
            ssl_context=ssl.create_default_context()
        )
    
    # create your application
    app = faust.App(
        'sofia',
        autodiscover=False,
        broker=broker,
        broker_credentials=credentials,
        topic_disable_leader=True,
        consumer_auto_offset_reset='earliest'
    )
    
    return app


def remove_empty_lines(text_init):
    lines = text_init.split('\n')
    new_lines = []
    for line in lines:
        line = line.strip('\n')
        line = re.sub(r'[^a-zA-Z0-9_ \n .,/?!@#$%^&*()-:;]', '', line)
        res_line = re.sub(r'[^\w\s]', '', line)
        res_line = re.sub("\d+", "", res_line)
        if len(res_line.split()) > 5 and len(res_line.split())<30:
            num_english= 0
            for i in res_line.split():
                if d.check(i):
                    num_english+=1
            if len(res_line.split())-num_english<2:
                new_lines.append(line)
    return '\n'.join(new_lines)

#TODO: this needs fixing, very hard to strip characters / non-words
def clean_text(text_init):
    text_init= remove_empty_lines(text_init)
    sentences = sent_tokenize(text_init)
    text=""
    for sentence in sentences:
        for letter in sentence:
            if ord(letter) < 128:
                if letter != '\n':
                    text += letter
        if len(sentence)>0 and sentence[-1]!= '.':
                text+= '.'
        text+= '\n'
    lines = text.split('\n')
    text_final = ""
    for line in lines:
        line = line.strip('\n')
        sentence = line.strip(' ')
        if len(sentence.split(' ')) > 30:
            if '\n' in sentence:
                i = sentence.index('\n')
                text_final +=  sentence[:i] + '. ' + sentence[i:]
        elif len(sentence.split(' ')) > 4:
            text_final += sentence + '\n'
    return text_final

def get_cdr_text(doc_id, cdr_api, sofia_user, sofia_pass):
    url = f'{cdr_api}/{doc_id}'

    http_auth = None
    if sofia_user is not None and sofia_pass is not None:
        http_auth = HTTPBasicAuth(sofia_user, sofia_pass)

    response = requests.get(url, auth=http_auth)

    if response.status_code == 200:
        cdr_json = json.loads(response.text)
        return clean_text(cdr_json['extracted_text'])
    else:
        # @eva - TODO - this is an error, you should log any error messages or perform any kind of recovery here
        print("Retrieving cdr failed. Please re-try.")
        return None


def upload_sofia_output(doc_id, file, upload_api, sofia_user, sofia_pass):
    metadata = {
        "identity": "sofia",
        "version": "1.1",
        "document_id": doc_id
    }

    form_request = {"file": (basename(file), file), "metadata": (None, json.dumps(metadata), 'application/json')}

    http_auth = None
    if sofia_user is not None and sofia_pass is not None:
        http_auth = HTTPBasicAuth(sofia_user, sofia_pass)

    response = requests.post(upload_api, files=form_request, auth=http_auth)

    if response.status_code == 201:
        # @eva - processing is complete and successful, you can either log this or ignore it
        print("File uploaded!")
    else:
        # @eva - this means uploading the output failed, you should log this and implement any kind of retry or recovery
        # logic here...

        print(f"Uploading of {doc_id} failed! Please re-try")


def run_sofia_stream(kafka_broker,
                     upload_api,
                     cdr_api,
                     sofia_user,
                     sofia_pwd,
                     ontology='compositional',
                     experiment='may2021',
                     version='v1',
                     save=True):
    sofia = SOFIA(ontology)
    sofia_path = os.getcwd()

    #corenlp_annotated = f'{sofia_path}/sofia/data/{experiment}/annotations'

    # if not exists(corenlp_annotated):
    #     makedirs(corenlp_annotated)
    app = create_kafka_app(kafka_broker, sofia_user, sofia_pwd)
    dart_update_topic = app.topic("dart.cdr.streaming.updates", key_type=str, value_type=str)
    # @eva - this is the function that will be called each time the kafka consumer receives a message
    # this is the "body" of the consumer loop
    @app.agent(dart_update_topic)
    async def process_document(stream: faust.StreamT):
        doc_stream = stream.events()
        async for cdr_event in doc_stream:
            doc_id = cdr_event.key
            extracted_text = get_cdr_text(doc_id, cdr_api, sofia_user, sofia_pwd)
            print(f"Doc {doc_id} received!")
            if extracted_text is not None:
                # @eva - i'm less sure what to do here... you will need to refactor these methods to handle docs
                # on a doc by doc basis instead of dealing with directories of docs
                file_name = f'{doc_id}_{version}'
                output = sofia.get_online_output(extracted_text, experiment= experiment, file_name= file_name)
                if save:
                    if not exists(f'sofia/data/{experiment}_input'):
                        makedirs(f'sofia/data/{experiment}_input')
                    with open(f'sofia/data/{experiment}_input/{file_name}.txt', 'w') as f:
                        f.write(extracted_text)
                if output is not None:
                    upload_sofia_output(doc_id, f'sofia/data/{experiment}_output/{file_name}.json', upload_api, sofia_user,
                                    sofia_pass)

                # upload file, etc...
    print("exits loop")
    app.main()


if __name__ == '__main__':
    # @michael - consider replacing these values with calls to `os.environ[...]` for docker build
 #   kafka_broker = 'localhost:9092'
    kafka_broker = 'kafka://wm-ingest-pipeline-streaming-1.prod.dart.worldmodelers.com:9093'
    upload_api = 'https://wm-ingest-pipeline-rest-1.prod.dart.worldmodelers.com/dart/api/v1/readers/upload'
 #   cdr_api = 'http://ec2-35-171-47-235.compute-1.amazonaws.com:8090/dart/api/v1/cdrs'
    cdr_api = ' https://wm-ingest-pipeline-rest-1.prod.dart.worldmodelers.com/dart/api/v1/cdrs'
#    sofia_user = None
    sofia_pass = None
    sofia_user = 'sofia'
    ontology = 'compositional'
    experiment = 'may2021'
    version = 'v1'
    save = True
    
    run_sofia_stream(kafka_broker, upload_api, cdr_api, sofia_user, sofia_pass, ontology, experiment, version,
                     save)

