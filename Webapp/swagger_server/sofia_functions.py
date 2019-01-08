from sofia import SOFIA
import json
import redis
from hashlib import sha1
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import configparser
import logging


config = configparser.ConfigParser()
config.read('config.ini')

if config['SOFIA']['DEBUG']:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Initialize Redis connection (if applicable)
if config['SOFIA']['REDIS'] == 'True':
    r = redis.Redis(host=config['SOFIA']['REDIS_HOST'],
                    port=config['SOFIA']['REDIS_PORT'],
                    db=config['SOFIA']['REDIS_DB'])
    logging.info('Using Redis')
else:
    r = None
    logging.info('Not using Redis')

# Initialize sofia
sofia = SOFIA(CoreNLP=config['SOFIA']['CORENLP'])    

def _process_text(text):
    '''
    Adds a reading task to the SOFIA-Queue.
    Adds the submission to Redis with key = id_
    '''    
    logging.debug(text)
    if r:
        id_ = gen_id(text)
        r_obj = {'Status': 'Processing', 'Text': text}
        r.hmset(id_, r_obj)
        r.lpush('SOFIA-Queue', id_)
        response = {'ID': id_, 'Status': 'Processing'}
    else:
        response = read_text(text)
    return response

def _process_query(request):
    '''
    Adds a query based reading task to the SOFIA-Queue.
    Adds the submission to Redis with key = id_
    '''
    obj = request.json
    text = obj['text']
    query = obj['query']
    logging.debug(text)
    logging.debug(query)
    if r:
        id_ = gen_id(text)
        r_obj = {'Status': 'Processing', 'Text': text, 'Query': ', '.join(query)}
        r.hmset(id_, r_obj)
        r.lpush('SOFIA-Queue', id_)    
        response = {'ID': id_, 'Status': 'Processing'}
    else:
        response = read_text(text)
    return json.dumps(response)

def _reading_status(request):
    '''
    Returns a JSON object which details the status of the reading for a 
    given ID. The status is either 'Processing' or 'Done'.
    '''
    if r:
        obj = request.json
        id_ = obj['ID']
        logging.info(id_)
        status = r.hget(id_, 'Status').decode('utf-8')
        response = {'ID': id_, 'Status': status}
        return json.dumps(response)
    else:
        return 'Endpoint not supported.'

def _obtain_results(request):
    '''
    If reading is done for a given request, the results are provided.
    Otherwise, the status is provided. Once results are provided, the 
    time to live (TTL) for the object in Redis is reset to 86400 seconds.
    If the results are requested again, the TTL is reset to this value.
    So, if a user requests the results once per day, the results will be 
    held by Redis indefinitely. Otherwise, they should normally expire after 
    24 hours of being requested.
    '''
    if r:
        obj = request.json
        id_ = obj['ID']
        logging.info(id_)
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
    else:
        return 'Endpoint not supported.'

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
        logging.info('Items found in queue.')
        id_ = r.rpop('SOFIA-Queue').decode('utf-8')
        logging.info('Processing {}'.format(id_))
        if r.hexists(id_,'Query'):
            query = r.hget(id_, 'Query').decode('utf-8').split(',')
        else:
            query = None
        text = r.hget(id_, 'Text').decode('utf-8')
        results = read_text(text, query)
        r.hset(id_, 'Results', json.dumps(results))
        r.hset(id_, 'Status', 'Done')
        logging.info('Finished processing {}'.format(id_))
        r.expire(id_, app.config['SOFIA']['REDIS_TTL'])

def initialize():
    '''
    Initializes the background scheduler and defines a recurring job.
    '''
    if r:
        apsched = BackgroundScheduler()
        apsched.add_job(SOFIATask, 'interval', seconds=5)
        apsched.start()