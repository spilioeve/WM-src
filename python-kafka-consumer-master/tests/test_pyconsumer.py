import os
os.environ['PROGRAM_ARGS'] = 'test.json'
import pathlib
import typing
import pytest
import faust
from pyconsumer.app import create_app


app = create_app()


SAMPLE_MESSAGE = {"key": "test1", "value": ["python-kafka-consumer"]}


@pytest.fixture()
def basic_stream_processor(event_loop):
    """passing in event_loop helps avoid 'attached to a different loop' error"""
    app.finalize()
    app.conf.store = 'memory://'
    app.flow_control.resume()
    return app


@pytest.mark.asyncio()
@pytest.mark.usefixtures('basic_stream_processor')
async def test_event_update(mocker, basic_stream_processor):
    async with basic_stream_processor.agents['pyconsumer.streams.agents.stream_out'].test_context() as agent:
        await agent.put(key='sample', value=SAMPLE_MESSAGE)
        testfile = pathlib.Path('sample.txt')
        assert testfile.exists()
        assert testfile.read_text() == '''{"key": "test1", "value": ["python-kafka-consumer"]}'''
