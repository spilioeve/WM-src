import connexion
import six

from swagger_server.models.id import ID  # noqa: E501
from swagger_server.models.results import Results  # noqa: E501
from swagger_server import util


def results(body):  # noqa: E501
    """Submit ID and receive reading results for request

    Submit an object containing the key &#x60;ID&#x60; whose value is the ID returned by a &#x60;process&#x60; request. Receive the results for this reading request if the reading is &#x60;Done&#x60;. # noqa: E501

    :param body: An &#x60;ID&#x60; object.
    :type body: dict | bytes

    :rtype: Results
    """
    if connexion.request.is_json:
        body = ID.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
