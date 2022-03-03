FROM centos:7

ENV LANG en_US.utf8
ENV LC_ALL en_US.utf8
ENV CORENLP_HOME /opt/app/pkg/corenlp

RUN yum upgrade -y

RUN yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
    yum install -y net-tools which python3 enchant java-1.8.0-openjdk && \
    python3 -m ensurepip --default-pip && \
    yum clean all && \
    rm -r -f /var/cache/yum && \
    mkdir -p /opt/app/{bin,conf,data,pkg,tmp}

COPY distro/stanford-corenlp-4.2.0.zip /opt/app/pkg

RUN yum install -y unzip && \
    unzip /opt/app/pkg/stanford-corenlp-4.2.0.zip -d /opt/app/pkg/ && \
    mv /opt/app/pkg/stanford-corenlp-4.2.0 $CORENLP_HOME && \
    rm /opt/app/pkg/*.zip && \
    chmod -R u+x $CORENLP_HOME


COPY requirements.txt /opt/app/tmp/
RUN pip3 install -r /opt/app/tmp/requirements.txt && \
    python3 -m nltk.downloader punkt

COPY . /opt/app/bin
RUN chmod -R u+x /opt/app/bin && \
    cd /opt/app/bin

COPY ontologies/* /opt/app/conf/

ENTRYPOINT /opt/app/bin/sofia-stream.py worker
