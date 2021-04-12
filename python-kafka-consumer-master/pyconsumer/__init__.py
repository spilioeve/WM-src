import os
import json
try:
    # python 3.7+
    import importlib.ressources as config_loader
except ImportError:
    # python <= 3.6
    import importlib_resources as config_loader


# get the configuration
config_name = os.environ.get('PROGRAM_ARGS', 'wm-sasl-example.json')
if not config_loader.is_resource('pyconsumer.resources.env', config_name):
    if not config_name.endswith('.json'):
        config_name += '.json'

config = json.loads(
    config_loader.read_text('pyconsumer.resources.env', config_name)
)
