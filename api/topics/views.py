import logging
from collections import OrderedDict

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.core.exceptions import MissingParameterException
from api.core.view_exception_handler import view_exception_handling
from api.questions.models import Question
from api.questions.serializers import QuestionOnlySerializer

LOGGER = logging.getLogger("roon")

FORBIDDEN_API_VALUES = settings.FORBIDDEN_API_VALUES


@view_exception_handling()
@api_view(["GET"])
def topics_root(request):
    """
    Default view for Questions root.
    """
    return Response(
        OrderedDict(
            (
                ("create", reverse("topics:create", request=request)),
                ("update", reverse("topics:update", request=request)),
                ("info", reverse("topics:info", request=request)),
                ("search", reverse("topics:search", request=request)),
            )
        )
    )


@view_exception_handling()
@api_view(["POST"])
# @permission_required("topics.topics_create", raise_exception=True)
def topics_create(request):
    """
    Please read documentation carefully.

    ### Creating a Question Topic ###

    ### NOT IMPLEMENTED ###
    """
    return Response({}, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["POST"])
# @permission_required("topics.topics_update", raise_exception=True)
def topics_update(request):
    """
    Please read documentation carefully.

    ### Updating a Question Topic ###

    ### NOT IMPLEMENTED ###
    """
    return Response({}, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["GET"])
# @permission_required("topics.topics_info", raise_exception=True)
def topics_info(request, topic_id=None):
    """
    Please read documentation carefully.

    ### Information on a Question Topic ###

    Retrieve information related to a **QuestionTopic** .

    ---
    ** VERSION **:

        V1

    ** RESPONSE_SERIALIZER **:

        QuestionOnlySerializer

    ** REQUIRED PARAMETERS **:

        - topic_id
    ---
    """
    if not topic_id:
        raise MissingParameterException("topic_id is required")

    questions = QuestionOnlySerializer.setup_eager_loading(Question.active_objects.all())
    questions = questions.filter(topics__topic_id=topic_id)
    serializer = QuestionOnlySerializer(questions, many=True)

    return Response(serializer.data, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["GET"])
# @permission_required("hl7_messages.hl7_messages_search", raise_exception=True)
def topics_search(request):
    """
    Please read documentation carefully.

    ### Search for a Question Topic ###

    Search information related to a **QuestionTopic** .

    ### NOT IMPLEMENTED ###
    """
    return Response({}, status.HTTP_200_OK)
