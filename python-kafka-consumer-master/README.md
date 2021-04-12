# python-kafka-consumer

[![Build Status](https://github.com/twosixlabs-dart/python-kafka-consumer/workflows/Build/badge.svg)](https://github.com/twosixlabs-dart/python-kafka-consumer/actions)

## What Is This?

This project contains an example for working with Kafka Streams via the [`Faust`](https://faust.readthedocs.io) library. This particular project contains a simple read-only consumer implementation. The full suite of projects are the following:

- [Producer](https://github.com/twosixlabs-dart/python-kafka-producer)
- [Stream Processor](https://github.com/twosixlabs-dart/python-kafka-streams)
- [Consumer](https://github.com/twosixlabs-dart/python-kafka-consumer) (this project)
- [Environment](https://github.com/twosixlabs-dart/kafka-examples-docker)

The *consumer* in this example is an agent that subscribes to some topic using SSL/SASL to consume and record events. When it receives an event it dumps the payload to a file. That is it!

## Getting Started

Getting started with this example requires a complete Kafka environment. [This project](https://github.com/twosixlabs-dart/kafka-examples-docker) contains a docker-compose file for setting up everything. You can use the configuration inputs to connect to a preexisting infrastructure if you have one already.

If you do not have a Python installation ready, you can configure the input and then build the Dockerfile and run the resulting image with:

```shell
docker build -t python-kafka-consumer-local .
docker run --env PROGRAM_ARGS=wm-sasl-example -it python-kafka-consumer-local:latest 
```

### Configuration File & SASL/SSL

The code here is configured to use JSON resources found at the subpackage `pyconsumer.resources.env`. Your configuration must be found within the [pyconsumer/resources/env](pyconsumer/resources/env) directory. When specifying your own you may omit the `.json` extension; it will attempt to load it as it and if that fails will attempt to load it assuming a `.json` extension. The default is to point to the [wm-sasl-example](/pyconsumer/resources/env/wm-sasl-example.json) configuration (which contains mostly nothing). Here is the expected format of the input file:

```json
{
    "broker": "",
    "auth": {
        "username": "",
        "password": ""
    },
    "app": {
        "id": "",
        "auto_offset_reset": "",
        "enable_auto_commit": false
    },
    "topic": {
        "from": ""
    },
    "persist_dir": ""
}
```

* `broker` - the hostname + port of the Kafka broker
* `auth`
  * `username` - username for SASL authentication
  * `password` - password for SASL authentication
* `app`
  * `id` - unique identifier for your application/group
  * `auto_offset_reset` - set to either `earliest` or `latest` to determine where a *new* app should start consuming from
  * `enable_auto_commit` - set to true to commit completed processing records
* `topic`
  * `from` - topic to consume from; currently only a single topic may be specified
* `persist_dir` - unique to this example, this is used during processing for dumping received records to disk.

These options are subject to change/refinement, and others may be introduced in the future.
