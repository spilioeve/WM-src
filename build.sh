#!/bin/bash

CORENLP_DOWNLOAD=http://nlp.stanford.edu/software/stanford-corenlp-4.2.0.zip
CORENLP_DIST=./distro/stanford-corenlp-4.2.0.zip

if [ -f $CORENLP_DIST ]; then
  echo 'using cached CoreNLP package'
else
    echo "no CoreNLP distro, downloading: $CORENLP_DOWNLOAD"
    mkdir -p distro
    curl -L -o ./distro/stanford-corenlp-4.2.0.zip $CORENLP_DOWNLOAD
fi

docker build -t sofia:march2022 .
