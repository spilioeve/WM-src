# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "swagger_server"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="SOFIA REST API",
    author_email="",
    url="",
    keywords=["Swagger", "SOFIA REST API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['swagger_server=swagger_server.__main__:main']},
    long_description="""\
    This API specification is for the SOFIA Reading System. SOFIA is an Information Extraction system that currently detects Causal Relationships explicitly mentioned in the same sentence. SOFIA is built based upon prominent Linguistic Theories that view Causality as a discourse relation between two Eventualities. Following this approach, SOFIA extracts three major classes of information: Entities, Events and Relations. All those classes are important in order to build a coherent model that captures the semantics of a sentence.
    """
)

