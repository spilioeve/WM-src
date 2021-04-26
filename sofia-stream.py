import json
import os
from sofia import *
import faust
import ssl
import requests


def create_consumer_app(broker, user, pwd):
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
        autodiscover=True,
        broker=broker,
        broker_credentials=credentials,
        topic_disable_leader=True
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
    cdr_json = json.loads(requests.get(url, auth=requests.HTTPBasicAuth(sofia_user, sofia_pass)).text)
    return remove_empty_lines(cdr_json['extracted_text'])


def upload_docs(path, upload_api, sofia_pwd):
    docs = os.listdir(path)
    command1 = 'curl --location --user sofia:{} --request POST {} --form file=@'.format(sofia_pwd, upload_api)
    command2 = ''' --form 'metadata={ "identity": "sofia", "version": "1.1", "document_id": "'''
    for doc in docs:
        command = command1 + path + doc + command2 + doc[:-5] + '"}' + "'"
        os.system(command)


def run_sofia_online(kafka_broker,
                     upload_api,
                     cdr_api,
                     sofia_user,
                     sofia_pwd,
                     ontology='compositional',
                     experiment='may2021',
                     version='v1',
                     save=True):
    sofia = SOFIA(ontology)
    print("Configure Docker...")
    sofia_path = os.getcwd()
    # docs_path = sofia_path+'/dart_docs'
    app = create_consumer_app(kafka_broker, sofia_user, sofia_pwd)
    topic = app.topic("dart.cdr.streaming.updates", key_type=str, value_type=str)

    @app.agent(topic)
    async def process_document(stream: faust.StreamT):
        doc_stream = stream.events()
        async for cdr_event in doc_stream:
            doc_id = cdr_event.key
            extracted_text = get_cdr_text(doc_id, cdr_api, sofia_user, sofia)
            print(len(extracted_text))
            # annotations = sofia.annotate(extracted_text, save=False)

    app.main()


def run():
    kafka_broker = 'localhost:9092'
    upload_api = ''
    cdr_api = 'http://ec2-35-171-47-235.compute-1.amazonaws.com:8090/dart/api/v1/cdrs'
    sofia_user = None
    sofia_pass = None
    ontology = 'compositional'
    experiment = 'may2021'
    version = 'v1'
    save = False
    run_sofia_online(kafka_broker, upload_api, cdr_api, sofia_user, sofia_pass, experiment, version, save)


if __name__ == '__main__':
    run()
