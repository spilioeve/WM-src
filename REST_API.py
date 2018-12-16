from flask import Flask, request
from Main import SOFIA
import json
import redis
from hashlib import sha1
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Set to local unzipped CoreNLP Path
sofia = SOFIA(CoreNLP='/Users/brandon/stanford-corenlp-full-2018-10-05')

# Set to True if a redis instance is running at localhost:6379
# and you wish to use queuing. Otherwise, set to False
REDIS = True

if REDIS:
    r = redis.Redis(host='localhost', port=6379, db=0)
else:
    r = None

@app.route('/process_text', methods=['POST'])
def process_text():
    '''
    Adds a reading task to the SOFIA-Queue.
    Adds the submission to Redis with key = id_
    '''    
    obj = request.json
    text = obj['text']
    print(text)
    if r:
        id_ = gen_id(text)
        r_obj = {'Status': 'Processing', 'Text': text}
        r.hmset(id_, r_obj)
        r.lpush('SOFIA-Queue', id_)
        response = {'ID': id_, 'Status': 'Processing'}
    else:
        response = read_text(text)
    return json.dumps(response)

@app.route('/process_query', methods=['POST'])
def process_query():
    '''
    Adds a query based reading task to the SOFIA-Queue.
    Adds the submission to Redis with key = id_
    '''
    obj = request.json
    text = obj['text']
    query = obj['query']
    print(text)
    print(query)
    if r:
        id_ = gen_id(text)
        r_obj = {'Status': 'Processing', 'Text': text, 'Query': ', '.join(query)}
        r.hmset(id_, r_obj)
        r.lpush('SOFIA-Queue', id_)    
        response = {'ID': id_, 'Status': 'Processing'}
    else:
        response = read_text(text)
    return json.dumps(response)

@app.route('/status', methods=['POST'])
def reading_status():
    '''
    Returns a JSON object which details the status of the reading for a 
    given ID. The status is either 'Processing' or 'Done'.
    '''
    obj = request.json
    id_ = obj['ID']
    print(id_)
    status = r.hget(id_, 'Status').decode('utf-8')
    response = {'ID': id_, 'Status': status}
    return json.dumps(response)

@app.route('/results', methods=['POST'])
def obtain_results():
    '''
    If reading is done for a given request, the results are provided.
    Otherwise, the status is provided. Once results are provided, the 
    time to live (TTL) for the object in Redis is set to 86400 seconds.
    If the results are requested again, the TTL is reset to this value.
    '''
    obj = request.json
    id_ = obj['ID']
    print(id_)
    status = r.hget(id_, 'Status').decode('utf-8')

    # if SOFIA is still processing text then return a status object
    if status == 'Processing':
        response = {'ID': id_, 'Status': status}
        return json.dumps(response)

    # otherwise, return reading results
    else:
        # obtain reading results
        response = r.hget(id_, 'Results').decode('utf-8')

        # Set TTL for Redis key = id_ to 1 day or 86400 seconds 
        r.expire(id_, 86400)
        return response

def gen_id(text):
    '''
    Generates a SHA1 as a SOFIA ID using the epoch timestamp
    of the request and the text itself
    '''
    ts = datetime.now().timestamp()
    concat = str(ts) + text
    concat_encoded = concat.encode('utf-8')
    id_ = sha1(concat_encoded).hexdigest()
    return id_

def read_text(text, query=None):
    '''
    Performs SOFIA reading on a given text (and optional) array of queries.
    '''
    if query:
        results = sofia.writeQueryBasedOutput(text, query)
    else:
        results = sofia.getOutputOnline(text)
    return results

def SOFIATask():
    '''
    Defines a task which will be scheduled with with the
    [Advanced Python Scheduler](https://apscheduler.readthedocs.io/en/latest/)
    which checks to see if any new text has entered the Redis SOFIA-Queue.
    Submissions are processed in FIFO order.
    '''
    if r.llen('SOFIA-Queue') > 0:
        print('Items found in queue.')
        id_ = r.rpop('SOFIA-Queue').decode('utf-8')
        print('Processing {}'.format(id_))
        if r.hexists(id_,'Query'):
            query = r.hget(id_, 'Query').decode('utf-8').split(',')
        else:
            query = None
        text = r.hget(id_, 'Text').decode('utf-8')
        results = read_text(text, query)
        r.hset(id_, 'Results', json.dumps(results))
        r.hset(id_, 'Status', 'Done')
        print('Finished processing {}'.format(id_))

@app.before_first_request
def initialize():
    '''
    Initializes the background scheduler and defines a recurring job.
    '''
    if r:
        apsched = BackgroundScheduler()
        apsched.add_job(SOFIATask, 'interval', seconds=5)
        apsched.start()

if __name__ == '__main__':  
   app.run()