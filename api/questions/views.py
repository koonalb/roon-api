import logging
from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.core.exceptions import MissingParameterException
from api.core.models import date_search, search_with_operator
from api.core.utils import remove_forbidden_data, model_search
from api.core.view_exception_handler import view_exception_handling
from api.questions.models import Question
from core.serializer import PaginationSerializer
from questions.serializers import QuestionSerializer

LOGGER = logging.getLogger("roon")

FORBIDDEN_API_VALUES = settings.FORBIDDEN_API_VALUES


@view_exception_handling()
@api_view(["GET"])
def questions_root(request):
    """
    Default view for Questions root.
    """
    return Response(
        OrderedDict(
            (
                ("create", reverse("questions:create", request=request)),
                ("update", reverse("questions:update", request=request)),
                ("info", reverse("questions:info", request=request)),
                ("search", reverse("questions:search", request=request)),
            )
        )
    )


@view_exception_handling()
@api_view(["POST"])
# @permission_required("questions.questions_create", raise_exception=True)
def questions_create(request):
    """
    Please read documentation carefully.

    ### Creating Questions ###

    ---
    ** VERSION **:

        V1

    ** RESPONSE_SERIALIZER **:

        QuestionSerializer

    ** REQUIRED PARAMETERS **:

        - title (str)

    ** FORBIDDEN CREATE PARAMETERS **:

        - owner
        - created_at
        - last_modified
        - deactivated_at
        - is_active

    ** OPTIONAL PARAMETERS **:

        - context (str)
        - topics (array[dict[str, str]])
            - Ex: [{"title": "treatment"}, {"title": "something else"}]
    ---
    """
    context = None

    if not {
        "title",
    }.issubset(set(request.data.keys())):
        raise MissingParameterException("Questions require title and context")

    params = remove_forbidden_data(
        request.data,
        [
            "owner",
        ],
        FORBIDDEN_API_VALUES,
    )

    serializer = QuestionSerializer(data=params, context=context)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    serializer.save(owner=request.user)

    return Response(serializer.data, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["POST"])
# @permission_required("questions.questions_update", raise_exception=True)
def questions_update(request):
    """
    Please read documentation carefully.

    ### Updating a Question ###

    ### NOT IMPLEMENTED ###
    """
    return Response({}, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["GET"])
# @permission_required("questions.questions_info", raise_exception=True)
def questions_info(request, question_id=None):
    """
    Please read documentation carefully.

    ### Information on a Question ###

    Retrieve information related to a **Question** .

    ---
    ** VERSION **:

        V1

    ** RESPONSE_SERIALIZER **:

        QuestionSerializer

    ** REQUIRED PARAMETERS **:

        - question_id
    ---
    """
    if not question_id:
        raise MissingParameterException("question_id is required")

    question = QuestionSerializer.setup_eager_loading(Question.active_objects.all())
    question = question.get(question_id=question_id)
    serializer = QuestionSerializer(question)

    return Response(serializer.data, status.HTTP_200_OK)


@view_exception_handling()
@api_view(["GET"])
# @permission_required("questions.questions_search", raise_exception=True)
def questions_search(request):
    """
    Please read documentation carefully.

    ### Search for Questions ###

    Search information related to a **Question**.

    All search params are insensitive startswith

    When `page` and `per_page` are not provided:

     * Only 100 cases are returned on page 1

    If `page` is only provided:

     * 100 cases are returned on that `page`

    If `per_page` is only provided:

     * Then those number of cases are returned on `page` 1

    Otherwise:

     * `page` and `per_page` data will be used

    ** DATE SEARCH PARAMETERS **:

        - name: desired_attribute_date_start
        - format: YYYY-MM-DDTH:M:S OR iso format
        - name: desired_attribute_date_end
        - format: YYYY-MM-DDTH:M:S OR iso format

        -EX: ?created_at_date_start=2020-01-01T00:00:00&created_at_date_end=2025-01-01T00:00:00

    ---
    ** VERSION **:

        V1

    ** RESPONSE_SERIALIZER **:

        QuestionSerializer

    ___
    """
    params = request.query_params
    questions = QuestionSerializer.setup_eager_loading(Question.active_objects.all())

    # Date search
    questions, params = date_search(questions, params)

    # Operator search
    if "operator" in list(params.keys()):
        questions = search_with_operator(questions, params)
    else:
        questions = model_search(params, qs=questions)

    # Sort results
    questions = questions.order_by(params.get("order_by", "-created_at"))

    # Get total per search params
    questions_total = questions.count()

    # Paginate results
    try:
        page = params.get("page", 1)
        per_page = params.get("per_page", 100)

        paginator = Paginator(questions, per_page)
        questions = paginator.page(page)
    except EmptyPage:
        questions = Question.objects.none()
    except (ValueError, PageNotAnInteger):
        raise PageNotAnInteger("Invalid value, per_page/page are integers only.")

    serializer = QuestionSerializer(questions, many=True)
    pagination_serializer = PaginationSerializer(
        data={"page": page, "page_count": len(serializer.data), "total_count": questions_total}
    )
    pagination_serializer.is_valid()
    return Response({"pagination_info": pagination_serializer.data, "questions": serializer.data})
