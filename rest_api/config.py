# Configuration file for `REST_API.py`

# Set to True for enhanced logging
DEBUG = False 

# Set to true to use Redis (per specified configuration)
REDIS = False

# Set the default number of seconds results should be 
# stored by Redis (604800 is equivalent to 7 days)
REDIS_TTL = 604800

# Specify Redis Instance (ignored if app.config['REDIS'] == False)
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Set to local unzipped CoreNLP Path
CORENLP = 'PATH_TO_CORENLP'

BASIC_AUTH_USERNAME = 'TESTUSER'
BASIC_AUTH_PASSWORD = 'TESTPASSWORD'