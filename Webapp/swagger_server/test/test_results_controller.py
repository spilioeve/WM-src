# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.id import ID  # noqa: E501
from swagger_server.models.results import Results  # noqa: E501
from swagger_server.test import BaseTestCase


class TestResultsController(BaseTestCase):
    """ResultsController integration test stubs"""

    def test_results(self):
        """Test case for results

        Submit ID and receive reading results for request
        """
        body = ID()
        response = self.client.open(
            '//results',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
