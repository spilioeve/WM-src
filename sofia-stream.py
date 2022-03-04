#!/usr/bin/env python3

import json
import os
import ssl
import re
from datetime import datetime

import faust
import requests
from nltk.tokenize import sent_tokenize
from requests.auth import HTTPBasicAuth

import enchant

from sofia import *

from pathlib import Path

lang_encoding_dict = enchant.Dict("en_US")


def create_kafka_app(broker, user, pwd, auto_offset_reset, enable_auto_commit):
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
        consumer_auto_offset_reset=auto_offset_reset,
        stream_wait_empty=enable_auto_commit,
        topic_disable_leader=True)

    return app


def remove_empty_lines(text_init):
    lines = text_init.split('\n')
    new_lines = []
    for line in lines:
        line = line.strip('\n')
        line = re.sub(r'[^a-zA-Z0-9_ \n .,/?!@#$%^&*()-:;]', '', line)
        res_line = re.sub(r'[^\w\s]', '', line)
        res_line = re.sub("\d+", "", res_line)
        if len(res_line.split()) > 5 and len(res_line.split()) < 30:
            num_english = 0
            for i in res_line.split():
                if lang_encoding_dict.check(i):
                    num_english += 1
            if len(res_line.split()) - num_english < 2:
                new_lines.append(line)
    return '\n'.join(new_lines)


# TODO: this needs fixing, very hard to strip characters / non-words
def clean_text(text_init):
    text_init = remove_empty_lines(text_init)
    sentences = sent_tokenize(text_init)
    text = ""
    for sentence in sentences:
        for letter in sentence:
            if ord(letter) < 128:
                if letter != '\n':
                    text += letter
        if len(sentence) > 0 and sentence[-1] != '.':
            text += '.'
        text += '\n'
    lines = text.split('\n')
    text_final = ""
    for line in lines:
        line = line.strip('\n')
        sentence = line.strip(' ')
        if len(sentence.split(' ')) > 30:
            if '\n' in sentence:
                i = sentence.index('\n')
                text_final += sentence[:i] + '. ' + sentence[i:]
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
        print(f'got CDR data for {doc_id} : {len(cdr_json["extracted_text"])}')
        return clean_text(cdr_json['extracted_text'])
    else:
        print(f'error getting CDR data from DART service: {response.status_code} : {response.text}')
        return None


def upload_sofia_output(doc_id, output_filename, upload_api, sofia_user, sofia_pass, ontology_version):
    metadata = {
        "identity": "sofia",
        "version": "1.3",
        "document_id": doc_id,
        "output_version": ontology_version
    }
    form_request = {"file": (output_filename, open(output_filename)),
                    "metadata": (None, json.dumps(metadata), 'application/json')}

    http_auth = None
    if sofia_user is not None and sofia_pass is not None:
        http_auth = HTTPBasicAuth(sofia_user, sofia_pass)

    response = requests.post(upload_api, files=form_request, auth=http_auth)

    if response.status_code == 201:
        print(f'uploaded - {output_filename} for doc {doc_id}')
    else:
        print(f"Uploading of {doc_id} failed with status code {response.status_code}! Please re-try")


def run_sofia_stream(kafka_broker,
                     kafka_auto_offset_reset,
                     kafka_enable_auto_commit,
                     upload_api,
                     cdr_api,
                     sofia_user,
                     sofia_pass,
                     ontology,
                     experiment,
                     version):
    sofia = SOFIA(ontology)
    ontology_version = Path(ontology).with_suffix('').name
    app = create_kafka_app(kafka_broker, sofia_user, sofia_pass, kafka_auto_offset_reset, kafka_enable_auto_commit)
    dart_update_topic = app.topic("dart.cdr.streaming.updates", key_type=str, value_type=str)

    @app.agent(dart_update_topic)
    async def process_document(stream: faust.StreamT):
        doc_stream = stream.events()
        async for cdr_event in doc_stream:
            doc_id = cdr_event.key
            print(f'received notification for {doc_id}')
            extracted_text = get_cdr_text(doc_id, cdr_api, sofia_user, sofia_pass)
            if extracted_text is not None:
                output = sofia.get_online_output(extracted_text, doc_id, experiment=experiment, save=False)
                if output is not None:
                    print(f'uploading output for {doc_id} : {ontology_version}')
                    upload_sofia_output(doc_id, output, upload_api, sofia_user, sofia_pass, ontology_version)

    app.main()


if __name__ == '__main__':
    datetime_slug = datetime.now().strftime("%m/%d/%Y-%H:%M:%S")
    _kafka_broker = os.getenv('KAFKA_BROKER') if os.getenv('KAFKA_BROKER') is not None else 'localhost:9092'
    _kafka_auto_offset_reset = os.getenv('KAFKA_AUTO_OFFSET_RESET') if os.getenv(
        'KAFKA_AUTO_OFFSET_RESET') is not None else 'latest'
    _kafka_enable_auto_commit = os.getenv('ENABLE_AUTO_COMMIT') if os.getenv('ENABLE_AUTO_COMMIT') is not None else True
    _upload_api = os.getenv('UPLOAD_API_URL') if os.getenv('UPLOAD_API_URL') is not None else 'localhost:1337'
    _cdr_api = os.getenv('CDR_API_URL') if os.getenv('CDR_API_URL') is not None else 'localhost:8090'
    _sofia_user = os.getenv('SOFIA_USER')
    _sofia_pass = os.getenv('SOFIA_PASS')
    _ontology = os.getenv('ONTOLOGY') if os.getenv('ONTOLOGY') is not None else 'compositional_2.2'
    _experiment = os.getenv('EXPERIMENT') if os.getenv('EXPERIMENT') is not None else f'test-{datetime_slug}'
    _version = os.getenv('VERSION') if os.getenv('VERSION') is not None else 'v1'

    run_sofia_stream(_kafka_broker,
                     _kafka_auto_offset_reset,
                     _kafka_enable_auto_commit,
                     _upload_api,
                     _cdr_api,
                     _sofia_user,
                     _sofia_pass,
                     _ontology,
                     _experiment,
                     _version)
