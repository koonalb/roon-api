import logging
from collections import OrderedDict

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.core.view_exception_handler import view_exception_handling

LOGGER = logging.getLogger("roon")


@view_exception_handling()
@api_view(["GET"])
def answers_root(request):
    """
    Default view for Questions root.
    """
    return Response(
        OrderedDict(
            (
                ("create", reverse("answers:create", request=request)),
                ("update", reverse("answers:update", request=request)),
                ("info", reverse("answers:info", request=request)),
                ("search", reverse("answers:search", request=request)),
            )
        )
    )


@view_exception_handling()
@api_view(["POST"])
# @permission_required("answers.answers_create", raise_exception=True)
def answers_create(request):
    """
    Please read documentation carefully.

    ### Creating an Answer ###

    ### NOT IMPLEMENTED ###
    """
    return Response({}, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["POST"])
# @permission_required("answers.answers_update", raise_exception=True)
def answers_update(request):
    """
    Please read documentation carefully.

    ### Updating an Answer ###

    ### NOT IMPLEMENTED ###
    """
    return Response({}, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["GET"])
# @permission_required("answers.answers_info", raise_exception=True)
def answers_info(request, answer_id=None):
    """
    Please read documentation carefully.

    ### Information on an Answer ###

    Retrieve information related to an **Answer** .

    ### NOT IMPLEMENTED ###
    """
    return Response({}, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["GET"])
# @permission_required("answers.answers_search", raise_exception=True)
def answers_search(request):
    """
    Please read documentation carefully.

    ### Search for an Answer ###

    Search information related to an **Answer** .

    ### NOT IMPLEMENTED ###
    """
    return Response({}, status.HTTP_200_OK)
