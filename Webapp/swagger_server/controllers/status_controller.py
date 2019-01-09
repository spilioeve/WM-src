import connexion
import six

from swagger_server.models.id import ID  # noqa: E501
from swagger_server.models.process_response import ProcessResponse  # noqa: E501
from swagger_server import util
from swagger_server.sofia_functions import _reading_status
from swagger_server.security import requires_auth


@requires_auth
def status(body):  # noqa: E501
    """Submit ID and receive reading status for request

    Submit an object containing the key &#x60;ID&#x60; whose value is the ID returned by a &#x60;process&#x60; request. Receive the status for this reading request. # noqa: E501

    :param body: An &#x60;ID&#x60; object.
    :type body: dict | bytes

    :rtype: ProcessResponse
    """
    if connexion.request.is_json:
        body = ID.from_dict(connexion.request.get_json())  # noqa: E501
        resp = _reading_status(body.id)
        return resp
