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
        if len(line) > 20:
            new_lines.append(line)
    return '\n'.join(new_lines)


def get_cdr_text(doc_id, cdr_api, sofia_user, sofia_pass):
    url = f'{cdr_api}/{doc_id}'

    http_auth = None
    if sofia_user is not None and sofia_pass is not None:
        http_auth = HTTPBasicAuth(sofia_user, sofia_pass)

    response = requests.get(url, auth=http_auth)

    if response.status_code == 200:
        cdr_json = json.loads(response.text)
        return remove_empty_lines(cdr_json['extracted_text'])
    else:
        # @eva - TODO - this is an error, you should log any error messages or perform any kind of recovery here
        return None


def upload_sofia_output(doc_id, file, output_api, sofia_user, sofia_pass):
    metadata = {
        "identity": "sofia",
        "version": "1.1",
        "document_id": doc_id
    }

    form_request = {"file": (basename(file.name), file), "metadata": (None, json.dumps(metadata), 'application/json')}

    http_auth = None
    if sofia_user is not None and sofia_pass is not None:
        http_auth = HTTPBasicAuth(sofia_user, sofia_pass)

    response = requests.post(output_api, files=form_request, auth=http_auth)

    if response.status_code == 201:
        # @eva - processing is complete and successful, you can either log this or ignore it
        pass
    else:
        # @eva - this means uploading the output failed, you should log this and implement any kind of retry or recovery
        # logic here...
        pass


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

    corenlp_annotated = f'{sofia_path}/sofia/data/{experiment}/annotations'

    if not exists(corenlp_annotated):
        makedirs(corenlp_annotated)

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

            if extracted_text is not None:
                # @eva - i'm less sure what to do here... you will need to refactor these methods to handle docs
                # on a doc by doc basis instead of dealing with directories of docs
                sofia.annotate(extracted_text, save=save, file_name=f'{corenlp_annotated}/{doc_id}')
                sofia.get_file_output(corenlp_annotated, version, docs=None)

                # upload file, etc...

    app.main()


if __name__ == '__main__':
    # @michael - consider replacing these values with calls to `os.environ[...]` for docker build
    kafka_broker = 'localhost:9092'
    upload_api = ''
    cdr_api = 'http://ec2-35-171-47-235.compute-1.amazonaws.com:8090/dart/api/v1/cdrs'
    sofia_user = None
    sofia_pass = None
    ontology = 'compositional'
    experiment = 'may2021'
    version = 'v1'
    save = False
    run_sofia_stream(kafka_broker, upload_api, cdr_api, sofia_user, sofia_pass, experiment, version, save)
