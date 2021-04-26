import json
import os
from sofia import *



def remove_empty_lines(text_init):
    lines=text_init.split('\n')
    new_lines=[]
    for line in lines:
        line=line.strip('\n')
        if len(line)>20:
            new_lines.append(line)
    return '\n'.join(new_lines)


def get_cdrs(docs_path, cdr_path, cdr_api, sofia_pwd):
    docs = os.listdir(docs_path)
    for doc in docs:
        thin_cdr = json.load(open(docs_path+'/'+doc))
        document_id = thin_cdr["document_id"]
        release_date = thin_cdr["timestamp"]
        #cdr_data = json.loads(thin_cdr['cdr-data'])
        #release_date = thin_cdr['release-date']
        #document_id = cdr_data['document_id']
        address = f'{cdr_api}/{document_id}?date={release_date}'
        os.system('curl -u sofia:{} -o kafka_text_mar21/{} {}'.format(sofia_pwd, doc, address))
        with open(cdr_path+'/'+doc) as f:
            content = json.load(f)
            text = content['extracted_text']
        text_proc = remove_empty_lines(text)
        with open(cdr_path+'/'+doc, 'w') as f:
            f.write(text_proc)

def upload_docs(path, upload_api, sofia_pwd):
    docs= os.listdir(path)
    command1 = 'curl --location --user sofia:{} --request POST {} --form file=@'.format(sofia_pwd, upload_api)
    command2 = ''' --form 'metadata={ "identity": "sofia", "version": "1.1", "document_id": "'''
    for doc in docs:
        command = command1 + path + doc  + command2 + doc[:-5] + '"}' + "'"
        os.system(command)


def run_sofia_online(upload_api, cdr_api, sofia_pwd, ontology= 'compositional', experiment= 'may2021', version= 'v1', save = True):
    sofia = SOFIA(ontology)
    print("Configure Docker...")
    sofia_path = os.getcwd()
    #docs_path = sofia_path+'/dart_docs'

    os.system('docker build -t python-kafka-consumer-local .')
    os.system('mkdir {}/{}/{}'.format('sofia', 'data', experiment))
    for i in ['kafka_out', 'text', 'annotations']:
        os.system('mkdir {}/{}/{}/{}'.format('sofia', 'data', experiment, i))
    kafka_path = '{}/{}/{}/{}/{}'.format(sofia_path, 'sofia', 'data', experiment, 'kafka_out')
    text_path = '{}/{}/{}/{}/{}'.format(sofia_path, 'sofia', 'data', experiment, 'text')
    ann_path = '{}/{}/{}/{}/{}'.format(sofia_path, 'sofia', 'data', experiment, 'annotations')
    os.system('docker run --env PROGRAM_ARGS=wm-sasl-example -it -v {}:/opt/app/data python-kafka-consumer-local:latest'
              .format(kafka_path))

    print("Downloading CDRS...")
    get_cdrs(kafka_path, text_path, cdr_api, sofia_pwd)

    print("Preprocessing files with corenlp...")
    docs = os.listdir(text_path)
    for doc in docs:
        #if doc != '.DS_Store':
        with open(text_path+'/'+doc) as f:
            text = f.read()
        annotations = sofia.annotate(text, save= save, file_name= ann_path+'/'+doc)

    print("Running Sofia...")
    sofia.get_file_output(ann_path, version, docs=None)

    print("Uploading docs to DART.....")
    output_path = 'sofia/data/{}_output{}'.format(ann_path, version)
    upload_docs(output_path, upload_api, sofia_pwd)
