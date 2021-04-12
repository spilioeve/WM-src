FROM lnk2past/centos-python3:latest

LABEL maintainer="nicholas.sanchirico@twosixlabs.com"

USER root

ADD requirements.txt /

RUN python -m pip install -r requirements.txt

ADD pyconsumer /pyconsumer

ENTRYPOINT python -m pyconsumer worker -l info
