import json
import os
from sofia import *
import argparse



def remove_empty_lines(text_init):
    lines=text_init.split('\n')
    new_lines=[]
    for line in lines:
        line=line.strip('\n')
        if len(line)>20:
            new_lines.append(line)
    return '\n'.join(new_lines)


def get_cdrs(exp_path, cdr_api, sofia_pwd):
    docs = os.listdir(exp_path+'/kafka_out')
    prev_docs = os.listdir(exp_path+'/text')
    new_docs = list(set(docs)-set(prev_docs))
    for doc in new_docs:
        thin_cdr = json.load(open(exp_path+'/kafka_out/'+doc))
        document_id = thin_cdr["document_id"]
        release_date = thin_cdr["timestamp"]
        #cdr_data = json.loads(thin_cdr['cdr-data'])
        #release_date = thin_cdr['release-date']
        #document_id = cdr_data['document_id']
        doc_path = '{}/{}/{}'.format(exp_path, 'text', doc)
        address = f'{cdr_api}/{document_id}?date={release_date}'
        os.system('curl -u sofia:{} -o {} {}'.format(sofia_pwd, doc_path, address))
        with open(doc_path) as f:
            content = json.load(f)
            text = content['extracted_text']
        text_proc = remove_empty_lines(text)
        with open(doc_path, 'w') as f:
            f.write(text_proc)
    return new_docs

def upload_docs(path, upload_api, sofia_pwd):
    docs= os.listdir(path)
    command1 = 'curl --location --user sofia:{} --request POST {} --form file=@'.format(sofia_pwd, upload_api)
    command2 = ''' --form 'metadata={ "identity": "sofia", "version": "1.1", "document_id": "'''
    for doc in docs:
        command = command1 + path + doc  + command2 + doc[:-5] + '"}' + "'"
        os.system(command)


def run_sofia_online(upload_api, cdr_api, sofia_pwd, ontology, experiment, version, save):
    sofia_path = os.getcwd()
    #docs_path = sofia_path+'/dart_docs'

    exp_path = '{}/{}/{}/{}'.format(sofia_path, 'sofia', 'data', experiment)
    text_path = exp_path + '/text'
    ann_path = exp_path+ '/annotations'

    print("Downloading CDRS...")
    new_docs = get_cdrs(exp_path, cdr_api, sofia_pwd)

    print("Preprocessing files with corenlp...")
    sofia = SOFIA(ontology)

    for doc in new_docs:
        #if doc != '.DS_Store':
        with open(text_path+'/'+doc) as f:
            text = f.read()
        annotations = sofia.annotate(text, save= save, file_name= ann_path+'/'+doc)

    print("Running Sofia...")
    sofia.get_file_output(ann_path, version, docs=new_docs)

    print("Uploading docs to DART.....")
    output_path = 'sofia/data/{}_output{}'.format(ann_path, version)
    upload_docs(output_path, upload_api, sofia_pwd)

def main():
    parser = argparse.ArgumentParser(description='Augment Data with Wikipedia Links')
    parser.add_argument('--experiment', type=str, default=None)
    parser.add_argument('--version', type=str, default='v1')
    parser.add_argument('--save', type=str, default=True)
    parser.add_argument('--ontology', type=str, default='compositional')
    parser.add_argument('--upload_api', type=str, default=upload_api)
    parser.add_argument('--cdr_api', type=str, default= cdr_api)
    parser.add_argument('--password', type=str, default=password)

    args = parser.parse_args()

    print("Configure Docker and create directories...")
    experiment = args.experiment
    os.chdir('python-kafka-consumer-master')
    os.system('docker build -t python-kafka-consumer-local .')
    os.chdir('../')
    os.system('mkdir {}/{}/{}'.format('sofia', 'data', experiment))
    for i in ['kafka_out', 'text', 'annotations']:
        os.system('mkdir {}/{}/{}/{}'.format('sofia', 'data', experiment, i))
    kafka_path = '{}/{}/{}/{}/{}'.format(os.getcwd(), 'sofia', 'data', experiment, 'kafka_out')
    prev_size = len(os.listdir(kafka_path))

    while True:
        #os.system('docker run --env PROGRAM_ARGS=wm-sasl-example -it -v {}:/opt/app/data '
         #         'python-kafka-consumer-local:latest'.format(kafka_path))

        curr_size = len(os.listdir(kafka_path))
        if curr_size!=prev_size:
            print("New documents detected!")
            print('#'*100)
            prev_size = curr_size
            run_sofia_online(args.upload_api, args.cdr_api, args.password, args.ontology,
                         experiment, args.version, args.save)



if __name__ == '__main__':
    main()