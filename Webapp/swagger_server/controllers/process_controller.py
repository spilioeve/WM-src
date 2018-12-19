import connexion
import six

from swagger_server.models.process_response import ProcessResponse  # noqa: E501
from swagger_server.models.text import Text  # noqa: E501
from swagger_server.models.text_query import TextQuery  # noqa: E501
from swagger_server import util


def process_query(body):  # noqa: E501
    """Submit text and queries for query-based reading

    Submit an object containing the key &#x60;text&#x60; whose value is the text to be processed by SOFIA. The object should also contain the key &#x60;query&#x60; which should be an array of queries to be used for query-based reading. # noqa: E501

    :param body: An object containing &#x60;text&#x60; and &#x60;query&#x60;.
    :type body: dict | bytes

    :rtype: ProcessResponse
    """
    if connexion.request.is_json:
        body = TextQuery.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def process_text(body):  # noqa: E501
    """Submit text for reading

    Submit an object containing the key &#x60;text&#x60; whose value is the text to be processed by SOFIA. # noqa: E501

    :param body: A &#x60;text&#x60; object.
    :type body: dict | bytes

    :rtype: ProcessResponse
    """
    if connexion.request.is_json:
        body = Text.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
