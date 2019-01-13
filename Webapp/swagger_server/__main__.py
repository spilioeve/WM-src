#!/usr/bin/env python3

import connexion

from swagger_server import encoder

# Custom imports
from swagger_server.sofia_functions import initialize

def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'SOFIA REST API'})
    return app

application = main()    

if __name__ == '__main__':
    # initialize background SOFIATask
    initialize()

    # run application
    application.run(port=8080)


