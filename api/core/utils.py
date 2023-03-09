"""
Roon Service Utils
"""
import logging
import operator
import time
from functools import wraps, reduce

from django.db.models import base, Q
from django.http import QueryDict

LOGGER = logging.getLogger("roon")


def computed_model_keys(model, field_name_exclusions=(), field_type_exclusions=()):
    """
    Return a list of attributes associated with the Django model.
    """

    assert isinstance(model, base.ModelBase), "Class: {} must be a Django model class".format(model.__class__.name)
    assert isinstance(field_name_exclusions, list), "Field name exclusions: {} must be list".format(
        field_name_exclusions
    )
    assert isinstance(field_type_exclusions, list), "Field type exclusions: {} must be list".format(
        field_type_exclusions
    )

    # Do not include these fields types into the returned keys
    field_type_exclusions.extend(["ForeignKey", "OneToOneField", "AutoField"])

    return [
        f.name
        for f in model._meta.fields + model._meta.many_to_many
        if f.get_internal_type() not in field_type_exclusions and f.name not in field_name_exclusions
    ]


def model_search(params, qs=None, qs_objs=None, exclude=[]):
    """
    Generic function to build out custom search Q nodes

    IF qs_objs=None/False, this will return qs_objs ONLY
    ELSE a reduced 'AND` qs for in view search
    """
    from django.conf import settings

    q_objs = []

    # Need to convert values into a list
    # For Ex: {hf_id: [1,2,3, ...]}
    if isinstance(params, QueryDict):
        search_iterator = params.lists()
    else:
        search_iterator = params.items()

    for param, values in search_iterator:
        if not isinstance(values, list):
            values = [values]
        for val in values:
            filter_param = "__istartswith"  # Default search
            if param in settings.SEARCH_FILTERS + exclude:
                continue
            if isinstance(val, (bytes, str)):
                if val.startswith("^"):  # TODO: Remove, once FE's stop using this for startswith search
                    filter_param = "__istartswith"
                    val = val[1:]
                elif val.startswith("$"):
                    filter_param = "__icontains"
                    val = val[1:]
                elif val.upper() in ["NULL", "NONE"]:
                    filter_param = "__isnull"
                    val = True
            elif val is None:
                filter_param = "__isnull"
                val = True

            q_objs.append(Q(**{param + filter_param: val}))

    if qs_objs:
        return q_objs

    assert qs is not None, "qs needs to be provided"
    if q_objs:
        return qs.filter(reduce(operator.and_, q_objs))

    return qs


def get_and_pop_querydict_entry(key, params, default=None):
    """
    helper to get value for 'key' (default to None), then remove params[key] if found
    """
    value = params.get(key, default)
    if key in list(params.keys()):
        params.pop(key)
    return value


def remove_forbidden_data(source, *args):
    """
    Makes a copy of the source dict and then remove all keys in args.
    returns the filtered copy of dict.  The source dict is not changed.
    """

    assert isinstance(source, dict)
    filtered = source.copy()
    to_remove = []
    for key in args:
        if isinstance(key, list):
            to_remove.extend(key)
        else:
            to_remove.append(key)
    for key in to_remove:
        filtered.pop(key, None)
    return filtered


def retry_on_exception(exceptions=(Exception,), max_tries=10, sleep_ration=0.2):
    """ Function wrapper, repeats calling function in case of exception.
        To repeat function foo() in case of RuntimeError, use this syntax:

       @retry_on_exception(RuntimeError)
        def foo():
            print "Function foo()"
            raise RuntimeError("error")

       Mainly used to address this issue, but can be used for other purposes:
            https://github.com/boto/boto3/issues/220
    """

    def decorate(func):
        @wraps(func)
        def call(*args, **kwargs):
            for i in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as err:
                    if i < max_tries - 1:
                        LOGGER.error(
                            "RETRYING (%s): Executing method: %s " "with data: %s and with error: %s",
                            str(i + 1) + "/" + str(max_tries),
                            func.__name__,
                            kwargs,
                            err,
                        )
                        time.sleep(sleep_ration * i)
                    else:
                        raise

        return call

    return decorate


def extract_protocol_and_ip(request):
    """
    Get requesting users IP
    """

    protocol = request.META.get("HTTP_X_FORWARDED_PROTO")
    if protocol is None:
        protocol = "https" if request.is_secure() else "http"
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0] or request.META.get("REMOTE_ADDR")

    return protocol, ip
