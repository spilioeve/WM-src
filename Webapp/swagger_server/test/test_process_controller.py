# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.process_response import ProcessResponse  # noqa: E501
from swagger_server.models.text import Text  # noqa: E501
from swagger_server.models.text_query import TextQuery  # noqa: E501
from swagger_server.test import BaseTestCase


class TestProcessController(BaseTestCase):
    """ProcessController integration test stubs"""

    def test_process_query(self):
        """Test case for process_query

        Submit text and queries for query-based reading
        """
        body = TextQuery()
        response = self.client.open(
            '//process_query',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_process_text(self):
        """Test case for process_text

        Submit text for reading
        """
        body = Text()
        response = self.client.open(
            '//process_text',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
