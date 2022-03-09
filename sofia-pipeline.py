import json
import os
import re
import argparse

from nltk.tokenize import sent_tokenize
import enchant

from sofia import *
import requests
from requests.auth import HTTPBasicAuth

lang_encoding_dict = enchant.Dict("en_US")

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
                if lang_encoding_dict.check(i):
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


def download_files(exp_path, credentials):
    #abs_path = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    os.chdir('../python-kafka-consumer-master')
    os.system(f'docker run --env PROGRAM_ARGS=wm-sasl-example -it -v {exp_path}/kafka_out:/opt/app/data python-kafka-consumer-local:latest')
    os.chdir('../')
    temp = os.listdir(f'{exp_path}/kafka_out')
    extension = os.path.splitext(temp[0])[1]
    docs= [i.split('.')[0] for i in temp]
    prev_docs = [i.split('.')[0] for i in os.listdir(f'{exp_path}/text')]
    new_docs = list(set(docs)-set(prev_docs))
    for doc_id in new_docs:
        try:
            thin_cdr = json.load(open(f'{exp_path}/kafka_out/{doc_id}{extension}'))
            doc_id = thin_cdr["document_id"]
            release_date = thin_cdr["timestamp"]
            #cdr_data = json.loads(thin_cdr['cdr-data'])
            #release_date = thin_cdr['release-date']
            #document_id = cdr_data['document_id']
            doc_path = f'{exp_path}/text/{doc_id}'
            address = f'{credentials["cdr_api"]}/{doc_id}?date={release_date}'
            os.system(f'curl -u sofia:{credentials["password"]} -o {doc_path} {address}')
            with open(doc_path) as f:
                content = json.load(f)
                text = content['extracted_text']
            text_proc = clean_text(text)
            with open(f'{exp_path}/clean_text/{doc_id}', 'w') as f:
                f.write(text_proc)
        except:
            print(f'Issue with doc {doc_id}')
    return new_docs


def upload_docs(experiment, doc_ids, credentials, ontology):
    http_auth = None
    if credentials["password"] is not None:
        http_auth = HTTPBasicAuth("sofia", credentials["password"])
    for doc_id in doc_ids:
        metadata = {
            "identity": "sofia",
            "version": "1.3",
            "document_id": doc_id,
            "output_version": ontology.split('_')[1]
        }
        output_filename = f'{os.getcwd()}/sofia/data/{experiment}_output/{doc_id}.json'

        if os.path.exists(output_filename):
            form_request = {"file": (output_filename, open(output_filename)),
                            "metadata": (None, json.dumps(metadata), 'application/json')}

            response = requests.post(credentials["upload_api"], files=form_request, auth=http_auth)

            if response.status_code == 201:
                print(f'uploaded - {output_filename} for doc {doc_id}')
            else:
                print(f"Uploading of {doc_id} failed! Please re-try")


def run_sofia_online(credentials, ontology, experiment, version, docs_file, mode):
    sofia_path = os.getcwd()
    exp_path = f'{sofia_path}/sofia/data/{experiment}'
    text_path = f'{exp_path}/text'
    #ann_path = f'{exp_path}/annotations'
    if docs_file == None:
        print("Downloading CDRS...")
        doc_ids = download_files(exp_path, credentials)
    else:
        f= open(f'sofia/data/{docs_file}')
        doc_ids = f.read().split('\n')[:-1]
    if mode == 'download':
        return "completed downloading"
    elif mode=='upload':
        print("Uploading docs to DART.....")
        upload_docs(experiment, doc_ids, credentials, ontology)
        return "completed uploading"

    sofia = SOFIA(ontology)
    print("Preprocessing files with corenlp...")
    print("Running Sofia...")
    for doc_id in doc_ids:
        #if doc != '.DS_Store':
        if doc_id in os.listdir(text_path):
            with open(text_path+'/'+doc_id) as f:
                text = f.read()
            output_file= sofia.get_online_output(text, doc_id, experiment, save=True)
            #f'{ann_path}/{doc_id}_{version}',
        print(f'Read {output_file}')
    if mode == 'read':
        return "completed reading"

    print("Uploading docs to DART.....")
    upload_docs(experiment, doc_ids, credentials, ontology)
    return "completed uploading"

def main():
    parser = argparse.ArgumentParser(description='Augment Data with Wikipedia Links')
    parser.add_argument('--experiment', type=str, default='aug2021')
    parser.add_argument('--version', type=str, default='v1')
    parser.add_argument('--ontology', type=str, default='compositional_3.0')
    parser.add_argument('--mode', type=str, help='Options are: download,read,all,upload', default= 'all')
    parser.add_argument('--docs_file', type=str, default= None)
    parser.add_argument('--upload_api', type=str, default= None)
    parser.add_argument('--cdr_api', type=str, default= None)
    parser.add_argument('--password', type=str, default= None)

    args = parser.parse_args()

    print("Configure Docker and create directories...")
    experiment = args.experiment
    #os.chdir('python-kafka-consumer-master')
    #os.system('docker build -t python-kafka-consumer-local .')
    #os.chdir('../')
    if os.path.exists('credentials.json'):
        credentials= json.load(open('credentials.json'))
    else:
        credentials= {'cdr_api': args.cdr_api, 'upload_api': args.upload_api, 'password': args.password}

    if not os.path.exists(f'sofia/data/{experiment}'):
        os.system(f'mkdir sofia/data/{experiment}')
        for i in ['kafka_out', 'text', 'annotations']:
            os.system(f'mkdir sofia/data/{experiment}/{i}')
    #kafka_path = '{}/{}/{}/{}/{}'.format(os.getcwd(), 'sofia', 'data', experiment, 'kafka_out')

        #os.system('docker run --env PROGRAM_ARGS=wm-sasl-example -it -v {}:/opt/app/data '
         #         'python-kafka-consumer-local:latest'.format(kafka_path))

    completed= run_sofia_online(credentials, args.ontology, experiment, args.version, args.docs_file, args.mode)
    print(completed)


if __name__ == '__main__':
    main()