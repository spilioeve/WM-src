import flask
import configparser
from functools import wraps

config = configparser.ConfigParser()
config.read('config.ini')


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    _username = config['SOFIA']['BASIC_AUTH_USERNAME']
    _password = config['SOFIA']['BASIC_AUTH_PASSWORD']
    return username == _username and password == _password


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return flask.Response('You have to login with proper credentials', 401,
                          {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = flask.request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated