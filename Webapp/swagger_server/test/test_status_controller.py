# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.id import ID  # noqa: E501
from swagger_server.models.process_response import ProcessResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestStatusController(BaseTestCase):
    """StatusController integration test stubs"""

    def test_status(self):
        """Test case for status

        Submit ID and receive reading status for request
        """
        body = ID()
        response = self.client.open(
            '//status',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
