from collections import OrderedDict

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


###
# Roots
###

@api_view(("GET",))
def root(request):
    """Default view for the Roon service root (/)."""
    return Response(
        OrderedDict(
            (
                ("heartbeat", reverse("heartbeat", request=request)),
                ("api", reverse("api_root", request=request)),
            ))
    )


@api_view(("GET",))
def api_root(request, format=None):
    """
    Default view for the PHI service API root (/api/v1).
    """

    # Using OrderedDict to fix URL positioning
    urls = OrderedDict(
        (
            ("answers", reverse("answers:root", request=request, format=format)),
            ("questions", reverse("questions:root", request=request, format=format)),
            ("topics", reverse("topics:root", request=request, format=format)),
        )
    )

    return Response(urls)


@api_view(("GET",))
@permission_classes((AllowAny,))
def heartbeat(request):
    """
    Basic healthcheck view

    * If `system_version` provided, the system_version will be returned in the payload
    """
    if request.query_params.get('system_version'):
        return Response({"success": True, "system_version": settings.SYSTEM_VERSION}, status=status.HTTP_200_OK)
    return Response({"success": True}, status=status.HTTP_200_OK)
